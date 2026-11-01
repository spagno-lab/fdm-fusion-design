#!/usr/bin/env python3
"""Flatten a Bambu Studio preset (machine/process/filament JSON) for the CLI.

The bambu-studio CLI rejects (or crashes on) presets that rely on "inherits".
This walks the inheritance chain by preset *name* across the folders you give it,
merges parent -> child, blanks "inherits", and guarantees "type" and "from".

Usage:
    python flatten_profile.py PRESET.json --search DIR [--search DIR ...] -o OUT.json
    python flatten_profile.py "0.20mm Standard @BBL X1C" --search DIR ... -o process.json

Search dirs, typically (check the user's install):
  system : <app resources>/profiles/BBL/{machine,process,filament}
  user   : <config dir>/user/<id>/{machine,process,filament}  (and .../base)
Put user dirs first if names collide.
Stdlib only. Read-only on inputs; writes only OUT.json.
"""
import argparse
import json
import os
import sys

VALID_TYPES = {"machine", "process", "filament"}
VALID_FROM = {"system", "User", "user"}
CHAIN_KEYS = ("inherits", "include")


def build_index(dirs):
    index = {}
    for d in dirs:
        for root, _, files in os.walk(d):
            for f in files:
                if not f.endswith(".json"):
                    continue
                p = os.path.join(root, f)
                try:
                    with open(p, encoding="utf-8") as fh:
                        data = json.load(fh)
                except (OSError, ValueError):
                    continue
                if isinstance(data, dict) and data.get("name"):
                    index.setdefault(data["name"], p)  # first dir wins
    return index


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(data, index, stack):
    """Return fully merged dict for `data` (already loaded)."""
    merged = {}
    parents = []
    inc = data.get("include")
    if isinstance(inc, list):
        parents.extend(inc)
    elif isinstance(inc, str) and inc:
        parents.append(inc)
    if data.get("inherits"):
        parents.append(data["inherits"])  # inherits applied last = closest parent wins
    for pname in parents:
        if pname in stack:
            sys.exit(f"inheritance cycle: {' -> '.join(stack + [pname])}")
        ppath = index.get(pname)
        if not ppath:
            sys.exit(f"parent preset not found in search dirs: {pname!r} "
                     f"(needed by {data.get('name')!r})")
        merged.update(resolve(load(ppath), index, stack + [pname]))
    for k, v in data.items():
        if k not in CHAIN_KEYS:
            merged[k] = v
    return merged


def main():
    ap = argparse.ArgumentParser(description="Flatten a Bambu Studio preset for CLI use")
    ap.add_argument("preset", help="path to a preset JSON, or a preset name to look up")
    ap.add_argument("--search", action="append", default=[], help="folder to index (repeatable)")
    ap.add_argument("--type", choices=sorted(VALID_TYPES), help="force 'type' if missing")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    index = build_index(a.search)
    if os.path.isfile(a.preset):
        start = load(a.preset)
    elif a.preset in index:
        start = load(index[a.preset])
    else:
        sys.exit(f"preset not found as file or name: {a.preset!r}")

    flat = resolve(start, index, [start.get("name", a.preset)])
    flat["inherits"] = ""
    if flat.get("type") not in VALID_TYPES:
        if not a.type:
            sys.exit("could not determine preset 'type'; pass --type machine|process|filament")
        flat["type"] = a.type
    if flat.get("from") not in VALID_FROM:
        flat["from"] = "User"
    src = a.preset if os.path.isfile(a.preset) else index.get(a.preset)
    if os.path.exists(a.out) and src and os.path.samefile(a.out, src):
        sys.exit("refusing to overwrite the input preset; choose another -o path")
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(flat, fh, indent=2, ensure_ascii=False)
    print(f"wrote {a.out}: type={flat['type']} name={flat.get('name')!r} keys={len(flat)}")


if __name__ == "__main__":
    main()
