from build123d import Axis, BuildPart, BuildSketch, Location, Mode, Plane, RectangleRounded, Vector, extrude

from ..label_style import ColoredPart, LabelStyle
from ..helpers.params import BASE_PARAMS, TEXT_PARAMS, TEXT_STYLE_OPTIONS
from ..helpers.geometry import CHAMFER, CORNER_RADIUS, build_base
from ..helpers.combine_geometry_and_text import combine_geometry_and_text

BORDER_WIDTH = 1.0
BORDER_DEPTH = 0.4


class Bordered(LabelStyle):
    STYLE_ID = "bordered"
    STYLE_NAME = "Bordered"
    PARAMS = {
        "text_style": {
            "type": "str",
            "default": "debossed",
            "label": "Text style",
            "options": TEXT_STYLE_OPTIONS,
        },
        **TEXT_PARAMS,
        **BASE_PARAMS,
    }

    def build(self, text: str, params: dict, base_color: str = "#FFFFFF", text_color: str = "#000000") -> list[ColoredPart]:
        full_base = build_base(params)
        top_face = full_base.faces().sort_by(Axis.Z)[-1]

        inner_radius = max(CORNER_RADIUS - BORDER_WIDTH, 0.5)
        with BuildPart() as ring_part:
            with BuildSketch(Plane(top_face)):
                RectangleRounded(params["width"], params["height"], CORNER_RADIUS)
                RectangleRounded(
                    params["width"] - 2 * BORDER_WIDTH,
                    params["height"] - 2 * BORDER_WIDTH,
                    inner_radius,
                    mode=Mode.SUBTRACT,
                )
            extrude(amount=BORDER_DEPTH)
        # Move ring down flush with top surface, clip to chamfered base boundary
        ring_fill = ring_part.part.moved(Location(Vector(0, 0, -BORDER_DEPTH))) & full_base

        base_with_ring = full_base
        for s in ring_fill.solids():
            base_with_ring = base_with_ring - s

        inner_top_face = base_with_ring.faces().sort_by(Axis.Z)[-1]
        return combine_geometry_and_text(
            base_with_ring, inner_top_face, text, params, base_color, text_color,
            accent_components=[ColoredPart(ring_fill, "border", text_color)],
        )
