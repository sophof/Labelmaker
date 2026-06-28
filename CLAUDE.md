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

The app follows **MVC**: the Model (`labels/`) owns all data and geometry logic; the View (`static/app.js`, `templates/`) handles display and user input only; the Controller (`main.py`) is the intermediary — it receives requests, resolves string IDs to real objects, and calls into the model.

### API (main.py)
```
GET  /                      → serves the UI
GET  /systems               → returns full system/box/style hierarchy for the UI
POST /generate              → LabelRequest → STL + 3MF URLs (preview, does not add to batch list)
POST /generate-batch        → list[LabelRequest] → batch 3MF URL (each label carries its own settings)
POST /generate-font-sampler → LabelRequest → font sampler 3MF URL
GET  /download/{file}
```
`LabelRequest` carries: `system_id`, `box_id`, `style_id`, `text`, `font`, `bold`, `italic`,
`font_size`, `text_style`, `base_color`, `text_color`, `column_separator`.

The `Label` dataclass (`labels/label.py`) is the central model object — the controller resolves
string IDs (`style_id` → `LabelStyle` instance, `system_id`/`box_id` → box param dict from YAML)
and creates a `Label`. Everything downstream uses the real object, not string IDs.

Files are UUID-named under `generated/`. Old files (>24 h) are cleaned up on startup and each
generate. Session files (base STL, text STL, 3MF) are deleted after the 3MF is downloaded via
`BackgroundTasks`.

### Label styles (labels/)
Label logic is split into two concerns — see `labels/CLAUDE.md` for full details.

- `labels/label.py` — `Label` dataclass: the central model object (holds `LabelStyle` instance, box params dict, and all text/font/color params). Created by the controller at the JSON boundary.
- `labels/styles/` — one file per label style; auto-discovered at startup
- `labels/helpers/` — shared geometry, text, and composition helpers (no file I/O)

**To add a new label style:** drop a `.py` file in `labels/styles/`. No other files need changing.

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

### Infrastructure (lib/)
File I/O and format logic — no label-specific geometry. See `lib/CLAUDE.md` for details.

### UI (templates/index.html)
Single-page app. On load, fetches `/systems` and populates System and Box dropdowns.

**Sidebar** (always visible):
- System / Box selectors
- Label text grid — expandable rows × columns of single-line inputs
  - `[+ Row]` / `[+ Col]` / `[− Row]` / `[− Col]` buttons
  - JS encodes the grid to a column-major string (`col0r0\ncol0r1|col1r0`) sent to the backend
- **Generate** → 3D STL preview (Three.js), does not add to batch list
- **Save to list** → stores a full snapshot (text + all settings) in the label list
- Status / warnings (amber if text overflows)
- **[Advanced]** / **[Label list N]** / **[Tools]** buttons

**Advanced modal** (popup): label style, base color, text color (+ Auto), text style, font, bold, italic, font size, column separator.

**Label list modal**: each entry has an editable text field (multi-row/column shown as inline text, e.g. `Resistors / 220Ω | Caps`), an Edit button (loads full snapshot back into the editor), and a ✕ remove button. Download 3MF sends all snapshots to `/generate-batch` — each label uses its own saved settings.

**Tools modal**: font sampler generator.

## Environment
- LXC on Proxmox, project at `/opt/labelmaker`
- Run dev server: `.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000` (port override for dev; production uses `port` from `config.yaml` via `python main.py`)
- Access from local network at `http://<lxc-ip>:8000`
- IDE: VS Code with the Claude Code extension (SSH remote into the LXC)
- `uv` is at `/home/kingmob/.local/bin/uv`

## System dependencies
All system-level packages required by this project are tracked in `deploy/install.sh`. Whenever a
new `apt` dependency is discovered during development, add it to the `apt install` line in
`deploy/install.sh` so the script stays complete and a fresh LXC can be set up from scratch.
