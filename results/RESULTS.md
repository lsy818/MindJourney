# MindJourney 全部实验结果汇总

最后更新：2026-09-23（Asia/Shanghai）

本文件汇总 4 个数据集 × 4 个模型，共 16 组 SVC 实验。目前 6 组已有可报告结果，另 10 组结果待补充或修复重评；“—”表示暂无可报告结果，不代表 0 分。

## 全部实验总览

| 数据集 | 模型 | 优先级 | 状态 | 正确 / 总数 | 准确率 | 结果文件 |
|---|---|---|---|---:|---:|---|
| MMSI-Bench 1000 | Qwen3.5-27B | P1 | 已完成 | 330 / 1000 | 33.00% | [JSON](./mmsi/qwen3.5-27b/svc/mj-p1-mmsi-qwen35-27b-mixed-schema8192-final-20260921/results_merged.json) |
| MMSI-Bench 1000 | Qwen2.5-VL-72B-Instruct | P1 | 已完成 | 306 / 1000 | 30.60% | [JSON](./mmsi/qwen2.5-vl-72b/svc/mj-p1-8192-mmsi-qwen25vl-72b-h20-r10-20260912/results_merged.json) |
| MMSI-Bench 1000 | Qwen3.5-9B | P3 | 未完成 | — | — | — |
| MMSI-Bench 1000 | Qwen3.8-27B | P3 | 未完成 | — | — | — |
| MindCube 1050 | Qwen3.5-27B | P0 | 未完成（解析失败，待重评） | — | — | — |
| MindCube 1050 | Qwen2.5-VL-72B-Instruct | P0 | 未完成（解析失败，待重评） | — | — | — |
| MindCube 1050 | Qwen3.5-9B | P1 | 未完成（解析失败，待重评） | — | — | — |
| MindCube 1050 | Qwen3.8-27B | P1 | 未完成（解析失败，待重评） | — | — | — |
| SAT-Syn 500 | Qwen3.5-27B | P0 | 已完成 | 392 / 500 | 78.40% | [JSON](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/results_merged.json) |
| SAT-Syn 500 | Qwen2.5-VL-72B-Instruct | P0 | 结果待补充 | — | — | — |
| SAT-Syn 500 | Qwen3.5-9B | P2 | 已完成 | 341 / 500 | 68.20% | [验收汇总](#sat-syn-qwen35-9b-20260923) |
| SAT-Syn 500 | Qwen3.8-27B | P2 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.5-27B | P0 | 已完成 | 119 / 150 | 79.33% | [JSON](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/results_merged.json) |
| SAT-Real 150 | Qwen2.5-VL-72B-Instruct（API FP8） | P4 | 已完成 | 114 / 150 | 76.00% | [验收汇总](#sat-real-qwen25-vl-72b-20260923) |
| SAT-Real 150 | Qwen3.5-9B | P4 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.8-27B | P4 | 结果待补充 | — | — | — |

## MMSI-Bench 1000

### Qwen3.5-27B（P1）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| Motion (Cam.) | 18 / 74 | 24.32% |
| Positional Relationship (Cam.–Obj.) | 25 / 86 | 29.07% |
| MSR | 70 / 198 | 35.35% |
| Positional Relationship (Cam.–Cam.) | 26 / 93 | 27.96% |
| Positional Relationship (Cam.–Reg.) | 35 / 83 | 42.17% |
| Attribute (Appr.) | 19 / 66 | 28.79% |
| Positional Relationship (Obj.–Reg.) | 34 / 85 | 40.00% |
| Positional Relationship (Obj.–Obj.) | 28 / 94 | 29.79% |
| Positional Relationship (Reg.–Reg.) | 23 / 81 | 28.40% |
| Motion (Obj.) | 21 / 76 | 27.63% |
| Attribute (Meas.) | 31 / 64 | 48.44% |
| **总体** | **330 / 1000** | **33.00%** |

### Qwen2.5-VL-72B-Instruct（P1）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| Positional Relationship (Cam.–Cam.) | 26 / 93 | 27.96% |
| Motion (Cam.) | 21 / 74 | 28.38% |
| Positional Relationship (Reg.–Reg.) | 26 / 81 | 32.10% |
| Positional Relationship (Cam.–Reg.) | 28 / 83 | 33.73% |
| MSR | 54 / 198 | 27.27% |
| Positional Relationship (Obj.–Reg.) | 31 / 85 | 36.47% |
| Positional Relationship (Cam.–Obj.) | 27 / 86 | 31.40% |
| Positional Relationship (Obj.–Obj.) | 26 / 94 | 27.66% |
| Attribute (Meas.) | 29 / 64 | 45.31% |
| Motion (Obj.) | 21 / 76 | 27.63% |
| Attribute (Appr.) | 17 / 66 | 25.76% |
| **总体** | **306 / 1000** | **30.60%** |

### Qwen3.5-9B（P3）

结果待补充。

### Qwen3.8-27B（P3）

结果待补充。

## MindCube 1050

这四组历史运行存在最终答案解析失败，当前标记为未完成；原准确率及分类成绩已撤下，待修复并统一重评后再展示。原始结果及日志保留于仓库，供问题追溯，不作为当前可报告成绩。

### Qwen3.5-27B（P0）

未完成。历史运行有 154 道最终答案解析失败，待修复重评。

### Qwen2.5-VL-72B-Instruct（P0）

未完成。历史运行有 4 道最终答案解析失败，待修复重评。

### Qwen3.5-9B（P1）

未完成。历史运行有 26 道最终答案解析失败，待修复重评。

### Qwen3.8-27B（P1）

未完成。历史运行有 62 道最终答案解析失败，待修复重评。

## SAT-Syn 500

### Qwen3.5-27B（P0）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 99 / 100 | 99.00% |
| `obj_movement`（物体运动） | 75 / 100 | 75.00% |
| `goal_aim`（目标朝向） | 89 / 100 | 89.00% |
| `action_consequence`（动作结果） | 74 / 100 | 74.00% |
| `perspective`（视角判断） | 55 / 100 | 55.00% |
| **总体** | **392 / 500** | **78.40%** |

### Qwen2.5-VL-72B-Instruct（P0）

结果待补充。

<a id="sat-syn-qwen35-9b-20260923"></a>

### Qwen3.5-9B（P2）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 86 / 100 | 86.00% |
| `obj_movement`（物体运动） | 80 / 100 | 80.00% |
| `goal_aim`（目标朝向） | 76 / 100 | 76.00% |
| `action_consequence`（动作结果） | 49 / 100 | 49.00% |
| `perspective`（视角判断） | 50 / 100 | 50.00% |
| **总体** | **341 / 500** | **68.20%** |

### Qwen3.8-27B（P2）

结果待补充。

## SAT-Real 150

### Qwen3.5-27B（P0）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 23 / 23 | 100.00% |
| `obj_movement`（物体运动） | 19 / 23 | 82.61% |
| `goal_aim`（目标朝向） | 26 / 34 | 76.47% |
| `action_conseq`（动作结果） | 31 / 37 | 83.78% |
| `perspective`（视角判断） | 20 / 33 | 60.61% |
| **总体** | **119 / 150** | **79.33%** |

### Qwen2.5-VL-72B-Instruct（P4）

<a id="sat-real-qwen25-vl-72b-20260923"></a>

#### API FP8（OpenRouter / Parasail）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 18 / 23 | 78.26% |
| `obj_movement`（物体运动） | 21 / 23 | 91.30% |
| `goal_aim`（目标朝向） | 27 / 34 | 79.41% |
| `action_conseq`（动作结果） | 32 / 37 | 86.49% |
| `perspective`（视角判断） | 16 / 33 | 48.48% |
| **总体** | **114 / 150** | **76.00%** |

### Qwen3.5-9B（P4）

结果待补充。

### Qwen3.8-27B（P4）

结果待补充。
