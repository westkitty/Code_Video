# Champion versus challenger — Code Video v0.2.0 to v0.3.0

| Property | v0.2.0 baseline | v0.3.0 challenger |
|---|---|---|
| Core automated tests | 46 | 51 |
| MCP tool definitions | 14 | 20 (registration fixture only, connection unverified) |
| Actual rendered 3D | VTK volumetric, rigid segmented | VTK 3D + four deformable, weighted skinned limb meshes |
| Performance length | 6s, 144 frames | 12s, 288 frames |
| Physically grounded foot/contact | Not demonstrated | Analytic two-link IK, fixed feet, explicit sphere grip and transfer |
| Shot render recovery | One bounded stage project | Three disjoint signed 96-frame shot batches and hash-constrained assembly |
| Face/head | independently moving segmented controls | Genuine parented 3D face/head yaw assembly |
| Source editable | Static rig+pivots in Python, JSON keyframe tracks | JSON actor performance curves, authored native Blender scene builder |
| Native Blender armature rig | Unverified | Still unverified; authored scene generator only |
| Live ChatGPT MCP | Unverified | Still unverified |
| Actual cinematic acting | Technical demo | More legible intent, still stylized prototype |

**Verdict:** v0.3.0 SURPASSES v0.2.0 on tested deformable geometry,
contact staging, meaningful shot sequence and recovery granularity.
It does not satisfy the final Blender-certified film or live deployment contract.

Biggest next proof: run the Blender builder under an authorized host,
inspect evaluated bone and skinned vertex changes in the actual scene,
then render and decode that native film, correcting any worker issues surfaced by real `bpy` execution.
