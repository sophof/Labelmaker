import warnings

from ..label_style import ColoredPart
from .text import build_text_compound, check_overflow

TEXT_DEPTH = 0.4


def combine_geometry_and_text(
    base, top_face, text: str, params: dict,
    base_color: str, text_color: str,
    text_depth: float = TEXT_DEPTH,
    accent_components: list[ColoredPart] | None = None,
) -> list[ColoredPart]:
    """Combine base geometry with text according to text_style, return colored parts."""
    accents = accent_components or []

    if not text.strip():
        return [ColoredPart(base, "base", base_color)] + accents

    style = params.get("text_style", "debossed")

    if style == "embossed":
        # Text rises above the face — positive depth, no repositioning needed.
        txt = build_text_compound(top_face, text, params, text_depth)
        check_overflow(txt, params)
        return [ColoredPart(base, "base", base_color)] + accents + [ColoredPart(txt, "text", text_color)]

    elif style in ("debossed", "debossed-open"):
        # Text sinks into the face — negative depth puts it directly in the cavity position.
        txt = build_text_compound(top_face, text, params, -text_depth)
        check_overflow(txt, params)
        base_carved = base
        for glyph in txt.solids():
            base_carved = base_carved - glyph
        parts = [ColoredPart(base_carved, "base", base_color)] + accents
        if style == "debossed":
            parts.append(ColoredPart(txt, "text", text_color))
        return parts

    else:
        warnings.warn(f"Unknown text style: {style}")
        return []
