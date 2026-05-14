from build123d import Compound, export_stl

from .build_3mf import export_3mf


def export_label(
    components: list[tuple],
    tmf_path: str,
    base_stl_path: str,
    text_stl_path: str | None = None,
) -> None:
    """Write STL and 3MF files from a components list produced by a label style's build().

    The first component is always the base (written to base_stl_path).
    All remaining components are combined into the text/accent STL (written to text_stl_path if provided).
    """
    base_shape = components[0][0]
    export_stl(base_shape, base_stl_path)

    secondary = [c[0] for c in components[1:]]
    if secondary and text_stl_path is not None:
        export_stl(Compound(secondary) if len(secondary) > 1 else secondary[0], text_stl_path)

    export_3mf(components, tmf_path)
