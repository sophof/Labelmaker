from build123d import Axis, BuildPart, BuildSketch, RectangleRounded, chamfer, extrude

PARAMS = {
    "width":         {"type": "float", "default": 60.0, "unit": "mm", "label": "Width"},
    "height":        {"type": "float", "default": 20.0, "unit": "mm", "label": "Height"},
    "depth":         {"type": "float", "default": 3.0,  "unit": "mm", "label": "Depth"},
    "font_size":     {"type": "float", "default": 8.0,  "unit": "mm", "label": "Font size"},
    "text_depth":    {"type": "float", "default": 0.4,  "unit": "mm", "label": "Text depth"},
    "corner_radius": {"type": "float", "default": 2.0,  "unit": "mm", "label": "Corner radius"},
    "chamfer":       {"type": "float", "default": 0.2,  "unit": "mm", "label": "Chamfer"},
}


def build_base(params: dict) -> BuildPart:
    with BuildPart() as base_part:
        with BuildSketch():
            RectangleRounded(params["width"], params["height"], params["corner_radius"])
        extrude(amount=params["depth"])
        top_edges = base_part.faces().sort_by(Axis.Z)[-1].edges()
        bot_edges = base_part.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edges + bot_edges, length=params["chamfer"])
    return base_part
