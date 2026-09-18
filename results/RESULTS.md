# MindJourney 全部实验结果汇总

最后更新：2026-09-18（Asia/Shanghai）

本文件维护 4 个数据集 × 4 个模型，共 16 组 **SVC** 实验的全量与分类结果。当前已归档 8 组完整结果，其余 8 组待补充可核验产物；“—”表示暂无可报告结果，不代表 0 分或从未运行。

**本表遵循用户原始清单，用户没有修改优先级。** 此前我将 MindCube/MMSI 的执行组合配反，旧 Run ID 及日志中的“P1”是错误执行清单的遗留命名，不代表用户要求的 P1 已完成。旧结果全部保留，正确四项 P1 已使用独立 Run ID 重启；详见[重启核对记录](./P1_RESTART_AUDIT_20260912.md)。

09-18 21:52最新状态：正确P1仍2/4组全量完成。MMSI/27B片0/1/2/4已核验，3/5运行、6/7/8/9排队；72B片0/1/2已核验36/100、31/100、32/100，片3/4/5排队。账户2/5运行、10/10提交，使用4×A100，H20暂被其他作业占满。27B片1和72B片2完整日志已保留于服务器/本地，上传待授权。见[72B片2核验与补交记录](./records/P1_MMSI72B_SHARD2_20260918.json)。

## 全部实验总览

| 数据集 | 模型 | 优先级 | 状态 | 正确 / 总数 | 准确率 | 结果文件 |
|---|---|---|---|---:|---:|---|
| MMSI-Bench 1000 | Qwen3.5-27B | P1 | 片0/1/2/4归档；3/5运行，6/7/8/9排队 | — | — | [续跑清单](./records/P1_AUDITFIX_EXECUTION_20260912.json) |
| MMSI-Bench 1000 | Qwen2.5-VL-72B-Instruct | P1 | 片0/1/2核验；片3/4/5排队 | — | — | [提交记录](./mmsi/qwen2.5-vl-72b/svc/mj-p1-8192-mmsi-qwen25vl-72b-h20-r10-20260912/submission_initial.txt) |
| MMSI-Bench 1000 | Qwen3.5-9B | P3 | 已验证完成 | 288 / 1000 | 28.80% | [JSON](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/results_merged.json) |
| MMSI-Bench 1000 | Qwen3.8-27B | P3 | 已验证完成 | 208 / 1000 | 20.80% | [JSON](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen3.5-27B | P0 | 已验证完成 | 498 / 1050 | 47.43% | [JSON](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen2.5-VL-72B-Instruct | P0 | 已验证完成 | 416 / 1050 | 39.62% | [JSON](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen3.5-9B | P1 | 已验证完成（8192） | 453 / 1050 | 43.14% | [JSON](./mindcube/qwen3.5-9b/svc/mj-p1-8192-mindcube-qwen35-9b-a100-r11-20260912/results_merged.json) |
| MindCube 1050 | Qwen3.8-27B | P1 | 已验证完成（8192） | 578 / 1050 | 55.05% | [JSON](./mindcube/qwen3.8-27b/svc/mj-p1-8192-mindcube-qwen38-27b-a100-r11-20260912/results_merged.json) |
| SAT-Syn 500 | Qwen3.5-27B | P0 | 已验证完成 | 392 / 500 | 78.40% | [JSON](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/results_merged.json) |
| SAT-Syn 500 | Qwen2.5-VL-72B-Instruct | P0 | 用户反馈已跑，结果待归档 | — | — | — |
| SAT-Syn 500 | Qwen3.5-9B | P2 | 结果待补充 | — | — | — |
| SAT-Syn 500 | Qwen3.8-27B | P2 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.5-27B | P0 | 已验证完成 | 119 / 150 | 79.33% | [JSON](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/results_merged.json) |
| SAT-Real 150 | Qwen2.5-VL-72B-Instruct | P4 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.5-9B | P4 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.8-27B | P4 | 结果待补充 | — | — | — |

当前版本：**8192最大输出、no-thinking**。三组Qwen3使用非致命告警修复r11，已保存r10题按明确来源续接；72B保留r10。旧1024全部保留、不混合统计。MindCube/3.8与9B均全量11片完成；正确P1完成2/4组；详见[续跑清单](./records/P1_AUDITFIX_EXECUTION_20260912.json)及[实验日志](./EXPERIMENTS.md)。

16:15更新：MindCube/9B片0/2/4/5运行，片1/3因thinking标签检查失败、保留现场未重试；实际已保存产物确认8192。MMSI/27B新增1–2片`70214`排队。当前8×A100、10/10提交槽位，详情见[实时核验](./records/P1_OUTPUT8192_LIVE_AUDIT_20260912_1615.json)，不把失败片视为完成。

16:30更新：MindCube/9B片0/1/3/4累计四片被thinking标签检查拦截、暂不重试；片2/5继续。MMSI/27B首片、MindCube/3.8首片已启动；MMSI/27B片3–4新数组`70219`排队。详情及诊断边界见[实验日志](./EXPERIMENTS.md)。

## 统计口径与设置说明

- 所有表格由对应合并结果的 `progress.<类别>.correct/wrong` 题 ID 列表重新计数，并与 `accuracy`、全量题数及无重复 ID 检查交叉核对；总体准确率为总正确数 ÷ 总题数，不是类别准确率的简单平均。
- 已归档结果均为 SVC，配置记录 `qwen_enable_thinking=false`、上下文上限 `65536`。BF16 等推理配置和模型/数据版本以各 Run 的正式清单及配置为准；本汇总不修改实验设置。
- MindCube/MMSI 是 **paper-aligned SVC multi-image adaptation**，不是论文原生 benchmark 成绩。保持官方原始图片顺序；SVC 以第 1 张原图生成视图，其余原图作为题目上下文。旧结果采用固定 r8；本轮8192结果使用固定 r11，并明确保留r10已保存答案的逐题来源。正式记录中 `model_dtype=bfloat16`；不同输出预算分别归档，不混合统计。
- SAT-Syn 使用用户提供的 `rand42` 500 题子集。论文未公开对应的确切随机题号，不能声称子集与论文完全相同；其中 1 道最终答案解析失败已计为错误。
- 原始分片、完成标记、配置及运行记录保留于各结果目录；逐文件哈希见 [SHA256SUMS](./SHA256SUMS)，详细运行历史与服务器路径见 [EXPERIMENTS.md](./EXPERIMENTS.md)。

## MMSI-Bench 1000

数据来源：[RunsenXu/MMSI-Bench](https://huggingface.co/datasets/RunsenXu/MMSI-Bench)。本次归档覆盖完整 1000 题；类别名称按结果文件保留。

### Qwen3.5-27B（P1）

8192版本片0 `72732_0` 已核验归档：**32 / 100（32.00%）**，0skip；最后一次续跑24:03:49（不含之前尝试）。2题r10继承与98题r11答案来源明确，2道最终答案解析失败按原规则计错。607文件完整原始日志保留，见[片0核验与结果索引](./records/P1_MMSI27B_SHARD0_20260918.json)。这是分片成绩，不是1000题全量成绩。

8192版本片4 `71510_4` 已核验归档：**28 / 100（28.00%）**，0skip，耗时2天10:53:07。3道r10继承答案与97道r11新答案分别保留来源；8道最终答案解析失败按原规则计错。完整618文件日志包和原始检查点保留，见[核验与结果索引](./records/P1_MMSI27B_SHARD4_20260917.json)。这是分片成绩，尚无1000题全量成绩，不填入全量总览。

8192版本片2 `72732_2` 已核验归档：**38 / 100（38.00%）**，0skip；最后一次续跑27:14:50，100题均为r11答案。571文件完整原始日志保留，5道最终答案解析失败按原规则计错。见[片2核验与结果索引](./records/P1_MMSI27B_SHARD2_20260918.json)。这是分片成绩，不能替代1000题全量成绩。

09-18 15:13片1/3/5运行，保存91/79/11题；6/7/8/9排队。最后未提交的片9已补交为`73846_9`；旧72732数组已全部终止，27B跨数组总并发上限仍5。历史ENOSPC根因未确认，所有旧结果保留，不混入1024结果。

8192版本片1 `73395_1` 已核验归档：**32 / 100（32.00%）**，0skip；最后一次续跑22:20:36，100题均为r11答案（64题旧检查点＋本次36题），无r10继承。630文件完整原始日志已在服务器/本地核验保留，GitHub原始日志上传待明确授权；2道最终答案解析失败按原规则计错。见[片1核验与结果索引](./records/P1_MMSI27B_SHARD1_20260918.json)。这是分片成绩，不是1000题全量成绩。09-18 20:01仅片3/5运行，6/7/8/9排队；完成73395后活动27B总并发上限为4，所有旧失败日志与检查点保留。

### Qwen2.5-VL-72B-Instruct（P1）

8192版本分片0 `70202_0` 已核验：**36 / 100（36.00%）**，0skip，耗时5:52:39。这是100题分片结果，尚无1000题全量成绩；结果、COMPLETE及552文件完整原始日志均保留，见[核验与归档索引](./records/P1_MMSI72B_SHARD0_20260916.json)。8192版本片1 `72432_1` 已核验归档：**31 / 100（31.00%）**，0skip，3×H20耗时6:11:31；100题全部为r10答案，无继承，576文件完整原始日志保留。见[片1核验与归档索引](./records/P1_MMSI72B_SHARD1_20260918.json)。上述是分片结果，不是1000题全量成绩。

8192版本分片2 `73646_2` 已核验：**32 / 100（32.00%）**，0skip，3×H20耗时4:34:02；100题均为r10答案，无继承。1道最终答案解析失败按原规则计错，516文件完整日志已在服务器/本地核验保留，上传待明确授权。见[片2核验与归档索引](./records/P1_MMSI72B_SHARD2_20260918.json)。这是分片成绩，不是1000题全量成绩。

09-18 21:52该组暂无运行分片；片3/4=`73879_3/4`、片5=`73893_5`等待GPU，片6–9待后续提交槽。各3×H20（TP2+独占SVC1），实际export显式0.93，跨数组总并发2。未取消/重启任何健康任务，见[片5实际提交记录](./submissions/P1_SUBMIT_73893.txt)。

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

MindCube 1050 全量 1050 题结果如下（8192输出预算）：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 234 / 600 | 39.00% |
| `around` | 122 / 250 | 48.80% |
| `rotation` | 97 / 200 | 48.50% |
| **总体** | **453 / 1050** | **43.14%** |

Run ID：`mj-p1-8192-mindcube-qwen35-9b-a100-r11-20260912`。11片、1050题无重复遗漏、0 skip。44题为r10保存答案，1006题由r11生成；逐题来源保留，旧1024不合并。原始解析器与评分不变；记录26次最终答案解析失败、868次评分解析异常事件（后者不是题数）。

[合并结果](./mindcube/qwen3.5-9b/svc/mj-p1-8192-mindcube-qwen35-9b-a100-r11-20260912/results_merged.json) · [逐题来源](./mindcube/qwen3.5-9b/svc/mj-p1-8192-mindcube-qwen35-9b-a100-r11-20260912/question_source_provenance.json) · [全量核验与日志索引](./records/P1_MINDCUBE9B_FULL_20260914.json)

### Qwen3.8-27B（P1）

MindCube 1050 全量 1050 题结果如下（8192输出预算）：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 257 / 600 | 42.83% |
| `around` | 150 / 250 | 60.00% |
| `rotation` | 171 / 200 | 85.50% |
| **总体** | **578 / 1050** | **55.05%** |

Run ID：`mj-p1-8192-mindcube-qwen38-27b-a100-r11-20260912`。严格全量核验通过，11片、1050题无重复遗漏、0 skip。358题来自r10已保存答案，692题由r11生成；r11仅将额外thinking检查改为非致命告警，推理参数与评分不变。旧1024结果不参与本次合并。

[合并结果](./mindcube/qwen3.8-27b/svc/mj-p1-8192-mindcube-qwen38-27b-a100-r11-20260912/results_merged.json) · [逐题来源](./mindcube/qwen3.8-27b/svc/mj-p1-8192-mindcube-qwen38-27b-a100-r11-20260912/question_source_provenance.json) · [全量核验与日志索引](./records/P1_MINDCUBE38_FULL_20260914.json)

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
