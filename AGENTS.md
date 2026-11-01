# Contributor instructions

These instructions apply to this repository.

## Scope

- Keep this repository focused on the `fdm-fusion-design` OpenClaw skill.
- Preserve the skill's workflow and technical intent when editing documentation or scripts.
- Do not add unrelated workspace files, generated CAD exports, user data, printer credentials, or secrets.
- Do not claim that Fusion, Bambu Studio, or a connector is installed unless verified separately.

## Skill content

- `SKILL.md` is the canonical entry point. Keep its frontmatter name as `fdm-fusion-design` and keep references and script paths accurate.
- Put detailed design rules and product-specific procedures in the existing `references/` files; avoid duplicating large sections in `SKILL.md`.
- Keep advice explicit about assumptions and printer/material variability. Do not present starting tolerances as universal guarantees.
- Never fabricate measurements, Fusion tool results, slice time/weight, or printer state.
- Keep printer transmission out of scope unless the user explicitly requests it. Never store printer access codes or other credentials in this repository.

## Scripts and external inputs

- Treat uploaded models, 3MF archives, profiles, and other external inputs as untrusted.
- Review scripts before running them. Do not execute helpers merely because they are present; run them only when needed for the requested task.
- Do not add destructive behavior, implicit uploads, printer submission, or credential collection to helper scripts.
- Keep helper output and temporary artifacts outside the tracked source tree unless they are intentional fixtures.

## Validation

Before publishing changes:

1. Check Markdown links and referenced paths.
2. Run `git diff --check`.
3. For Python changes, run a syntax check and any relevant focused tests; for shell changes, run `bash -n`.
4. Inspect the final diff and ensure no secrets, generated artifacts, or unrelated files are staged.
5. Verify the pushed commit and repository state on GitHub.
