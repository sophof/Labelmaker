# labels/ — Label Architecture

## Structure

```
labels/
  helpers/           — shared building blocks (geometry, text, params); no file I/O
  styles/            — one file per label style; auto-discovered at startup
  label_style.py     — LabelStyle ABC and ColoredPart dataclass: the shared contract for all styles
  __init__.py        — scans styles/ and registers all styles by STYLE_ID
```

The key separation: **helpers build geometry**, **styles define label types**, **label_style.py defines the shared contract**.
A style subclasses LabelStyle and returns a list of ColoredParts from build(). Helpers never import from styles/ and never write files.

## Adding a new label style

Drop a `.py` file in `labels/styles/`. No other files need changing — `__init__.py` picks it up automatically.

See `labels/styles/CLAUDE.md` for the required interface.
See `labels/helpers/CLAUDE.md` for available building blocks.
