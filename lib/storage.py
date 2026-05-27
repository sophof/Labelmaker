import glob
import os
import time
import uuid

from .export import export_labels_batch

GENERATED_DIR = "generated"
MAX_FILE_AGE = 86400  # 24 hours


def ensure_dir() -> None:
    os.makedirs(GENERATED_DIR, exist_ok=True)


def path_for(filename: str) -> str:
    return os.path.join(GENERATED_DIR, filename)


def cleanup_old_files() -> None:
    now = time.time()
    for f in glob.glob(os.path.join(GENERATED_DIR, "*")):
        try:
            if now - os.path.getmtime(f) > MAX_FILE_AGE:
                os.remove(f)
        except OSError:
            pass


def cleanup_session(session_id: str) -> None:
    for f in glob.glob(os.path.join(GENERATED_DIR, f"{session_id}_*.3mf")):
        try:
            os.remove(f)
        except OSError:
            pass


def write_batch_session(
    label_parts_list: list,
    params: dict,
    base_color: str,
    text_color: str,
) -> dict:
    session_id = str(uuid.uuid4())
    tmf_path = path_for(f"{session_id}_batch.3mf")
    base_stl_path = path_for(f"{session_id}_batch_base.stl")
    text_stl_path = path_for(f"{session_id}_batch_text.stl")
    label_width = float(params.get("width", 0))
    label_height = float(params.get("height", 0))
    has_text = any(len(parts) > 1 for parts in label_parts_list)
    export_labels_batch(
        label_parts_list, tmf_path,
        label_width=label_width,
        label_height=label_height,
        base_stl_path=base_stl_path,
        text_stl_path=text_stl_path if has_text else None,
    )

    response = {
        "3mf_url": f"/download/{session_id}_batch.3mf",
        "base_stl_url": f"/download/{session_id}_batch_base.stl",
        "base_color": base_color,
        "text_color": text_color,
    }
    if has_text:
        response["text_stl_url"] = f"/download/{session_id}_batch_text.stl"
    return response
