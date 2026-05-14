FONTS = ["Impact", "Arial", "DejaVu Sans", "Liberation Sans", "Verdana", "Courier New"]

TEXT_STYLE_OPTIONS = ["embossed", "debossed", "debossed-open"]

TEXT_PARAMS = {
    "font":             {"type": "str",   "default": "Impact", "label": "Font", "options": FONTS},
    "font_size":        {"type": "float", "default": 6.0,  "unit": "mm", "label": "Font size"},
    "column_separator": {"type": "str",   "default": "|",   "label": "Column separator"},
}

BASE_PARAMS = {
    "width":  {"type": "float", "default": 60.0, "unit": "mm", "label": "Width"},
    "height": {"type": "float", "default": 20.0, "unit": "mm", "label": "Height"},
    "depth":  {"type": "float", "default": 1.0,  "unit": "mm", "label": "Depth"},
}
