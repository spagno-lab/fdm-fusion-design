# Bambu Studio: projects, .3mf internals, headless slicing

Facts below come from Bambu Studio's `--help` (2.8.x, tracked by Printago), the BambuStudio source
and GitHub issues, and community reverse-engineering of the 3MF format. Bambu Studio's CLI is
**not officially documented**; verify flags with `bambu-studio --help` on the user's install.

## 1. Choose the path

| Situation | Path |
|---|---|
| No shell on the user's machine, or a one-off part | **GUI hand-off**: give the slicing sheet (§2) |
| Claude Code/Cowork on the machine with Bambu Studio installed, repeated parts, CI-ish flows | **CLI** (§4) |

## 2. GUI slicing sheet (template)

```
Printer / nozzle : Bambu Lab <model>, 0.4 mm <hardened/stainless>
Process preset   : 0.20mm Standard @BBL <model>   (Strength preset for load-bearing)
Filament         : <brand type> (AMS slot n)
Import           : <file>.step → if multi-body: right-click › Split › to parts
Orientation      : <face> on plate (already oriented in CAD — don't auto-orient)
Walls            : <n> wall loops   Top/bottom: <n>/<n> layers
Infill           : <pct> <gyroid|cubic|grid>
Supports         : none | tree(auto) threshold 45° | enforcers only on <feature>
Plate adhesion   : brim <none|outer 5 mm> ; mouse ears for ABS/ASA corners
Modifiers        : e.g. box modifier around insert bosses → 6 walls, 60% infill
Check in preview : <first layer contact>, <bridge over X>, supports = none, est. time/grams
```

Useful Studio features to suggest:
- **Per-object / per-part settings**, **modifiers** (box/cylinder volume with its own walls/infill),
  **height range modifiers** (different settings above/below Z).
- **Negative part** (subtract a volume in the slicer — handy for quick holes, but prefer CAD).
- **Support enforcer / blocker** painting; **seam painting**; **colour painting** for AMS.
- Multi-plate projects; one project `.3mf` keeps parts, plates, settings together.

### Process keys worth knowing (names used in `project_settings.config` and presets)
`layer_height`, `wall_loops`, `top_shell_layers`, `bottom_shell_layers`, `sparse_infill_density`,
`sparse_infill_pattern`, `enable_support`, `support_type` (e.g. `tree(auto)`, `normal(auto)`),
`support_threshold_angle`, `brim_type`, `seam_position`, `elefant_foot_compensation` (sic),
`xy_hole_compensation`, `xy_contour_compensation`. Confirm exact names/values for the installed
version by exporting resolved settings (`--export-settings out.json`) or reading a project file.

## 3. Inside a `.3mf` project

A `.3mf` is a ZIP (OPC package):

| Path | Content |
|---|---|
| `3D/3dmodel.model` | XML geometry, build items (transforms), app metadata (`Application`, `BambuStudio:3mfVersion`) |
| `3D/Objects/*.model` | Per-object meshes in newer versions (referenced from the main model) |
| `Metadata/project_settings.config` | JSON: the full flattened print/printer/filament settings |
| `Metadata/model_settings.config` | XML: objects, parts (type, name, extruder), per-object overrides, `<plate>` blocks, `<assemble>` |
| `Metadata/filament_settings_N.config`, `machine_settings_*.config`, `process_settings_*.config` | Preset overrides (inheritance-based) |
| `Metadata/slice_info.config` | Sliced only: per-plate prediction (s), weight (g), filament usage, warnings |
| `Metadata/plate_N.gcode` (+ `.md5`) | Sliced only: G-code per plate |
| `Metadata/plate_N.png`, `top_N.png`, `pick_N.png` | Thumbnails |

Gotchas when editing a project programmatically:
- `model_settings.config` is what makes Studio treat the file as a Bambu project; without it you
  get geometry only.
- If you change a value in `project_settings.config`, also list the key in
  `different_settings_to_system`, otherwise Studio may reset it to the preset value.
- Multi-plate layouts live in one shared coordinate space with per-plate offsets; read
  `printable_area` before moving objects between plates.
- Prefer letting the CLI/GUI write projects; hand-edit only for small, verified changes and
  re-open in Studio to confirm.

Use `scripts/inspect_3mf.py <file>` to dump plates, objects, key settings and slice results.

## 4. Headless slicing with the CLI

Binary locations (typical):
- macOS: `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio`
- Windows: `C:\Program Files\Bambu Studio\bambu-studio.exe`
- Linux: AppImage or Flatpak (`flatpak run com.bambulab.BambuStudio`); may need a virtual
  display (`xvfb-run`) on headless servers.

Typical slice:
```bash
bambu-studio \
  --slice 0 \
  --load-settings "machine.json;process.json" \
  --load-filaments "pla.json" \
  --allow-newer-file \
  --skip-useless-pick \
  --mstpp 300 \
  --outputdir out/ \
  --export-3mf part.gcode.3mf \
  part.3mf
```
`--slice 0` = all plates (`i` = plate i); `--load-settings` takes the machine file **first**,
then process; `--load-filaments` takes one file per AMS slot, `;`-separated; `--mstpp` caps
slicing time per plate (no built-in timeout otherwise). Input can be a project `.3mf` or STL/OBJ.
Note: `--outputdir` is string-prepended to the `--export-3mf` name, so pass a bare filename there.

Other useful flags: `--orient 1`, `--arrange 1`, `--rotate/--rotate-x/--rotate-y <deg>`,
`--scale`, `--export-png 0 --camera-view 0` (plate images), `--export-settings`, `--info`
(model info without slicing), `--load-assemble-list` (multi-object plates from STLs without a
project), `--pipe <fifo>` (JSON progress), `--check-preset` (≥ 2.8.2: fail on incompatible
filament), `--datadir` (≥ 2.8.2: isolated settings dir).

Settings precedence: **CLI flags > `--load-settings`/`--load-filaments` > values in the 3MF**.

Outputs and gotchas:
- Output is a **`.gcode.3mf`** (ZIP with `Metadata/plate_N.gcode`), which Bambu printers prefer;
  unzip if raw G-code is needed.
- `result.json` is written to `--outputdir` (or cwd) with return code, error string, per-plate
  warnings, filament grams and estimated time — read it after every run.
- **Presets with `inherits` are rejected or crash the CLI.** Loaded JSONs must be complete
  (flattened) with `type` = machine/process/filament and `from` = system/User/user. Use
  `scripts/flatten_profile.py` to merge the inheritance chain from the user's profile folders
  (system profiles under the app's `resources/profiles/BBL/`; user presets under the config
  dir: macOS `~/Library/Application Support/BambuStudio/`, Windows `%APPDATA%\BambuStudio`,
  Linux `~/.config/BambuStudio`).
- A 3MF saved by a newer Studio is refused without `--allow-newer-file`.
- Each run leaves large temp files: run in a dedicated work directory (`scripts/slice_bambu.sh`
  does this) and tell the user where it is.
- Bambu Studio and OrcaSlicer share the CLI but **not** profile files — export presets from the
  slicer you'll run.
- Machine presets assume the stock nozzle type; set it if the user runs a hardened nozzle.

After slicing, verify with `scripts/inspect_3mf.py out/part.gcode.3mf`: time, grams,
`support_used`, and the per-feature line counts (support present or not, from the G-code itself).

## 5. Out of scope by default

Uploading/starting prints over LAN/cloud (tools like `bambu-rs`, Bambu Connect). If the user asks,
the printer access code / credentials must be injected from a secret manager (e.g. 1Password
`op run` / `op read`), never written into scripts, project files or chat.
