import glob
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import labels as label_registry
from systems import load_systems

GENERATED_DIR = "generated"


@asynccontextmanager
async def lifespan(app):
    os.makedirs(GENERATED_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(GENERATED_DIR, "*")):
        os.remove(f)
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


class GenerateParams(BaseModel):
    text: str
    style: str
    params: dict[str, float | str]


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/systems")
def systems():
    return load_systems()


@app.post("/generate")
def generate(req: GenerateParams):
    style = label_registry.get_style(req.style)
    if style is None:
        raise HTTPException(status_code=400, detail=f"Unknown style: {req.style}")

    file_id = str(uuid.uuid4())
    tmf_path = os.path.join(GENERATED_DIR, f"{file_id}.3mf")
    base_stl_path = os.path.join(GENERATED_DIR, f"{file_id}_base.stl")
    text_stl_path = os.path.join(GENERATED_DIR, f"{file_id}_text.stl")

    style.build(req.text, req.params, tmf_path, base_stl_path, text_stl_path)

    response = {
        "3mf_url": f"/download/{file_id}.3mf",
        "base_stl_url": f"/download/{file_id}_base.stl",
    }
    if os.path.exists(text_stl_path):
        response["text_stl_url"] = f"/download/{file_id}_text.stl"
    return response


@app.get("/download/{filename}")
def download(filename: str):
    path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
