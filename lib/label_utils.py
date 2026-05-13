from build123d import Axis, BuildPart, BuildSketch, Color, RectangleRounded, chamfer, extrude

FONTS = ["Impact", "Arial", "DejaVu Sans", "Liberation Sans", "Verdana", "Courier New"]


def hex_to_color(hex_str: str) -> Color:
    r, g, b = (int(hex_str[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return Color(r, g, b)

PARAMS = {
    "font":      {"type": "str",   "default": "Impact", "label": "Font", "options": FONTS},
    "font_size": {"type": "float", "default": 6.0,  "unit": "mm", "label": "Font size"},
    "width":     {"type": "float", "default": 60.0, "unit": "mm", "label": "Width"},
    "height":    {"type": "float", "default": 20.0, "unit": "mm", "label": "Height"},
    "depth":     {"type": "float", "default": 3.0,  "unit": "mm", "label": "Depth"},
}


def build_base(params: dict, corner_radius: float, chamfer_size: float) -> BuildPart:
    with BuildPart() as base_part:
        with BuildSketch():
            RectangleRounded(params["width"], params["height"], corner_radius)
        extrude(amount=params["depth"])
        top_edges = base_part.faces().sort_by(Axis.Z)[-1].edges()
        bot_edges = base_part.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edges + bot_edges, length=chamfer_size)
    return base_part
