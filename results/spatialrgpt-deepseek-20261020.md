# MindJourney SpatialRGPT-Bench 最终交付（2026-10-20）

## SpatialRGPT-Bench 定量子集（749 题）

| 模型 | 方法 | 平台 | 当前状态 | 正确 / 总数 | Overall |
|---|---|---|---|---:|---:|
| `deepseek/deepseek-v4.1-flash`（非 1017） | MindJourney / SVC | DAAI A100 + OpenRouter / DeepInfra FP8 | 全量完成，独立审计通过（2026-10-20） | 374 / 749 | **49.93%** |

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| Direction | 74 / 107 | 69.16% |
| Distance | 68 / 148 | 45.95% |
| Horizontal distance | 43 / 122 | 35.25% |
| Vertical distance | 53 / 106 | 50.00% |
| Width | 59 / 133 | 44.36% |
| Height | 77 / 133 | 57.89% |
| **Overall（按题数加权）** | **374 / 749** | **49.93%** |

749 个原始 ID 全覆盖、无重复：6 道预检结果复用，加 743 道正式结果；742 道有效答案、7 道严格单位解析失败。失败题保留全部原始响应并计 0 分，仍纳入 749 题分母。使用固定 WorldLoop 评分器：长度误差容限 25%（含边界），方向为循环时钟距离不超过 1 小时。最终来源、文件 SHA、图片、重试与费用独立审计通过。

共 3,355 次逻辑 VLM 调用、3,446 次网络尝试、4,416 次 SVC 候选生成调用。已记录 API 费用 **1.7269897512 USD**；另有 **24 次费用未知**，不能将已知费用当作完整实付总额。该费用口径覆盖本次 749 题的全部保留尝试；独立合成 API 测试已知费用 0.00006034 USD 单列，不包含在上述金额内。

运行沿用原 SVC 设置及固定模型路由。传输修复后复用了已保存结果、有效响应和视频，330 个旧文件 SHA 保持不变。仅一个历史耗尽 payload 按修复后续跑授权成功执行编号 9；其余同 payload 总上限为 8。7 道无效题均未增加第 9 次或放宽解析。大请求通过服务器内部 SSH 承载的端到端 TLS 通道传输，无本机 API 数据中转。五天四卡资源池独立于实验，完成后继续保留。

最终验收回执 SHA-256：`441b28ee1af3d89c7d21691f1f74b38f6c531ed1bdb546041a384f53ba6e80b9`。最终汇总 SHA-256：`a6ee39d828f696b6a8df1260c2d7c7b4e36c320b3e3cf070e37a60e39b09bbec`。

[设置与适配说明](../experiments/spatialrgpt_20261018/README.md) · [最终交付报告](./spatialrgpt-deepseek-20261020.md)。本次 OpenRouter 第三方 FP8 路由与下方历史官方 DeepSeek API 分别标注。原始题图、答案、请求响应和详细审计仅保留于私有服务器。

## 固定设置与审计依据

- OpenRouter `deepseek/deepseek-v4.1-flash`，`deepinfra/fp8`，不允许路由回退；temperature 0、top_p 1、max_tokens 8192、reasoning none。提交 JSON schema 并进行严格本地解析，不假定服务器强制 schema。
- SVC depth 3、beam 2、阈值 8/8；9 requested frames、8 targets、interval 3、CFG 4、guider 1、L_short 576、20 steps、seed 23。冻结实现实际保存 16 帧视频，保持原行为。
- WorldLoop commit `e66d5f5cf4c42687fc250ca84e638c926bfa9e10`，评分器 SHA-256 `5acac7af6f0c7459740a05e0e81ea5cee56f2df557f1d2e1891a9979961040d0`。
- 输入 manifest SHA-256 `e970446093596ecd21e53f9e064ffe361f3f332e0340cf2fb49a2e35576e4aba`；标签 SHA-256 `41752ec0a02365571d712f717d0e1c73f9cc8ddc3aea1dc4217d79380b335c2a`。
- 独立审计器 SHA-256 `e185abff08d981e45f4f2efde253be3917b7c33b53387a69624a3a0ffd4d8b92`；终态验证器 SHA-256 `bc8a9628993ef971b638802fe3044eb9ead63b68123cc38b408668069969f5bc`。
- 7 道无效答案按预定规则计零；不选择重试中最有利答案，不删除失败题。此前针对其中 3 道的只读解析诊断发现百分号或泛称 unit，不是合法长度单位；21 个标准单位测试通过。未改变冻结提示、解析器或评分器。

本报告只包含汇总、设置与哈希；逐题来源、原始响应、视频和失败记录均在 DAAI 私有归档中保留。
