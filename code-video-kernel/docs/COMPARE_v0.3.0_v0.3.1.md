# Code Video 0.3.0 vs 0.3.1 — Technical comparison

| Capability | 0.3.0 | 0.3.1 | Evidence |
|---|---|---|---|
| VTK skinned MP4 | 12s, 288 frames | Preserved | 51 original regression tests included |
| Portable editable skeletal asset | No verified GLB handoff | Real animated `.glb` | GLB parsed and independently loaded |
| Skeleton/mesh animation | VTK NumPy LBS | Real glTF skins, inverse binds, node animations | 289x4 vertex deformation reconstruction |
| Non-root rotating joints in GLB | No | 9 | Read-back of exported animation channels |
| Weighted continuous limb meshes | 4 in VTK | 4 in glTF with JOINTS_0/WEIGHTS_0 | Read-back and rest-mesh equality checks |
| Native Blender import | Not executed | Fail-closed import worker prepared | Syntax checks only; host not available |
| Automated Python tests | 51 | 68 | Local pytest |
| MCP adapter registered methods | 20 | 24 | Mock registration test only |
| Actual Blender MP4 | Unverified | Still unverified | No Blender host |
| ChatGPT MCP connection | Unverified | Still unverified | No authenticated handshake |

**Verdict:** 0.3.1 materially improves portable *asset* completeness and interoperability testing. It is not a demonstrated upgrade in Blender-rendered film quality. It inherits the v0.3.0 MP4 evidence, not a new film.
