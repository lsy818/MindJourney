# MindJourney 全部实验结果汇总

最后更新：2026-09-12（Asia/Shanghai）

本文件维护 4 个数据集 × 4 个模型，共 16 组 **SVC** 实验的全量与分类结果。当前已归档 6 组完整结果，其余 10 组待补充可核验产物；“—”表示暂无可报告结果，不代表 0 分或从未运行。

**本表遵循用户原始清单，用户没有修改优先级。** 此前我将 MindCube/MMSI 的执行组合配反，旧 Run ID 及日志中的“P1”是错误执行清单的遗留命名，不代表用户要求的 P1 已完成。旧结果全部保留，正确四项 P1 已使用独立 Run ID 重启；详见[重启核对记录](./P1_RESTART_AUDIT_20260912.md)。

## 全部实验总览

| 数据集 | 模型 | 优先级 | 状态 | 正确 / 总数 | 准确率 | 结果文件 |
|---|---|---|---|---:|---:|---|
| MMSI-Bench 1000 | Qwen3.5-27B | P1 | 8192重跑排队 `70201_0` | — | — | [提交记录](./mmsi/qwen3.5-27b/svc/mj-p1-8192-mmsi-qwen35-27b-a100-r10-20260912/submission_initial.txt) |
| MMSI-Bench 1000 | Qwen2.5-VL-72B-Instruct | P1 | 8192重跑排队 `70202_0` | — | — | [提交记录](./mmsi/qwen2.5-vl-72b/svc/mj-p1-8192-mmsi-qwen25vl-72b-h20-r10-20260912/submission_initial.txt) |
| MMSI-Bench 1000 | Qwen3.5-9B | P3 | 已验证完成 | 288 / 1000 | 28.80% | [JSON](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/results_merged.json) |
| MMSI-Bench 1000 | Qwen3.8-27B | P3 | 已验证完成 | 208 / 1000 | 20.80% | [JSON](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen3.5-27B | P0 | 已验证完成 | 498 / 1050 | 47.43% | [JSON](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen2.5-VL-72B-Instruct | P0 | 已验证完成 | 416 / 1050 | 39.62% | [JSON](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen3.5-9B | P1 | 8192重跑；0–3启动中 `70200` | — | — | [提交记录](./mindcube/qwen3.5-9b/svc/mj-p1-8192-mindcube-qwen35-9b-a100-r10-20260912/submission_initial.txt) |
| MindCube 1050 | Qwen3.8-27B | P1 | 8192重跑排队 `70207_0` | — | — | [提交记录](./mindcube/qwen3.8-27b/svc/mj-p1-8192-mindcube-qwen38-27b-a100-r10-20260912/submission_initial.txt) |
| SAT-Syn 500 | Qwen3.5-27B | P0 | 已验证完成 | 392 / 500 | 78.40% | [JSON](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/results_merged.json) |
| SAT-Syn 500 | Qwen2.5-VL-72B-Instruct | P0 | 用户反馈已跑，结果待归档 | — | — | — |
| SAT-Syn 500 | Qwen3.5-9B | P2 | 结果待补充 | — | — | — |
| SAT-Syn 500 | Qwen3.8-27B | P2 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.5-27B | P0 | 已验证完成 | 119 / 150 | 79.33% | [JSON](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/results_merged.json) |
| SAT-Real 150 | Qwen2.5-VL-72B-Instruct | P4 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.5-9B | P4 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.8-27B | P4 | 结果待补充 | — | — | — |

当前版本：按用户要求改为 **8192最大输出、no-thinking**，独立r10从头重跑正确四项P1。15:58 MindCube/9B四片启动中、其余三组排队；新8192首题尚未核验。旧1024结果全部保留、不混合统计，详见[8192执行清单](./P1_OUTPUT8192_EXECUTION_20260912.json)及[实验日志](./EXPERIMENTS.md)。

16:15更新：MindCube/9B片0/2/4/5运行，片1/3因thinking标签检查失败、保留现场未重试；实际已保存产物确认8192。MMSI/27B新增1–2片`70214`排队。当前8×A100、10/10提交槽位，详情见[实时核验](./P1_OUTPUT8192_LIVE_AUDIT_20260912_1615.json)，不把失败片视为完成。

## 统计口径与设置说明

- 所有表格由对应合并结果的 `progress.<类别>.correct/wrong` 题 ID 列表重新计数，并与 `accuracy`、全量题数及无重复 ID 检查交叉核对；总体准确率为总正确数 ÷ 总题数，不是类别准确率的简单平均。
- 已归档结果均为 SVC，配置记录 `qwen_enable_thinking=false`、上下文上限 `65536`。BF16 等推理配置和模型/数据版本以各 Run 的正式清单及配置为准；本汇总不修改实验设置。
- MindCube/MMSI 是 **paper-aligned SVC multi-image adaptation**，不是论文原生 benchmark 成绩。保持官方原始图片顺序；SVC 以第 1 张原图生成视图，其余原图作为题目上下文。两类数据的已归档运行均采用固定 r8，正式记录中 `model_dtype=bfloat16`。
- SAT-Syn 使用用户提供的 `rand42` 500 题子集。论文未公开对应的确切随机题号，不能声称子集与论文完全相同；其中 1 道最终答案解析失败已计为错误。
- 原始分片、完成标记、配置及运行记录保留于各结果目录；逐文件哈希见 [SHA256SUMS](./SHA256SUMS)，详细运行历史与服务器路径见 [EXPERIMENTS.md](./EXPERIMENTS.md)。

## MMSI-Bench 1000

数据来源：[RunsenXu/MMSI-Bench](https://huggingface.co/datasets/RunsenXu/MMSI-Bench)。本次归档覆盖完整 1000 题；类别名称按结果文件保留。

### Qwen3.5-27B（P1）

8192版本已提交，首片 `70201_0` 排队；旧1024部分结果保留，不合并到本轮。见[执行清单](./P1_OUTPUT8192_EXECUTION_20260912.json)。

### Qwen2.5-VL-72B-Instruct（P1）

8192版本已提交，首片 `70202_0` 排队，3×H20。见[执行清单](./P1_OUTPUT8192_EXECUTION_20260912.json)。

### Qwen3.5-9B（P3）

MMSI-Bench 1000 全量 1000 题结果如下：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `Positional Relationship (Cam.–Cam.)` | 34 / 93 | 36.56% |
| `Motion (Cam.)` | 14 / 74 | 18.92% |
| `Positional Relationship (Reg.–Reg.)` | 25 / 81 | 30.86% |
| `Positional Relationship (Cam.–Reg.)` | 28 / 83 | 33.73% |
| `MSR` | 45 / 198 | 22.73% |
| `Positional Relationship (Obj.–Reg.)` | 22 / 85 | 25.88% |
| `Positional Relationship (Cam.–Obj.)` | 28 / 86 | 32.56% |
| `Positional Relationship (Obj.–Obj.)` | 20 / 94 | 21.28% |
| `Attribute (Meas.)` | 35 / 64 | 54.69% |
| `Motion (Obj.)` | 21 / 76 | 27.63% |
| `Attribute (Appr.)` | 16 / 66 | 24.24% |
| **总体** | **288 / 1000** | **28.80%** |

Run ID：`mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908`。

[合并结果](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/results_merged.json) · [正式汇总](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/formal_run_summary.json) · [完整归档目录](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/)

### Qwen3.8-27B（P3）

MMSI-Bench 1000 全量 1000 题结果如下：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `Positional Relationship (Cam.–Cam.)` | 18 / 93 | 19.35% |
| `Motion (Cam.)` | 18 / 74 | 24.32% |
| `Positional Relationship (Reg.–Reg.)` | 11 / 81 | 13.58% |
| `Positional Relationship (Cam.–Reg.)` | 31 / 83 | 37.35% |
| `MSR` | 28 / 198 | 14.14% |
| `Positional Relationship (Obj.–Reg.)` | 11 / 85 | 12.94% |
| `Positional Relationship (Cam.–Obj.)` | 13 / 86 | 15.12% |
| `Positional Relationship (Obj.–Obj.)` | 18 / 94 | 19.15% |
| `Attribute (Meas.)` | 30 / 64 | 46.88% |
| `Motion (Obj.)` | 22 / 76 | 28.95% |
| `Attribute (Appr.)` | 8 / 66 | 12.12% |
| **总体** | **208 / 1000** | **20.80%** |

Run ID：`mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908`。

[合并结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/results_merged.json) · [正式汇总](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/formal_run_summary.json) · [完整归档目录](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/)

## MindCube 1050

使用已核验的官方 1050 题快照，`among / around / rotation` 分别为 600 / 250 / 200 题。

### Qwen3.5-27B（P0）

MindCube 1050 全量 1050 题结果如下：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 213 / 600 | 35.50% |
| `around` | 140 / 250 | 56.00% |
| `rotation` | 145 / 200 | 72.50% |
| **总体** | **498 / 1050** | **47.43%** |

Run ID：`mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908`。

[合并结果](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/results_merged.json) · [正式汇总](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/formal_run_summary.json) · [完整归档目录](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/)

### Qwen2.5-VL-72B-Instruct（P0）

MindCube 1050 全量 1050 题结果如下：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 221 / 600 | 36.83% |
| `around` | 109 / 250 | 43.60% |
| `rotation` | 86 / 200 | 43.00% |
| **总体** | **416 / 1050** | **39.62%** |

Run ID：`mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908`。

[合并结果](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/results_merged.json) · [正式汇总](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/formal_run_summary.json) · [完整归档目录](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/)

### Qwen3.5-9B（P1）

8192版本已提交，数组 `70200` 分片0–5；0–3已分配GPU启动中，4–5候补。旧1024部分结果保留，不合并到本轮。见[执行清单](./P1_OUTPUT8192_EXECUTION_20260912.json)。

### Qwen3.8-27B（P1）

8192版本已提交，首片 `70207_0` 排队；旧1024部分结果保留，不合并到本轮。见[执行清单](./P1_OUTPUT8192_EXECUTION_20260912.json)。

## SAT-Syn 500

### Qwen3.5-27B（P0）

SAT-Syn 500 全量 500 题结果如下：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 99 / 100 | 99.00% |
| `obj_movement`（物体运动） | 75 / 100 | 75.00% |
| `goal_aim`（目标朝向） | 89 / 100 | 89.00% |
| `action_consequence`（动作结果） | 74 / 100 | 74.00% |
| `perspective`（视角判断） | 55 / 100 | 55.00% |
| **总体** | **392 / 500** | **78.40%** |

Run ID：`mj-svc-qwen35-sat-syn500-20260903T185438Z`。

[合并结果](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/results_merged.json) · [正式汇总](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/formal_run_summary.json) · [完整归档目录](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/)

原始类别键为 `action_consequence`，与示例图中的 `action_conseq` 均表示“动作结果”；此处保留原始键，便于核对。

### Qwen2.5-VL-72B-Instruct（P0）

用户反馈此前已跑；目前仓库未归档可核验的该组结果，分类及总体成绩待补充。

### Qwen3.5-9B（P2）

目前仓库暂无该组可核验的全量结果；分类及总体成绩待补充。

### Qwen3.8-27B（P2）

目前仓库暂无该组可核验的全量结果；分类及总体成绩待补充。

## SAT-Real 150

### Qwen3.5-27B（P0）

SAT-Real 150 全量 150 题结果如下：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 23 / 23 | 100.00% |
| `obj_movement`（物体运动） | 19 / 23 | 82.61% |
| `goal_aim`（目标朝向） | 26 / 34 | 76.47% |
| `action_conseq`（动作结果） | 31 / 37 | 83.78% |
| `perspective`（视角判断） | 20 / 33 | 60.61% |
| **总体** | **119 / 150** | **79.33%** |

Run ID：`mj-svc-qwen35-paper150-20260902T173648Z`。

[合并结果](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/results_merged.json) · [正式清单](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/formal_run_manifest.json) · [完整归档目录](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/)

### Qwen2.5-VL-72B-Instruct（P4）

目前仓库暂无该组可核验的全量结果；分类及总体成绩待补充。

### Qwen3.5-9B（P4）

目前仓库暂无该组可核验的全量结果；分类及总体成绩待补充。

### Qwen3.8-27B（P4）

目前仓库暂无该组可核验的全量结果；分类及总体成绩待补充。

## 后续维护规则

1. 每片完成后先核验并归档到原 Run 目录，在实验日志记录部分进度；未完整覆盖的数据不得冒充全量成绩。
2. 全量结果验证通过后，更新本文件对应总览行和分类表，同时链接合并 JSON、正式汇总/清单和归档目录。缺少原始证据的历史结果继续标为待补充。
3. 统计准确率保留两位小数；不要将不同模型、数据快照或 Run 的分片混合统计，不因解析失败而缩小总题数。
4. 保留已有结果和日志。新 Run 的结果追加归档，不覆盖或删除旧 Run；若替换本表展示的 Run，记录变更理由和旧 Run 链接。
5. 更新日期及受影响文件的 SHA256 后一起提交到仓库。未来优先级变更仅更新当前总览，保留历史运行命名与记录。
