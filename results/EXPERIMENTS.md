# MindJourney 实验结果与计划

最后更新：2026-09-06（Asia/Shanghai）

本文件同时记录实验优先级和已验证的实验产物。优先级数字越小，优先级越高；`P0` 表示用户指定为已经运行的项目，但只有带有正式 `COMPLETE`、可复核结果文件和哈希的项目才记为“已验证完成”。

## 结果保留约定

1. `results/` 采用追加式归档。不要删除或覆盖已有 run；重跑时创建新的 run ID。
2. Git 中保存紧凑且可复核的结果：合并结果、分片结果、配置、运行/提交清单和完成标记。
3. 大型逐题图像、视频和日志继续保留在 DAAI 原始运行目录，不复制进 Git，也不得删除。
4. 完成一项实验后，必须登记数据快照、模型 revision、thinking 模式、方法配置、Slurm ID、结果路径、指标及 SHA256。
5. 所有归档产物的逐文件校验值见 [SHA256SUMS](./SHA256SUMS)。

## 实验优先级矩阵

| 数据集 | Qwen3.5-27B | Qwen2.5-VL-72B-Instruct | Qwen3.5-9B | Qwen3.8-27B |
|---|---|---|---|---|
| MindCube 1050 | P1 · 准备中 | P1 · 准备中 | P3 · 待跑 | P3 · 待跑 |
| MMSI-Bench 1000 | P0 · 用户称此前已跑，产物待定位/验证 | P0 · 用户称此前已跑，产物待定位/验证 | P1 · 准备中 | P1 · 准备中 |
| SAT Real | P0 · **已验证完成** | P0 · 用户称此前已跑，产物待定位/验证 | P2 · 待跑 | P2 · 待跑 |
| SAT Syn (`rand42-500`) | P0 · **已验证完成** | P4 · 待跑 | P4 · 待跑 | P4 · 待跑 |

用户后续指令已确认第 1、2 行分别对应 MindCube 1050 与 MMSI-Bench 1000。`Qwen3.8-27B` 的规范模型 ID 已确认为 `Qwen/Qwen3.8-27B`。当前先完成四项 P1：MindCube 1050 的 Qwen3.5-27B、Qwen2.5-VL-72B-Instruct，以及 MMSI-Bench 1000 的 Qwen3.5-9B、Qwen3.8-27B；高优先级分片完成并验证后再进入 P2/P3/P4。

## P1 准备与运行状态

| 数据集 / 模型 | 数据 | 权重 | Smoke | 全量分片 | 结果文件 |
|---|---|---|---|---|---|
| MindCube / `Qwen/Qwen3.5-27B` | 1050 题及完整原始图片树已就绪并严格验证 | 已就绪；revision marker 已验证 | 首次 Job `65458` 因节点缺少系统 `ninja` 失败；修复后的 Job `65469` 在 `hkbugpusrv15` 运行 24:08 后失败，退出码 `1:0`，日志根因待恢复 DAAI 连接后核验 | 未通过；不得提交全量 | DAAI: `/home/comp/tyjiang/mindjourney_runtime/p1_runs/mj-p1-mindcube-qwen35-27b-smoke-20260905T160025Z` |
| MindCube / `Qwen/Qwen2.5-VL-72B-Instruct` | 1050 题及完整原始图片树已就绪并严格验证 | 固定 revision 下载中；Job `65446` | 等待权重完整性 marker | 等待 smoke 通过 | — |
| MMSI-Bench / `Qwen/Qwen3.5-9B` | 1000 题 / 2550 图已就绪并严格验证 | 已就绪；revision marker 已验证 | 首次 Job `65452` 因节点缺少系统 `ninja` 失败；修复后的 Job `65468` 在 `hkbugpusrv15` 运行 35:05 后失败，退出码 `1:0`，日志根因待恢复 DAAI 连接后核验 | 未通过；不得提交定向 smoke 或全量 | DAAI: `/home/comp/tyjiang/mindjourney_runtime/p1_runs/mj-p1-mmsi-qwen35-9b-smoke-20260905T155306Z` |
| MMSI-Bench / `Qwen/Qwen3.8-27B` | 1000 题 / 2550 图已就绪并严格验证 | 固定 revision 下载中；Job `65447` | 等待权重完整性 marker | 等待 smoke 通过 | — |

- 推理统一使用 BF16 和 no-thinking；Qwen2.5-VL 不发送其不支持的 Qwen3 thinking 参数。
- 正式计算只在 DAAI 运行。H20 96GB 空闲时优先；否则使用 A100 80GB，并排除 40GB DGX。硬件切换不得改变 SVC/搜索参数。
- 每个组合必须先完成一题端到端 smoke，再提交正式数组；“已提交/排队”不等于“已完成”。
- 统一配置：[p1_svc_multiimage.json](../configs/p1_svc_multiimage.json)。
- 本次提交前 H20 节点的 8 张卡均已占用，故两个已提交 smoke 按资源约定回退到 A100-80G；每次后续提交前仍会重新检查 H20，而不会把本次回退固化为实验设置。
- 首轮 smoke 的模型权重均已成功载入 GPU，但 FlashInfer 首次编译采样内核时在 A100 节点找不到裸命令 `ninja`。固定 Qwen 运行环境实际包含 `ninja 1.13.2`；提交代码已在 vLLM 子进程范围内补回该固定环境的 `bin`，未改变模型、精度、thinking 模式或 SVC 参数。修复 commit：`087be7a`。
- 标准 9B/27B 任务统一申请 8 CPU，72B 保持 16 CPU；续跑 Job `65468`、`65469` 的资源均已同步更新为 8 CPU。该调整只改变 Slurm 资源配额与线程上限，不改变 GPU 数、TP、BF16、提示、数据顺序或 SVC 算法设置。资源计划 commit：`8d8bd12`。
- Slurm accounting 已确认 Job `65468`、`65469` 均失败且没有可验证的 `COMPLETE`；因此没有触发任何后续全量提交。当前 Jumpmachine 可登录，但 DAAI 管理节点在目标认证后主动断开，须取得 attempt 日志后才能归因和安全续跑，不能仅凭退出码猜测。

## 已验证运行

| Run ID | 数据集 / 协议 | 模型 | 方法 | Thinking | 分片 | 结果 | 状态 |
|---|---|---|---|---|---:|---:|---|
| `mj-svc-qwen35-paper150-20260902T173648Z` | SAT Real / `SAT-Real-paper-exact-150` | `Qwen/Qwen3.5-27B` | SVC | `false` | 5 × 30 | **119/150 (79.33%)** | 已验证完成 |
| `mj-svc-qwen35-sat-syn500-20260903T185438Z` | SAT Syn / `SAT-Syn-user-rand42-500-paper-aligned` | `Qwen/Qwen3.5-27B` | SVC | `false` | 5 × 100 | **392/500 (78.40%)** | 已验证完成 |

### SAT Real 150

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement` | 23 / 23 | 100.00% |
| `obj_movement` | 19 / 23 | 82.61% |
| `goal_aim` | 26 / 34 | 76.47% |
| `action_conseq` | 31 / 37 | 83.78% |
| `perspective` | 20 / 33 | 60.61% |
| **总体** | **119 / 150** | **79.33%** |

- Slurm：初始数组 `64028`，恢复数组 `64071`，最终合并 `64072`。
- 合并结果：[results_merged.json](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/results_merged.json)
- 正式清单：[formal_run_manifest.json](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/formal_run_manifest.json)
- 完成标记：[COMPLETE](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/COMPLETE)
- 配置：[config.json](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/config.json)
- 合并结果 SHA256：`256b38dba9f2219cd055999ddc7cb0807de520a41f6ff2cf979e46224483ee0a`
- DAAI 原始运行目录：`/home/comp/tyjiang/mindjourney_runtime/formal_runs/mj-svc-qwen35-paper150-20260902T173648Z`

### SAT Syn 500

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement` | 99 / 100 | 99.00% |
| `obj_movement` | 75 / 100 | 75.00% |
| `goal_aim` | 89 / 100 | 89.00% |
| `action_consequence` | 74 / 100 | 74.00% |
| `perspective` | 55 / 100 | 55.00% |
| **总体** | **392 / 500** | **78.40%** |

- Slurm：初始数组 `64587`，恢复数组 `64865`，最终合并 `64866`。
- 合并结果：[results_merged.json](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/results_merged.json)
- 正式汇总：[formal_run_summary.json](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/formal_run_summary.json)
- 完成标记：[COMPLETE](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/COMPLETE)
- 配置：[config.json](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/config.json)
- 合并结果 SHA256：`f88d6ebfc52703b4be3283e57528304bd1f704619e9ebf7709f64e2744b9ca27`
- DAAI 原始运行目录：`/home/comp/tyjiang/mindjourney_runtime/formal_runs_sat_syn500/mj-svc-qwen35-sat-syn500-20260903T185438Z`
- 说明：该运行使用用户提供的 `rand42` 500 题子集。论文未公开 Table 2 的具体随机题号，因此方法设置与论文对齐，但不能声称题目子集完全相同。1 道最终答案解析失败并计为错误。

## MindCube 与 MMSI 预处理要求

在任何正式运行前，必须先锁定预处理产物及多图输入顺序；不能仅凭第三方脚本生成数据后直接运行。

### MindCube 1050

- 官方仓库：<https://github.com/mll-lab-nu/MindCube>
- 官方代码 commit：`b8b7062adf6d3e49d588a7d014a0a787553d09ec`。
- 官方 Hugging Face revision：`9c941b46a6bd65b6914669ef7a579948fc9c8467`。
- `MindCube_tinybench.jsonl`：1050 题，SHA256 `0289eb82d81ff9aa0201ae75f86da7fd1924cf23dc202856d0579a0effd22ac8`；`among/around/rotation = 600/250/200`，2/3/4 图题分别为 274/345/431，共 3307 次图片引用、428 张唯一图片、0 缺图。
- DAAI 正式输入：`/home/datasets/shiyang/MindCube_9c941b46/processed/test.json`，SHA256 `03a62d4928f790eb2dad9e18a9f5f65643342100b93955de80debea171e88083`；provenance SHA256 `55af7c4dd6e125b5323a798ba871d3297c6c89098f5911b6d84561af26effac6`；官方有序图片序列摘要 `0b092454a3ceb25f513f3f1428f1b9fad06cf4e297a7d754980521f0cce2abdb`。
- 第三方参考脚本（A100-2）：`/data/chentao/WorldLoop/examples/spatial_reasoning/prepare_data.py`
- 以官方 `images` 数组作为 `Image 1..N` 的唯一语义顺序；转换工具：[prepare_mindcube.py](../utils/prepare_mindcube.py)。

### MMSI-Bench

- 官方仓库：<https://github.com/InternRobotics/MMSI-Bench>
- 官方代码 commit：`13e58a2b8b30d880d7e8a1e4a6aa1c0feda94cac`；官方 Hugging Face revision：`ec7c92bfaf7728fcca1d61e3e224e190af309436`。
- 已核验的 A100-2 快照：1000 题、2550 张图、2–10 图；JSONL SHA256 `9448f3ffc9c2364d396ab29bfc5a66ecab26fcc076ce1b6b364bdcad7c721601`，逐题元数据与官方 revision 全量一致。
- DAAI 正式输入：`/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed/test.json`，SHA256 `5de75a94eebb2ad31b44ab0f33d7225c56157165292d8112e287c410f56180c9`；provenance SHA256 `a86a9aa8ce007f06af5667848b5f47c2b6999c68fa36d1964e08b4e7d9fd8da2`；图片树摘要 `1915bcb705e661d46bab44dd8fe9513153466bca458bef26d030235d9e9c07d9`。
- 第三方参考脚本（A100-2）：`/data/chentao/WorldLoop/smoke/build_mmsi_full.py`
- 转换工具：[prepare_mmsi_bench.py](../utils/prepare_mmsi_bench.py)；保留官方图片顺序与 A–D 标签，严格按答案字母计分。

### 多图 SVC 适配边界

- MindJourney 论文和公开实现原生针对 SAT；MindCube/MMSI 的运行记为 **paper-aligned SVC multi-image adaptation**，不得写成论文中的原生 benchmark row。
- 所有原始图片按 benchmark 官方列表顺序进入每次 VLM scoring 和最终回答 prompt；SVC 仍只以 `Image 1` 作为参考图生成想象视图，其余原始图片只作为题目上下文。
- `max_images` 固定为 MindCube 4、MMSI 10。输入验证会拒绝缺图、乱序、超限或题数不匹配，不能静默跳题。

### 正式运行前检查项

- 固定官方仓库 commit、原始数据版本及预处理脚本 SHA256。
- 对单图/多图样本分别抽查，记录原始图片列表、预处理输出顺序、MindJourney 读取顺序和最终模型输入顺序。
- 确认没有因排序、拼接、文件名遍历、resize 或 prompt 模板而改变图片语义对应关系。
- 第三方 WorldLoop 脚本只作交叉参考；出现差异时先回到官方实现和 benchmark 定义核实。
- 预处理验证通过后再按优先级分片提交，且先完成并验证高优先级任务。

## 尚待归档/确认

- 用户提到的 Qwen2.5-VL-72B-Instruct 既有结果尚未在当前正式运行目录和 fork 仓库中定位到；定位后再补充原始产物和验证状态，不能只录入口头准确率。
- 用户提到的 MMSI-Bench Qwen3.5-27B 既有结果同样需要定位并核验。
- 每次新增结果时保留旧 run，不覆盖当前两个已验证目录。
