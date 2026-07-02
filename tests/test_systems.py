import pytest
import yaml

import systems


@pytest.fixture
def systems_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(systems, "SYSTEMS_DIR", str(tmp_path))
    return tmp_path


def _write_yaml(path, data):
    path.write_text(yaml.safe_dump(data))


def test_load_systems_merges_box_params_into_style_schemas(systems_dir):
    sys_dir = systems_dir / "alpha"
    sys_dir.mkdir()
    _write_yaml(sys_dir / "system.yaml",
                {"name": "Alpha", "description": "test system", "side_margin": 3})
    _write_yaml(sys_dir / "box-a.yaml",
                {"name": "Box A", "params": {"width": 41.4, "height": 16, "depth": 1, "font_size": 5}})

    result = systems.load_systems()

    assert len(result) == 1
    system = result[0]
    assert system["id"] == "alpha"
    assert system["name"] == "Alpha"
    assert len(system["boxes"]) == 1

    box = system["boxes"][0]
    assert box["id"] == "box-a"
    style_ids = {label["style"] for label in box["labels"]}
    assert {"plain", "bordered"} <= style_ids

    params = box["labels"][0]["params"]
    assert params["width"]["value"] == 41.4          # box overrides default
    assert params["width"]["default"] == 60.0        # schema default untouched
    assert params["font_size"]["value"] == 5
    assert params["side_margin"]["value"] == 3       # injected from system.yaml


def test_side_margin_defaults_to_zero(systems_dir):
    sys_dir = systems_dir / "alpha"
    sys_dir.mkdir()
    _write_yaml(sys_dir / "system.yaml", {"name": "Alpha"})
    _write_yaml(sys_dir / "box-a.yaml", {"name": "Box A", "params": {}})

    box = systems.load_systems()[0]["boxes"][0]
    assert box["labels"][0]["params"]["side_margin"]["value"] == 0


def test_dirs_without_system_yaml_are_skipped(systems_dir):
    (systems_dir / "not-a-system").mkdir()
    (systems_dir / "stray.txt").write_text("ignore me")

    assert systems.load_systems() == []
