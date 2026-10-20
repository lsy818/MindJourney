# MindJourney × SpatialRGPT-Bench: local Qwen FP8 runs

Status (2026-10-20): preparation and synthetic compatibility validation. **No formal Qwen result yet.** The two model weight snapshots passed full-file verification. This document distinguishes intended settings from the configuration that will be frozen after preflight.

| Run | Quantized weight repository | Pinned revision | Base model |
|---|---|---|---|
| First | `Qwen/Qwen3.5-27B-FP8` | `97f5941bf617e31c5e237364a8602ce3f03a551a` | `Qwen/Qwen3.5-27B` |
| Second | `RedHatAI/Qwen2.5-VL-72B-Instruct-FP8-dynamic` | `f8823f1615cfc3cf40c5a8f3da5a24ece52cc2b8` | `Qwen/Qwen2.5-VL-72B-Instruct` |

The quantized publishers identify the base repositories but do not establish an exact base-weight commit in the inspected metadata. A current upstream base revision must not be represented as proof of that quantization provenance. The actual deployed quantized revisions are pinned above. See [model/configuration hashes](model_pins.json).

27B uses publisher FP8 block weights (128×128) with dynamic activation configuration and publisher exclusions. 72B uses compressed-tensors FP8 channel-wise weights and dynamic token-wise activations with publisher exclusions. These stored configurations do not imply native FP8 arithmetic on A100. The initial 27B load on A100 selected Marlin weight-only FP8 compression, with BF16 activation computation; it allocated approximately 28.9 GiB for model loading. This is an observed initialization path, **not yet a passed end-to-end benchmark**. No other model or dense-weight precision substitute is authorized. Final reports must include the actual per-model kernel path, memory and measured throughput.

## Original protocol to preserve

Both runs use the same original 749 IDs, order, questions, RGB/marked images and region annotations as the original DeepSeek experiment. Category counts: Direction 107; Distance 148; Horizontal distance 122; Vertical distance 106; Width 133; Height 133. The original six development IDs count toward each model's 749; only 743 remain after successful preflight. Models have separate searches, output/video/request ledgers and audits; no DeepSeek search trajectory or answer reuse.

- temperature 0, top_p 1, max_tokens 8192. Qwen3.5 explicitly disables thinking; Qwen2.5-VL uses its own non-thinking template without an unsupported thinking argument. The service will use `generation_config=vllm` and explicit request parameters, with effective behavior checked before admission.
- Original task prompts, JSON schema and strict local parsing. The seven-answer DeepSeek repair protocol is **excluded**. The gateway records the original schema in the request ledger; it omits `response_format` at the vLLM engine boundary so vLLM does not add new server-enforced guided decoding. That boundary transformation is explicit and audited, not a claim of identical provider-side schema enforcement.
- SVC depth 3, beam 2, thresholds 8/8, at most 18 selected views. Requested frames 9, targets 8, interval 3, CFG 4, guider 1, L_short 576, 20 steps, seed 23. Preserve the frozen implementation's actual **16 saved frames**.
- Base movement 0.25 m / 9°, expansion 0.75 m / 27°, limits 1.5 m / 60°. Original marked image and 0.28 alpha overlay, boxes and zero-based Region[i], image order; raw RGB short-side-512 staging for SVC; no added region labels on generated views.
- No image removal, input-resolution reduction, context truncation, answer cherry-picking or silent precision fallback. Eight total attempts per identical payload, including restarts. Saved valid responses and videos within one model are reused; uncertain requests are looked up before any further action. Exhausted format failures remain in the 749 denominator.
- Fixed WorldLoop length tolerance 25%, inclusive; circular clock distance at most one hour. Independent full-source coverage/retry/answer audit and `FINAL_VERIFIED` required before a final score.

Input manifest SHA-256: `e970446093596ecd21e53f9e064ffe361f3f332e0340cf2fb49a2e35576e4aba`.

Labels SHA-256: `41752ec0a02365571d712f717d0e1c73f9cc8ddc3aea1dc4217d79380b335c2a`.

Scorer SHA-256: `5acac7af6f0c7459740a05e0e81ea5cee56f2df557f1d2e1891a9979961040d0` (WorldLoop `e66d5f5cf4c42687fc250ca84e638c926bfa9e10`). All 60 original frozen SVC source files remain byte-identical.

## Deployment preparation and resource boundaries

Independent model environment: vLLM distribution `0.31.0+cu129`, Torch `2.13.0+cu129`, Transformers `5.17.0`, compressed-tensors `0.17.0`, Triton `3.7.1`. The initial environment archive included a CUDA-13-linked TorchCodec, so an isolated official `torchcodec 0.16.0+cu129` overlay is used; wheel SHA-256 `1d103c30631a2c04b2acd1602a56af7762d41051700d2077c2b6a964dbcf7f2c`. Original SVC environment remains unchanged. Complete effective launch settings, templates, preprocessing and execution receipts are pending preflight.

Intended allocation: 27B one model GPU + six SVC GPUs; 72B two model GPUs within one node + five SVC GPUs. If the original long multi-image input cannot fit 72B on two GPUs, use four model GPUs on one node and three SVC GPUs on the other. Per-allocation steps and a shared durable item queue; one SVC worker per video GPU. Concurrency changes are calibrated before formal configuration freeze.

Jobs 90438 (four A100 PCIe 80GB; expires 2026-10-24 13:39:50 Asia/Shanghai) and 90247 (three A100 SXM4 80GB; expires 2026-10-23 22:09:27) must remain allocated after experiment completion or failure. Both have live resource-holding mechanisms. 90247 still has existing model services requiring safe handoff; it is not reported as three free GPUs. Neither job has been cancelled or renewed by this experiment. Local inference will report measured GPU time, not fictitious API costs.

Preflight and final scores, logical calls, video generation counts and elapsed times will be added only when verified. The preliminary 8–15 h / 12–22 h budgets are not measured seven-GPU estimates and exclude preparation and audit.
