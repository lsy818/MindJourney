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
| MindCube / `Qwen/Qwen3.5-27B` | 1050 题及完整原始图片树已就绪并严格验证；A100-2 诊断副本已就绪 | DAAI 目录含 `config`、11 个 safetensors；精确 revision marker 已验证且组可读；A100-2 完整权重树已核验 | DAAI Job `65458` 因节点缺少系统 `ninja` 失败；修复后的 Job `65469` 在 `hkbugpusrv15` 运行 24:08 后仍失败（`1:0`）。A100-2 诊断 smoke 因无安全空闲 GPU 尚未启动 | `65516`、`65523`、`65526`、`65535`、`65539`、`65591` 均在运行前取消；最终 A100 80GB 提交器 Job `65707` 当前依赖等待 `afterok:65706` 与 `afterok:65533`，计划分片 `0-2`（共 11 片中的前 3 片），从未启动；其余分片按 QOS 容量续提 | 计划 Run ID：`mj-p1-mindcube-qwen35-27b-a100-20260906`；DAAI：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mindcube-qwen35-27b-a100-20260906` |
| MindCube / `Qwen/Qwen2.5-VL-72B-Instruct` | 1050 题及完整原始图片树已就绪并严格验证；A100-2 诊断副本已就绪 | DAAI 下载仍未完成且尚无 revision marker；Job `65504` 在续传 13:15:26 后因分块传输中断失败，缓存与残留均保留；单 worker 续传 Job `65785` 当前在 `hkbugpusrv08` 运行 | 等待权重严格验证；72B 不在 40GB A100 上启用诊断 smoke | 等待 smoke 通过；无正式 P1 全量提交 | — |
| MMSI-Bench / `Qwen/Qwen3.5-9B` | Job `65519` 已在 00:33:20 完成：1000 题 / 2550 图，严格官方预处理与独立校验通过；新的 `processed_daai` 输入对 `24482277` 可读，旧 `processed/test.json` 仅保留审计 | DAAI 目录含 `config`、4 个 safetensors；精确 revision marker 已验证且组可读；A100-2 固定 revision 的完整权重树已核验 | DAAI Job `65452` 因节点缺少系统 `ninja` 失败；修复后的 Job `65468` 在 `hkbugpusrv15` 运行 35:05 后仍失败（`1:0`）。A100-2 基础及 10 图定向诊断 smoke 因无安全空闲 GPU 尚未启动 | `65520`、`65524`、`65527`、`65536`、`65540`、`65592` 均在运行前取消；最终 A100 80GB 提交器 Job `65708` 当前依赖等待 `afterok:65706` 与 `afterok:65533`，计划正式分片 `0`，从未启动；通过后再按 QOS 容量续提 | 计划 Run ID：`mj-p1-mmsi-qwen35-9b-a100-20260906`；DAAI：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mmsi-qwen35-9b-a100-20260906` |
| MMSI-Bench / `Qwen/Qwen3.8-27B` | 1000 题 / 2550 图已就绪并严格验证；A100-2 诊断副本已就绪 | DAAI 目录含 `config` 和 9 个 safetensors；Job `65447` 最后观测仍为 `RUNNING`，未发现 revision marker，不能视为完整 | 等待权重严格验证；A100-2 诊断 smoke 尚未启动 | 等待 smoke 通过；无正式 P1 全量提交 | — |

- 推理统一使用 BF16 和 no-thinking；Qwen2.5-VL 不发送其不支持的 Qwen3 thinking 参数。
- 诊断 smoke/debug 允许且优先在 A100-1 或 A100-2 直接运行，避免为调试占用 DAAI 的 Slurm 队列；仅在有足够、可安全独占的空闲 GPU 时启动，不抢占、不超卖，也不终止其他用户进程。
- 正式全量计算只在 DAAI 运行。H20 96GB 空闲时优先；否则使用 A100 80GB，并排除 40GB DGX。硬件切换不得改变 BF16、no-thinking、图片顺序或 SVC/搜索参数。
- 每个组合必须先完成一题端到端 smoke，再提交正式数组；“已提交/排队”不等于“已完成”。
- 统一配置：[p1_svc_multiimage.json](../configs/p1_svc_multiimage.json)。
- A100-1 与 A100-2 均为 8 × A100 PCIe 40GB；最后观测时两台机器的 8 张卡均有常驻进程，没有可安全独占的空闲卡，因此尚未启动任何 A100 诊断 smoke。A100-2 的工作副本位于 `/data/shiyang/MindJourney`。
- H20 节点的 8 张卡当前均由 Job `65509` 占用，最长可能持续 5 天；两个历史 smoke 已按资源约定回退到 A100 80GB，本轮正式首批也改用 A100 80GB。所有 A100 回退都显式排除 40GB DGX；每次后续提交前仍会重新检查 H20，而不会把本次回退固化为实验设置。
- 首轮 smoke 的模型权重均已成功载入 GPU，但 FlashInfer 首次编译采样内核时在 A100 节点找不到裸命令 `ninja`。固定 Qwen 运行环境实际包含 `ninja 1.13.2`；提交代码已在 vLLM 子进程范围内补回该固定环境的 `bin`，未改变模型、精度、thinking 模式或 SVC 参数。修复 commit：`087be7a`。
- 标准 9B/27B 任务统一申请 8 CPU，72B 保持 16 CPU；续跑 Job `65468`、`65469` 的资源均已同步更新为 8 CPU。该调整只改变 Slurm 资源配额与线程上限，不改变 GPU 数、TP、BF16、提示、数据顺序或 SVC 算法设置。资源计划 commit：`8d8bd12`。
- Slurm accounting 已确认 Job `65468`、`65469` 均失败且没有可验证的 `COMPLETE`；因此没有触发任何后续全量提交，当前四项 P1 均无正式完成结果。
- 已使用用户再次确认的凭据重试 `daai_tangyu` 登录，但目标仍返回认证失败；本地同时缺少该主机配置引用的 `~/.ssh/id_ed25519_daai_tangyu`，因此不能读取 `tyjiang` 私有日志或以该账号重提任务。`daai`（24482277）账号已确认可成功登录，后续正式实验将改用该账号提交；既有 `tyjiang` 失败运行路径继续保留作审计。本文不记录密码或令牌，也不根据不可见日志的退出码臆测失败根因。

### A100-2 诊断环境与权重核验

- A100-2 上的数据和代码准备已完成，仓库为 `/data/shiyang/MindJourney`。MindCube 正式诊断副本、单题 smoke，以及 MMSI 正式诊断副本、2 图 smoke、10 图边界 smoke 均已生成并完成题数、图片存在性与官方图片顺序检查；具体路径和哈希见后文预处理章节。
- SVC 环境 `/data/shiyang/envs/svc` 已通过导入验证：Python 3.11.15、PyTorch 2.9（CUDA 12.8）、Transformers 4.46.3、Diffusers 0.35.1、NumPy 1.26.0、Pillow 11.3、OpenCLIP 3.3、Hugging Face Hub 0.35、quaternion 2024.0.3。运行时需加入 MindJourney、`pipelines` 与 Stable Virtual Camera 的 `PYTHONPATH`。
- Qwen/vLLM 环境 `/data/shiyang/envs/qwen0280` 已通过依赖一致性检查：Python 3.12.13、PyTorch 2.13（CUDA 13.0）、vLLM 0.28.0、Transformers 5.14.1、ninja 1.13.2，`pip check` 无冲突。
- `/data/shiyang/models/Qwen3.5-9B` 已固定到 revision `c202…` 并完成 4 个权重分片的全树校验；`/data/models/Qwen3.5-27B` 也已完成全树校验。两台 A100 调试机最后观测均无可安全独占 GPU，因此这些记录表示环境/静态权重验证完成，不表示 GPU smoke 已运行。

### DAAI 队列快照

快照时间：北京时间 2026-09-07（本轮下载续传提交后；具体状态以 Slurm accounting 为准）。

- 环境首试 Job `65505` 因 Slurm 脚本错误定位仓库而立即失败；定位逻辑已在 commit `01ef26c` 修复。后续环境 Job `65510` 运行 00:59:38 后因 Cargo home 缓存的 disk I/O / `proc_macro2` 错误失败；Job `65532` 又在 00:00:07 因 Linux/NFS 上 `flock` 返回 `EBADF` 失败。SVC 锁兼容修复 commit `9eaea12` 已通过 62/62 测试，环境安全续传与隔离缓存修复 commit `c63e58e` 已通过全量 64/64 测试；为确保 `puccinialin` / Cargo 子进程实际缓存路径与记录一致，最终修复 commit `a2d77b6` 又通过了定向 10/10 测试，此前的全量 64/64 结论仍适用。
- SVC exact-revision 预取 Job `65533` 当前仍为 `RUNNING`：OpenCLIP 已在 4:33:51 完成，VAE 两个文件已在 23:34 完成，目前正在下载受限 SVC 权重；当前 incomplete 文件约为 2,280,016,336 bytes。持久环境续传 Job `65534` 在运行 00:03:10 后被主动取消；后续环境续建 Job `65537` 运行 03:03:49 后以 Exit 1 失败。`65537` 的根因不是先前的缓存 I/O，而是 Cargo 下载 `ring 0.17.14` 时代理连接出现 `SSL_ERROR_SYSCALL` / unexpected EOF；该作业已成功下载的大量 crate 缓存全部保留。
- 基于安全 `--resume` 和已有隔离缓存，环境续建 Job `65590` 曾显式设置 `CARGO_NET_RETRY=20`、`CARGO_HTTP_TIMEOUT=600`、`CARGO_HTTP_MULTIPLEXING=false`，但运行 01:28:46 后以 Exit 1 失败。该次根因不是 Cargo 的 `ring` 下载，而是 uv 下载/解压 `nvidia-cudnn-cu13 9.20.0.48` 时触发 30 秒网络超时。安全续建 Job `65706` 已重提并处于 `RUNNING`：保留上述三个 Cargo 参数，并新增 `UV_HTTP_RETRIES=20`、`UV_HTTP_TIMEOUT=600`、`UV_CONCURRENT_DOWNLOADS=1`。Job `65533`、`65706` 均未被记为完成，必须等待各自完成标记与严格校验；全部失败日志继续保留。
- Qwen2.5-VL-72B 首次下载 Job `65502` 因计算节点缺少 `huggingface_hub` 失败；旧重复 Job `65499` 已取消。后续 HTTP 续传 Job `65504` 运行 13:15:26 后因 `requests.exceptions.ChunkedEncodingError` / `IncompleteRead` 失败：当时主分片已读取 3,782,619,236 bytes，尚余 212,564,732 bytes；已下载缓存、未完成文件和失败日志全部保留。
- 单 worker 续传 Job `65785` 已自动提交，当前在 `hkbugpusrv08` 为 `RUNNING`；显式设置 `HF_HUB_DOWNLOAD_TIMEOUT=600`、`HF_HUB_ETAG_TIMEOUT=60`，并通过 `24482277` 账号的 `HF_TOKEN_PATH` 读取凭据。本文和 Git 中不记录令牌内容；只有完整索引、全部权重分片、固定 revision marker 与严格校验均通过后，72B 才会记为下载完成。
- Qwen3.8-27B 原下载 Job `65447` 当前为 `RUNNING`；严格校验 Job `65500` 正在依赖等待，尚未产生可验证的 revision/完整性结论。
- 旧的四个正式提交器 Job `65511`–`65514` 已取消。这些提交器试图一次创建四个完整数组，而集群 `QOSMaxSubmitJobPerUserLimit` 会把数组中的每个 task 计入约 10 个可提交槽位，继续保留会阻塞真正的计算分片。取消提交器不删除任何已有结果或日志。
- MindCube / Qwen3.5-27B 的 H20 首批数组 Job `65516` 原计划运行 `0-2%3`，依赖也已修正为 `afterok:65510`；但因 H20 节点被 Job `65509` 全部占用且最长可能持续 5 天，`65516` 已在任何 task 启动前取消，旧 H20 Run ID 只保留作审计，不能记为已运行。首个 A100 80GB 提交器 Job `65523` 的预检发现 `p1_submit` 默认指向不存在的 `/home/datasets/shiyang/model_cache` 与 `/home/datasets/shiyang/model_validation`，因此同样在启动前取消；Job `65526` 随后因环境 Job `65510` 失败而取消；Job `65535` 因替换环境链取消；Job `65539` 因环境 Job `65537` 失败而取消；Job `65591` 又因环境 Job `65590` 失败而取消。五者均从未运行。最终 A100 80GB 提交器 Job `65707` 当前为 `PENDING`，同时依赖 `afterok:65706` 与 `afterok:65533`，计划以 Run ID `mj-p1-mindcube-qwen35-27b-a100-20260906` 提交分片 `0-2`。每个实际 task 仍使用 2 张 GPU（TP=1、SVC=1）、8 CPU、BF16、no-thinking，并排除 40GB DGX；截至本快照，提交器及其计算分片均未开始运行。
- `24482277` 对旧 MMSI `processed/test.json` 无读取权限，但可读取原始 `mmsi_full.jsonl` 和 2550 张图片。交互式预处理 Job `65518` 被外部取消且未产生正式输入；持久批处理 Job `65519` 已在 00:33:20 完成，使用官方严格转换程序生成 `/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed_daai/test.json`（SHA256 `5de75a94eebb2ad31b44ab0f33d7225c56157165292d8112e287c410f56180c9`）与 `/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed_daai/test_provenance.json`（SHA256 `fa5f4ee9223cf72fd4dcbc941b8fbd66788b37d854844532bde581cd2aebdf9f`）；1000 题 / 2550 图及官方图片顺序已通过独立严格校验，原始文件和失败记录均保留。
- MMSI / Qwen3.5-9B 的 H20 提交器 Job `65520` 同样已在运行前取消，旧 H20 Run ID 只保留作审计。首个 A100 80GB 提交器 Job `65524` 因相同的默认缓存/marker 路径错误在启动前取消；Job `65527` 随后因环境 Job `65510` 失败而取消；Job `65536` 因替换环境链取消；Job `65540` 因环境 Job `65537` 失败而取消；Job `65592` 又因环境 Job `65590` 失败而取消。五者均从未运行。最终 A100 80GB 提交器 Job `65708` 当前为 `PENDING`，同时依赖 `afterok:65706` 与 `afterok:65533`，计划为 Run ID `mj-p1-mmsi-qwen35-9b-a100-20260906` 创建分片 `0`。A100 任务显式排除 40GB DGX；截至本快照，提交器及其计算分片均未开始运行。
- Job `65707`、`65708` 均沿用显式的 `P1_CACHE_ROOT=/home/datasets/shiyang/daai_runtime/model_cache` 和 `P1_MODEL_VALIDATION_ROOT=/home/datasets/shiyang/mindjourney_storage/model_validation`，不依赖错误默认值。该 marker 目录中的 Qwen3.5-27B 与 Qwen3.5-9B 精确 revision 标记均已确认对 `24482277` 组可读；只有预检通过后提交器才会创建实际计算数组。
- Hugging Face read token 仅安装在 `24482277` 账号的凭据存储中，并已验证能够读取 gated Stable Virtual Camera 仓库；Git 记录、结果文档和日志中均不保存 token 值或其他 secret。
- 当前 QOS 策略是只让可用槽位承载实际计算 task：先以 A100 80GB 跑 MindCube `0-2` 和 MMSI `0`，完成并释放槽位后依次续提 MindCube `3-5`、`6-8`、`9-10` 及 MMSI 后续分片。后续续跑使用各自的 A100 Run ID 和 `--resume`。排队、提交器成功或单个分片结束都不等于实验完成；只有完整覆盖、零静默跳题、正式 `COMPLETE`、合并结果与哈希全部通过后才更新为“已验证完成”。

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
- A100-2 诊断输入：`/data/shiyang/datasets/MindCube_9c941b46/processed/test.json`，1050 题，SHA256 `5748bdb2b4933d41d50f190d35b5a494cba633ce1258e066beddf9d17560a08c`；`test_provenance.json` SHA256 `3bf65a9d752c958accdb147f7cec746e0ad3c9d34555994db76ef6d675b8a2f5`；3307 次图片引用、428 张唯一图片、0 缺图，官方有序图片序列摘要同为 `0b092454a3ceb25f513f3f1428f1b9fad06cf4e297a7d754980521f0cce2abdb`。其文件哈希与 DAAI 副本不同是因为绝对图片路径不同，不代表图片语义顺序变化。
- A100-2 单题诊断子集：`/data/shiyang/datasets/MindCube_9c941b46/smoke_index66`，1 题（ID `among_group525_q0_2_2`，4 图），`test.json` SHA256 `20badbdd83963470f9138191af8ed104ec94971802296bf2a690a1d8203eddef`。
- 第三方参考脚本（A100-2）：`/data/chentao/WorldLoop/examples/spatial_reasoning/prepare_data.py`
- 以官方 `images` 数组作为 `Image 1..N` 的唯一语义顺序；转换工具：[prepare_mindcube.py](../utils/prepare_mindcube.py)。

### MMSI-Bench

- 官方仓库：<https://github.com/InternRobotics/MMSI-Bench>
- 官方代码 commit：`13e58a2b8b30d880d7e8a1e4a6aa1c0feda94cac`；官方 Hugging Face revision：`ec7c92bfaf7728fcca1d61e3e224e190af309436`。
- 已核验的 A100-2 快照：1000 题、2550 张图、2–10 图；JSONL SHA256 `9448f3ffc9c2364d396ab29bfc5a66ecab26fcc076ce1b6b364bdcad7c721601`，逐题元数据与官方 revision 全量一致。
- DAAI 正式输入：`/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed_daai/test.json`，1000 题 / 2550 图，SHA256 `5de75a94eebb2ad31b44ab0f33d7225c56157165292d8112e287c410f56180c9`；`test_provenance.json` SHA256 `fa5f4ee9223cf72fd4dcbc941b8fbd66788b37d854844532bde581cd2aebdf9f`；严格官方预处理和独立校验均通过，图片树摘要 `1915bcb705e661d46bab44dd8fe9513153466bca458bef26d030235d9e9c07d9`。
- 旧 DAAI 快照 `/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed/test.json` 归属 `tyjiang`，`24482277` 无读取权限，仅保留作审计，不作为本轮正式输入；不得用其旧 provenance 哈希替代新的 `processed_daai` provenance。
- A100-2 诊断输入：`/data/shiyang/datasets/MMSI_Bench_ec7c92bf/processed/test.json`，1000 题 / 2550 图，SHA256 `8f5be1f6b09991ceb1ddb1761df70a0ff730aba1ac38a4081881ebfa6edbff94`；`test_provenance.json` SHA256 `c3afa4b86d7088fc162c2d0fb9f80053f692edee5c00032215ae20380acda2be`。
- A100-2 基础单题诊断子集：`/data/shiyang/datasets/MMSI_Bench_ec7c92bf/smoke_index585`，1 题（2 图），`test.json` SHA256 `4a3b6ab94c0cfe8b439e2687423f28710e1ba0a3058e5850db451e2dd496b831`。
- A100-2 多图边界定向子集：`/data/shiyang/datasets/MMSI_Bench_ec7c92bf/smoke10_index140`，1 题（10 图），`test.json` SHA256 `6acf0d4a8345ca172694fe0d212cde802942abea64470c583691cadefaa21beb`。MMSI 在正式提交前必须同时通过基础 smoke 和该 10 图 smoke。
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
