FONTS = ["Arial", "Impact", "Arial Black", "Trebuchet MS", "Verdana", "Georgia",
         "Times New Roman", "DejaVu Sans", "Liberation Sans", "Courier New"]

TEXT_STYLE_OPTIONS = ["embossed", "debossed", "debossed-open"]

TEXT_PARAMS = {
    "font":             {"type": "str",  "default": "Arial", "label": "Font", "options": FONTS},
    "bold":             {"type": "bool", "default": True,    "label": "Bold"},
    "font_size":        {"type": "float", "default": 6.0,  "unit": "mm", "label": "Font size"},
    "column_separator": {"type": "str",   "default": "|",   "label": "Column separator"},
}

BASE_PARAMS = {
    "width":  {"type": "float", "default": 60.0, "unit": "mm", "label": "Width"},
    "height": {"type": "float", "default": 20.0, "unit": "mm", "label": "Height"},
    "depth":  {"type": "float", "default": 1.0,  "unit": "mm", "label": "Depth"},
}
