import glob
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

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
    label_type: str = "flat"
    width: float = 60.0
    height: float = 20.0
    depth: float = 3.0
    font_size: float = 8.0
    text_depth: float = 1.0


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/generate")
def generate(params: GenerateParams):
    file_id = str(uuid.uuid4())
    tmf_path = os.path.join(GENERATED_DIR, f"{file_id}.3mf")
    stl_path = os.path.join(GENERATED_DIR, f"{file_id}.stl")

    if params.label_type == "flat":
        from labels.flat import build_flat_label
        build_flat_label(params, tmf_path, stl_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown label type: {params.label_type}")

    return {
        "3mf_url": f"/download/{file_id}.3mf",
        "stl_url": f"/download/{file_id}.stl",
    }


@app.get("/download/{filename}")
def download(filename: str):
    path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
