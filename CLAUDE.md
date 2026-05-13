  # Label Maker — Project Context

  ## What this is
  A local web app that generates 3D-printable label models for a physical sorting system.
  Labels are simple shaped models with text, designed for two-color FDM printing.
  Hosted on a Proxmox LXC, controlled via a browser-based web UI.

  ## Stack
  - **Python** with **uv** for package management (venv at `/opt/labelmaker/.venv`)
  - **FastAPI** — web server and API
  - **build123d** — 3D geometry generation (wraps OpenCASCADE)
  - **Three.js** with STLLoader — in-browser 3D preview
  - **Jinja2** — HTML templating

  ## Output format
  Single **3MF file** containing two objects/components:
  - Object 1: label base plate (color/filament 1)
  - Object 2: raised or recessed text (color/filament 2)

  Slicers (PrusaSlicer, OrcaSlicer) assign different extruders per object in a single 3MF.

  ## Architecture
  FastAPI app
  ├── POST /generate    → params in, returns 3MF file URL
  ├── GET  /download/{file}
  └── GET  /            → serves the UI

  build123d label modules
  ├── labels/flat.py    → basic flat label with raised text
  └── labels/...        → add new label types here

  Single-page UI
  ├── Form: text, label type, size params
  ├── Three.js 3MF/STL preview
  └── Download button

  ## MVP goal
  Enter text in the UI, pick label type, hit generate → see 3D preview → download a two-color 3MF ready for slicing.

  ## Label type extensibility
  Each label type is a separate Python module in `labels/`. New types added there without touching core app.

  ## Environment
  - LXC on Proxmox, project at `/opt/labelmaker`
  - Run dev server: `.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000`
  - Access from local network at `http://<lxc-ip>:8000`
  - IDE: VS Code with the Claude Code extension (SSH remote into the LXC)

  ## System dependencies
  All system-level packages required by this project are tracked in `setup.sh`. Whenever a new `apt` dependency is discovered during development, add it to the `apt install` line in `setup.sh` so the script stays complete and a fresh LXC can be set up from scratch by running it.
