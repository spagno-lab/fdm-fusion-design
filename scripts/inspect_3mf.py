#!/usr/bin/env python3
"""Summarise a Bambu Studio / OrcaSlicer .3mf or .gcode.3mf (stdlib only).

Usage:
    python inspect_3mf.py FILE.3mf [--json] [--keys k1,k2,...]

Reports: producing application, plates and their objects, key process settings,
and - for sliced files - per-plate time, weight, filament usage, warnings and a
feature breakdown read from the G-code itself (so "supports: yes/no" is a fact,
not a checkbox).
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

DEFAULT_KEYS = [
    "printer_model", "printer_settings_id", "print_settings_id", "filament_settings_id",
    "nozzle_diameter", "layer_height", "wall_loops", "top_shell_layers", "bottom_shell_layers",
    "sparse_infill_density", "sparse_infill_pattern", "enable_support", "support_type",
    "support_threshold_angle", "brim_type", "elefant_foot_compensation",
    "xy_hole_compensation", "xy_contour_compensation", "filament_type",
]
FEATURE_RE = re.compile(r"^;\s*FEATURE:\s*(.+?)\s*$")


def _meta(elem):
    return {m.get("key"): m.get("value") for m in elem.findall("metadata") if m.get("key")}


def _strip_ns(root):
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def read_xml(z, name):
    try:
        return _strip_ns(ET.fromstring(z.read(name)))
    except KeyError:
        return None
    except ET.ParseError as e:
        return {"_parse_error": str(e)}


def inspect(path, keys):
    out = {"file": path, "warnings": []}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        out["entries"] = len(names)

        model = read_xml(z, "3D/3dmodel.model")
        if isinstance(model, ET.Element):
            app = {m.get("name"): (m.text or "").strip() for m in model.findall("metadata")}
            out["application"] = app.get("Application")
            out["unit"] = model.get("unit")
            out["build_items"] = len(model.findall("build/item"))
        else:
            out["warnings"].append("3D/3dmodel.model missing or unreadable")

        ms = read_xml(z, "Metadata/model_settings.config")
        objects = {}
        plates = []
        if isinstance(ms, ET.Element):
            for obj in ms.findall("object"):
                md = _meta(obj)
                parts = []
                for p in obj.findall("part"):
                    pm = _meta(p)
                    parts.append({"name": pm.get("name"), "subtype": p.get("subtype"),
                                  "extruder": pm.get("extruder")})
                objects[obj.get("id")] = {"name": md.get("name"), "extruder": md.get("extruder"),
                                          "parts": parts,
                                          "overrides": {k: v for k, v in md.items()
                                                        if k not in ("name", "extruder")}}
            for pl in ms.findall("plate"):
                pm = _meta(pl)
                inst = [_meta(mi).get("object_id") for mi in pl.findall("model_instance")]
                plates.append({"id": pm.get("plater_id"), "name": pm.get("plater_name") or "",
                               "objects": [objects.get(i, {}).get("name", i) for i in inst],
                               "gcode_file": pm.get("gcode_file") or None})
        else:
            out["warnings"].append("No Metadata/model_settings.config: not a Bambu/Orca project "
                                   "(geometry-only 3MF)")
        out["objects"] = list(objects.values())
        out["plates"] = plates

        settings = {}
        if "Metadata/project_settings.config" in names:
            try:
                ps = json.loads(z.read("Metadata/project_settings.config"))
                for k in keys:
                    if k in ps:
                        settings[k] = ps[k]
                dts = ps.get("different_settings_to_system")
                if dts:
                    settings["different_settings_to_system"] = dts
            except (ValueError, UnicodeDecodeError) as e:
                out["warnings"].append(f"project_settings.config unreadable: {e}")
        out["settings"] = settings

        si = read_xml(z, "Metadata/slice_info.config")
        sliced = []
        if isinstance(si, ET.Element):
            for pl in si.findall("plate"):
                pm = _meta(pl)
                entry = {
                    "index": pm.get("index"),
                    "prediction_s": pm.get("prediction"),
                    "prediction_h": round(int(pm["prediction"]) / 3600, 2)
                    if (pm.get("prediction") or "").isdigit() else None,
                    "weight_g": pm.get("weight"),
                    "support_used": pm.get("support_used"),
                    "filaments": [dict(f.attrib) for f in pl.findall("filament")],
                    "warnings": [dict(w.attrib) for w in pl.findall("warning")],
                }
                sliced.append(entry)
        out["slice_info"] = sliced

        gcodes = sorted(n for n in names if re.match(r"Metadata/plate_\d+\.gcode$", n))
        feats = {}
        for g in gcodes:
            counts = {}
            with z.open(g) as fh:
                for raw in fh:
                    if not raw.startswith(b";"):
                        continue
                    m = FEATURE_RE.match(raw.decode("utf-8", "replace"))
                    if m:
                        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
            support = any("support" in k.lower() for k in counts)
            feats[g] = {"feature_blocks": counts, "supports_in_gcode": support}
        out["gcode"] = feats
    return out


def print_human(r):
    print(f"File: {r['file']}  ({r['entries']} entries)")
    if r.get("application"):
        print(f"Made by: {r['application']}  unit={r.get('unit')}  build items={r.get('build_items')}")
    for w in r["warnings"]:
        print(f"! {w}")
    if r["plates"]:
        print("\nPlates:")
        for p in r["plates"]:
            print(f"  #{p['id']} {p['name']!r}: {', '.join(map(str, p['objects'])) or '-'}")
    if r["objects"]:
        print("\nObjects:")
        for o in r["objects"]:
            extra = f" overrides={o['overrides']}" if o["overrides"] else ""
            print(f"  {o['name']} (filament {o['extruder']}){extra}")
            for p in o["parts"]:
                if p["subtype"] and p["subtype"] != "normal_part":
                    print(f"    - {p['subtype']}: {p['name']}")
    if r["settings"]:
        print("\nSettings:")
        for k, v in r["settings"].items():
            print(f"  {k} = {v}")
    if r["slice_info"]:
        print("\nSlice results:")
        for s in r["slice_info"]:
            print(f"  plate {s['index']}: {s['prediction_h']} h, {s['weight_g']} g, "
                  f"support_used={s['support_used']}")
            for f in s["filaments"]:
                print(f"    filament {f.get('id')} {f.get('type')} {f.get('color', '')} "
                      f"{f.get('used_g', '?')} g / {f.get('used_m', '?')} m")
            for w in s["warnings"]:
                print(f"    ! {w.get('msg') or w}")
    for g, d in r["gcode"].items():
        print(f"\n{g}: supports in G-code = {'YES' if d['supports_in_gcode'] else 'no'}")
        top = sorted(d["feature_blocks"].items(), key=lambda kv: -kv[1])[:12]
        print("  " + ", ".join(f"{k}:{v}" for k, v in top))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--keys", help="comma-separated settings keys to report")
    a = ap.parse_args()
    keys = a.keys.split(",") if a.keys else DEFAULT_KEYS
    try:
        r = inspect(a.file, keys)
    except zipfile.BadZipFile:
        sys.exit(f"{a.file}: not a ZIP/3MF archive")
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print_human(r)


if __name__ == "__main__":
    main()
