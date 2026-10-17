# Blender Native Rig Integration Gate

`blender/create_organic_reach.py` is an **authored and syntax-checked worker**, not an
executed Blender certification. Run only on an authorized machine that truly has Blender.
Use original noncanonical assets for its benchmark. It builds an armature with parented
bones, continuous limb meshes, normalized vertex groups and an ARMATURE modifier. It
creates camera markers for the three shots and attempts to keyframe the deterministic IK
performance. Independent Blender evaluation is MANDATORY before promotion.

Requirements to mark Blender PASS:
- Actual `.blend` saved, reopened, and inspected through Blender, with all modifiers and
  vertex groups present and bound to the correct armature.
- Root and camera fixed during neutral/extreme pose images; at least four independent
  non-root parent-relative joints move and deform evaluated skin geometry.
- IK reaches, planted feet, prop grasp and object ownership tested in evaluated scene.
- Multi-angle stress-pose renders prove seams and silhouette; camera markers and cuts
  tested in Blender render, not inferred from source.
- MP4 encode, full decode, audio/subtitle checks and shot-level visual review.

If any of these are missing, mark `BLENDER_ARMATURE_UNVERIFIED`. The VTK actor results
must never be treated as a Blender runtime test.

## v0.3.2 real-native shot pipeline

The portable-GLB import worker additionally creates `CodeVideo_Shot_01/02/03` cameras, a graphite stage and frame markers. The new separate worker renders real camera views only from the verified native scene. `native-finish` creates a `.blend` and an encoded silent 12-second benchmark **only if Blender actually runs**. Exact shot ranges are 1–96, 97–192 and 193–288. No output from a Blender-missing environment is a valid native film. See [native film contract](native-film.md).
