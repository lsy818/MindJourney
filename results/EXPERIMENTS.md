# MindJourney 实验结果与计划

最后更新：2026-09-08（Asia/Shanghai）

本文件同时记录实验优先级和已验证的实验产物。优先级数字越小，优先级越高；`P0` 表示用户指定为已经运行的项目，但只有带有正式 `COMPLETE`、可复核结果文件和哈希的项目才记为“已验证完成”。

## 最新进展：2026-09-08 中午（覆盖下文历史队列快照）

- 原 r3 首片 `66599_0`、`66600_0`、`66601_0` 已加载权重并开始 vLLM 编译，但在 7200 秒就绪上限处退出，尚无正式题目结果。日志与缓存保留。相同 Run ID 已分别续提为 `66705_0`、`66706_0`、`66707_0`，显式传入 `P1_READY_TIMEOUT_SECONDS=21600`；截至 11:56，前者在 srv11 运行，后两者排队。
- 72B 权重下载 `65957` 已 `COMPLETED 0:0`，耗时 17:58:51，依赖提交器 `66598` 也已完成。此前 5×A100 首片 `66618` 已由 `66708` 替代；用户随后授权进一步减少卡数，改试 3×A100（72B TP=2 + SVC 独占 1 卡）。BF16、65536 上下文、多图顺序和 SVC 搜索/生成设置保持原值。三卡可运行性仍须以实际启动和推理结果确认。
- 三卡源码 commit `61c318670876f9b0208b05d2cf56b40f05fa732f`，source SHA256 `c78ffdb2d4a9e54d5a07ae3138234a4089015af48e14155042e3a0773636b6eb`；实验清单同步记录 A100 TP=2，清单 SHA256 `1b13b98fc39873515eb3794a4c417197ae222f844b6ae41402442103aa93f77f`。就绪超时默认 21600 秒。资源配置定向测试 4/4 通过；无服务器环境重检。
- 72B 独立代码目录：`/home/comp/24482277/shiyang/MindJourney-p1-72b-tp2-20260908`。其他三项继续使用原目录 commit `774f754`，按各自源码和清单指纹续跑。
- 72B 三卡 Run ID：`mj-p1-mindcube-qwen25vl-72b-a100-tp2-r4-20260908`；产物目录：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mindcube-qwen25vl-72b-a100-tp2-r4-20260908`。提交器 `66714` 已 `COMPLETED 0:0`（00:01:43），三卡首分片为 `66716_0`；五卡待运行作业 `66708` 已取消，旧日志保留。不将 TP=4 的旧 Run 与 TP=2 新 Run 合并。

## 结果保留约定

1. `results/` 采用追加式归档。不要删除或覆盖已有 run；重跑时创建新的 run ID。
2. Git 中保存紧凑且可复核的结果：合并结果、分片结果、配置、运行/提交清单和完成标记。
3. 大型逐题图像、视频和日志继续保留在 DAAI 原始运行目录，不复制进 Git，也不得删除。
4. 完成一项实验后，必须登记数据快照、模型 revision、thinking 模式、方法配置、Slurm ID、结果路径、指标及 SHA256。
5. 所有归档产物的逐文件校验值见 [SHA256SUMS](./SHA256SUMS)。

## 实验优先级矩阵

| 数据集 | Qwen3.5-27B | Qwen2.5-VL-72B-Instruct | Qwen3.5-9B | Qwen3.8-27B |
|---|---|---|---|---|
| MindCube 1050 | P1 · 首片运行中 | P1 · 等待权重续传 | P3 · 待跑 | P3 · 待跑 |
| MMSI-Bench 1000 | P0 · 用户称此前已跑，产物待定位/验证 | P0 · 用户称此前已跑，产物待定位/验证 | P1 · 首片运行中 | P1 · 首片排队中 |
| SAT Real | P0 · **已验证完成** | P0 · 用户称此前已跑，产物待定位/验证 | P2 · 待跑 | P2 · 待跑 |
| SAT Syn (`rand42-500`) | P0 · **已验证完成** | P4 · 待跑 | P4 · 待跑 | P4 · 待跑 |

用户后续指令已确认第 1、2 行分别对应 MindCube 1050 与 MMSI-Bench 1000。`Qwen3.8-27B` 的规范模型 ID 已确认为 `Qwen/Qwen3.8-27B`。当前先完成四项 P1：MindCube 1050 的 Qwen3.5-27B、Qwen2.5-VL-72B-Instruct，以及 MMSI-Bench 1000 的 Qwen3.5-9B、Qwen3.8-27B；高优先级分片完成并验证后再进入 P2/P3/P4。

## P1 准备与运行状态

| 数据集 / 模型 | 数据 | 权重 | Smoke | 全量分片 | 结果文件 |
|---|---|---|---|---|---|
| MindCube / `Qwen/Qwen3.5-27B` | 1050 题及完整原始图片树已就绪并严格验证；A100-2 诊断副本已就绪 | DAAI 目录含 `config`、11 个 safetensors；精确 revision marker 已验证且组可读；A100-2 完整权重树已核验 | SVC 精确缓存 Job `65533` 与持久环境 Job `66420` 均已严格验证完成 | r3 提交器 `66595` 已完成；正式首片 `66599_0` 正在 `hkbugpusrv11` 使用 2 × A100 80GB 运行，其余分片待按同一 Run ID 逐片续提 | Run ID：`mj-p1-mindcube-qwen35-27b-a100-r3-20260908`；DAAI：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mindcube-qwen35-27b-a100-r3-20260908` |
| MindCube / `Qwen/Qwen2.5-VL-72B-Instruct` | 1050 题及完整原始图片树已就绪并严格验证；A100-2 诊断副本已就绪 | DAAI 固定 revision 权重续传 Job `65957` 仍在运行；partial 和下载日志全部保留 | SVC 精确缓存与持久环境均已完成；仅等待 72B 权重树和 marker 严格验证，72B 不在 40GB A100 上运行 | r3 提交器 `66598` 等待 `65957` 的依赖；下载成功后仅创建正式分片 `0` | 计划 Run ID：`mj-p1-mindcube-qwen25vl-72b-a100-r3-20260908`；DAAI：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mindcube-qwen25vl-72b-a100-r3-20260908` |
| MMSI-Bench / `Qwen/Qwen3.5-9B` | Job `65519` 已在 00:33:20 完成：1000 题 / 2550 图，严格官方预处理与独立校验通过；新的 `processed_daai` 输入对 `24482277` 可读，旧 `processed/test.json` 仅保留审计 | DAAI 目录含 `config`、4 个 safetensors；精确 revision marker 已验证且组可读；A100-2 固定 revision 的完整权重树已核验 | SVC 精确缓存 Job `65533` 与持久环境 Job `66420` 均已严格验证完成 | r3 提交器 `66596` 已完成；正式首片 `66600_0` 正在 `hkbugpusrv11` 使用 2 × A100 80GB 运行，其余分片待按同一 Run ID 逐片续提 | Run ID：`mj-p1-mmsi-qwen35-9b-a100-r3-20260908`；DAAI：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mmsi-qwen35-9b-a100-r3-20260908` |
| MMSI-Bench / `Qwen/Qwen3.8-27B` | 1000 题 / 2550 图已就绪并严格验证；A100-2 诊断副本已就绪 | 下载 Job `65447` 与严格验证 Job `65500` 均已完成；固定 revision 目录完整，外部 marker 为 `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` | SVC 精确缓存 Job `65533` 与持久环境 Job `66420` 均已严格验证完成 | r3 提交器 `66597` 已完成；正式首片 `66601_0` 等待 A100 80GB 调度，其余分片待按同一 Run ID 逐片续提 | Run ID：`mj-p1-mmsi-qwen38-27b-a100-r3-20260908`；DAAI：`/home/datasets/shiyang/daai_runtime/p1_runs/mj-p1-mmsi-qwen38-27b-a100-r3-20260908` |

- 推理统一使用 BF16 和 no-thinking；Qwen2.5-VL 不发送其不支持的 Qwen3 thinking 参数。
- 诊断 smoke/debug 允许且优先在 A100-1 或 A100-2 直接运行，避免为调试占用 DAAI 的 Slurm 队列；仅在有足够、可安全独占的空闲 GPU 时启动，不抢占、不超卖，也不终止其他用户进程。
- 正式全量计算只在 DAAI 运行。H20 96GB 空闲时优先；否则使用 A100 80GB，并排除 40GB DGX。硬件切换不得改变 BF16、no-thinking、图片顺序或 SVC/搜索参数。
- 数据、模型、SVC 缓存和持久环境已经在准备阶段一次性完成严格检查；正式 worker 启动时只核对不可变 `COMPLETE` / freeze / source 哈希，不再重复导入 vLLM、SVC pipeline 或执行版本探测。“已提交/排队”仍不等于“已完成”。
- 统一配置：[p1_svc_multiimage.json](../configs/p1_svc_multiimage.json)。
- A100-1 与 A100-2 均为 8 × A100 PCIe 40GB；最后观测时两台机器的 8 张卡均有常驻进程，没有可安全独占的空闲卡，因此尚未启动任何 A100 诊断 smoke。A100-2 的工作副本位于 `/data/shiyang/MindJourney`。
- H20 节点 `hkbugpusrv16` 本轮提交前 8 张卡中已有 7 张被占用，仅剩 1 张，不足任何一项 P1 所需的最少 2 张，因此当前正式首批回退到 A100 80GB。所有 A100 回退都显式排除 40GB DGX；后续提交前仍会重新检查 H20，而不会把本次回退固化为实验设置。
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

快照时间：北京时间 2026-09-08（驱动兼容恢复后的 r3 首片；具体状态以 Slurm accounting 为准）。

- 环境首试 Job `65505` 因 Slurm 脚本错误定位仓库而立即失败；定位逻辑已在 commit `01ef26c` 修复。后续环境 Job `65510` 运行 00:59:38 后因 Cargo home 缓存的 disk I/O / `proc_macro2` 错误失败；Job `65532` 又在 00:00:07 因 Linux/NFS 上 `flock` 返回 `EBADF` 失败。SVC 锁兼容修复 commit `9eaea12` 已通过 62/62 测试，环境安全续传与隔离缓存修复 commit `c63e58e` 已通过全量 64/64 测试；为确保 `puccinialin` / Cargo 子进程实际缓存路径与记录一致，最终修复 commit `a2d77b6` 又通过了定向 10/10 测试，此前的全量 64/64 结论仍适用。
- SVC exact-revision 预取 Job `65533` 已在 `hkbugpusrv07` 以状态 `COMPLETED 0:0` 完成，Elapsed 12:46:04。完成标记为 `/home/datasets/shiyang/daai_runtime/model_cache/mindjourney/svc-assets-v1/COMPLETE`，manifest SHA256 为 `aa311c4796b36c8c995344d1eae0a5f7ca38d8c7a89cc9966f1edfbf0ff09381`；manifest 中的固定 revision 与预期三项权重 SHA 均一致。另使用 `hf0350` Python 离线执行 `scripts/p1_svc_assets.py validate`，结果为 `5 files valid`，因此该依赖已独立验证完成。
- 持久环境续传 Job `65534` 在运行 00:03:10 后被主动取消；后续环境续建 Job `65537` 运行 03:03:49 后以 Exit 1 失败。`65537` 的根因不是先前的缓存 I/O，而是 Cargo 下载 `ring 0.17.14` 时代理连接出现 `SSL_ERROR_SYSCALL` / unexpected EOF；该作业已成功下载的大量 crate 缓存全部保留。
- 基于安全 `--resume` 和已有隔离缓存，环境续建 Job `65590` 曾显式设置长超时，但运行 01:28:46 后因 uv 下载/解压 `nvidia-cudnn-cu13 9.20.0.48` 网络超时而失败。随后 Job `65706` 运行 05:02:39 后以 `FAILED 1:0` 结束；这次根因是 Cargo registry / SQLite / target 位于 NFS 时出现 disk I/O error，并进一步触发 Rust `E0463`。两次环境残留、共享 uv 缓存与全部失败日志均保留。
- 修复 commit `53687b2` 将 Rust/Cargo registry、target 和临时目录迁到计算节点本地 `mktemp`，仅保留 uv cache 在共享目录以支持断点续传。环境重试 Job `65956` 在 `hkbugpusrv07` 运行 00:17:29 后以 `FAILED 1:0` 结束；allocation 内已验证本地 `/tmp` 为 XFS，因此此前 NFS disk I/O 问题确已消除。本次失败点转为 `puccinialin` 在本地 `/tmp` 下载 Rust toolchain 时无法解析 `static.rust-lang.org`；日志和可复用缓存全部保留。
- 已验证持久旧 Rust toolchain 完整可用：stable `cargo` / `rustc 1.98.1`，并保留 `1.95` 备用。修复 commit `f0eb87a` 让 `RUSTUP_HOME` 和工具链只读复用该持久路径，同时继续让 `CARGO_HOME` / registry / target / tmp 使用计算节点本地 XFS；全量 64 tests 通过。Job `66000` 已完成全部安装，但其最终 pipeline import 长期处于共享 NFS 的 `rpc_wait`，在运行 10:25:48 后主动取消；partial、锁语义与完整日志均保留。保守导入瘦身 commit `503f0f0` 仅延迟 Gradio/InternVL 等 P1 Qwen 不使用的依赖并删除未使用导入，未改 prompt、图片顺序、SVC 采样、RNG 或实验设置；全量 65/65 tests 通过。原地续跑 Job `66420` 随后在 00:51:17 内以 `COMPLETED 0:0` 结束，完整 pipeline import 成功并原子写出 `COMPLETE`。独立重算的 `VERSIONS.txt`、`qwen.freeze.txt`、`svc.freeze.txt` SHA256 分别为 `c6765f2734b25a38878a1a9ce28d1269732f19c1d7fc55551e275c3f3d93d81f`、`36c5df8411292df7f652ff6fc6c1ab16e23931fb5305a4c56ca256f061385891`、`635e5158038ca9d2b56290908e69cd67e069fad84d105e3514f2172b883f706b`，与 `COMPLETE` 全部一致；固定版本包括 Python 3.12.4、vLLM 0.28.0、Torch 2.9.0、Transformers 4.46.3、Diffusers 0.35.1、NumPy 1.26.0 与 numpy-quaternion 2024.0.3。
- Qwen2.5-VL-72B 首次下载 Job `65502` 因计算节点缺少 `huggingface_hub` 失败；旧重复 Job `65499` 已取消。后续 HTTP 续传 Job `65504` 运行 13:15:26 后因 `requests.exceptions.ChunkedEncodingError` / `IncompleteRead` 失败：当时主分片已读取 3,782,619,236 bytes，尚余 212,564,732 bytes；已下载缓存、未完成文件和失败日志全部保留。
- 单 worker 续传 Job `65785` 在运行 02:55:32 后再次因 `ChunkedEncodingError` 以 `FAILED 1:0` 结束；当时分片 19 为 3,565,158,400 / 3,995,183,968 bytes，完整文件 26/50、完整权重分片 19/38，缓存、partial 和日志全部保留。修复 commit `53687b2` 为同一作业加入最多 20 次断点重试；commit `bd85282` 修复“权重结构已完整但尚无 marker”时仍须按固定 Hub revision 补全并验证的路径。重试 Job `65957` 当前仍为 `RUNNING`，约 29/50 个文件完整且暂无新错误；它使用单 worker、最多 20 次尝试和 60–300 秒退避，并通过 `24482277` 账号的 `HF_TOKEN_PATH` 读取凭据。本文和 Git 中不记录令牌内容；只有完整索引、全部权重分片、固定 revision marker 与严格校验均通过后，72B 才会记为下载完成。
- Qwen3.8-27B 下载 Job `65447` 已以 `COMPLETED 0:0` 结束，Elapsed 1-04:36:58；严格验证 Job `65500` 也已以 `COMPLETED 0:0` 结束，Elapsed 00:00:18。外部 marker 为 `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`，日志确认固定 revision 目录完整，因此该模型权重前置项已严格验证完成。
- 旧的四个正式提交器 Job `65511`–`65514` 已取消。这些提交器试图一次创建四个完整数组，而集群 `QOSMaxSubmitJobPerUserLimit` 会把数组中的每个 task 计入约 10 个可提交槽位，继续保留会阻塞真正的计算分片。取消提交器不删除任何已有结果或日志。
- 首轮 A100 数组暴露出节点驱动差异：`66493_1`、`66493_2` 和 `66494_0` 在 `hkbugpusrv08` 上失败，vLLM 日志显示该节点 CUDA driver 为 `555.42.02`（API 12.5），不能运行 Qwen 服务环境的 PyTorch 2.13 + CUDA 13.0 / vLLM 0.28.0；同为 R555 的 `hkbugpusrv07` 也已排除。`hkbugpusrv11`、`hkbugpusrv12`、`hkbugpusrv15` 已观测到 R580 驱动，其中 r3 运行使用 `hkbugpusrv11`。A100 资源计划现同时排除 `hkbugpusrv07`、`hkbugpusrv08` 与 40GB DGX。
- 持久环境同时包含职责不同的两个环境，不能用单一 Torch 版本概括：Qwen/vLLM 服务侧是 PyTorch 2.13 + CUDA 13.0，SVC pipeline 侧是已冻结的 PyTorch 2.9 环境。环境完成标记 SHA256 为 `4c3ccc5763b452719ee9564c6afbff63c9e13bfc1f0b6513ddfbfa0b4e5dec50`；提交清单会绑定该 SHA 以及既有 freeze 哈希，防止在不同环境上静默运行。
- 驱动兼容与启动优化 commit `a2dd3e2` 将已知旧驱动节点加入排除列表，并让正式 prolog 信任已验证的不可变环境清单；后续 commit `774f754` 删除 `scripts/p1_serve_vllm.sh` 中最后一次 `vllm --version` 重型导入。两次修改均未改变数据、prompt、图片顺序、BF16、no-thinking、SVC 或搜索参数，最新全量测试为 67/67 通过。环境、模型、数据在准备阶段已检查，正式 task 启动仅核对标记与哈希，不再重复 vLLM/SVC 导入或版本探测。
- 驱动失败后的原数组 `66493`、`66494` 及当时仍在运行的 `66492_0` 均停止继续使用；它们没有可验证的正式结果。首次恢复 r2 的 `66587_0`、`66588_0` 等 task 也在发现残余 `vllm --version` 后取消，尚未进入逐题推理。所有旧 run root、partial、失败日志和取消记录均原样保留，不删除、不合并到 r3。
- 当前正式 r3：MindCube / Qwen3.5-27B 提交器 `66595` 已完成，`66599_0` 正在 `hkbugpusrv11` 的 2 × A100 80GB 上运行；MMSI / Qwen3.5-9B 提交器 `66596` 已完成，`66600_0` 正在同节点的 2 × A100 80GB 上运行；MMSI / Qwen3.8-27B 提交器 `66597` 已完成，`66601_0` 因 Priority 等待调度；72B 续传 Job `65957` 继续运行，其依赖提交器 `66598` 等待下载成功。
- r3 Run ID 分别为 `mj-p1-mindcube-qwen35-27b-a100-r3-20260908`、`mj-p1-mmsi-qwen35-9b-a100-r3-20260908`、`mj-p1-mmsi-qwen38-27b-a100-r3-20260908`，以及计划中的 `mj-p1-mindcube-qwen25vl-72b-a100-r3-20260908`。r1/r2 及更早运行目录继续保留作审计；任何 r3 结果只写入自己的新目录。
- `24482277` 对旧 MMSI `processed/test.json` 无读取权限，但可读取原始 `mmsi_full.jsonl` 和 2550 张图片。交互式预处理 Job `65518` 被外部取消且未产生正式输入；持久批处理 Job `65519` 已在 00:33:20 完成，使用官方严格转换程序生成 `/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed_daai/test.json`（SHA256 `5de75a94eebb2ad31b44ab0f33d7225c56157165292d8112e287c410f56180c9`）与 `/home/datasets/shiyang/MMSI_Bench_ec7c92bf/processed_daai/test_provenance.json`（SHA256 `fa5f4ee9223cf72fd4dcbc941b8fbd66788b37d854844532bde581cd2aebdf9f`）；1000 题 / 2550 图及官方图片顺序已通过独立严格校验，原始文件和失败记录均保留。
- MindCube / Qwen3.5-27B 和 MMSI / Qwen3.5-9B 的历史 H20 数组、失效提交器及 r1/r2 A100 尝试均保留审计；MMSI / Qwen3.8-27B 的早期提交器 `66425` 曾因提交节点默认 Python 过旧失败，后来已使用固定 Python 3.12 控制面路径修复。上述控制面修复均不改变 worker 环境或实验设置。
- MindCube / Qwen2.5-VL-72B-Instruct 的旧提交器 `66491` 已取消并保留；r3 提交器 `66598` 仅依赖仍在续传的 72B 权重 Job `65957`。下载 partial 与重试日志全部保留，只有固定 revision 文件树及 marker 严格验证成功后才会创建正式分片 `0`。
- r3 提交器继续显式使用 `P1_CACHE_ROOT=/home/datasets/shiyang/daai_runtime/model_cache` 和 `P1_MODEL_VALIDATION_ROOT=/home/datasets/shiyang/mindjourney_storage/model_validation`。Qwen3.5-27B、Qwen3.5-9B 与 Qwen3.8-27B 的精确 revision 标记均已验证；所有 A100 task 都排除 40GB DGX 及已知 R555 节点。
- Hugging Face read token 仅安装在 `24482277` 账号的凭据存储中，并已验证能够读取 gated Stable Virtual Camera 仓库；Git 记录、结果文档和日志中均不保存 token 值或其他 secret。
- 当前 QOS 策略是让每个 array 一次只创建一个 task（r3 首轮均为 `--array 0`），因为 `QOSMaxSubmitJobPerUserLimit` 会将 array 的每个 task 计入约 10 个可提交槽位。当前 task 完成并释放槽位后，再用同一 Run ID、`--resume --array <下一片>` 逐片续提；不得创建新 Run ID，也不得覆盖已有片。排队、提交器成功或单片结束都不等于实验完成；只有完整覆盖、零静默跳题、正式 `COMPLETE`、合并结果与哈希全部通过后才更新为“已验证完成”。
- DAAI r3 worker 源码固定为 commit `774f75435b43f7cadc35ced50341fbc65d5e90ed`，正式 source SHA256 为 `1d441a15d0f7d28e365d897598fc16307632eb62f1b734a58c5d138dcf9c2d3d`。本次仅在远端追加结果记录文档，不在 r3 运行期间拉取该文档 commit，以免改变运行目录中的 tracked 状态；后续分片继续使用相同 worker commit、source SHA 与环境 `COMPLETE` SHA。

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
