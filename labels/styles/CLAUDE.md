# labels/styles/ — Label Style Definitions

Each `.py` file here defines one label style and is auto-discovered by `labels/__init__.py`.

## Required module interface

Every style module must expose:

- `STYLE_ID: str` — unique identifier (used as the key in the API)
- `STYLE_NAME: str` — human-readable name shown in the UI
- `PARAMS: dict` — full parameter schema for this style: `{key: {type, default, unit, label, options?}}`
- `build(text, params, base_color="#FFFFFF", text_color="#000000") -> tuple[list[tuple], list[str]]` — builds the label geometry and returns `(components, warnings)`. `components` is a list of `(shape, name, color)` tuples ready for export. No file I/O happens here.

## Conventions

- Assemble `PARAMS` by composing from `helpers/params.py` (`BASE_PARAMS`, `TEXT_PARAMS`, `TEXT_STYLE_OPTIONS`) plus any style-specific parameters.
- `build()` can use helpers from `helpers/` for any repeated or shared geometry tasks. Style-specific geometry that isn't shared can live directly in the style file.
