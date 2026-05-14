import importlib
import inspect
import os

from .label_style import LabelStyle

_styles: dict[str, LabelStyle] = {}

_styles_dir = os.path.join(os.path.dirname(__file__), "styles")
for _fname in os.listdir(_styles_dir):
    if _fname.endswith(".py") and not _fname.startswith("_"):
        _mod = importlib.import_module(f"labels.styles.{_fname[:-3]}")
        for _name, _cls in inspect.getmembers(_mod, inspect.isclass):
            if issubclass(_cls, LabelStyle) and _cls is not LabelStyle:
                _instance = _cls()
                _styles[_instance.STYLE_ID] = _instance


def get_style(style_id: str) -> LabelStyle | None:
    return _styles.get(style_id)


def all_styles() -> dict:
    return {
        sid: {"name": style.STYLE_NAME, "params": style.PARAMS}
        for sid, style in _styles.items()
    }
