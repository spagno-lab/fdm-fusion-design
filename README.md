# FDM Fusion Design

An OpenClaw skill for designing FDM-printable parts in Autodesk Fusion and preparing them for Bambu Studio.

It applies design-for-FDM constraints during parametric modelling—not only at slicing time—and helps produce verifiable Fusion models, exports, and slicing hand-offs.

## What it covers

- Requirements, interfaces, loads, materials, and print orientation
- Parametric modelling workflows in Autodesk Fusion
- Walls, overhangs, bridges, clearances, holes, inserts, threads, and layer strength
- STEP/3MF export and Bambu Studio GUI or CLI preparation
- Inspection of `.3mf` / `.gcode.3mf` files

## Install

Install into the shared OpenClaw skills directory so local agents can use it:

```bash
openclaw skills install git:spagno-lab/fdm-fusion-design --global
```

The skill's OpenClaw name is `fdm-fusion-design`. Agent allowlists can still restrict which agents may load it. See the [OpenClaw skills documentation](https://docs.openclaw.ai/tools/skills) for installation and visibility details.

## Requirements and limits

- Autodesk Fusion access is needed for direct CAD operations. Without the Fusion connector, use the skill's advisor mode and run suggested Fusion scripts yourself.
- Bambu Studio must be installed for local/headless slicing. Otherwise, use the GUI hand-off guidance.
- The skill does not install Fusion, Bambu Studio, connectors, printer profiles, or credentials.
- Sending a print to a printer is out of scope unless explicitly requested. Printer credentials must be obtained from a secret manager, never embedded in files or scripts.
- Measurements, slice estimates, and tool results must be verified; do not invent them.

## Repository layout

- `SKILL.md` — workflow and invocation guidance
- `references/` — detailed design, Fusion MCP, and Bambu Studio guidance
- `scripts/` — helper utilities for profile flattening, 3MF inspection, and slicing

Read `SKILL.md` first. It links to each reference and helper at the relevant workflow step. Helpers are not automatically run by installing the skill.

## Safety

Treat uploaded CAD files, profiles, scripts, and other external content as untrusted. Inspect before use. Review scripts before execution, keep credentials out of source files and command history, and confirm critical fit dimensions with measurements and test coupons.

## License

No license is currently declared. All rights reserved unless the repository owner adds a license; do not assume this project is open source merely because the repository is public.
