# Label Maker — Project Context

## What this is
A local web app that generates 3D-printable label models for a physical sorting system.
Labels are simple shaped models with text, designed for two-color FDM printing.
Hosted on a Proxmox LXC, controlled via a browser-based web UI.

## Stack
- **Python** with **uv** for package management (venv at `/opt/labelmaker/.venv`)
- **FastAPI** — web server and API
- **build123d** — 3D geometry generation (wraps OpenCASCADE)
- **PyYAML** — loading system/box config files
- **Three.js** with STLLoader — in-browser 3D preview
- **Jinja2** — HTML templating

## Output format
Single **3MF file** containing two objects/components:
- Object 1: label base plate (color/filament 1)
- Object 2: raised or recessed text (color/filament 2)

Slicers (PrusaSlicer, OrcaSlicer) assign different extruders per object in a single 3MF.

## Architecture

### API (main.py)
```
GET  /          → serves the UI
GET  /systems   → returns full system/box/style hierarchy for the UI
POST /generate  → {text, style, params} → returns 3MF + STL file URLs
GET  /download/{file}
```

### Label styles (labels/)
Each file in `labels/` defines one label geometry style. Current styles:
- `embossed.py` — raised text above the base plate (two objects: base + text)
- `debossed.py` — text recessed into the base, filled by a second object (two-color inlay)
- `debossed_open.py` — text recessed into the base, open cutout (single object)

A style module must expose:
- `STYLE_ID: str` — unique identifier
- `STYLE_NAME: str` — human-readable name
- `PARAMS: dict` — parameter schema: `{key: {type, default, unit, label}}`
- `build(text, params, tmf_path, stl_path)` — geometry builder

All current styles share the same `PARAMS` and base-building logic from `lib/label_utils.py`:
rounded corners (2 mm default), chamfer on front and back face edges (0.2 mm default), 0.4 mm text depth default.

`labels/__init__.py` auto-discovers all style modules at import time.
**To add a new label style:** create a new `.py` file in `labels/` with the above interface. No other files need changing.

### Storage systems and box types (systems/)
The `systems/` folder is a data registry — no Python, just YAML.
```
systems/
  <system-id>/
    system.yaml          # name, description
    <box-id>.yaml        # one file per box type
```

Each box YAML lists the label configurations for that box:
```yaml
name: Small bin
labels:
  - style: flat
    params:
      width: 40
      height: 15
      depth: 3
      font_size: 6
      text_depth: 0.8
```

`systems/__init__.py` loads this hierarchy and merges the style param schemas with the box YAML values for the API response.

**To add a new box type:** drop a `.yaml` file in the appropriate system folder.
**To add a new storage system:** create a new subfolder with a `system.yaml` inside.

### Shared label utilities (lib/)
- `threemf.py` — assembles multi-component 3MF files from build123d shapes
- `label_utils.py` — shared `PARAMS` dict and `build_base()` function used by all current label styles

### UI (templates/index.html)
Single-page app. On load, fetches `/systems` and populates:
1. System selector → Box selector → Style selector (cascading dropdowns)
2. Parameter fields (pre-filled from the selected box YAML, editable)
3. Generate button → 3D STL preview + Download 3MF button
4. Export as YAML button — downloads current params as a ready-to-save box YAML

## Environment
- LXC on Proxmox, project at `/opt/labelmaker`
- Run dev server: `.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Access from local network at `http://<lxc-ip>:8000`
- IDE: VS Code with the Claude Code extension (SSH remote into the LXC)
- `uv` is at `/home/kingmob/.local/bin/uv`

## System dependencies
All system-level packages required by this project are tracked in `setup.sh`. Whenever a new `apt` dependency is discovered during development, add it to the `apt install` line in `setup.sh` so the script stays complete and a fresh LXC can be set up from scratch by running it.
