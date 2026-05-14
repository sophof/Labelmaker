# labels/styles/ — Label Style Definitions

Each `.py` file here defines one label style as a class subclassing `LabelStyle` (from `labels/label_style.py`). Styles are auto-discovered by `labels/__init__.py`.

## Required interface

Every style class must define:

- `STYLE_ID: ClassVar[str]` — unique identifier (used as the key in the API)
- `STYLE_NAME: ClassVar[str]` — human-readable name shown in the UI
- `PARAMS: ClassVar[dict]` — full parameter schema: `{key: {type, default, unit, label, options?}}`
- `build(text, params, base_color="#FFFFFF", text_color="#000000") -> list[ColoredPart]` — builds and returns the colored parts of the label. No file I/O. Overflow or other issues are issued via `warnings.warn()`.

## Conventions

- Assemble `PARAMS` by composing from `helpers/params.py` (`BASE_PARAMS`, `TEXT_PARAMS`, `TEXT_STYLE_OPTIONS`) plus any style-specific parameters.
- `build()` can use helpers from `helpers/` for any repeated or shared geometry tasks. Style-specific geometry that isn't shared can live directly in the style file.
