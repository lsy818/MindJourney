# MindJourney 全部实验结果汇总

最后更新：2026-10-20（Asia/Shanghai）

本文件保留原 16 组 SVC 实验，并补充 4 组已验收的 DeepSeek 官方 API 结果，以及新的 SpatialRGPT-Bench 定量实验。现有 11 组可报告结果；“—”表示暂无可报告结果，不代表 0 分。


## SpatialRGPT-Bench 本地 Qwen FP8（准备中）

| 模型 | 状态 | 正式题完成数 | Overall |
|---|---|---:|---:|
| Qwen3.5-27B FP8，thinking 关闭 | 权重全量校验、A100 单节点 19 图合成验证通过；待资源交接和六类预检 | 0 / 749 | — |
| Qwen2.5-VL-72B-Instruct FP8 | 权重全量校验通过；待第一组完成后运行 | 0 / 749 | — |

两组沿用原始 749 题与原始严格协议，不包含 DeepSeek 七题的单独答案修复提示。90247 的原模型服务尚待安全交接；当前未开始正式 Qwen 预检。四卡/三卡主资源池均保留，不因实验结束或报错释放。当前仅为准备状态，不能据此报告成绩或实测完成时间。[权重 revision、量化格式、环境、设置与 SHA](../experiments/spatialrgpt_qwen_local_20261020/README.md)。

## SpatialRGPT-Bench 定量子集（749 题）

模型：`deepseek/deepseek-v4.1-flash`（非 1017），OpenRouter / DeepInfra FP8；方法为 MindJourney / SVC。

| 运行版本 | 状态 | 正确 / 总数 | Overall |
|---|---|---:|---:|
| 原始运行 | 742 有效、7 格式失败计零；历史成绩保留 | 374 / 749 | 49.93% |
| **7 题最终答案格式修复版（2026-10-20）** | **749/749 有效，全量独立审计通过** | **379 / 749** | **50.60%** |

修复版分类成绩：

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| Direction | 74 / 107 | 69.16% |
| Distance | 68 / 148 | 45.95% |
| Horizontal distance | 43 / 122 | 35.25% |
| Vertical distance | 53 / 106 | 50.00% |
| Width | 60 / 133 | 45.11% |
| Height | 81 / 133 | 60.90% |
| **Overall（按题数加权）** | **379 / 749** | **50.60%** |

用户授权修复原来 7 道格式失败题；仅重发这 7 题的最终答案请求，全部一次成功，原有 742 道有效答案不变。原问题、输入图片、已生成视图、模型路由和采样设置保留；只在最终回答阶段追加“以米输出物理长度”的格式说明并收紧对应 schema。此为单独披露的格式修复协议，并非声称与原始提示完全相同。原失败响应包含百分比、像素、person、image height 或泛称 unit，均不按物理长度直接换单位或强行解析。

完整核验 749 个原始 ID、源文件 SHA、输入/生成图像对应、请求内容、模型/提供商、重试和费用来源；最终 749 个答案均通过严格格式与有限数值检查，0 个无效答案。有效不代表正确。固定 WorldLoop 评分器及 749 题分母不变（长度误差容限 25%，含边界；方向循环时钟距离不超过 1 小时）；7 道修复题中 5 道正确。新生成视频 **0**，原响应、视频、失败证书及原始成绩完整保留。

新增 **7 次**网络请求，新增已知费用 **0.0015333640 USD**。历史与本次合计 **3453 次**网络尝试，累计已知费用 **1.7285231152 USD**；仍有 **24 次历史费用未知**，不是完整实付总额。独立合成 API 测试费用 0.00006034 USD 单列，不包含于上述金额。

修复版最终验收 SHA-256：`5d18be0ed2945c21f8e9220a8faf6e34ea8a04b19d76b9478e64addb3748d1ff`；汇总 SHA-256：`a4b510c213a9f7247f5c9f15a957fbbce704d9da128f056cec5c91e7c0a55280`。

[修复版报告](./spatialrgpt-deepseek-repair-20261020.md) · [原始成绩归档](./spatialrgpt-deepseek-20261020.md) · [固定设置](../experiments/spatialrgpt_20261018/README.md) · [修复协议与代码](../experiments/spatialrgpt_20261018/answer_repair_v1/README.md)。原始题图、答案、请求响应和逐题审计均留在 DAAI 私有服务器。

## DeepSeek 官方 API 已验收结果（2026-09-24）

| 数据集 | 方法 | 正确 / 总数 | 准确率 |
|---|---|---:|---:|
| MMSI-Bench 1000 | MindJourney / SVC | 312 / 1000 | 31.20% |
| MindCube 1050 | MindJourney / SVC | 466 / 1050 | 44.38% |
| SAT-Syn 500 | MindJourney / SVC | 340 / 500 | 68.00% |
| SAT-Real 150 | MindJourney / SVC | 87 / 150 | 58.00% |

| Model | Method | Rotation | Among | Around | Overall |
|---|---|---:|---:|---:|---:|
| DeepSeek（官方 API） | MindJourney | 36.00% (72/200) | 40.50% (243/600) | 60.40% (151/250) | 44.38% (466/1050) |

以上沿用 9 月最终验收记录，未重新运行模型。[历史设置与验收摘要](./deepseek-official-20260924.md)。原始题图、答案及详细审计保留在私有服务器。

## 原 16 组实验总览

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
