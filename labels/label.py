from build123d import Axis

from ._label_utils import BASE_PARAMS, TEXT_PARAMS, apply_text_and_export, build_base

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
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]
    return apply_text_and_export(
        base, top_face, text, params, TEXT_DEPTH,
        tmf_path, base_stl_path, text_stl_path, base_color, text_color,
    )
