# MindJourney 全部实验结果汇总

最后更新：2026-09-23（Asia/Shanghai）

本文件汇总 4 个数据集 × 4 个模型，共 16 组 SVC 实验。目前展示 9 组完整结果，另 7 组结果待补充；“—”表示暂无可报告结果，不代表 0 分。

## 全部实验总览

| 数据集 | 模型 | 优先级 | 状态 | 正确 / 总数 | 准确率 | 结果文件 |
|---|---|---|---|---:|---:|---|
| MMSI-Bench 1000 | Qwen3.5-27B | P1 | 已完成 | 330 / 1000 | 33.00% | [JSON](./mmsi/qwen3.5-27b/svc/mj-p1-mmsi-qwen35-27b-mixed-schema8192-final-20260921/results_merged.json) |
| MMSI-Bench 1000 | Qwen2.5-VL-72B-Instruct | P1 | 已完成 | 306 / 1000 | 30.60% | [JSON](./mmsi/qwen2.5-vl-72b/svc/mj-p1-8192-mmsi-qwen25vl-72b-h20-r10-20260912/results_merged.json) |
| MMSI-Bench 1000 | Qwen3.5-9B | P3 | 未完成 | — | — | — |
| MMSI-Bench 1000 | Qwen3.8-27B | P3 | 未完成 | — | — | — |
| MindCube 1050 | Qwen3.5-27B | P0 | 已完成 | 498 / 1050 | 47.43% | [JSON](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen2.5-VL-72B-Instruct | P0 | 已完成 | 416 / 1050 | 39.62% | [JSON](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/results_merged.json) |
| MindCube 1050 | Qwen3.5-9B | P1 | 已完成 | 453 / 1050 | 43.14% | [JSON](./mindcube/qwen3.5-9b/svc/mj-p1-8192-mindcube-qwen35-9b-a100-r11-20260912/results_merged.json) |
| MindCube 1050 | Qwen3.8-27B | P1 | 已完成 | 578 / 1050 | 55.05% | [JSON](./mindcube/qwen3.8-27b/svc/mj-p1-8192-mindcube-qwen38-27b-a100-r11-20260912/results_merged.json) |
| SAT-Syn 500 | Qwen3.5-27B | P0 | 已完成 | 392 / 500 | 78.40% | [JSON](./sat-syn/qwen3.5-27b/svc/mj-svc-qwen35-sat-syn500-20260903T185438Z/results_merged.json) |
| SAT-Syn 500 | Qwen2.5-VL-72B-Instruct | P0 | 结果待补充 | — | — | — |
| SAT-Syn 500 | Qwen3.5-9B | P2 | 结果待补充 | — | — | — |
| SAT-Syn 500 | Qwen3.8-27B | P2 | 结果待补充 | — | — | — |
| SAT-Real 150 | Qwen3.5-27B | P0 | 已完成 | 119 / 150 | 79.33% | [JSON](./sat-real/qwen3.5-27b/svc/mj-svc-qwen35-paper150-20260902T173648Z/results_merged.json) |
| SAT-Real 150 | Qwen2.5-VL-72B-Instruct | P4 | 已完成 | 114 / 150 | 76.00% | [验收汇总](#sat-real-qwen25-vl-72b-20260923) |
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

### Qwen3.5-27B（P0）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 213 / 600 | 35.50% |
| `around` | 140 / 250 | 56.00% |
| `rotation` | 145 / 200 | 72.50% |
| **总体** | **498 / 1050** | **47.43%** |

### Qwen2.5-VL-72B-Instruct（P0）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 221 / 600 | 36.83% |
| `around` | 109 / 250 | 43.60% |
| `rotation` | 86 / 200 | 43.00% |
| **总体** | **416 / 1050** | **39.62%** |

### Qwen3.5-9B（P1）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 234 / 600 | 39.00% |
| `around` | 122 / 250 | 48.80% |
| `rotation` | 97 / 200 | 48.50% |
| **总体** | **453 / 1050** | **43.14%** |

### Qwen3.8-27B（P1）

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `among` | 257 / 600 | 42.83% |
| `around` | 150 / 250 | 60.00% |
| `rotation` | 171 / 200 | 85.50% |
| **总体** | **578 / 1050** | **55.05%** |

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

### Qwen3.5-9B（P2）

结果待补充。

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

<a id="sat-real-qwen25-vl-72b-20260923"></a>

### Qwen2.5-VL-72B-Instruct（P4）

2026-09-23 完成。原 SAT-Real 150 题全量验收通过：150 个唯一题目，重复 0、跳题 0、继承旧实验答案 0。

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| `ego_movement`（自身运动） | 18 / 23 | 78.26% |
| `obj_movement`（物体运动） | 21 / 23 | 91.30% |
| `goal_aim`（目标朝向） | 27 / 34 | 79.41% |
| `action_conseq`（动作结果） | 32 / 37 | 86.49% |
| `perspective`（视角判断） | 16 / 33 | 48.48% |
| **总体** | **114 / 150** | **76.00%** |

实验设置与验收：

- 模型：OpenRouter `qwen/qwen2.5-vl-72b-instruct`，固定 Parasail FP8，禁用供应商回退；输出上限 8192，temperature=0、top_p=1、API seed=44。使用严格 JSON schema 服务端约束及客户端字段、类型、范围、数量、合法选项和重复键校验。
- 原 SAT 提示、选项、评分、冻结题目 ID、顺序及 5×30 分片保持不变。SVC 使用 depth=3、beam=2、阈值 8/8、9 frames、8 targets、interval=3、CFG=4、guider=1、Lshort=576、20 扩散步、seed=23，保留原图顺序及生成图加入顺序。API 的 FP8 精度、图像处理、上下文和 seed 确定性与原本地 BF16 部署不能视为完全等价。
- HTTP 429/520 等已授权瞬态错误采用同请求有限重试。中断恢复逐条核对完整请求、图像字节及顺序；同次实验已成功响应只离线复用、不重复调用。全量覆盖、去重、零跳题、逐题来源、模型参数、严格解析及重试记录均验收通过。
- 正式采用 792 条 API 记录，输入 4,033,313 tokens、输出 21,149 tokens；正式采用响应的已确认费用为 **$3.1991914**，含测试累计确认 **$3.2280152**。失败请求的 $13.68 为未知消耗预算预留，不计入已确认费用；最终以供应商账单为准。

验收文件 SHA256（原始审计保存在私有归档）：

| 文件 | SHA256 |
|---|---|
| `MERGED_COMPLETE.json` | `d8db9b3768f40c8cf087e9e0c3314ebd6f423a9ed6becdab417fe230c3192cea` |
| `results_merged.json` | `d67b1a719333f0d0d6047c3ea024341d1ce2558d9ce4ef3397afef5691408c2f` |
| `question_provenance.json` | `1ed8451cd3632c24ce13ba71d9a28436dfe4aabb742e1c3cdae1b6d4fa2cdd5a` |
| 恢复源码清单 | `aaf5a89c7e4f750475b97e1cc1efb4216e2a9b005012113910f2db0245ca680e` |

### Qwen3.5-9B（P4）

结果待补充。

### Qwen3.8-27B（P4）

结果待补充。
