# Actor Engine v0.3.0 — Executable Proof Boundary

The Golden Scene uses the same deterministic performer and 288-frame 12-second contract
across three separately signed VTK shots. The actor has continuous volumetric arm and leg
meshes with normalized two-bone vertex weights. The renderer evaluates 3D XZ IK targets,
updates actual mesh positions and normals, fixes both feet in world coordinates, and
attaches the orb to the hand after 9.3 seconds. The head/face assembly actually yaws.

## Producer sequence
1. `codevideo actor-batch shot1 0 96`
2. `codevideo actor-batch shot2 96 96`
3. `codevideo actor-batch shot3 192 96`
4. Validate each with `codevideo actor-batch-check RECEIPT`.
5. `codevideo actor-assemble final RECEIPT1 RECEIPT2 RECEIPT3`.
6. `codevideo actor-assembly-check projects/final/assembly_receipt.json`.

Do not equate batch status PARTIAL with failure: each 96-frame batch is partial BY DESIGN;
its signed `actor-batch-check` must PASS. Neither a signed batch nor the assembled technical
PASS certifies subjective acting, lip sync, artistic identity, public delivery or Blender.

Critical negative cases: missing frame, tampered scene, unsigned batch, mixed source,
duplicate/missing time interval, unreachable IK, negative/non-normalized weights,
unplanted foot, arbitrary subtitle, invalid .blend claim.
