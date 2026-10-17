# Code Video — Operational State (2026-10-17)

Project identity: Code Video film-production kernel + native Blender proof. Publishing target: `westkitty/Code_Video` on GitHub, Pages from `main` `/`.

## Verified
- Exact native MP4 file SHA-256 `e180b5320636c2d31b411426f526eb27795b5e0e6895230bcf94c133b758e022`, full 288-frame H.264 decode PASS at 24fps, 480×270, 12s; intentionally silent, subtitle-free.
- Native Blender `.blend` SHA-256 `3a778c61eaa53493d1471df54c3ccd1a4d5967e54bc3c575a2b3a9aefae98ceb`; 18 bones, four deforming weighted limb meshes, cross-machine Blender evaluation PASS.
- Prepared source snapshot: kernel v0.3.2 + unreleased v2 film contract module and test + Blender standalone actor module; 85 local pytest PASS.

## Verified only after deployment
- `main` HEAD contains the staged release and Pages main/root is enabled (must read GitHub state).
- Public Pages URL responds HTTP 200 and displays the actual native video (must request live site and media URL).

## Partially verified / unverified
- 480×270 demo is not the promised full-HD film studio quality, and no speech or full multi-character production.
- Live MCP/ChatGPT production tool connection remains UNVERIFIED.
- Portable GLB and this native Blender scene are two different actors; glTF -> Blender import proof is a separate, still-open gate.
- No subtitles unless user explicitly requests them; no unapproved voices.

## Guardrails
- No rewriting existing repository history, force-push, destructive cleanup, credential commits, replacing canon, or claiming full production readiness.
- Pages is static; do not imply that it enables remote full-film rendering.
- Preserve source frame hash receipts separately on producing host; not all 288 PNGs are committed to Git.
