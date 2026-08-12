import re
import struct
import zipfile

import lib.build_3mf as build_3mf
from lib.build_3mf import _parse_binary_stl, _to_rgba, export_3mf


# --- _to_rgba ---

def test_rgb_gets_opaque_alpha_and_uppercase():
    assert _to_rgba("#ff6600") == "#FF6600FF"


def test_rgba_passes_through():
    assert _to_rgba("#ff6600aa") == "#FF6600AA"


def test_missing_hash_is_added():
    assert _to_rgba("ff6600") == "#FF6600FF"


# --- _parse_binary_stl ---

def _binary_stl(triangles: list[tuple]) -> bytes:
    data = b"\0" * 80 + struct.pack("<I", len(triangles))
    for tri in triangles:
        data += struct.pack("<fff", 0, 0, 0)  # normal
        for v in tri:
            data += struct.pack("<fff", *v)
        data += struct.pack("<H", 0)  # attribute byte count
    return data


def test_parse_stl_dedups_shared_vertices():
    v0, v1, v2, v3 = (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)
    data = _binary_stl([(v0, v1, v2), (v1, v2, v3)])
    vertices, triangles = _parse_binary_stl(data)
    assert len(vertices) == 4
    assert triangles == [[0, 1, 2], [1, 2, 3]]


def test_parse_stl_empty():
    vertices, triangles = _parse_binary_stl(_binary_stl([]))
    assert vertices == []
    assert triangles == []


# --- export_3mf colorgroup assembly (geometry stubbed out) ---

def _fake_shape_to_xml(shape, obj_id, name, pid, pindex):
    return f'<object id="{obj_id}" name="{name}" pid="{pid}" pindex="{pindex}"/>'


def _read_model(path) -> str:
    with zipfile.ZipFile(path) as zf:
        return zf.read("3D/3dmodel.model").decode()


def test_colorgroup_dedups_colors_preserving_order(monkeypatch, tmp_path):
    monkeypatch.setattr(build_3mf, "_shape_to_xml", _fake_shape_to_xml)
    out = tmp_path / "out.3mf"
    export_3mf(
        [
            [(object(), "label1_base", "#112233"), (object(), "label1_text", "#AABBCC")],
            [(object(), "label2_base", "#112233")],
        ],
        str(out),
    )
    model = _read_model(out)
    colors = re.findall(r'<m:color color="([^"]+)"/>', model)
    assert colors == ["#112233FF", "#AABBCCFF"]
    # Mesh objects keep their color hints (pid/pindex) unchanged; the third
    # reuses the first color's index.
    assert '<object id="2" name="label1_base" pid="1" pindex="0"/>' in model
    assert '<object id="3" name="label1_text" pid="1" pindex="1"/>' in model
    assert '<object id="4" name="label2_base" pid="1" pindex="0"/>' in model


def test_each_label_is_one_grouped_object_with_components(monkeypatch, tmp_path):
    monkeypatch.setattr(build_3mf, "_shape_to_xml", _fake_shape_to_xml)
    out = tmp_path / "out.3mf"
    export_3mf(
        [
            [(object(), "label1_base", "#112233"), (object(), "label1_text", "#AABBCC")],
            [(object(), "label2_base", "#112233")],
        ],
        str(out),
    )
    model = _read_model(out)
    # Mesh ids are 2,3,4; container objects follow (5,6), each grouping one
    # label's parts via <components>.
    assert re.search(
        r'<object id="5" type="model">\s*<components>\s*'
        r'<component objectid="2"/>\s*<component objectid="3"/>\s*'
        r'</components>\s*</object>',
        model,
    )
    assert re.search(
        r'<object id="6" type="model">\s*<components>\s*'
        r'<component objectid="4"/>\s*</components>\s*</object>',
        model,
    )
    # Only the containers are built — never the individual meshes.
    assert re.findall(r'<item objectid="(\d+)"/>', model) == ["5", "6"]


def test_export_without_colors_omits_colorgroup(monkeypatch, tmp_path):
    monkeypatch.setattr(build_3mf, "_shape_to_xml", _fake_shape_to_xml)
    out = tmp_path / "out.3mf"
    export_3mf([[(object(), "base", None)]], str(out))
    model = _read_model(out)
    assert "<m:colorgroup" not in model
    # Mesh id 2, container id 3 is the one placed in the build.
    assert '<item objectid="3"/>' in model
    assert '<item objectid="2"/>' not in model


def test_zip_contains_required_members(monkeypatch, tmp_path):
    monkeypatch.setattr(build_3mf, "_shape_to_xml", _fake_shape_to_xml)
    out = tmp_path / "out.3mf"
    export_3mf([[(object(), "base", "#000000")]], str(out))
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert {"[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"} <= names
