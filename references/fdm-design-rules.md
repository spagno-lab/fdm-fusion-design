# FDM design rules (0.4 mm nozzle unless stated)

Starting values gathered from published test data and design guides (CNC Kitchen, Hydra Research /
U. Louisville AMIST cheat sheet, service-bureau DFM guides). They are **starting points**: printer,
material, speed and cooling move them. Put anything fit-critical in a User Parameter and suggest a
small test coupon.

## Contents
1. Mental model
2. Walls and minimum features
3. Overhangs, chamfers vs fillets
4. Bridges and horizontal holes
5. Hole sizing and clearances
6. Fasteners: inserts, screws, nuts, threads
7. First layer, warping, corners
8. Orientation and strength
9. Clips, snap fits, flexures
10. Text and details
11. Materials (qualitative)
12. Multi-colour / AMS
13. Review checklist

---

## 1. Mental model

- A print is stacked extrusion lines. Default Bambu line width with a 0.4 nozzle ≈ 0.42 mm;
  layer height usually 0.2 mm (0.08–0.28 range). Geometry thinner than ~2 lines or shallower
  than ~2 layers resolves badly.
- **Anisotropic**: inter-layer (Z) strength is typically ~50% of in-plane strength; it can be
  much worse with heavy cooling (e.g. ABS). CNC Kitchen's tests show the strength vs angle
  curve is S-shaped, so a slight tilt doesn't help — if you tilt to dodge a weak layer
  direction, go to ≥ 45°.
- XY accuracy is better than Z; circles are only true circles in the XY plane.
- Strength comes mostly from **walls (perimeters)**, not infill. More walls > more infill.

## 2. Walls and minimum features

| Feature | Minimum | Recommended |
|---|---|---|
| Wall (0.4 nozzle) | ~0.9 mm (2 lines) | 1.2 mm cosmetic, 1.6–2.4 mm functional |
| Wall (0.6 nozzle) | ~1.3 mm | 1.8–3.6 mm |
| Free-standing pin Ø | ~1.8–2 mm | ≥ 3 mm if loaded |
| Unsupported thin edge/fin | ~0.9 mm | — |

- Make wall thickness a multiple of line width so the slicer doesn't leave gaps or gap-fill.
- Keep walls uniform; stiffen with ribs (rib ≈ 0.6–1× wall, add root fillet) instead of thickening.
- Tall thin features wobble: keep height/width below ~8–10 or add a brim/buttress.

## 3. Overhangs, chamfers vs fillets

- Overhang angle measured **from vertical**: ≤ 45° prints clean everywhere; 50–55° usually OK
  on well-cooled machines (Bambu); beyond needs supports or redesign.
- Downward-facing edges and the bottom edge of horizontal features: **45° chamfer**. A fillet
  on a downward edge starts horizontal = unsupported.
- Fillets are fine on vertical edges and upward-facing edges.
- Remove overhangs by geometry first: 45° gussets, chamfered ledges, teardrops, or by changing
  orientation/splitting. Supports are the last resort (they cost time and surface quality).

## 4. Bridges and horizontal holes

- Bridges: design for ≤ ~10 mm; longer spans (20–30 mm) often work on well-cooled printers but
  test first. Bridges should land on solid walls at both ends.
- **Horizontal holes**: use a teardrop (45° pointed roof) or a flat roof (bridged) instead of a
  full circle. Ø ≤ ~5 mm round holes usually survive without support but come out oval/droopy.
- Counterbores/counterbridges on the top of a vertical hole: use a 1-layer **sacrificial bridge**
  (drill through afterwards) or the "stacked bridges" trick (two layers of rectangular bridges
  rotated 90°) so the hole doesn't start on air.

## 5. Hole sizing and clearances

Printed holes come out **undersized**; CNC Kitchen measured ≈ 0.25 mm under nominal on a
well-tuned printer with PLA. Outer dimensions come out slightly oversized.

- Vertical holes: start with **+0.2 mm on the diameter** in CAD, tune per printer/material.
- Bambu Studio also has `X-Y hole compensation` / `X-Y contour compensation` in the process —
  prefer design-time offsets per feature; use slicer compensation only as a global correction.

Clearance between mating printed parts (**gap per side**; diametral = 2×):

| Fit | Gap per side | Examples |
|---|---|---|
| Press / interference | 0.0–0.1 mm | pegs, bearing seats (or design undersize and ream/drill) |
| Snug / sliding | 0.1–0.2 mm | lids, caps, drawers |
| Free / rotating | 0.25–0.4 mm | hinges, pivots |
| Print-in-place moving | 0.3–0.5 mm | hinges printed assembled |
| Cable / connector pass-through | 0.5–1.0 mm | USB-C cut-outs, grommets |

Store the chosen value as `clearance` and reference it everywhere.

## 6. Fasteners

### Heat-set inserts (best default for anything re-screwed)
- **Hole Ø in CAD = datasheet hole Ø + 0.2–0.3 mm.** CNC Kitchen's 2026 pull-out tests on M3
  (datasheet 4.0 mm): as-printed 4.2 mm in CAD was the sweet spot — the insert pre-seats in the
  hole with slight resistance, no burr underneath, ~90% of max pull-out strength; strength falls
  off a cliff if the hole gets much larger. Practical rule: the insert should just pre-seat.
- Hole depth ≥ insert length + ~1 mm (displaced plastic needs somewhere to go); small entry
  chamfer.
- Material around the insert: boss wall ≥ ~2 mm (≥ 1.5× insert OD boss), and enough slicer
  walls (4+) around the hole region so the knurl bites solid plastic, not infill.
- Install: iron ~10–20 °C above the print temperature, melt ~90% of the way, press flush with a
  flat tool. Expect ~1.4 kN pull-out for a good M3 in PLA (CNC Kitchen, one setup — trend, not spec).

### Screws directly into plastic
- Clearance hole M3: 3.2–3.4 mm; M4: 4.3–4.5 mm; M5: 5.3–5.5 mm.
- Self-tapping into plastic: start M3 ≈ 2.6–2.8 mm, M4 ≈ 3.5–3.7 mm; calibrate. Fine for a few
  assembly cycles, not for frequent disassembly (use inserts).
- Hex nut traps: across-flats + 0.2–0.3 mm (M3 nut 5.5 mm AF → 5.7–5.8 mm pocket), depth = nut
  height + 0.2 mm. Orient so the hex pocket is in the XY plane or use a teardropped side entry.

### Modelled threads
- Only for ≥ M5 (smaller ones don't resolve). Use Fusion's *Modeled* thread with a clearance
  offset, print thread axis vertical, add 45° lead-in chamfers. Below M5: insert, tap, or
  self-tap.

## 7. First layer, warping, corners

- Bottom edges: **0.3–0.5 mm × 45° chamfer** — hides elephant foot and helps parts fit. Bambu
  Studio also has `Elephant foot compensation` (key `elefant_foot_compensation`).
- Large flat parts warp at corners: corner radius ≥ ~4 mm, avoid big sharp-cornered slabs in
  ABS/ASA/PA; add mouse ears or a brim in the slicer when unavoidable.
- Internal sharp corners concentrate stress — fillet them (≥ 1 mm) on loaded parts.
- Give the part a flat, sufficiently large base in the chosen orientation; tall narrow parts
  need a brim or a design-in foot.

## 8. Orientation and strength

Think of layers as wood grain. Decide orientation first, then design.

| Situation | Do |
|---|---|
| Bracket / L-angle under bending | Print so the L lies flat (both legs in XY); the bend is then in-plane. |
| Hook / cantilever | Hook outline in XY plane, extruded in Z; load never tries to peel layers. |
| Snap-fit / clip | Flexing beam lies along layers (printed flat), never standing up. |
| Shaft / pin under bending | Print lying down (axis in XY), accept flat or teardrop underside; or use a metal pin. |
| Gear | Flat on the bed (teeth are whole layers). |
| Pressure / sealing | Expect leaks between layers; add walls, prefer PETG, or post-seal. |
| Conflicting requirements | Split the part, print each in its best orientation, join with screws/inserts/dovetails. |

Strength levers in priority order: orientation → geometry (fillets, ribs, section depth) →
walls (4–6) → material → infill (40–60% only when compressive/bearing).

## 9. Clips, snap fits, flexures

- Cantilever snap: beam printed flat, thickness tapering toward the tip, generous root fillet,
  deflection modest. PLA is brittle (few cycles); PETG and nylon tolerate much more.
- Living hinges work reasonably only in PP/TPU/nylon-like materials and printed flat with the
  hinge lines along the extrusion direction; in PLA/PETG prefer pin hinges.
- Add a lead-in chamfer on every engaging edge.

## 10. Text and details

- Embossed/debossed text: stroke ≥ ~0.8–1 mm (≥ 2 lines), depth/height ≥ 0.4–0.6 mm (2–3
  layers). Bold sans-serif fonts. Best on top faces or vertical walls; text on the bottom face
  is mirrored and blurred by the first layer.
- Multi-colour text with AMS: make it a separate body flush with (or 1–2 layers into) the face
  so it can be assigned another filament.

## 11. Materials (qualitative guide)

| Material | Use for | Watch out |
|---|---|---|
| PLA | Prototypes, fixtures, stiff indoor parts | Brittle, creeps under constant load, softens around 55–60 °C (no car interiors) |
| PETG | Functional/indoor-outdoor parts, clips | Stringing, slightly less stiff, better layer adhesion |
| ABS / ASA | Heat (~90–100 °C class), ASA for UV/outdoor | Warping, needs enclosure; fumes |
| TPU | Flexible parts, gaskets, bumpers | Slow; avoid AMS for soft grades; design thicker walls |
| PA / PA-CF / PET-CF | Tough, heat-resistant engineering parts | Very hygroscopic — must be dried; abrasive (hardened nozzle) |

Always treat temperatures and speeds as the filament preset's job, not the design's.

## 12. Multi-colour / AMS

- One colour region = one body (or a painted region in Studio). Fusion appearances do **not**
  transfer to Bambu Studio.
- Colour changes cost purge waste and time per layer that has multiple colours: keep colour
  regions confined to few layers (e.g. top 2–3 layers for logos) when possible.

## 13. Review checklist

Report each as ✅ / ⚠️ / 🔧(fixed):

- [ ] Orientation stated; main loads in XY; no layer-peeling load paths
- [ ] All walls ≥ 2 lines; load-bearing walls ≥ 1.6 mm; no razor edges
- [ ] No downward overhang > 45° (or deliberately supported); downward edges chamfered
- [ ] Bridges ≤ ~10 mm or tested; horizontal holes teardropped/flat-roofed
- [ ] Holes compensated; clearances from a parameter; mating dimensions from real data
- [ ] Inserts: hole = datasheet + 0.2–0.3 mm, depth margin, boss ≥ 2 mm
- [ ] Threads < M5 not modelled
- [ ] Bottom-edge chamfer; base large/flat enough; warping risk for material considered
- [ ] Text/details ≥ 2 lines wide, ≥ 2 layers deep
- [ ] Fits on the plate (Bambu A1 mini 180³, A1/P1/X1 class 256³ mm — check the user's model)
- [ ] One component per printed part; bodies for colours; names meaningful
