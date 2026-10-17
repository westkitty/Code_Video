# Code Video — 3D Puppet Film Studio

**[Live demonstration](https://westkitty.github.io/Code_Video/)** · [Native film](assets/the-reach-native-blender.mp4) · [Blender scene](assets/the-reach-editable.blend) · [Portable rig](assets/the-reach-animated-rig.glb)

This repository preserves the Code Video Production Kernel **v0.3.2** and its later, tested film-contract source additions, along with the actual **The Reach** native Blender demonstration rendered on 2026-10-17. It does **not** claim that an arbitrary-input autonomous studio or connected ChatGPT MCP plugin is finished.

## Proof that exists

- Native Blender 5.2.2 Eevee film, **12.0 seconds**, **24 fps**, **288 frames**, **480×270**, H.264/yuv420p, intentionally silent, **no subtitles**.
- A native `.blend` scene with an **18-bone armature** and **four weighted, deforming limb meshes**; independent Blender 5.2.2 verification on a second Mac proved motion in the four meshes.
- Original source-frame SHA-256 ledger checked **288/288** PNGs before encoding; MP4 fully decoded; file hashes in `docs/NATIVE_QA.md` and `native/NATIVE_MANIFEST.json`.
- `code-video-kernel/` implements film contracts, portable animated GLB export, Blender render workers, VTK technical preview, source-bound proofs, and packaged Skills. **85/85 tests passed on the prepared source snapshot.** This is a local suite result, not a claim of a live MCP handshake.

## Repository layout

- `index.html`, `styles.css` — zero-dependency static GitHub Pages showcase hosted from `main` / root.
- `assets/` — actual native MP4, portable GLB, editable `.blend`, and preview frames extracted from the MP4.
- `code-video-kernel/` — editable Python engine, Blender integration, Skill and MCP adapter. Includes experimental film-contract v2 additions without a new certified plugin release number.
- `native/` — source/proof handoff and original immutable media manifest.
- `docs/` — original native and distribution QA (retained with their dates, earlier blocker language is historical).
- `downloads/` — untouched v0.3.2 plugin and certified standalone Skill ZIPs.

## Run code tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e './code-video-kernel[dev]'
python -m pytest -q code-video-kernel/tests
```

This excludes the optional VTK dependency; VTK-specific integration tests may skip when unavailable. Blender rendering additionally requires a real Blender 5.2+ binary and FFmpeg. Do not assume the code's optional MCP server is connected until an authenticated live handshake has been verified.

## Publication / safety

GitHub Pages serves only a **static showcase and local-file downloads**, not a remote rendering service, authenticated API, or hosted Blender engine. Do not upload user-provided licensed audio, private references, generated credential files or diagnostic raw logs to this public repository. The kernel retains its `code-video-kernel/LICENSE` license; media has not been relicensed by publishing this showcase.
