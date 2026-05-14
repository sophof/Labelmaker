from build123d import Location, Vector

from .text import build_text_compound, overflow_warnings


def combine_geometry_and_text(
    base, top_face, text: str, params: dict, text_depth: float,
    base_color: str, text_color: str,
    accent_components: list | None = None,
) -> tuple[list[tuple], list[str]]:
    """Combine base geometry with text according to text_style.

    Returns (components, warnings) where components is a list of (shape, name, color)
    tuples ready for export. The first component is always the base.
    """
    style = params.get("text_style", "debossed")
    accents = accent_components or []

    if style == "embossed":
        txt = build_text_compound(top_face, text, params, text_depth)
        warnings = overflow_warnings(txt, params)
        components = [(base, "base", base_color)] + accents + [(txt, "text", text_color)]

    elif style == "debossed":
        txt = build_text_compound(top_face, text, params, text_depth)
        text_fill = txt.moved(Location(Vector(0, 0, -text_depth)))
        warnings = overflow_warnings(txt, params)
        base_carved = base
        for glyph in text_fill.solids():
            base_carved = base_carved - glyph
        components = [(base_carved, "base", base_color)] + accents + [(text_fill, "text", text_color)]

    elif style == "debossed-open":
        txt = build_text_compound(top_face, text, params, -text_depth)
        warnings = overflow_warnings(txt, params)
        base_carved = base
        for glyph in txt.solids():
            base_carved = base_carved - glyph
        components = [(base_carved, "base", base_color)] + accents

    else:
        return [], [f"Unknown text style: {style}"]

    return components, warnings
