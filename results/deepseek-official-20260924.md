# September DeepSeek official API: verified results and settings

These aggregate results were accepted on 2026-09-24 and are transcribed from
the final private delivery reports; no models or completed audits were rerun.

| Dataset | Correct / total | Accuracy |
|---|---:|---:|
| MMSI | 312 / 1000 | 31.20% |
| MindCube | 466 / 1050 | 44.38% |
| SAT-Syn | 340 / 500 | 68.00% |
| SAT-Real | 87 / 150 | 58.00% |

MindCube: Rotation 72/200 (36.00%), Among 243/600 (40.50%), Around
151/250 (60.40%). All 1050 original IDs were covered exactly once, with zero
missing or skipped items. Mixed-source merge and independent verification
finished on 2026-09-24 at 17:33:12 UTC.

## Settings

The model was the official DeepSeek endpoint's `deepseek-flash` alias (recorded
as V4.1 in the run), via the official Responses API. This is a different route
from the October OpenRouter experiment; third-party FP8 equivalence is not claimed.
Maximum output 8192, reasoning effort none, temperature 0, top_p 1. Submitted
JSON schema and strict local parsing were used; server-side schema enforcement
was not asserted. Up to eight same-payload attempts, including inherited failures.

The original dataset prompts, question IDs, image order and multiple-choice
scoring were retained. SVC depth 3 / beam 2; exploration and helpfulness
thresholds 8/8; up to 18 selected views. Primitive movement 0.25 m / 9 degrees;
expansion 0.75 m / 27 degrees; consecutive caps 1.5 m / 60 degrees.
Generation: 9 frames / 8 targets / interval 3, CFG 4, guider 1,
L_short 576, 20 steps, seed 23, original image-to-trajectory video pipeline.

The final recovery used ten RTX 3090 GPUs. Eight used frozen source v25;
two used v27, retaining GPU generation and random state while delegating the
CPU camera/exp/video encoding operations to an Intel host. Offline full-question
checks proved matching requests, image bytes and contexts before admission.
No frozen experimental data/prompt/API files were changed in that transition.

## Receipt hashes

| Dataset / receipt | SHA256 |
|---|---|
| MMSI merge | `5ad5922d12f105d665ebf37ad9c4978290b51ad30a283e79f3bcfaa64d690e26` |
| SAT-Real merge | `a073c48a87a359e1ded6c0dc9486a156880695a0f43048d798d6c6d3474526f5` |
| SAT-Syn merge | `33a57ac19153180d1029aa152a8b923ea0be4761d9d9c2cd17f83cd8a9e66f0d` |
| MindCube merge | `ceb24823f393235aa3cfd21d381b371fc08f74120b377fba26ab929d55af4ba4` |
| MindCube independent verification | `15c86e0c3628f6dc00be1eabfa6b489f59e26715c2e173138ca3b60944e887be` |
| MindCube merged results | `4b2953b8cae331bad5d6ae0162641e5ee4635573a96dc1d25c8cdf526af68225` |

Known-usage peak non-cache cost estimates: SAT-Real CNY 5.744108 (four unknown
usage attempts), SAT-Syn CNY 17.144948 (three unknown), MindCube CNY 60.582678
(seven unknown). These are estimates, not confirmed paid charges or total
experiment spend. Network attempts were deduplicated by original host/path/SHA,
including unused responses; inherited successful responses were not billed twice.

Private source reports: `DEEPSEEK_P3_FINAL_20260924.md`,
`DEEPSEEK_MINDCUBE1050_FINAL_20260924.md`, `DEEPSEEK_SATSYN500_FINAL_20260924.md`,
`DEEPSEEK_SATREAL150_FINAL_20260924.md`. Credentials, raw requests, answers,
images and per-item private traces are not published here.
