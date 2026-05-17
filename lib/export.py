from build123d import Compound, Location, Vector, export_stl

from labels.label_style import ColoredPart
from .build_3mf import export_3mf


def export_label(
    parts: list[ColoredPart],
    tmf_path: str,
    base_stl_path: str,
    text_stl_path: str | None = None,
) -> None:
    """Write STL and 3MF files from a list of ColoredParts produced by a label style's build().

    The first part is always the base (written to base_stl_path).
    All remaining parts are combined into the text/accent STL (written to text_stl_path if provided).
    """
    export_stl(parts[0].shape, base_stl_path)

    secondary = [p.shape for p in parts[1:]]
    if secondary and text_stl_path is not None:
        export_stl(Compound(secondary) if len(secondary) > 1 else secondary[0], text_stl_path)

    export_3mf([(p.shape, p.name, p.color) for p in parts], tmf_path)


def export_labels_batch(
    label_parts_list: list[list[ColoredPart]],
    tmf_path: str,
    label_width: float = 0.0,
    gap: float = 2.0,
) -> None:
    """Write a single 3MF containing all labels laid out in a row."""
    all_shapes = []
    for i, parts in enumerate(label_parts_list):
        x_offset = i * (label_width + gap)
        for p in parts:
            shifted = p.shape.moved(Location(Vector(x_offset, 0, 0)))
            all_shapes.append((shifted, f"label{i + 1}_{p.name}", p.color))
    export_3mf(all_shapes, tmf_path)
