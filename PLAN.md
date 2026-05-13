# Text Layout Plan

Three incremental features: overflow warning → multi-line → multi-column.
Each phase is independently shippable.

---

## Phase 1 — Overflow warning

After text geometry is built, check its bounding box against the usable label area
and return any warnings in the generate response.

**Backend**

- In each `labels/*.py`, after the `BuildPart` text block, read `text_part.part.bounding_box()`
  and compare `bbox.size.X` / `bbox.size.Y` against `params["width"]` / `params["height"]`
  minus a margin (e.g. `2 * CORNER_RADIUS`).
- Change `build()` return type from `None` to `list[str]` (empty = no warnings).
- `main.py`: collect the returned list and include it in the generate response as `"warnings"`.

**Frontend (`templates/index.html`)**

- After a successful generate, if `data.warnings?.length`, show them in `#status`
  in a warning color (amber). Non-fatal — the model is still generated.

**No new params.** No changes to PARAMS dict or YAML format.

---

## Phase 2 — Multi-line (explicit `\n`)

User types newlines in the text field; each line is rendered as a separate `Text()` call,
stacked vertically and centered as a block.

**Frontend**

- Replace `<input type="text" id="text">` with `<textarea id="text" rows="3">`.
- Preserve `\n` when reading the value (`.value` already contains real newlines — no change needed).

**Backend — shared helper in `lib/label_utils.py`**

Add `iter_text_lines(text: str, params: dict)` that splits on `\n` and yields
`(line, x_offset, y_offset)` tuples. Vertical offsets center the block:

```
line_spacing = params["font_size"] * 1.3
y_i = (num_lines - 1) / 2 * line_spacing - i * line_spacing
```

**Backend — `labels/*.py`**

Replace the single `Text(...)` call with a loop over `iter_text_lines()` using
`with Locations([(x, y)]):` inside the `BuildSketch`. All lines stay in the same
`BuildPart`, so they union correctly and `text_part.part` is still one Compound.

Overflow check from Phase 1 covers the multi-line block automatically (bounding box
of the whole compound).

---

## Phase 3 — Multi-column

User provides a separator string; the text is split on it and each chunk is laid out
as its own column (possibly also multi-line within each column).

**New param — added to `PARAMS` in `lib/label_utils.py`**

```python
"column_separator": {"type": "str", "default": "", "label": "Column separator"}
```

**Backend — extend `iter_text_lines()` → `iter_text_blocks()`**

1. If `column_separator` is non-empty and present in text, split on it → N column strings.
2. Compute `col_width = (params["width"] - 4 * CORNER_RADIUS) / N`.
3. For each column, compute its center `x = -total_usable/2 + (j + 0.5) * col_width`.
4. Within each column, apply the multi-line `\n` split from Phase 2.
5. Yield `(line_text, x_offset, y_offset)` for every line in every column.

The `labels/*.py` build loop stays the same — it just calls `iter_text_blocks()` instead
of `iter_text_lines()`, using the same `Locations` pattern.

Overflow is still detected by the bounding box of the full compound.

**Frontend**

- The `column_separator` param renders automatically via `renderParams()` as a text input
  (type `"str"` without `options`). No special-case UI code needed.

---

## Files changed (summary)

| File | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| `lib/label_utils.py` | — | add `iter_text_lines()` | extend to `iter_text_blocks()`, add `column_separator` param |
| `labels/embossed.py` | bounding-box check, return warnings | use helper loop | — (loop unchanged) |
| `labels/debossed.py` | same | same | — |
| `labels/debossed_open.py` | same | same | — |
| `main.py` | pass `warnings` in response | — | — |
| `templates/index.html` | show warnings in status | `<input>` → `<textarea>` | — (param auto-renders) |

---

## Decisions

1. **Line spacing factor**: hardcoded at `1.3×` font_size. No param.
2. **Column separator UX**: checkbox "Multi-column" that reveals a separator text input when checked.
3. **Overflow margin**: compare against full label dimensions (`params["width"]` / `params["height"]`).
   Rounded corners only affect the physical corners, not the edges where text sits.
4. **`build()` return type**: changed from `None` to `list[str]` (warnings). All three style
   modules updated together; `main.py` forwards the list as `"warnings"` in the response.
