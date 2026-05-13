from build123d import Align, Axis, BuildPart, BuildSketch, Compound, Locations, Mode, Plane, Rectangle, RectangleRounded, Text, export_stl, extrude

from ._label_utils import BASE_PARAMS, DIVIDER_CLEARANCE, DIVIDER_WIDTH, TEXT_PARAMS, build_base, divider_positions, iter_text_blocks
from lib.build_3mf import export_3mf

STYLE_ID = "bordered"
STYLE_NAME = "Bordered"

CORNER_RADIUS = 2.0
CHAMFER = 0.2
BORDER_WIDTH = 1.0
ACCENT_DEPTH = 0.4

PARAMS = {**TEXT_PARAMS, **BASE_PARAMS}


def build(text: str, params: dict, tmf_path: str, base_stl_path: str,
          text_stl_path: str | None = None, base_color: str = "#FFFFFF", text_color: str = "#000000") -> list[str]:
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]

    with BuildPart() as text_part:
        for line, x, y in iter_text_blocks(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(x, y)]):
                    Text(line, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
            extrude(amount=ACCENT_DEPTH)
        for div_x in divider_positions(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(div_x, 0)]):
                    Rectangle(DIVIDER_WIDTH, params["height"] - 2 * DIVIDER_CLEARANCE)
            extrude(amount=ACCENT_DEPTH)
    txt = text_part.part

    warnings = []
    bbox = txt.bounding_box()
    if bbox.size.X > params["width"]:
        warnings.append("Text overflows label width")
    if bbox.size.Y > params["height"]:
        warnings.append("Text overflows label height")

    inner_radius = max(CORNER_RADIUS - BORDER_WIDTH, 0.5)
    with BuildPart() as frame_part:
        with BuildSketch(Plane(top_face)):
            RectangleRounded(params["width"], params["height"], CORNER_RADIUS)
            RectangleRounded(
                params["width"] - 2 * BORDER_WIDTH,
                params["height"] - 2 * BORDER_WIDTH,
                inner_radius,
                mode=Mode.SUBTRACT,
            )
        extrude(amount=ACCENT_DEPTH)
    frame = frame_part.part

    export_3mf([(base, "base", base_color), (frame, "border", text_color), (txt, "text", text_color)], tmf_path)
    export_stl(base, base_stl_path)
    if text_stl_path is not None:
        export_stl(Compound([frame, txt]), text_stl_path)
    return warnings
