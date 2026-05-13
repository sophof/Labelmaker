from build123d import Align, Axis, BuildPart, BuildSketch, Location, Locations, Plane, Rectangle, Text, Vector, export_stl, extrude

from ._label_utils import BASE_PARAMS, DIVIDER_CLEARANCE, DIVIDER_WIDTH, TEXT_PARAMS, build_base, divider_positions, iter_text_blocks
from lib.build_3mf import export_3mf

STYLE_ID = "label"
STYLE_NAME = "Label"

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4

PARAMS = {
    "text_style": {
        "type": "str",
        "default": "debossed",
        "label": "Text style",
        "options": ["embossed", "debossed", "debossed-open"],
    },
    **TEXT_PARAMS,
    **BASE_PARAMS,
}


def build(text: str, params: dict, tmf_path: str, base_stl_path: str,
          text_stl_path: str | None = None, base_color: str = "#FFFFFF", text_color: str = "#000000") -> list[str]:
    style = params.get("text_style", "debossed")
    if style == "embossed":
        return _build_embossed(text, params, tmf_path, base_stl_path, text_stl_path, base_color, text_color)
    elif style == "debossed":
        return _build_debossed(text, params, tmf_path, base_stl_path, text_stl_path, base_color, text_color)
    elif style == "debossed-open":
        return _build_debossed_open(text, params, tmf_path, base_stl_path, text_stl_path, base_color, text_color)
    else:
        return [f"Unknown text style: {style}"]


def _text_part(top_face, text: str, params: dict, depth: float):
    with BuildPart() as part:
        for line, x, y in iter_text_blocks(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(x, y)]):
                    Text(line, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
            extrude(amount=depth)
        for div_x in divider_positions(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(div_x, 0)]):
                    Rectangle(DIVIDER_WIDTH, params["height"] - 2 * DIVIDER_CLEARANCE)
            extrude(amount=depth)
    return part


def _overflow_warnings(compound, params: dict) -> list[str]:
    bbox = compound.bounding_box()
    warnings = []
    if bbox.size.X > params["width"]:
        warnings.append("Text overflows label width")
    if bbox.size.Y > params["height"]:
        warnings.append("Text overflows label height")
    return warnings


def _build_embossed(text, params, tmf_path, base_stl_path, text_stl_path, base_color, text_color):
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]
    tp = _text_part(top_face, text, params, TEXT_DEPTH)
    txt = tp.part
    warnings = _overflow_warnings(txt, params)
    export_3mf([(base, "base", base_color), (txt, "text", text_color)], tmf_path)
    export_stl(base, base_stl_path)
    if text_stl_path is not None:
        export_stl(txt, text_stl_path)
    return warnings


def _build_debossed(text, params, tmf_path, base_stl_path, text_stl_path, base_color, text_color):
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]
    tp = _text_part(top_face, text, params, TEXT_DEPTH)
    text_fill = tp.part.moved(Location(Vector(0, 0, -TEXT_DEPTH)))
    warnings = _overflow_warnings(tp.part, params)
    base_with_recess = base
    for glyph in text_fill.solids():
        base_with_recess = base_with_recess - glyph
    export_3mf([(base_with_recess, "base", base_color), (text_fill, "text", text_color)], tmf_path)
    export_stl(base_with_recess, base_stl_path)
    if text_stl_path is not None:
        export_stl(text_fill, text_stl_path)
    return warnings


def _build_debossed_open(text, params, tmf_path, base_stl_path, text_stl_path, base_color, text_color):
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]
    tp = _text_part(top_face, text, params, -TEXT_DEPTH)
    warnings = _overflow_warnings(tp.part, params)
    base_with_recess = base
    for glyph in tp.solids():
        base_with_recess = base_with_recess - glyph
    export_3mf([(base_with_recess, "base", base_color)], tmf_path)
    export_stl(base_with_recess, base_stl_path)
    return warnings
