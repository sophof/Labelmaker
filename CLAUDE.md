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
A **3MF file** containing one object per color component (base plate, text fill, accent ring, etc.).
Each component is assigned a color via a single `m:colorgroup` resource (3MF Materials Extension).
Bambu Studio / OrcaSlicer detect the colors and prompt the user to map them to filaments.
Colors are configured in `config.yaml` (`base_color`, `text_color`) as hex strings; `#RRGGBB` is
auto-expanded to `#RRGGBBAA` (fully opaque) when writing the 3MF.

## Architecture

### API (main.py)
```
GET  /          → serves the UI
GET  /systems   → returns full system/box/style hierarchy for the UI
POST /generate  → {text, style, params} → returns 3MF + STL file URLs
GET  /download/{file}
```
Files are UUID-named under `generated/`. Old files (>24 h) are cleaned up on startup and each
generate. Session files (base STL, text STL, 3MF) are deleted after the 3MF is downloaded via
`BackgroundTasks`.

### Label styles (labels/)
Each file in `labels/` defines one label geometry style. Current styles:
- `label.py` — base label with text; text style (embossed / debossed / debossed-open) is a param
- `bordered.py` — same as label but with a 1 mm accent-color border ring inlaid 0.4 mm deep

A style module must expose:
- `STYLE_ID: str` — unique identifier
- `STYLE_NAME: str` — human-readable name
- `PARAMS: dict` — parameter schema: `{key: {type, default, unit, label, options?}}`
- `build(text, params, tmf_path, base_stl_path, text_stl_path=None, base_color="#FFFFFF", text_color="#000000") -> list[str]` — returns a list of warning strings (empty = success)

`labels/__init__.py` auto-discovers all non-underscore `.py` files at import time.
**To add a new label style:** create a new `.py` file in `labels/`. No other files need changing.

Shared geometry helpers live in `labels/_label_utils.py` (underscore prefix = not auto-discovered):
- `build_base(params, corner_radius, chamfer_size)` — builds the chamfered rounded-rect base
- `build_text_compound(top_face, text, params, depth)` — text + column dividers extruded from a face
- `apply_text_and_export(...)` — central dispatch for embossed/debossed/debossed-open; handles
  STL + 3MF export; accepts optional `accent_components` list for extra colored parts (e.g. border ring)
- `overflow_warnings(text_compound, params)` — checks bounding box against label dimensions
- `TEXT_PARAMS`, `BASE_PARAMS` — shared param schema dicts

### Storage systems and box types (systems/)
The `systems/` folder is a data registry — no Python, just YAML.
```
systems/
  <system-id>/
    system.yaml      # name, description
    <box-id>.yaml    # one file per box type
```

Each box YAML has only `name` and `params` (width, height, depth; optionally font_size):
```yaml
name: 2x5 half-width bin
params:
  width: 41.4
  height: 16
  depth: 1
```

All label styles are always available for every box. `systems/__init__.py` merges the box params
into each style's param schema as the default values. Width, height and depth are fixed per box
and not shown as editable fields in the UI.

**To add a new box type:** drop a `.yaml` file in the appropriate system folder.
**To add a new storage system:** create a new subfolder with a `system.yaml` inside.

### 3MF export (lib/build_3mf.py)
Builds a standards-compliant 3MF from a list of `(shape, name, color)` tuples.
Uses a single `m:colorgroup` resource with deduplicated colors; objects sharing the same hex
color string get the same `pindex` and are merged into one filament slot by the slicer.

### UI (templates/index.html)
Single-page app. On load, fetches `/systems` and populates:
1. System selector → Box selector → Style selector (hidden when only one style exists)
2. Editable parameter fields: text style, font, font size (width/height/depth come from the box and are not shown)
3. Text entry (textarea, supports `\n` for multi-line)
4. Multi-column checkbox — reveals a separator input; injects `column_separator` param at generate time
5. Generate button → 3D STL preview (Three.js) + Download 3MF button
6. Warnings shown in amber if text overflows the label dimensions

## Environment
- LXC on Proxmox, project at `/opt/labelmaker`
- Run dev server: `.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Access from local network at `http://<lxc-ip>:8000`
- IDE: VS Code with the Claude Code extension (SSH remote into the LXC)
- `uv` is at `/home/kingmob/.local/bin/uv`

## System dependencies
All system-level packages required by this project are tracked in `setup.sh`. Whenever a new `apt`
dependency is discovered during development, add it to the `apt install` line in `setup.sh` so the
script stays complete and a fresh LXC can be set up from scratch by running it.
