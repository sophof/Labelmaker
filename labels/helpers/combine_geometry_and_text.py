import warnings

from build123d import Location, Vector

from ..label_style import ColoredPart
from .text import build_text_compound, check_overflow


def combine_geometry_and_text(
    base, top_face, text: str, params: dict, text_depth: float,
    base_color: str, text_color: str,
    accent_components: list[ColoredPart] | None = None,
) -> list[ColoredPart]:
    """Combine base geometry with text according to text_style, return colored parts."""
    accents = accent_components or []

    if not text.strip():
        return [ColoredPart(base, "base", base_color)] + accents

    style = params.get("text_style", "debossed")

    if style == "embossed":
        txt = build_text_compound(top_face, text, params, text_depth)
        check_overflow(txt, params)
        return [ColoredPart(base, "base", base_color)] + accents + [ColoredPart(txt, "text", text_color)]

    elif style == "debossed":
        txt = build_text_compound(top_face, text, params, text_depth)
        text_fill = txt.moved(Location(Vector(0, 0, -text_depth)))
        check_overflow(txt, params)
        base_carved = base
        for glyph in text_fill.solids():
            base_carved = base_carved - glyph
        return [ColoredPart(base_carved, "base", base_color)] + accents + [ColoredPart(text_fill, "text", text_color)]

    elif style == "debossed-open":
        txt = build_text_compound(top_face, text, params, -text_depth)
        check_overflow(txt, params)
        base_carved = base
        for glyph in txt.solids():
            base_carved = base_carved - glyph
        return [ColoredPart(base_carved, "base", base_color)] + accents

    else:
        warnings.warn(f"Unknown text style: {style}")
        return []
