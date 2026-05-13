import yaml

with open("config.yaml") as f:
    _cfg = yaml.safe_load(f)

BASE_COLOR: str = _cfg.get("base_color", "#FFFFFF")
TEXT_COLOR: str = _cfg.get("text_color", "#000000")
