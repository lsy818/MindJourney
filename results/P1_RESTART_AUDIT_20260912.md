# 正确 P1 重启：提交前核对记录（2026-09-12）

## 纠错与结果保留

此前是执行清单配错，并非用户变更优先级。旧 r8 实际完成 MindCube/27B、MindCube/72B、MMSI/9B、MMSI/3.8-27B，分别属于用户原始清单的 P0、P0、P3、P3。旧结果、Run ID、日志和冻结目录全部保留；不得移名作为正确 P1 成绩。此前“四项 P1 全部完成”的结论撤回。

本轮只运行：

| 数据集 | 模型 | 优先级 | 题数 | 分片 | 原图上限 |
|---|---|---|---:|---:|---:|
| MMSI-Bench | Qwen3.5-27B | P1 | 1000 | 10 | 10 |
| MMSI-Bench | Qwen2.5-VL-72B-Instruct | P1 | 1000 | 10 | 10 |
| MindCube | Qwen3.5-9B | P1 | 1050 | 11 | 4 |
| MindCube | Qwen3.8-27B | P1 | 1050 | 11 | 4 |

使用独立 r9 工作目录和新 Run ID，不能续接旧组合的分片。

## 论文、发布代码与扩展边界

已重新阅读 [MindJourney 论文 §3.3、附录 A.1.1 与 C.1](https://arxiv.org/html/2507.12508v1)，并对照官方发布代码 commit `aeed003e76e8a96fbb20990405128913f8f49486`。

| 项目 | 本轮设置 | 依据 |
|---|---|---|
| 世界模型 / 搜索方法 | SVC / spatial beam search | 用户指定，论文 §3 |
| 搜索深度 / beam | 3 / 2 | 附录 A.1.1 |
| exploration / helpful 阈值 | 8 / 8 | 附录 A.1.1 |
| 最大轨迹长度 | 8 | 附录 A.1.1；代码每条生成轨迹 8 个动作 + 参考帧 |
| 基元 / 每次扩展最多重复 | 前进 0.25 m、左右旋转 9° / 3 | 附录 A.1.1 |
| 扩展终点 | 0.75 m / 27° | 三次基元 |
| SVC 帧数 / targets / frame interval | 9 / 8 / 3 | 发布 SVC 管线 |
| CFG / guider / L_short | 4.0 / 1 / 576 | 发布 SVC 运行脚本 |
| SVC 扩散步数 | **20，沿用发布代码** | `stable_virtual_camera/demo.py:svc_main` |
| VLM | BF16、65536 上下文、1024 最大输出 | 用户要求及既有固定 Qwen 适配 |
| 生成采样 | temperature 0、top_p 1、seed 44 | 固定 Qwen 适配，不冒称论文参数 |
| Thinking | Qwen3 系列 false；Qwen2.5-VL 不支持该开关 | 客户端与服务器设置一致 |

重要差异：论文附录 C.1 的独立世界模型质量比较写明 **50 个扩散步**，而作者发布的 SVC 基准运行代码实际固定 **20 步**。正文未单独明确主基准的扩散步数。本轮沿用发布代码的 20 步，不将其表述为已证实与论文主表逐项完全相同，也不擅自把 C.1 的参数移植到主基准。

MindCube/MMSI 及这四个 Qwen 模型不是原论文的原生实验组合，协议准确名称为 **paper-aligned SVC multi-image adaptation**。所有原图按官方顺序进入评分和最终回答；只有 Image 1 用于 SVC 条件生成，想象视图附在原图之后。图片缩放及问答模板沿用 MindJourney，不复制 WorldLoop 的 cognitive-map 增强条件，不向模型泄露答案或官方推理标注。

## 预处理及最终输入顺序：全量核验通过

2026-09-12 在 DAAI 使用已有固定快照，只读核对原始行与预处理行，并直接执行当前代码的评分、最终回答和消息格式化函数（不加载模型）逐题核对图片列表。没有重新下载或重新生成数据。

| 数据集 | 行数 | 图片引用 | 唯一图片 | 缺图 | 题目/答案标签 | 原始→预处理→评分/QA 图片顺序 |
|---|---:|---:|---:|---:|---|---|
| MindCube | 1050 | 3307 | 428 | 0 | 全量一致 | 全量一致 |
| MMSI-Bench | 1000 | 2550 | 2550 | 0 | 全量一致 | 全量一致 |

### MindCube

- 官方代码：`b8b7062adf6d3e49d588a7d014a0a787553d09ec`；数据 revision：`9c941b46a6bd65b6914669ef7a579948fc9c8467`。
- 原始 `MindCube_tinybench.jsonl` SHA256：`0289eb82d81ff9aa0201ae75f86da7fd1924cf23dc202856d0579a0effd22ac8`。
- 输入：`/home/datasets/shiyang/MindCube_9c941b46/processed/test.json`。
- 输入 SHA256：`03a62d4928f790eb2dad9e18a9f5f65643342100b93955de80debea171e88083`。
- 官方 `src/inference/engines/qwen_engine.py` 的 `process_input` 读取原始 image_paths；最终 Transformers 的 `images=images`、vLLM 的 `multi_modal_data.image=images` 保持该顺序。
- 特别检查：官方聊天模板组装中有重复 `insert(0, img_msg)`，模板对象列表会倒序；但实际像素数组另行以原始顺序传给 processor/vLLM。因此不能仅看模板对象就把实际图片反转。本轮保持数据定义的 Image 1…N 顺序。
- 官方原始快照为 among/around/rotation = 600/250/200。

### MMSI-Bench

- 官方代码：`13e58a2b8b30d880d7e8a1e4a6aa1c0feda94cac`；数据 revision：`ec7c92bfaf7728fcca1d61e3e224e190af309436`。
- 原始 JSONL SHA256：`9448f3ffc9c2364d396ab29bfc5a66ecab26fcc076ce1b6b364bdcad7c721601`。
- 路径无关的官方元数据核验摘要：`22eb8a59a75e318f52c7cc83eb0714952397e84d9bc092ef8837747599d64b1d`。
- 输入：`/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed_daai/test.json`。
- 输入 SHA256：`5de75a94eebb2ad31b44ab0f33d7225c56157165292d8112e287c410f56180c9`。
- 官方 `vlmeval/dataset/mmsi_bench.py` 的 dump_image 与 build_prompt 顺序遍历图片，不做文件名排序；MindJourney 的 img_paths 与该顺序逐题一致。
- 本轮使用既定一次作答、严格 A–D 标签计分，不是 circular testing；不启用官方评测器的外部 LLM 答案提取回退。MindJourney 保留自己的评分和答案模板，不能称为 MMSI 官方端到端推理协议完全一致。

### A100-2 第三方交叉参考

已只读查看用户指定两份脚本：

- `/data/chentao/WorldLoop/examples/spatial_reasoning/prepare_data.py`：按 `rec["images"]` 顺序构造输入；另含 raw_qa/cognitive-map 条件，本轮不使用增强条件。
- `/data/chentao/WorldLoop/smoke/build_mmsi_full.py`：按原始 images 枚举导出；有计时退出和失败跳过分支。因此不把脚本正常退出等同完整性通过，本轮以 1000 题/2550 图独立核验为准。

## 提交保护与运行策略

- shell 注册表与独立 Python 合约均只接受正确四组；错误组合在提交前及节点加载模型前被拒绝。
- 合约额外固定题数、原图上限、test split、完整输入 SHA256、去重题 ID 和论文搜索配置；源码和清单继续有独立指纹。
- 72B 使用 TP2 + SVC 独占 1 卡，3×H20，实际 sbatch export 固定 `P1_GPU_MEMORY_UTILIZATION=0.93`。其他模型 TP1 + SVC1，2 卡；H20 优先，无资源时使用已确认兼容的 A100 80GB 节点。
- 复用既有环境及节点本地副本；新节点使用已发布压缩包。未变化 SVC 权重复用完整校验记录；不重复扫描权重或安装环境。
- 账户查询：daai_qos 最大运行作业 5、最大提交任务 10；当前有 1 个无关排队作业，不取消。并发按同一实验全部活动数组合计，不重复提交同一分片。
- 用户再次明确最高原则：**优先用满用户额度，其次优先跑完同一组实验**。初步主组 MindCube/9B，MMSI/27B 补位；主组无可适配资源时允许另一组先运行，不能为了集中而闲置额度。排队任务数不算 GPU 额度已经用满。
- 本轮新增组合先核对正式首题产物；首题通过即可并行补充剩余分片，不必等首片全部结束。补充时优先用满额度，再集中推进少数 setting。
- 每片完成即核验归档并推送；旧结果永久保留。具体作业 ID 与实时状态见 [实验日志](./EXPERIMENTS.md)。
- 四组首片已于 2026-09-12 13:29–13:30 提交，初始均 PENDING/Priority，尚未进行首题产物核验。[新执行清单](./P1_CORRECTED_EXECUTION_20260912.json)记录固定源码及完整参数。已恢复本任务每 10 分钟自动推进（automation ID: `mindjourney-p1`），无实质变化时不重复通知。
