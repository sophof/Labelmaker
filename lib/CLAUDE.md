# lib/ — Infrastructure

File I/O and output format logic. No label-specific geometry lives here.

## 3MF output strategy

**Current approach:** Standard 3MF with `m:colorgroup` per-object colors. Each mesh `<object>`
has `pid="1" pindex="N"` referencing the colorgroup resource. BambuStudio/OrcaSlicer detect
the colors and prompt the user to map them to filaments on open.

**Known issue — BambuStudio 2.5+ regression (issue #9666):** `pid`/`pindex` color data is
treated as Color Painting, which bleeds through `top_shell_layers × layer_height` of depth
regardless of actual geometry. Waiting for upstream fix.

**Bambu-native workaround (was tried, reverted):** Adding `Metadata/model_settings.config` to
the ZIP sets `m_is_bbl_3mf = true` in BambuStudio, which bypasses Standard 3MF Color Parsing.
The workaround grouped all parts under one `<object>` in model_settings.config with nested
`<part subtype="normal_part">` elements and per-part `extruder` metadata (0-indexed). This gave
correct color depth without Color Painting, but the color-hint dialog on open was lost (everything
loaded white) — reverted until a better approach is found or the upstream bug is fixed.

**If the workaround is re-attempted:**
- Keep m:colorgroup for hints but remove `pid`/`pindex` from all mesh `<object>` elements
  (Color Painting is triggered by per-triangle color data, not by the colorgroup declaration).
- Add `Metadata/model_settings.config` to the ZIP with nested `<object>/<part>` structure:
  ```xml
  <config>
    <object id="2" name="label">
      <metadata key="name" value="label"/>
      <part id="2" name="base" subtype="normal_part">
        <metadata key="name" value="base"/>
        <metadata key="extruder" value="0"/>
      </part>
      <part id="3" name="text" subtype="normal_part">
        <metadata key="name" value="text"/>
        <metadata key="extruder" value="1"/>
      </part>
    </object>
  </config>
  ```
- Add `<Default Extension="config" ContentType="application/xml"/>` to `[Content_Types].xml`.
- All mesh objects must appear in `<build>` (missing `<build>` entry = object not loaded).
- Extruder values are 0-indexed (0 = filament 1, 1 = filament 2, …).
- Note: `subtype="modifier"` CAN assign a second filament but requires an uncarved base
  (color change only, no physical indentation). `normal_part` with carved base preserves
  actual debossed geometry.
