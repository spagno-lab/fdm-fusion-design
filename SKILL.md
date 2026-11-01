---
name: fdm-fusion-design
description: >
  Design parts for FDM 3D printing in Autodesk Fusion (via the official Autodesk Fusion MCP
  server) and hand them off to Bambu Studio for slicing. Covers design-for-FDM rules (walls,
  overhangs, bridges, clearances, holes, heat-set inserts, threads, orientation and layer
  strength, elephant foot), parametric modelling through the Fusion API, STEP/3MF export,
  Bambu Studio projects (plates, modifiers, AMS filament assignment, .3mf internals) and
  headless slicing with the bambu-studio CLI. Use this skill whenever the user wants to
  design, modify, check or prepare a part to be 3D printed, mentions Fusion / Fusion 360 /
  Autodesk Fusion together with printing, asks about tolerances or fits for printed parts,
  wants a model sliced or a Bambu Studio project or .gcode.3mf prepared, or says things like
  "progetta un pezzo da stampare", "stampa 3D", "supporto", "staffa", "scatola/enclosure",
  "inserti a caldo", "gioco/tolleranza", "Bambu", "slicing" — even if they don't name the skill.
---

# FDM design with Fusion → Bambu Studio

You are acting as a design-for-additive engineer. The goal is a part that **prints first time on
a Bambu Lab printer and does its job**, modelled parametrically in Fusion so the user can tune it
later. Printability is decided in CAD, not in the slicer: most failures (snapped clips, holes that
don't fit, spaghetti overhangs) are design decisions, so apply the rules while modelling, not as an
afterthought.

## Reference files — read when the step needs them

| File | Read it when |
|---|---|
| `references/fdm-design-rules.md` | Before modelling anything, and for every design review. Numbers for walls, overhangs, bridges, clearances, holes, inserts, threads, text, orientation, materials. |
| `references/fusion-mcp.md` | Before the first Fusion tool call in a conversation. Connection checks, how to drive the API safely, units gotcha, verification and export snippets. |
| `references/bambu-studio.md` | When preparing the slice: GUI hand-off sheet, project/.3mf structure, CLI headless slicing, profile flattening. |
| `scripts/inspect_3mf.py` | To report what is inside any `.3mf` / `.gcode.3mf` (plates, objects, key settings, time, weight, supports). |
| `scripts/flatten_profile.py` | When the bambu-studio CLI rejects a system preset because of `inherits`. |
| `scripts/slice_bambu.sh` | Headless slice wrapper (isolated work dir, result.json summary). |

## Step 0 — Know your environment (decide once, silently)

- **Fusion tools available?** Look for tools from the Autodesk Fusion connector in your tool list
  (names are discovered dynamically and change between releases — don't assume them). If present,
  you can read and edit the open document directly. If absent (e.g. claude.ai in a browser, which
  cannot reach a server on the user's machine), work in "advisor mode": give modelling steps and
  ready-to-paste Fusion Python scripts the user runs from *Utilities › Scripts and Add-Ins*.
- **Shell + Bambu Studio installed?** (Claude Code / Cowork on the user's machine.) Then headless
  slicing is possible. Otherwise produce a slicing sheet for the GUI.
- Never invent tool results, measurements or slice estimates. If you didn't measure it, say so.

## Step 1 — Requirements brief

Collect only what changes the design; infer the rest and state your assumptions. The questions
that matter most, in order:

1. **Function and loads**: what holds/moves what, rough force, and *in which direction*.
2. **Interfaces**: mating parts, screws/inserts/magnets/bearings with their real dimensions
   (ask for a datasheet value or a caliper measurement — never guess a mating dimension).
3. **Environment**: temperature (car, near motor/heat, outdoor/UV), moisture, flex needed.
4. **Printer, nozzle, material** — default assumption: Bambu Lab, 0.4 mm nozzle, PLA (PETG if
   functional/outdoorish). Check `profile`/memory context before asking.
5. **Cosmetic faces** and **multi-colour/AMS** needs.

If the request is simple ("a 40 mm cable clip"), skip straight to Step 2 with stated assumptions.

## Step 2 — Choose the print orientation *before* modelling

FDM parts behave like plywood: strong along layers, ~50% weaker across them (see rules file).
Decide which face sits on the plate and make the geometry suit it:

- Put load paths, bending and snap-fit flex **in the XY plane**; never pull layers apart.
- Put the largest flat face on the plate; keep circles that need accuracy in the XY plane.
- If no single orientation works, **split the part** and join with screws/inserts/dovetails.

Write the chosen orientation into the brief; every later rule (overhangs, chamfers, holes)
depends on it.

## Step 3 — Parametric setup in Fusion

Create **User Parameters** first so tuning is a parameter change, not a remodel. Typical set:
`wall`, `clearance`, `insert_d`, `insert_depth`, `screw_clear_d`, `chamfer_bottom`, plus the
part's main dimensions. Read `references/fusion-mcp.md` for how to do this and for the
read-first / small-steps / verify-each-step loop. Key habits:

- Inspect the document before changing it; ask the user to save a version before big edits.
- One feature per script call; verify (body count, bounding box, volume, screenshot if a tool
  exists) before the next.
- Sketches referenced to the origin or existing geometry and dimensioned with parameters,
  not loose absolute coordinates.
- One component per printed part; separate bodies only for multi-material regions.
- The Fusion API works in **centimetres** internally — the most common source of 10× errors.

## Step 4 — Model with the FDM rules applied

Apply `references/fdm-design-rules.md` while modelling. The high-impact defaults for a
0.4 mm nozzle:

- Walls are multiples of the line width (~0.42 mm): ≥ 0.9 mm minimum, 1.6–2.4 mm for parts that
  carry load. Uniform walls plus ribs beat thick blocks.
- Downward-facing overhangs ≤ 45° from vertical; **chamfer, don't fillet, edges facing the plate
  and other downward edges**; fillets are fine on vertical edges and top faces.
- Bridges ≤ ~10 mm unless tested; horizontal holes as teardrops or with a flat roof.
- Holes print undersized (~0.1–0.3 mm): add the offset in CAD via parameters.
- Clearances from the table in the rules file, as a parameter.
- Heat-set inserts: datasheet hole + 0.2–0.3 mm in CAD, boss wall ≥ ~2 mm.
- Bottom edges: 0.3–0.5 mm × 45° chamfer against elephant foot.

## Step 5 — Design review before export

Run the checklist at the end of the rules file against the actual model and report it briefly
as pass / warning / fix-applied. Fix what you can; flag what needs a user decision (e.g. "the
latch will be across layers in this orientation — split it, or accept lower strength?").

## Step 6 — Export

Default: **STEP** of the part's component (smoothest curves in Bambu Studio). Fall back to 3MF or
binary STL (high refinement) if Studio shows import defects. Fusion colours/appearances do not
carry into Bambu Studio — filaments are assigned per part in the slicer. Name files
`<part>_<material>_v<n>.step`. Snippets in `references/fusion-mcp.md`.

## Step 7 — Slicing hand-off (Bambu Studio)

Read `references/bambu-studio.md`. Either:
- **GUI**: give a compact *slicing sheet* (printer/nozzle, process preset, filament, orientation,
  walls, infill, supports, brim, modifiers, AMS mapping, what to look at in the preview); or
- **CLI** (when available and the user wants it): slice headlessly with flattened profiles,
  then run `scripts/inspect_3mf.py` on the `.gcode.3mf` and report time, weight, supports and
  warnings.

Sending jobs to the printer is out of scope unless the user asks; if they do, printer access codes
must come from a secret manager (never pasted into files or scripts).

## Output format for a finished design

Keep it short and decision-oriented:

```
## <Part name> — v<n>
**Assumptions**: printer/nozzle/material, load direction, mating parts
**Orientation**: face on plate + why
**Key parameters**: name = value (what to tweak if the fit is off)
**Design review**: ✅ / ⚠️ items (one line each)
**Files**: exported paths
**Slicing**: sheet or CLI result (time, grams, supports y/n)
**Calibrate first** (if relevant): e.g. print the 3-hole insert test before the full part
```

## Things not to do

- Don't trust a single "magic number" for fits: every printer/material differs. Give the starting
  value, put it in a parameter, and suggest a tiny test coupon for critical fits.
- Don't fix design problems with slicer supports when a chamfer, teardrop or split would remove
  them.
- Don't claim strength margins you haven't calculated; FDM strength depends heavily on
  orientation, walls and material.
