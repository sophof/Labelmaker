import warnings

from ..label_style import LabelStyle
from .params import FONTS


def build_font_sampler(
    style: LabelStyle,
    params: dict,
    base_color: str,
    text_color: str,
) -> list:
    parts_list = []
    for font in FONTS:
        for bold in (False, True):
            text = font if not bold else f"{font} (bold)"
            label_params = {**params, "font": font, "bold": bold}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parts_list.append(style.build(text, label_params, base_color, text_color))
    return parts_list
