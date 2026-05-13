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


def _shape_to_xml(shape: Shape, obj_id: int, name: str, pid: int | None = None, pindex: int | None = None) -> str:
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
    color_attrs = f' pid="{pid}" pindex="{pindex}"' if pid is not None else ""
    return f"""\
    <object id="{obj_id}" name="{name}" type="model"{color_attrs}>
      <mesh>
        <vertices>
        {verts}
        </vertices>
        <triangles>
        {tris}
        </triangles>
      </mesh>
    </object>"""


def export_3mf(shapes: list[tuple[Shape, str, str | None]], output_path: str) -> None:
    """Write a 3MF file with one component per (shape, name, color) tuple.

    color is an optional hex string like '#FFFFFF'. When any color is provided,
    a colorgroup is written using the 3MF Materials extension.
    """
    unique_colors = list(dict.fromkeys(c for _, _, c in shapes if c is not None))
    has_colors = bool(unique_colors)
    color_index = {c: i for i, c in enumerate(unique_colors)}

    # colorgroup occupies id=1 when present; objects start after it
    id_offset = 2 if has_colors else 1

    objects_xml_parts = []
    for idx, (shape, name, color) in enumerate(shapes):
        pid = pindex = None
        if has_colors and color is not None:
            pid, pindex = 1, color_index[color]
        objects_xml_parts.append(_shape_to_xml(shape, idx + id_offset, name, pid, pindex))

    objects_xml = "\n".join(objects_xml_parts)
    items_xml = "\n  ".join(
        f'<item objectid="{idx + id_offset}"/>' for idx in range(len(shapes))
    )

    xmlns_m = ""
    colorgroup_xml = ""
    if has_colors:
        xmlns_m = '\n  xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02"'
        color_entries = "\n      ".join(f'<m:color color="{c}"/>' for c in unique_colors)
        colorgroup_xml = f'    <m:colorgroup id="1">\n      {color_entries}\n    </m:colorgroup>\n'

    model = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
  xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"{xmlns_m}>
  <resources>
{colorgroup_xml}{objects_xml}
  </resources>
  <build>
  {items_xml}
  </build>
</model>"""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("3D/3dmodel.model", model)
