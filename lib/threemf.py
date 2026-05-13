"""Assemble a multi-component 3MF file from build123d Shape objects."""
import struct
import tempfile
import zipfile

from build123d import Shape, export_stl

_CONTENT_TYPES = """\
<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""

_RELS = """\
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0"
    Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""


def _parse_binary_stl(data: bytes):
    num_triangles = struct.unpack_from("<I", data, 80)[0]
    vertices = []
    triangles = []
    vertex_index: dict[tuple, int] = {}

    for i in range(num_triangles):
        base = 84 + i * 50 + 12  # skip header(80) + count(4) + normal(12)
        tri = []
        for j in range(3):
            v = struct.unpack_from("<fff", data, base + j * 12)
            if v not in vertex_index:
                vertex_index[v] = len(vertices)
                vertices.append(v)
            tri.append(vertex_index[v])
        triangles.append(tri)

    return vertices, triangles


def _shape_to_xml(shape: Shape, obj_id: int, name: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
        tmp = f.name
    export_stl(shape, tmp)
    with open(tmp, "rb") as f:
        data = f.read()

    vertices, triangles = _parse_binary_stl(data)

    verts = "\n        ".join(
        f'<vertex x="{v[0]:.6f}" y="{v[1]:.6f}" z="{v[2]:.6f}"/>' for v in vertices
    )
    tris = "\n        ".join(
        f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>' for t in triangles
    )
    return f"""\
    <object id="{obj_id}" name="{name}" type="model">
      <mesh>
        <vertices>
        {verts}
        </vertices>
        <triangles>
        {tris}
        </triangles>
      </mesh>
    </object>"""


def export_3mf(shapes: list[tuple[Shape, str]], output_path: str) -> None:
    """Write a 3MF file with one component per (shape, name) pair."""
    objects_xml = "\n".join(
        _shape_to_xml(shape, idx + 1, name)
        for idx, (shape, name) in enumerate(shapes)
    )
    items_xml = "\n  ".join(
        f'<item objectid="{idx + 1}"/>' for idx in range(len(shapes))
    )
    model = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
  xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
{objects_xml}
  </resources>
  <build>
  {items_xml}
  </build>
</model>"""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("3D/3dmodel.model", model)
