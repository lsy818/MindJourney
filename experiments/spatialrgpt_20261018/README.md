# MindJourney on SpatialRGPT-Bench quantitative (2026-10-18)

Status: eight adapter tests and three synthetic OpenRouter checks passed.
All 749 input file sets transferred and verified on DAAI. Six-case preflight
v2 submitted as Slurm job 90197 (two-hour allocation limit). Job 90195 failed
before any rendered prediction or API call because frozen SVC expects the raw
source at `step_0/img_0.png`. The v2 adapter stages that exact filename, with a
regression test for raw-to-SVC / marked-to-VLM isolation. Frozen SVC is unchanged;
the failed run remains preserved. No benchmark accuracy reported yet.
Progress is tracked in [results/RESULTS.md](../../results/RESULTS.md).

## Protocol

All 749 quantitative records from the three original SpatialRGPT Parquet files:
direction 107, distance 148, horizontal distance 122, vertical distance 106,
width 133, height 133. The source contains 1406 records in total. The input
manifest SHA256 is `e970446093596ecd21e53f9e064ffe361f3f332e0340cf2fb49a2e35576e4aba`.
`SOURCE_INPUT_VERIFIED.json` records independent alignment of every selected ID,
question, raw RGB pixel array, box, and decoded RLE mask to the Parquet source.

Input preparation uses the shared zero-based Region[i] labels, mask overlay
alpha 0.28, and boxes. Original marked images are supplied to the VLM without
local resizing/cropping. Provider-side image preprocessing is not controlled.
The unmarked RGB image alone conditions SVC, with the original pipeline's
short-side-512 staging resize. Generated images have no pasted region labels;
cross-view correspondence is inferred by the VLM. Reference-view instructions
remain explicit. Other methods' geometry/generated caches are never read.
Ground truth is loaded only by the offline scorer, never by the worker.

## Fixed inference settings

- Model for both ranking and answering: `deepseek/deepseek-v4.1-flash` through
  OpenRouter; not the 1017 variant. Route: `deepinfra/fp8`, fallbacks disabled.
  This third-party FP8 route differs from the September official DeepSeek API.
- `max_tokens=8192`, reasoning `none`, temperature 0, top_p 1.
  JSON schema is submitted, with strict local parsing; server enforcement is
  not assumed. At most eight identical-payload network attempts per logical call.
  Authentication/payment failures stop without retries or automatic recharge.
- Original SVC search depth 3, beam width 2, exploration/helpfulness thresholds
  8/8, up to 18 selected views; at most six rank calls and one answer call.
- Original movement primitives 0.25 m and 9 degrees; expansions 0.75 m and
  27 degrees; maximum consecutive forward 1.5 m / turn 60 degrees.
- SVC requested settings: num_frames 9, num_targets 8, interval 3, CFG 4, guider 1, L_short 576,
  20 denoising steps, seed 23; original image-to-trajectory video task and
  interpolation strategy. Model/AE/CLIP revisions and weight hashes are pinned
  in `environment.sh`.
- Saved-video detail: the frozen SVC model uses context `T=17`; its interpolation
  prior logic retains 16 anchor frames and saves the first-pass prior video.
  Thus `pred.mp4` has 16 frames, not 9. The first completed development item
  passed independent receipt / source-pixel checks, and all 15 candidate videos
  decoded to these 16 frames. This is inherited behavior; no settings were changed.
- DAAI Slurm A100 80 GB, existing Python 3.12 / Torch 2.9.0 SVC environment.
  No 3090 jobs. API credentials are private, outside the checkout.

`frozen/` is a byte-identical 60-file copy of the prior September v25 SVC
implementation; `FROZEN_SOURCE_SHA256.json` pins each file. The adapter preserves
its search/ranking/generation loop. Necessary changes: answer-free input loader,
raw/marked routing, OpenRouter transport, numeric/clock answer protocol,
private audit receipts, and offline scoring. `test_adapter.py` verifies the
search core against the frozen source and tests schema/scoring boundaries.

## Validation and reporting

Six predetermined development IDs (one per category, from the common manifest)
are used for end-to-end preflight, without accuracy-based selection or tuning.
The full run requires an explicit passed preflight with matching source hashes.
Each item records final answer, status, latency, VLM calls, SVC candidate calls,
all network attempts/usage, and private trace location. Existing terminal items
are not replayed; incomplete traces require inspected recovery.

Only final answers are scored using the fixed WorldLoop implementation at
`e66d5f5cf4c42687fc250ca84e638c926bfa9e10`, scorer SHA256
`5acac7af6f0c7459740a05e0e81ea5cee56f2df557f1d2e1891a9979961040d0`.
Metric tolerance is 25% inclusive; direction uses circular clock distance at
most one hour. Every one of the 749 IDs remains in the denominator, including
invalid/missing/failed answers. Per-category and weighted overall accuracy,
coverage, status counts, latency, calls, and known/unknown API cost are reported.
Partial progress is never presented as a full-benchmark score.

Raw questions, images, labels, API payloads/responses and detailed traces remain
private on the authorized servers. Public files contain code, settings, counts,
hashes and aggregate results only.
