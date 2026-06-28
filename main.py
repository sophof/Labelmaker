import os
import warnings
from contextlib import asynccontextmanager

import yaml
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import labels as label_registry
from config import BASE_COLOR, PORT, TEXT_COLOR
from labels.label import Label
from labels.helpers.sampler import build_font_sampler
from lib.storage import (
    cleanup_old_files,
    cleanup_session,
    ensure_dir,
    path_for,
    write_batch_session,
)
from systems import load_systems


@asynccontextmanager
async def lifespan(app):
    ensure_dir()
    cleanup_old_files()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class LabelRequest(BaseModel):
    system_id: str
    box_id: str
    style_id: str
    text: str = ""
    font: str = "Arial"
    bold: bool = True
    italic: bool = False
    font_size: float = 6.0
    text_style: str = "debossed"
    base_color: str = BASE_COLOR
    text_color: str = TEXT_COLOR
    column_separator: str = "|"


def _resolve_style(style_id: str):
    style = label_registry.get_style(style_id)
    if style is None:
        raise HTTPException(status_code=400, detail=f"Unknown style: {style_id}")
    return style


def _load_box_params(system_id: str, box_id: str) -> dict:
    sys_path = os.path.join("systems", system_id)
    sys_yaml_path = os.path.join(sys_path, "system.yaml")
    box_yaml_path = os.path.join(sys_path, f"{box_id}.yaml")

    if not os.path.isfile(sys_yaml_path) or not os.path.isfile(box_yaml_path):
        raise HTTPException(status_code=400, detail=f"Unknown system/box: {system_id}/{box_id}")

    with open(sys_yaml_path) as f:
        sys_info = yaml.safe_load(f)
    with open(box_yaml_path) as f:
        box_info = yaml.safe_load(f)

    params = dict(box_info.get("params", {}))
    params["side_margin"] = sys_info.get("side_margin", 0)
    return params


def _build_label(req: LabelRequest) -> Label:
    return Label(
        style=_resolve_style(req.style_id),
        box_params=_load_box_params(req.system_id, req.box_id),
        text=req.text,
        font=req.font,
        bold=req.bold,
        italic=req.italic,
        font_size=req.font_size,
        text_style=req.text_style,
        base_color=req.base_color,
        text_color=req.text_color,
        column_separator=req.column_separator,
    )


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"base_color": BASE_COLOR, "text_color": TEXT_COLOR})


@app.get("/systems")
def systems():
    return load_systems()


@app.post("/generate")
def generate(req: LabelRequest):
    label = _build_label(req)
    cleanup_old_files()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parts = label.style.build(label.text, label.params(), label.base_color, label.text_color)

    result = write_batch_session([parts], label.box_params, label.base_color, label.text_color)
    result["warnings"] = [str(w.message) for w in caught]
    return result


@app.post("/generate-batch")
def generate_batch(reqs: list[LabelRequest]):
    if not reqs:
        raise HTTPException(status_code=400, detail="No labels provided")

    cleanup_old_files()

    all_warnings = []
    label_parts_list = []
    for req in reqs:
        label = _build_label(req)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            label_parts_list.append(
                label.style.build(label.text, label.params(), label.base_color, label.text_color)
            )
        all_warnings.extend(str(w.message) for w in caught)

    first_label = _build_label(reqs[0])
    result = write_batch_session(label_parts_list, first_label.box_params, reqs[0].base_color, reqs[0].text_color)
    result["warnings"] = all_warnings
    return result


@app.post("/generate-font-sampler")
def generate_font_sampler(req: LabelRequest):
    label = _build_label(req)
    cleanup_old_files()

    label_parts_list = build_font_sampler(label.style, label.params(), label.base_color, label.text_color)
    return write_batch_session(label_parts_list, label.box_params, label.base_color, label.text_color)


@app.get("/download/{filename}")
def download(filename: str, background_tasks: BackgroundTasks):
    if filename != os.path.basename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = path_for(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    if filename.endswith("_batch.3mf"):
        session_id = filename[: -len("_batch.3mf")]
        background_tasks.add_task(cleanup_session, session_id)

    return FileResponse(path)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
