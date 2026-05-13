import os
import yaml

import labels as label_registry

SYSTEMS_DIR = "systems"


def load_systems() -> list[dict]:
    styles = label_registry.all_styles()
    result = []

    for sys_id in sorted(os.listdir(SYSTEMS_DIR)):
        sys_path = os.path.join(SYSTEMS_DIR, sys_id)
        if not os.path.isdir(sys_path):
            continue
        sys_yaml = os.path.join(sys_path, "system.yaml")
        if not os.path.exists(sys_yaml):
            continue

        with open(sys_yaml) as f:
            sys_info = yaml.safe_load(f)

        boxes = []
        for box_file in sorted(os.listdir(sys_path)):
            if box_file == "system.yaml" or not box_file.endswith(".yaml"):
                continue
            with open(os.path.join(sys_path, box_file)) as f:
                box_info = yaml.safe_load(f)

            box_labels = []
            for entry in box_info.get("labels", []):
                style_id = entry["style"]
                style = styles.get(style_id)
                if style is None:
                    continue
                # Merge style param schema with yaml values
                merged_params = {
                    key: {**schema, "value": entry.get("params", {}).get(key, schema["default"])}
                    for key, schema in style["params"].items()
                }
                box_labels.append({
                    "style": style_id,
                    "style_name": style["name"],
                    "params": merged_params,
                })

            boxes.append({
                "id": box_file[:-5],
                "name": box_info["name"],
                "labels": box_labels,
            })

        result.append({
            "id": sys_id,
            "name": sys_info["name"],
            "description": sys_info.get("description", ""),
            "boxes": boxes,
        })

    return result
