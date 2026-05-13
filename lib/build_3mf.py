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

_MATERIALS_NS = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"


def _to_rgba(color: str) -> str:
    """Normalise a hex color to #RRGGBBAA (fully opaque if no alpha given)."""
    h = color.lstrip("#")
    if len(h) == 6:
        h += "FF"
    return "#" + h.upper()


def _parse_binary_stl(data: bytes):
    num_triangles = struct.unpack_from("<I", data, 80)[0]
    vertices = []
    triangles = []
    vertex_index: dict[tuple, int] = {}

    for i in range(num_triangles):
        offset = 84 + i * 50 + 12  # skip header(80) + count(4) + normal(12)
        tri = []
        for j in range(3):
            v = struct.unpack_from("<fff", data, offset + j * 12)
            if v not in vertex_index:
                vertex_index[v] = len(vertices)
                vertices.append(v)
            tri.append(vertex_index[v])
        triangles.append(tri)

    return vertices, triangles


def _shape_to_xml(shape: Shape, obj_id: int, name: str, pid: int | None, pindex: int | None) -> str:
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
    mat_attrs = f' pid="{pid}" pindex="{pindex}"' if pid is not None else ""
    return f"""\
    <object id="{obj_id}" name="{name}" type="model"{mat_attrs}>
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

    Colors are collected into a single m:colorgroup resource so Bambu Studio /
    OrcaSlicer can map each distinct color to a filament via the standard 3MF
    color-parsing dialog.  Two shapes sharing the same hex color string get the
    same pindex and will be assigned to the same filament slot.
    """
    # Deduplicate colours in order of first appearance.
    color_order: list[str] = []
    color_index: dict[str, int] = {}
    for _, name, color in shapes:
        if color is not None and color not in color_index:
            color_index[color] = len(color_order)
            color_order.append(color)

    # Build the m:colorgroup resource (id=1).
    colorgroup_xml = ""
    if color_order:
        entries = "\n      ".join(
            f'<m:color name="filament{i + 1}" color="{_to_rgba(c)}"/>'
            for i, c in enumerate(color_order)
        )
        colorgroup_xml = f'    <m:colorgroup id="1">\n      {entries}\n    </m:colorgroup>\n'

    # Objects start at id=2 (id=1 is the colorgroup).
    obj_id_start = 2
    objects_xml = "\n".join(
        _shape_to_xml(
            shape, obj_id_start + i, name,
            pid=1 if color is not None else None,
            pindex=color_index.get(color) if color is not None else None,
        )
        for i, (shape, name, color) in enumerate(shapes)
    )
    items_xml = "\n  ".join(
        f'<item objectid="{obj_id_start + i}"/>' for i in range(len(shapes))
    )

    model = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
  xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
  xmlns:m="{_MATERIALS_NS}">
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
