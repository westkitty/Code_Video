# Performance evidence — 2026-10-16 (v0.1.0 versus v0.1.1)

Measured on the same isolated Python/FFmpeg container, Python 3.13.5; no Blender or MCP SDK. These are *execution measurements for narrow workloads*, not proof of real Blender GPU performance or full-film rendering speed.

## Matched 10-shot visual review extraction

- Input: one 5-second H.264 video, 64×64, 30fps, ten 15-frame shots; 30 review frames per run.
- Cold output directory for every sample; three separate subprocess invocations per revision.
- Original v0.1.0: 2.799s, 2.827s, 2.776s, **mean 2.801s**.
- Repaired v0.1.1: 0.957s, 0.982s, 0.992s, **mean 0.977s**.
- **65.1% lower mean wall time** on this microbenchmark. v0.1.1 also performs its own full decoded-video verification, unlike the original extraction path. One FFmpeg select pass replaces 30 independent launches.

## Matched original 23-test suite

- v0.1.0 wall times: 3.134s, 3.255s, 3.173s, mean **3.187s**.
- v0.1.1 wall times: 3.183s, 3.235s, 3.800s, mean **3.406s**.
- The stricter version is **6.9% slower** on this three-run sample; likely variance and validation overhead, not evidence of improved overall kernel throughput. Do not claim a universal speedup.

## Structural Skill performance

- Original Skill: 43 lines, 607 words, zero bundled references or trigger/regression tests. Original release certification BLOCKED.
- Repaired Skill: 62 lines, 1,039 words, two conditional references and three fixture suites; certification PASS. Increased context weight is deliberate for stronger decision gates, not a measured host behavior improvement.
- Host Skill auto-trigger routing, invocation latency, MCP negotiation and actual render times are **UNMEASURED**.

## Next performance checks

Benchmark real Blender skinning evaluation, scene-load overhead, shader compilation, shot render time, resource exhaustion, resumable partial renders and long-song shot extraction on the authorized target machine. Record matched cold/warm results and compare cache-preserving vs clean-restart renders. No performance claim should be generalized from these synthetic tests.
