import importlib
import os

_styles: dict = {}

_styles_dir = os.path.join(os.path.dirname(__file__), "styles")
for _fname in os.listdir(_styles_dir):
    if _fname.endswith(".py") and not _fname.startswith("_"):
        _mod = importlib.import_module(f"labels.styles.{_fname[:-3]}")
        if hasattr(_mod, "STYLE_ID"):
            _styles[_mod.STYLE_ID] = _mod


def get_style(style_id: str):
    return _styles.get(style_id)


def all_styles() -> dict:
    return {
        sid: {"name": mod.STYLE_NAME, "params": mod.PARAMS}
        for sid, mod in _styles.items()
    }
