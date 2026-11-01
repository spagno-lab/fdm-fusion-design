# Driving Autodesk Fusion through the official MCP server

## 1. What it is (as documented by Autodesk, 2026)

- **Autodesk Fusion MCP Server** is built into the Fusion *desktop* app. Enable it in
  `Preferences › General › API › Fusion MCP Server (runs locally on this device)`, then **Apply**
  (closing without Apply silently discards the tick). Default endpoint
  `http://127.0.0.1:27182/mcp`, Streamable HTTP, loopback only, **no authentication**.
- Clients: Claude Desktop (connector "Autodesk Fusion" from the directory), Claude Code
  (`claude mcp add --transport http fusion http://127.0.0.1:27182/mcp`), Cursor, VS Code
  (VS Code uses `"servers"` + `"type": "http"`, not `"mcpServers"`). Not reachable from
  claude.ai in a browser.
- **Dynamic tooling**: the tool list is discovered at connect time and can change between Fusion
  releases. Observed tool families: execute a Python script against the Fusion API, read
  document/API information, search the API docs, capture viewport screenshots. Use whatever is
  in your tool list; if a documentation-search tool exists, use it before writing an API call
  you're not sure about.
- Not the same as **Fusion Data MCP** (cloud: hubs/projects/permissions, can't see geometry) or
  **Fusion Compute MCP** (cloud headless Fusion, public beta). This skill targets the local one.

### Troubleshooting (Autodesk's table, condensed)
| Symptom | Cause / fix |
|---|---|
| Can't connect / "connection refused" | Fusion not running, checkbox not applied, or port mismatch — re-read port in Fusion prefs |
| Tools list empty | Restart the client after Fusion is up |
| Commands don't execute | No document open — open or create a design |
| Worked, then "transport closed" | Fusion restarted (maybe on another port) — recheck port |
| Checkbox missing | Fusion too old — update |

## 2. Working loop

1. **Read first.** Describe the active document: units, design type (parametric vs direct),
   components, bodies, user parameters, timeline length, feature health. Confirm names you will
   edit.
2. **Protect the user's work.** Before non-trivial edits ask the user to save a version (or do it
   if a tool exists). There is no undo on the Claude side; Fusion's undo/timeline still works.
3. **Parameters first.** Create/reuse User Parameters; reference them in every dimension.
4. **Small steps.** One feature (or one tight group) per script. After each, verify: feature
   health, body count, bounding box, volume, and a screenshot if a screenshot tool exists.
5. **Fail loudly.** Wrap scripts in try/except and return the traceback text; never leave a
   half-built feature silently.
6. **Name things**: components `part_name`, bodies `part_name_colour`, features meaningful.

### Hard rules
- **Never call modal UI** (`ui.messageBox`, `ui.inputBox`, file dialogs, command dialogs). A modal
  pauses Fusion and the agent can't dismiss it. Return text instead.
- **Internal units are centimetres.** `ValueInput.createByReal(1.0)` = 10 mm. Prefer
  `ValueInput.createByString('10 mm')` or a parameter name. Volumes come back in cm³, lengths in cm.
- Prefer constrained, parameter-driven sketches anchored to origin/existing geometry. Absolute
  coordinates break as soon as one dimension changes.
- Keep the timeline linear and readable; avoid direct-modelling edits in a parametric design.
- Don't export to paths the user didn't approve; default to a folder they name.

## 3. Snippets (Fusion Python API — verify signatures with the docs tool if unsure)

The exact entry point the MCP script tool expects may differ (some expect a `run(context)`
function, some execute top-level code); follow the tool's description.

### Inspect the design
```python
import adsk.core, adsk.fusion, traceback
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
out = []
um = design.unitsManager
out.append(f"units={um.defaultLengthUnits} type={'parametric' if design.designType == adsk.fusion.DesignTypes.ParametricDesignType else 'direct'}")
for p in design.userParameters:
    out.append(f"param {p.name} = {p.expression}")
for comp in design.allComponents:
    for b in comp.bRepBodies:
        bb = b.boundingBox
        size_mm = [round((bb.maxPoint.x-bb.minPoint.x)*10,2), round((bb.maxPoint.y-bb.minPoint.y)*10,2), round((bb.maxPoint.z-bb.minPoint.z)*10,2)]
        vol_cm3 = b.physicalProperties.volume if b.isSolid else 0
        out.append(f"{comp.name}/{b.name} solid={b.isSolid} bbox_mm={size_mm} vol_cm3={vol_cm3:.2f}")
bad = [t.entity.name for t in design.timeline if t.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState and t.entity]
out.append(f"timeline_items={design.timeline.count} errors={bad}")
print("\n".join(out))   # or return the string, depending on the tool
```

### Create / update user parameters
```python
def set_param(design, name, expr, units='mm', comment=''):
    p = design.userParameters.itemByName(name)
    if p:
        p.expression = expr
    else:
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expr), units, comment)

for n, e, c in [
    ('wall', '2.0 mm', 'functional wall, ~5 lines @0.42'),
    ('clearance', '0.2 mm', 'gap per side, snug fit'),
    ('insert_d', '4.2 mm', 'M3 insert: datasheet 4.0 + 0.2'),
    ('insert_depth', '6.7 mm', 'insert 5.7 + 1.0'),
    ('chamfer_bottom', '0.4 mm', 'elephant foot'),
]:
    set_param(design, n, e, 'mm', c)
```

### Minimum distance between two entities (e.g. checking a wall)
```python
r = app.measureManager.measureMinimumDistance(entity_a, entity_b)
print(f"min distance = {r.value*10:.2f} mm")
```

### Interference check between bodies (assembly fits)
```python
bodies = adsk.core.ObjectCollection.create()
for comp in design.allComponents:
    for b in comp.bRepBodies: bodies.add(b)
inp = design.createInterferenceInput(bodies)
res = design.analyzeInterference(inp)
print(f"interferences: {res.count}")
```

### Export
```python
em = design.exportManager
target = design.rootComponent            # or a specific component / occurrence
folder = '/path/the/user/approved'
# STEP (preferred for Bambu Studio)
em.execute(em.createSTEPExportOptions(f'{folder}/part_pla_v1.step', target))
# 3MF (fallback) — note the C prefix in the API name
opt = em.createC3MFExportOptions(target, f'{folder}/part_pla_v1.3mf')
opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
em.execute(opt)
# binary STL of a single body
stl = em.createSTLExportOptions(body, f'{folder}/part_pla_v1.stl')
stl.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
stl.isBinaryFormat = True
em.execute(stl)
```

### Viewport image (if no screenshot tool exists)
```python
app.activeViewport.fit()
app.activeViewport.saveAsImageFile('/path/preview.png', 1200, 900)
```

## 4. What it's good and bad at (Autodesk's own sample-server notes + reviews)

- Good: reading/summarising designs, parameter edits, prismatic parts describable in sentences
  (brackets, enclosures, spacers, adapters), batch renames/appearances/exports, writing add-ins.
- Weak: freeform surfaces, lofts/T-splines, fully constrained complex sketches, recovering from
  failed features (you only see error text), anything needing engineering judgement it can't
  measure. For these, propose the approach and let the user model the hard feature, then
  continue (e.g. add inserts, chamfers, parameters, export).

## 5. Security

The server runs any Python the agent sends, with the user's permissions, and any local process
can reach it while enabled. Keep Claude's per-tool approval on, avoid filesystem operations
outside the approved export folder, and suggest disabling the server when finished.

## 6. Export notes for Bambu Studio

- STEP gives smoother curves and smaller files; occasionally Studio's STEP tessellation shows
  defects — inspect, and fall back to 3MF/STL (high refinement) for that part.
- Multiple bodies exported as one STEP/3MF arrive as one object: in Studio use
  *Split › to parts* (keeps them together, lets you assign filaments) or *to objects*.
- Studio imports only geometry from non-Bambu 3MF files; settings and colours are set in Studio.
- Check units on import (a 10× or 25.4× size error = units mismatch).
