import os
import warnings
from contextlib import asynccontextmanager

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import labels as label_registry
from config import BASE_COLOR, PORT, TEXT_COLOR
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


class BatchGenerateParams(BaseModel):
    texts: list[str]
    style: str
    params: dict[str, float | str | bool]
    base_color: str = BASE_COLOR
    text_color: str = TEXT_COLOR


class GenerateParams(BaseModel):
    text: str
    style: str
    params: dict[str, float | str | bool]
    base_color: str = BASE_COLOR
    text_color: str = TEXT_COLOR


def _resolve_style(style_id: str):
    style = label_registry.get_style(style_id)
    if style is None:
        raise HTTPException(status_code=400, detail=f"Unknown style: {style_id}")
    return style


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"base_color": BASE_COLOR, "text_color": TEXT_COLOR})


@app.get("/systems")
def systems():
    return load_systems()


@app.post("/generate")
def generate(req: GenerateParams):
    style = _resolve_style(req.style)
    cleanup_old_files()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        style.build(req.text, req.params, req.base_color, req.text_color)

    return {"warnings": [str(w.message) for w in caught]}


@app.post("/generate-batch")
def generate_batch(req: BatchGenerateParams):
    style = _resolve_style(req.style)
    if not req.texts:
        raise HTTPException(status_code=400, detail="No labels provided")

    cleanup_old_files()

    label_parts_list = []
    for text in req.texts:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            label_parts_list.append(style.build(text, req.params, req.base_color, req.text_color))

    return write_batch_session(label_parts_list, req.params, req.base_color, req.text_color)


@app.post("/generate-font-sampler")
def generate_font_sampler(req: BatchGenerateParams):
    style = _resolve_style(req.style)
    cleanup_old_files()

    label_parts_list = build_font_sampler(style, req.params, req.base_color, req.text_color)
    return write_batch_session(label_parts_list, req.params, req.base_color, req.text_color)


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
