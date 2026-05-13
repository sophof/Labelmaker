import importlib
import os

_styles: dict = {}

for _fname in os.listdir(os.path.dirname(__file__)):
    if _fname.endswith(".py") and not _fname.startswith("_"):
        _mod = importlib.import_module(f"labels.{_fname[:-3]}")
        _styles[_mod.STYLE_ID] = _mod


def get_style(style_id: str):
    return _styles.get(style_id)


def all_styles() -> dict:
    return {
        sid: {"name": mod.STYLE_NAME, "params": mod.PARAMS}
        for sid, mod in _styles.items()
    }
