import glob
import os
import time
import uuid
import warnings
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import labels as label_registry
from config import BASE_COLOR, TEXT_COLOR
from lib.export import export_label
from systems import load_systems

GENERATED_DIR = "generated"
MAX_FILE_AGE = 86400  # 24 hours


def cleanup_old_files():
    now = time.time()
    for f in glob.glob(os.path.join(GENERATED_DIR, "*")):
        try:
            if now - os.path.getmtime(f) > MAX_FILE_AGE:
                os.remove(f)
        except OSError:
            pass


def cleanup_session(session_id: str):
    for f in glob.glob(os.path.join(GENERATED_DIR, f"{session_id}_*")):
        try:
            os.remove(f)
        except OSError:
            pass


@asynccontextmanager
async def lifespan(app):
    os.makedirs(GENERATED_DIR, exist_ok=True)
    cleanup_old_files()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class GenerateParams(BaseModel):
    text: str
    style: str
    params: dict[str, float | str]
    base_color: str = BASE_COLOR
    text_color: str = TEXT_COLOR


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"base_color": BASE_COLOR, "text_color": TEXT_COLOR})


@app.get("/systems")
def systems():
    return load_systems()


@app.post("/generate")
def generate(req: GenerateParams):
    style = label_registry.get_style(req.style)
    if style is None:
        raise HTTPException(status_code=400, detail=f"Unknown style: {req.style}")

    cleanup_old_files()

    session_id = str(uuid.uuid4())
    tmf_path = os.path.join(GENERATED_DIR, f"{session_id}_label.3mf")
    base_stl_path = os.path.join(GENERATED_DIR, f"{session_id}_label_base.stl")
    text_stl_path = os.path.join(GENERATED_DIR, f"{session_id}_label_text.stl")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parts = style.build(req.text, req.params, req.base_color, req.text_color)

    export_label(parts, tmf_path, base_stl_path, text_stl_path)

    response = {
        "3mf_url": f"/download/{session_id}_label.3mf",
        "base_stl_url": f"/download/{session_id}_label_base.stl",
        "base_color": req.base_color,
        "text_color": req.text_color,
        "warnings": [str(w.message) for w in caught],
    }
    if len(parts) > 1:
        response["text_stl_url"] = f"/download/{session_id}_label_text.stl"
    return response


@app.get("/download/{filename}")
def download(filename: str, background_tasks: BackgroundTasks):
    if filename != os.path.basename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    if filename.endswith("_label.3mf"):
        session_id = filename[: -len("_label.3mf")]
        background_tasks.add_task(cleanup_session, session_id)

    return FileResponse(path)
