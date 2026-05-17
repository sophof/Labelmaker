from build123d import Axis, BuildPart, BuildSketch, Solid, RectangleRounded, chamfer, extrude

CORNER_RADIUS = 2.0
CHAMFER = 0.2


def build_base(params: dict, corner_radius: float = CORNER_RADIUS, chamfer_size: float = CHAMFER) -> Solid:
    with BuildPart() as base_part:
        with BuildSketch():
            RectangleRounded(params["width"], params["height"], corner_radius)
        extrude(amount=params["depth"])
        top_edges = base_part.faces().sort_by(Axis.Z)[-1].edges()
        bot_edges = base_part.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edges + bot_edges, length=chamfer_size)
    return base_part.solids()[0]
