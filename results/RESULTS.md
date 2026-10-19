# MindJourney 全部实验结果汇总

最后更新：2026-10-19（Asia/Shanghai）

本文件保留原 16 组 SVC 实验，并补充 4 组已验收的 DeepSeek 官方 API 结果，以及新的 SpatialRGPT-Bench 定量实验。现有 10 组可报告结果；“—”表示暂无可报告结果，不代表 0 分。


## SpatialRGPT-Bench 定量子集（749 题）

| 模型 | 方法 | 平台 | 当前状态 | 正确 / 总数 | Overall |
|---|---|---|---|---:|---:|
| `deepseek/deepseek-v4.1-flash`（非 1017） | MindJourney / SVC | DAAI A100 + OpenRouter / DeepInfra FP8 | 6/6 道预检及独立审计通过；四卡继续运行，60/749 条终态记录（59 有效、1 无效，2026-10-19 15:18 CST） | — / 749 | — |

六类题数：Direction 107、Distance 148、Horizontal distance 122、Vertical distance 106、Width 133、Height 133。全部原始 1406 条记录已解码；749 条定量记录的 ID、问题、原图像素和区域信息独立核对一致。完整结果将按固定 749 题分母与原版 WorldLoop 评分器统计；当前没有可报告的本组准确率。

2026-10-19 核对：学校代理的大请求上传已复现缓慢/停滞；旧请求缺少上传指标，无法事后确定每次超时的具体阶段。已改为服务器内部 SSH 承载的端到端 TLS 通道，实际计算节点完整上传 25.90 MB 合成数据耗时 1.465 秒，TLS 校验通过；该测试未认证、零推理。原始输入、模型、SVC 设置和请求字节均不变，未使用本机 API 中转。

V5 的 15 项测试及零 API / 零 GPU 生成离线重放通过，330 个旧文件 SHA 不变，保留 2 道结果、29 个视频、15 个有效响应和 37 次历史尝试。按用户新的修复后续跑指令，仅指定耗尽请求增加一次编号 9 的受控尝试，原 8 次记录及未知 usage 保留；其他 payload 仍最多 8 次，传输异常立即停止该 worker 检查。受控请求已成功；六道预检全部独立验收通过，现已开放四槽，仅计算其余 743 道，最终合并核验 749 道，不重复计算已有题目或视频。五天资源池独立于实验进程，内部程序失败不释放资源池。当前尚无最终准确率。

最新真实验证：原始 25,898,232 字节请求在约 13 秒内返回 HTTP 200，精确模型/提供商及严格响应解析全部通过；该次已知费用为 0.00130858 USD。恢复 worker 正常退出，旧 29 个视频未重生成。随后六类预检全部完成，独立审计通过；四个正式 worker 已在同一资源池运行。上述单次费用不代表全部实验实付，历史未知 usage 仍保留未知。

2026-10-19 15:18 CST：一题收到 8 次 HTTP 200 响应，但单位均未通过严格解析；该题已停止请求，保留全部尝试和费用记录，以无效答案计入 749 题分母，最终计 0 分。未放宽解析、未修改提示、未增加第 9 次请求。独立来源与原始文件 SHA 审计通过后，新增 V7 续跑控制器仅处理停止分片尚未开始的题目；另外三个健康 worker 持续运行。V5 推理源保持原样。控制状态移至独立目录并使用唯一临时文件及有限权限错误重试，旧控制器和启动失败的包装版本均不恢复。

预检验收回执 SHA-256：`10be9e997963c1db901d6221bf8c33f41daf3cb19b9309ed2af6833f46a46743`。已保存计数不等于最终验收或正确题数，最终全量来源、重试、费用审计和固定评分尚未完成。

[本次设置、适配代码与验证说明](../experiments/spatialrgpt_20261018/README.md)。本次是 OpenRouter 第三方 FP8 路由，与下面的历史官方 DeepSeek API 设置分别标注。

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
