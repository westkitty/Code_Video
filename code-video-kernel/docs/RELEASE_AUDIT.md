# Release audit — Code Video Production Kernel 0.1.1

**Audit type:** independent two-pass original ZIP inspection, confirmed defect reproduction, repair, and regression proof.

## Confirmed issues and closure

| ID | Severity | v0.1.0 problem | 0.1.1 repair / validation |
|---|---|---|---|
| CV-01 | High | Any PNG with matching dimensions could be reused as a Blender-rendered frame. | Require signed, scene-bound hashes in benchmark/progress/shot receipts; unsigned frames are rerendered; regression PASS. |
| CV-02 | High | Encoder could regard incomplete signed frame-hash maps as sufficient. | Require exactly the expected filenames and full shot metadata; sparse receipt rejection PASS. |
| CV-03 | High | Encoded staging fingerprint omitted actual frame bytes; edited frames could reuse stale segments. | Fingerprint actual signed frame hash maps and inspect cached segment/video SHA; changed-frame/tamper tests PASS. |
| CV-04 | High | `production_status` advanced an arbitrary valid MP4 without a rig/provenance. | Require validated rig, graph and matching technical delivery receipt; regression PASS. |
| CV-05 | Medium | Shot contract accepted unsupported fractional FPS, empty title and invalid scene types. | Require integer FPS and valid nonempty source metadata; regression PASS. |
| CV-06 | Medium | Rig proof did not check sample-frame alignment or cyclic parent chains. | Reject mismatched frames, nonfinite quaternions and cycles; regression PASS. |
| CV-07 | High | Standalone Skill ZIP omitted conditional references and release test metadata. | Self-contained references, trigger/non-trigger/negative fixtures, VERSION, CHANGELOG; release certificate PASS. |
| CV-08 | Medium | Review extraction launched FFmpeg separately for every shot frame and reused old review images. | One-pass sample extraction to unique review directory plus MP4 verification; freshness tests and speed benchmark PASS. |
| CV-09 | Medium | The Python wheel excluded Blender subprocess scripts. | Package the `blender` worker module in the wheel; actual wheel built, installed into clean venv and CLI preflight executed. |
| CV-10 | Medium | CLI could leak traceback when optional MCP SDK absent. | Return structured BLOCKED instead; regression PASS. |
| CV-11 | Medium | Malformed ffprobe frame/duration strings could crash parsing. | Treat unknown counts/durations as validation failures; regression PASS. |
| CV-12 | High | Multi-armature scenes could certify only the largest rig while leaving other puppets unverified. | Blender probe now fails closed if more than one armature is present; multi-character certification remains outside this release. |
| CV-13 | Medium | Audio mux pathway lacked a source-audio positive integration fixture. | Added real FFmpeg sine-wave AAC mux/frame/duration/subtitle-off integration test; PASS. |

## Remaining blockers and risks

- **Blender live integration BLOCKED by environment:** no Blender executable, no actual `.blend` rig probe or 3D film sample completed here.
- **MCP live integration BLOCKED by environment:** no installed SDK, no stdio/HTTP protocol handshake, no remote authenticated ChatGPT connection.
- **Visual/canon/user access NOT CERTIFIED:** there is no character-performance footage, human/vision G7 approval or independently opened G8 link.
- **External `.blend` asset dependencies NOT hashed by current render key:** explicit workspace asset locking is required before production reuse.
- **Multi-armature/multi-character films unsupported by v0.1.1 proof:** fail closed; future extension requires each character separately certified.
- **Local HMAC is a trusted-workspace integrity check, not tamper-proof against a compromised local user.**
- **Rig script version/API behavior unverified against live Blender:** no smoke test should be waived.
- **MCP SDK API shape matches documented v2 but no working host transport was observed.**

## Verdict

**LOCAL PACKAGE PASS / SKILL RELEASE PASS / BLENDER DEPLOYMENT UNVERIFIED / MCP CONNECTION UNVERIFIED.** Do not call this a fully installed production studio or claim FINISHED_VERIFIED.
