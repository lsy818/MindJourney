# 实验结果目录

全量及分类成绩见 [RESULTS.md](./RESULTS.md)，实验进展和历史记录见 [EXPERIMENTS.md](./EXPERIMENTS.md)。

| 路径 | 内容 |
|---|---|
| 顶层 `*.md` | 结果汇总、实验记录和设置核对文档 |
| [SHA256SUMS](./SHA256SUMS) | 归档文件的 SHA-256 校验清单 |
| [records/](./records/) | 执行清单、进度快照、核验及归档索引 JSON |
| [submissions/](./submissions/) | 实际作业提交输出 TXT |
| [scheduling/](./scheduling/) | 调度历史记录 |
| [raw_logs/](./raw_logs/) | 完整原始日志压缩包 |
| `mindcube/`、`mmsi/`、`sat-real/`、`sat-syn/` | 按数据集、模型、方法和 Run ID 保存的原始分片与合并结果 |

当前 P1 执行清单：[records/P1_AUDITFIX_EXECUTION_20260912.json](./records/P1_AUDITFIX_EXECUTION_20260912.json)。

2026-09-14 目录整理只迁移原顶层 JSON/TXT 并更新引用和 SHA 清单。实验答案、评分、配置、Run ID、数据集产物和原始日志内容不变，服务器运行目录不变。后续新增非 Markdown/SHA 文件请归入上述子目录，不再写入 `results/` 顶层。

校验清单保留历史路径写法：以 `./` 开头的条目相对于 `results/`，以 `results/` 开头的条目相对于仓库根目录。
