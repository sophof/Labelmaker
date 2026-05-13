from build123d import Align, Axis, Box, BuildPart, BuildSketch, Plane, Text, extrude, export_stl

from labels.threemf import export_3mf


def build_flat_label(params, tmf_path: str, stl_path: str) -> None:
    with BuildPart() as base_part:
        Box(params.width, params.height, params.depth)

    top_face = base_part.faces().sort_by(Axis.Z)[-1]
    with BuildPart() as text_part:
        with BuildSketch(Plane(top_face)):
            Text(
                params.text,
                font_size=params.font_size,
                align=(Align.CENTER, Align.CENTER),
            )
        extrude(amount=params.text_depth)

    export_3mf(
        [(base_part.part, "base"), (text_part.part, "text")],
        tmf_path,
    )
    export_stl(base_part.part + text_part.part, stl_path)
