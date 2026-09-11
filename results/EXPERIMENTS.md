# MindJourney 实验结果与计划

最后更新：2026-09-12（Asia/Shanghai）

本文件同时记录实验优先级和已验证的实验产物。优先级数字越小，优先级越高；`P0` 表示用户指定为已经运行的项目，但只有带有正式 `COMPLETE`、可复核结果文件和哈希的项目才记为“已验证完成”。

## 最新进展：2026-09-12 06:26 MMSI/3.8 完成7/10片，剩余三片全部运行

- MMSI/Qwen3.8-27B片6 `69413_6` COMPLETED 0:0，用时06:51:25，15对85错。冻结r8严格验证100题精确覆盖、0skip、参数/run-group和COMPLETE结果SHA通过。原始[结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_6/results.json)、COMPLETE及validation_summary已归档，SHA `0b608afd36bc3cf16165c46eb7991d36f4026d7bb869b313d75c62cedcb18869`。正式完成0–6共700题142对558错，20.29%仅为部分准确率；P1累计39个正式完成片，不提前合并全量。
- 06:26剩余片7/8/9 `69723_7`、`69736_8`、`69913_9`全部RUNNING，分别srv15/srv11/srv11，各2A10080GB，合计6×A100；进度76/100、31/100、31/100，均0skip。片9已自动接替片6启动，无剩余P1候补或未提交片。当前只剩这三片，不能为用满5个运行名额而重复提交。
- 原Run/r8、本地环境、BF16/no-thinking/65536/官方图片顺序及论文SVC设置完全不变，未重启任务、重新检查环境或删除结果。全部完成和失败尝试日志均保留，后续三片逐片核验归档，十片全部完成后再严格合并。

## 历史进展：2026-09-12 03:54 MMSI/3.8 完成6/10片

- MMSI/Qwen3.8-27B片5 `69413_5` COMPLETED 0:0，用时06:41:05，23对77错。冻结r8严格验证100题精确覆盖、0skip、参数/run-group和COMPLETE结果SHA通过。原始[结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_5/results.json)、COMPLETE及validation_summary已归档，SHA `ebfbc08a599fb2b8080bc009ab98fafde412d8c559f8126f7260b4c905b57cf4`。正式完成0–5共600题127对473错，21.17%仅为部分准确率；P1累计38个正式完成片，不提前合并全量。
- 03:54片6 `69413_6`（srv11）、片7 `69723_7`（srv15）继续RUNNING，分别92/100、35/100，0skip；片8 `69736_8`已在srv11接替启动约40秒，尚无首题结果。片9 `69913_9`仍PENDING Priority。每片2A10080GB，合计3/5运行、6×A100，1个P1候补。全部剩余6–9均已活动，无未提交片，禁止重复提交。
- 原Run/r8、本地环境、BF16/no-thinking/65536/官方图片顺序及论文SVC设置完全不变，未取消或重启健康任务，未重新检查环境。所有历史结果、视频及日志保留。

## 历史进展：2026-09-12 01:17 MMSI/3.8 完成5/10片，最后一片已提交

- MMSI/Qwen3.8-27B片4 `69413_4` COMPLETED 0:0，用时07:24:49，20对80错。冻结r8严格核验100题精确覆盖、0skip、参数/run-group及COMPLETE结果SHA通过。原始[结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_4/results.json)、COMPLETE和validation_summary已归档，SHA `72a082d981c75ac467e11b3176bbc5ef8f9650b7d767e5b301da00770323699f`。正式完成0–4共500题104对396错，20.80%仅为部分准确率；P1累计37个正式完成片，不提前合并全量。
- 01:16片5/6 `69413_5/6`继续RUNNING srv11，各2A10080GB，已58/100、55/100；片7 `69723_7`于01:11接替片4在srv15启动，尚未保存首题，不冒充已开始题目推理。片8 `69736_8`仍PENDING Priority。01:17检查GPU/配额并跨数组去重后，补交最后未提交片9为 `69913_9`，2A10080GB，即时PENDING。全部剩余5–9现在均已运行或排队，跨数组cap5，不再新增重复分片。
- 即时3/5运行、6×A100，2个P1候补；含无关55278共6/10活动。兼容A100 srv11/12/15均8/8已分配，等待资源，不把排队算作额度已满。见[最后一片提交审计](./scheduling/20260911T171712Z-mmsi38-last-shard.json)。原Run/r8、本地环境和BF16/no-thinking/65536/官方图片顺序/论文SVC设置完全不变，未重启健康作业或重复环境检查，全部结果及日志保留。

## 历史进展：2026-09-11 23:34 MindCube/72B 全量完成并严格合并

- MindCube / Qwen2.5-VL-72B-Instruct / SVC 全量1050题：**416对 / 634错，准确率39.62%**。11/11片全部完成，0skip；冻结r8验证器通过精确题ID覆盖、无重复遗漏、正式参数、run-group和所有COMPLETE结果SHA检查。[全量结果](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/results_merged.json)与[正式汇总](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/formal_run_summary.json)已归档。合并SHA `e8a48d429b72c20a2efb2f8eeebfd6135cf84d32f8446606f9a2ade341833f95`，服务器原Run根目录results_merged.json保留。
- 最后片9/10分别37/95、43/100正确，作业 `69407_9/10` 均COMPLETED 0:0，用时05:40:24、05:36:52；原始JSON、COMPLETE和validation_summary均已逐片核验归档。类别准确率among 36.83%、around 43.60%、rotation 43.00%。TP2＋独占SVC1、每片3H20、实际export 0.93及BF16/no-thinking/65536/官方图片顺序/论文SVC设置不变。
- 四项P1现已有三项全量完成（MC27B 498/1050、MC72B 416/1050、MMSI9B 288/1000），累计36个正式完成片。只剩MMSI/3.8，已完成0–3共400题84对，21.00%仅部分。23:32片4/5/6 `69413_4/5/6` 继续RUNNING，各2A10080GB，进度75/100、33/100、30/100；片7/8 `69723_7`、`69736_8` PENDING Priority。当前3/5运行、6×A100，不能称账户已满；23:34兼容A100 srv11/12/15全8/8已分配，虽H20有6张空余，但不混改既有A100 Run硬件指纹。MMSI活动4–8达到跨数组cap5，剩余片9待活动容量释放后补交，不重复提交、不重启健康作业。所有历史结果和日志保留。

## 历史进展：2026-09-11 21:34 MMSI/3.8 已完成4/10片

- MMSI/Qwen3.8-27B片3 `69413_3` 已COMPLETED 0:0，用时07:30:43，20对80错。固定r8严格验证100题精确覆盖、0skip、配置/run-group及COMPLETE原始结果SHA均通过。原始[结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_3/results.json)、COMPLETE和validation_summary已归档，SHA `8163aa9864ebccb090969794365ae87f75d0dc61b0f6914de2a8d1ee1dc92f33`。正式完成0–3四片，共400题84对316错，21.00%仅为部分准确率；P1累计34个正式完成片，不提前合并全量。
- 21:33账户仍5/5运行名额、6×H20＋6×A10080GB。MindCube/72B最后片9/10 `69407_9/10`已61/95、63/100；MMSI片4/5 `69413_4/5`已52/100、3/100；片6 `69413_6`已自动接替片3并保存首题。均0skip，无新失败，所有健康作业继续运行。
- 21:34刷新GPU/配额并跨所有数组去重，实际补交MMSI片8为 `69736_8`，每片2×A10080GB，即时PENDING QOSMaxJobsPerUserLimit；片7 `69723_7`亦候补。MMSI活动4/5/6/7/8共5片达到cap5，账号含无关55278共8/10活动，剩余未提交仅片9。见[补位审计](./scheduling/20260911T133413Z-mmsi38-chunk8-refill.json)。原Run/r8、本地环境、BF16/no-thinking/65536/官方图片顺序和论文SVC设置完全不变；72B仍TP2＋独占SVC1、实际export 0.93。未重启、删除或重新配环境。

## 历史进展：2026-09-11 21:20 MMSI/3.8 新完成片1，持续5片并行

- MMSI/Qwen3.8-27B片1 `69413_1` 已COMPLETED 0:0，本次续跑用时07:16:03（不含旧失败尝试），24对76错。固定r8验证器通过100题精确覆盖、0skip、配置/run-group及COMPLETE结果SHA检查。原始[结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_1/results.json)、COMPLETE和validation_summary已归档，SHA `ca590d614f708d1aee485a0755d651651a6d751b424404c9d706bd2af08b790c`。该setting正式完成0/1/2三片，共300题64对236错，21.33%仅为部分准确率；P1累计33个正式完成片。
- 21:18账户仍占满5/5运行名额，共6×H20＋6×A10080GB。MindCube/72B最后片9/10 `69407_9/10`（srv16）已57/95、59/100；MMSI片3/4 `69413_3/4`（srv11/srv15）已98/100、48/100；片5 `69413_5`已自动接替片1在srv11启动，尚未保存首题。未发现新失败，不将未完成片提前记为正式结果。
- 21:19刷新GPU/配额并跨数组去重后，补交MMSI片7为 `69723_7`，每片2×A10080GB，即时PENDING QOSMaxJobsPerUserLimit。与候补片6 `69413_6`共同等待名额；MMSI跨数组活动3–7共5片达到cap5，账号含无关55278共8/10活动。见[补位审计](./scheduling/20260911T131957Z-mmsi38-chunk7-refill.json)。沿用原Run/r8及节点本地环境；72B TP2＋独占SVC1、实际export 0.93及全部BF16/no-thinking/65536/官方图片顺序/论文SVC设置不变。所有结果和日志保留，未重启健康作业。

## 历史进展：2026-09-11 13:39 27B全量已推送，72B收尾＋MMSI/3.8补位

- MindCube/27B全量498/1050（47.43%）及全部原始分片、严格合并文件已push `ec770eb`，不再提交该已完成Run。MMSI/9B亦为已完成全量288/1000（28.80%）。
- MC72B新增片4–8已逐片严格验证：精确95题/片、0skip、配置/run-group及COMPLETE结果SHA全通过。各片原始results.json、COMPLETE与validation_summary均已归档至该Run的chunks/question_chunk_4至8；共0–8九片855题336对519错，39.30%为部分准确率，不提前合并全量。新增片作业与用时：4=`68005_4` 05:25:37（39对）、5=`68454_5` 05:51:44（36对）、6=`68804_6` 04:58:37（37对）、7=`68871_7` 06:18:18（31对）、8=`69002_8` 06:02:19（39对）。P1累计32个正式完成片。
- 13:39在27B全量push后，刷新配额与资源，实际提交MMSI/3.8未完成片1/3/4/5/6为 `69413_[1,3,4,5,6]`，各2×A10080GB；原Run/r8、已有0/2结果及旧片1断点保留，不重复提交完成片。与72B最后片9/10 `69407_9/10`（各3H20、TP2＋独占SVC1、export 0.93）组成两组集中队列。无重启或环境复查，全部论文设置保持不变。
- 即时7个P1均PENDING，账户含无关55278共8/10提交，运行0/5不能算已用满：兼容A100 srv11/12各8/8占用、srv15为7/8，仅1张空余不足单片2张；H20 srv16为8/8占用。是集群资源等待，不是分片串行依赖。MMSI跨数组活动cap5已满，72B最后两片全部已活动，不能为填提交槽重复提交。见[两组补位审计](./scheduling/20260911T053909Z-mmsi38-second-setting.json)。后续资源释放即由Slurm启动，完成继续核验归档与补交MMSI7–9。

## 历史进展：2026-09-11 13:35 MindCube/27B 全量完成并严格合并

- MindCube / Qwen3.5-27B / SVC 全量1050题：**498对 / 552错，准确率47.43%**。11/11片全部COMPLETED 0:0，0skip。冻结r8严格合并器通过全部题ID精确覆盖、无重复遗漏、正式设置、run-group及COMPLETE原始结果SHA检查。[全量原始结果](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/results_merged.json)与[正式汇总](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/formal_run_summary.json)已归档。合并SHA `9d7f93fb15994a31549fdae0e5efb921dc0ee3c515a9a6cf2fc59eadccc96966`；服务器原文件保留于原Run根目录results_merged.json。
- 新增27B片8/9/10分别47/95、38/95、47/100正确，作业 `68453_8/9/10` 用时14:52:08、14:13:22、15:56:24；三个原始JSON、COMPLETE和validation_summary均已严格核验归档。按类别准确率among 35.50%、around 56.00%、rotation 72.50%。BF16、no-thinking、65536、官方图片顺序及论文SVC设置不变。
- 13:32远端发现此前活动实验均已完成、P1队列为空；这是本次监控实际恢复时间，不将旧快照冒充实时。72B片4–8均COMPLETED 0:0，分别39/36/37/31/39对、每片95题，尚待本轮逐片正式归档；该Run共9/11片完成，不提前标记全量。
- 13:33查资源配额并去重后，实际补交72B最后片9/10为 `69407_9/10`，各3H20、TP2＋独占SVC1，实际export显式0.93，原Run/r8不变，即时PENDING。见[最后两片提交审计](./scheduling/20260911T053346Z-mindcube72-last-two.json)。待本次27B合并结果push后，以MMSI/3.8作为第二setting补位，保持两组集中与额度优先。所有旧结果、日志和失败断点保留，未重新配置环境。

## 历史进展：2026-09-10 20:46 MindCube/72B 已完成4/11片

- MC72B chunk3 `68005_3` 已COMPLETED 0:0，用时04:30:02；严格核验95/95题、34对61错、0skip，精确题ID、配置/run-group和COMPLETE结果SHA全通过。原始[结果](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/chunks/question_chunk_3/results.json)、COMPLETE与validation_summary已归档，结果SHA `04dc0a548b0029b97c074d160dcdfa7c262d9e504a1f0e267b7b03320174941d`。72B完成0–3共380题154对226错，40.53%仅为部分准确率；P1累计24个正式完成片，不提前合并全量。
- 20:45 MC72B chunk5 `68454_5` 已接替RUNNING且保存首题，chunk4 `68005_4` 已60/95题。MC27B chunk8/9/10 `68453_8/9/10` 继续运行，分别59/41/42题，均0skip。仍5/5运行名额、6×A10080GB＋6×H20，未发现新失败。
- 20:46刷新GPU、配额及全部数组去重后，新增72B chunk8为 `69002_8`，即时PENDING QOSMaxJobsPerUserLimit；待运行6/7/8为 `68804_6`、`68871_7`、`69002_8`，该setting跨数组活动4–8共5片已满。含无关55278账号9/10活动，MC27B剩余全已运行，不重复提交、不引入第三setting。72B原Run/r8、TP2＋独占SVC1共3H20及实际export 0.93保持不变，未重启作业或重配环境。见[补位审计](./scheduling/20260910T124620Z-mindcube72-chunk8-refill.json)。所有结果和日志保留，共享存储不宣称根治。

## 历史进展：2026-09-10 17:09 MindCube/72B 已完成3/11片

- MC72B chunk2 `68005_2` 已COMPLETED 0:0，本次续跑用时05:35:05（不含旧失败尝试）；严格核验95/95题、42对53错、0skip，精确题ID、配置/run-group和COMPLETE结果SHA全通过。原始[结果](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/chunks/question_chunk_2/results.json)、COMPLETE与validation_summary已归档，结果SHA `0f7834c2ed6a0d0a16e2c06e9a75540db530f72085d4e99989f0239df3d366e8`。72B完成0–2共285题120对165错，42.11%仅为部分准确率；P1累计23个正式完成片，不提前合并全量。
- 17:07 MC72B chunk4 `68005_4` 已接替RUNNING约2分钟，尚无结果文件，不冒充已开始题目推理；chunk3 `68005_3` 已21/95题。MC27B chunk8/9/10 `68453_8/9/10` 继续运行，分别35/18/18题，均0skip。合计5/5运行名额、6×A10080GB＋6×H20，未发现新失败。
- 17:09刷新GPU、配额与全部数组去重后，新增72B chunk7为 `68871_7`，即时PENDING QOSMaxJobsPerUserLimit；待运行5/6/7为 `68454_5`、`68804_6`、`68871_7`，该setting跨数组活动3–7共5片已满。含无关55278账号9/10活动，MC27B剩余全已运行，不重复提交、不引入第三setting。72B原Run/r8、TP2＋独占SVC1共3H20及实际export 0.93保持不变，未重启作业或重配环境。见[补位审计](./scheduling/20260910T090900Z-mindcube72-chunk7-refill.json)。所有结果和日志保留，共享存储不宣称根治。

## 历史进展：2026-09-10 16:20 MindCube/72B 新完成分片1，保持5片并行

- MC72B chunk1 `68005_1` 已COMPLETED 0:0，本次续跑用时04:39:40（不含旧失败尝试）；严格核验95/95题、40对55错、0skip，精确题ID、配置/run-group和COMPLETE结果SHA全通过。原始[结果](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/chunks/question_chunk_1/results.json)、COMPLETE与validation_summary已归档，结果SHA `b112a7818010f66fb5e2323963b006c38eab692ec208c8a74361e5209a77a37f`。72B现完成0–1两片共190题78对112错，41.05%仅为部分准确率；P1累计22个正式完成片，不提前合并全量。
- MC72B chunk3 `68005_3` 已自动接替运行，16:19已保存3题；chunk2 `68005_2` 已85/95题。MC27B chunk8/9/10 `68453_8/9/10` 继续运行，分别28/13/12题，均0skip。合计5/5运行名额、6×A10080GB＋6×H20；未发现新失败。
- 16:20刷新资源、配额、全部数组活动与完成片后，补交72B chunk6为 `68804_6`，即时PENDING QOSMaxJobsPerUserLimit。72B待运行4/5/6为 `68005_4`、`68454_5`、`68804_6`，跨数组活动合计5片已满；含无关55278账户9/10活动。MC27B剩余8–10已全部运行，不重复补交、不引入第三setting。72B原Run/r8、TP2＋独占SVC1共3H20不变，实际export显式保留0.93；未重启作业或重配环境。见[补位审计](./scheduling/20260910T082036Z-mindcube72-chunk6-refill.json)。全部历史结果和日志保留，共享存储不宣称根治。

## 历史进展：2026-09-10 14:32 MindCube/27B 已完成8/11片

- MC27B chunk7 `68108_7` 已COMPLETED 0:0，用时13:27:32；严格验证95/95题、36对59错、0skip，配置/run-group和COMPLETE原始结果SHA通过。原始[结果](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_7/results.json)、COMPLETE与validation_summary已归档，SHA `42ff07ea953582151922a5a64acba47ec4bcc597e2f45e3a8c07dc5552712dd1`。MC27B正式完成0–7共760题366对394错，48.16%为部分准确率；P1累计21个完成片，不提前合并未完整Run。
- 候补MC27B chunk9 `68453_9`已接上srv15，刚启动不冒充已推理；chunk8 `68453_8`在srv11已15/95题，chunk10 `68453_10`仍PENDING Resources。全部剩余8–10已活动，无缺失可新增片，禁止重复提交。
- MC72B chunk1/2 `68005_1/2`继续srv16 RUNNING，各3H20，题数67/54；chunk3/4/5 `68005_3/4`、`68454_5`仍排队QOSMaxGRESPerUser，跨数组cap5满。即时共4RUNNING（4A100+6H20）、4个P1候补；含55278账号9/10活动。虽有1个提交槽，但两组无可在既定cap内补交的分片，不重复提交、不引入第三组。未发现新失败或skip，所有设置和既有产物保留。

## 历史进展：2026-09-10 12:06 MindCube/27B 已完成7/11片，72B两片已推理

- 新增MC27B chunk3/4/5/6均COMPLETED 0:0，严格验证95/95题、0skip、精确ID、配置/run-group及COMPLETE原始结果SHA全通过；四片原始JSON、COMPLETE与validation_summary均已归档。MC27B正式完成0–6共665题330对335错，49.62%为部分准确率；P1累计20个完成片，不提前发布1050题全量成绩。

| 分片 / 作业 | 正确 / 总数 | 本次用时 | 原始结果 |
|---|---|---|---|
| 3 / `67605_3` | 48 / 95 | 11:48:47 | [results.json](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_3/results.json) |
| 4 / `67605_4` | 48 / 95 | 13:01:50 | [results.json](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_4/results.json) |
| 5 / `67605_5` | 44 / 95 | 13:13:09 | [results.json](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_5/results.json) |
| 6 / `67823_6` | 49 / 95 | 12:23:56 | [results.json](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_6/results.json) |

- 12:04远端实查MC27B chunk7 `68108_7` RUNNING srv15，79/95题；MC72B chunk1/2 `68005_1/2`均RUNNING srv16，分别24/16题，超过旧断点18/10题，已实际继续推理；各3H20，0skip。MC72B3/4仍排队QOSMaxGRESPerUser。查询qos_short的MaxTRESPU显示H20上限8卡，两片已用6卡，第三片会需9卡，且srv16总共也只有8卡。
- 12:06去重后补交MC27B全部剩余未提交片8/9/10为 `68453_[8,9,10]`，各2A100；再补交72B chunk5为 `68454_5`，3H20且实际export显式0.93，均即时PENDING。原有运行作业不动，全部沿用原Run/r8/本地环境和论文设置。即时3个RUNNING（2A100+6H20）、6个P1候补；加无关55278共10/10提交槽，运行3/5未满，兼容A100 srv11/12/15全8/8已分配，新增需等资源，不能把候补算运行。
- MC27B剩余7–10已全部活动，不重复补交；72B活动合计5片达到cap5。实际资源、配额与命令见[补位审计](./scheduling/20260910T040621Z-mindcube-refill.json)。未发现新失败；共享存储不宣称已根治，全部旧结果和日志保留。

## 历史进展：2026-09-10 01:04 MindCube/27B 完成第3片并补交chunk7

- MindCube/27B chunk2 `67579_2` 已COMPLETED 0:0，本次作业用时11:45:53。严格核验95/95题、54对41错、0skip，配置/run-group与已归档片一致，COMPLETE哈希通过。原始[结果](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_2/results.json)、COMPLETE及validation_summary已归档，结果SHA `7aab77ce33aebddbd9c39b25dcc976c4adfba0e924af101a39e60651bf0e17e3`。MC27B正式完成0–2共285题141对144错，49.47%为部分准确率；P1累计16个完成片。
- 01:03实查MC27B chunk3/4/5/6 `67605_3/4/5`、`67823_6`继续RUNNING，分别87/68/59/54题，均0skip；72B `68005_1/2/3/4`仍PENDING Resources，H20全8卡已分配，旧断点保留不冒充新进度。未发现新失败。
- 01:04更新配额（5运行/10提交）及GPU资源，去重后实际补交MC27B chunk7为 `68108_7`，每片2×A10080GB，即时PENDING；不将提交成功误报为已经推理。账号回到10/10活动提交（含无关55278），MC27B跨数组cap5已满。操作后即时4运行、5个P1候补，待Slurm分配可用资源；实际命令及前后队列见[续提审计](./scheduling/20260909T170441Z-mindcube27-next-shard.json)。所有Run/r8/本地环境和论文设置不变，未中断其他作业。

## 历史进展：2026-09-09 21:02 转入MindCube两组集中队列

- MMSI/9B全量288/1000（28.80%）及全部原始分片已严格验证、归档并push（`e185b52`）；不再提交该已完成Run。现在主攻MindCube/27B，72B为第二setting候补，其他setting暂不新增。
- 21:02刷新GPU/配额和全部活动数组后，27B chunk2–6共5片仍RUNNING、10×A100，5/5运行额度已满；27B跨数组活动cap5已满，不重复提交。为利用候补提交额度，实际提交72B chunk1/2/3/4为 `68005_[1,2,3,4]`，各3×H20（TP2+独占SVC1），全部PENDING QOSMaxJobsPerUserLimit。实际sbatch的export显式保留 `P1_GPU_MEMORY_UTILIZATION=0.93`，原Run/r8及所有论文设置不变，旧chunk1/2断点和日志保留。
- 两setting共9个P1活动片，加无关55278为10/10提交额度满；未取消/重启任何已启动作业。实际命令和前后队列见[第二setting提交审计](./scheduling/20260909T130226Z-mindcube72-next-setting.json)。当前H20仅1卡未分配，不能将候补误报为已开始推理；继续逐片核验归档与动态补位，共享存储未声明根治。

## 历史进展：2026-09-09 21:00 MMSI/9B 全量完成并严格合并

- MMSI-Bench / Qwen3.5-9B / SVC 正式全量1000题：**288对 / 712错，准确率28.80%**，10/10片完成，0skip。最后chunk9 `67600_9` 已COMPLETED 0:0，用时03:30:10，37/100正确。原始[最后一片](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_9/results.json)、COMPLETE和validation_summary已归档，结果SHA `29f343f8e55324bc4c5651728649a2c55f13d482b8ccb4329f863dc6ae6ffa60`。
- 用冻结r8的严格合并器核对全部10片的精确题ID、无遗漏/重复、0skip、正式配置、run-group指纹、完成标记及原始结果哈希，均通过。正式[合并结果](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/results_merged.json)及[全量摘要](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/formal_run_summary.json)已保存，合并SHA `3c32217b6e7ce23274c47de105e8f6f860b250a6b330513dd860e324580fbc81`。服务器合并文件位于原Run的results_merged.json，不覆盖已有分片结果。P1累计15个完成片。
- 20:59远端实查：MindCube/27B chunk2 `67579_2`、chunk3/4/5 `67605_3/4/5`、chunk6 `67823_6`均RUNNING，分别75/56/38/31/24题，均0skip；共5/5运行名额、10×A100满额。MC27B正式完成仍为chunk0/1两片，不把运行部分计为全量。
- 9B全量归档推送后，按既定两组策略转以MindCube/27B为主，MindCube/72B作为候补第二组；不重启这5个活动任务，不更改Run、冻结源码、环境及BF16/no-thinking/65536/官方图片顺序/论文SVC设置。

## 历史进展：2026-09-09 16:24 MindCube/27B 新完成chunk0并续提

- MindCube/Qwen3.5-27B chunk0 `67579_0` 已COMPLETED 0:0，本次续跑耗时04:46:08（非包含旧失败尝试的总耗时）。严格验证95/95题、45对50错、0skip，run-group与既有chunk1一致，COMPLETE结果SHA为 `ea0641df980f90c0801648b148922ad1b8b7c7160e6237f939b90cb4a052c854`。原始[结果](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_0/results.json)、COMPLETE及validation_summary已归档，原始字节保持。MC27B正式完成0/1两片，共190题87对103错，45.79%为部分成绩；P1累计14个完成片。
- 候补chunk5 `67605_5`已自动接上srv12；16:24仍5个RUNNING、10×A100：9B最后chunk9 `67600_9`，MC27B chunk2 `67579_2`、chunk3/4/5 `67605_3/4/5`。16:22题数快照：9B9为63/100，MC27B2/3/4为41/18/3题，0skip；chunk5刚启动不冒充已进入推理。
- 刷新配额与资源后，MC27B活动4片、完成0/1，去重补交未完成chunk6为 `67823_6`，每片2×A10080GB，即时PENDING QOSMaxJobsPerUserLimit。MC27B跨数组活动回到cap5，含无关55278账号共7/10提交；5/5运行额度已满。H20此时有4卡未分配，但不能越过5个运行上限，也不在两组集中策略中额外引入第三组。实际命令及资源证据见[续提审计](./scheduling/20260909T082405Z-mindcube27-next-shard.json)。所有Run/r8/环境与论文设置不变，未重启或删除任何任务、结果和日志。

## 历史进展：2026-09-09 15:55 MMSI/9B 已完成9/10片

- 新增3个完成片均COMPLETED 0:0，严格题ID覆盖、配置/run-group、零skip和COMPLETE哈希一致；原始results.json字节（无尾换行）、COMPLETE及validation_summary均已归档。9B已完成chunk0–8，共900/1000题，251对649错，27.89%仅为已完成9片的部分准确率。P1正式归档累计13片，尚不合并未完成的全量结果。

| 分片 / 作业 | 正确 / 总数 | 本次作业用时 | COMPLETE时间（HKT） | 原始结果 |
|---|---|---|---|---|
| 6 / `67550_6` | 27 / 100 | 03:27:46 | 14:03:16 | [results.json](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_6/results.json) |
| 7 / `67560_7` | 27 / 100 | 03:16:59 | 14:06:12 | [results.json](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_7/results.json) |
| 8 / `67600_8` | 25 / 100 | 03:50:08 | 15:37:49 | [results.json](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_8/results.json) |

- 15:55远端实查：9B最后chunk9 `67600_9` 在srv15 RUNNING，已48/100题（15对33错），未COMPLETE。MindCube/27B chunk0/2 `67579_0/2`（srv12）、chunk3/4 `67605_3/4`（srv15/srv11）也RUNNING；chunk0/2/3分别92/37/15题，chunk4尚未发现结果文件，不能宣称已开始题目推理。无新失败，旧失败日志保留。
- 当前仍5/5运行名额、共10×A100；MindCube chunk5 `67605_5`等待QOS运行名额。含无关55278共7个活动作业，虽有3个提交槽，但MC27B已跨数组活动5片、9B仅余最后1片已运行，因此不重复提交、不超既定cap或扩大到第三组。候补已接替完成片，未重启任何作业；继续两组集中推进，完成即严格归档。

## 历史进展：2026-09-09 11:55 已用满5个运行名额

- MMSI/9B chunk8 `67600_8` 已在srv11启动并产出3题（1对2错），不是仅排队或模型加载。连同9B chunk6 `67550_6`、chunk7 `67560_7`（srv15），以及MindCube/27B chunk0/2 `67579_0/2`（srv12），共5个RUNNING、10×A10080GB，已用满MaxJobsPU=5。
- 9B chunk9 `67600_9`、MindCube/27B chunk3/4/5 `67605_[3,4,5]` 共4个P1候补，排队原因均为QOSMaxJobsPerUserLimit。加无关55278，仍占满10/10提交槽；不重复提交。
- 当前9B chunk6/7/8分别已保存32/35/3题，MindCube/27B chunk0/2分别58/7题，均0 skip。没有新增COMPLETE，不提前记为分片完成；本次未发现新的失败作业。两组继续集中推进，设置、环境及活动作业不改动。

## 历史进展：2026-09-09 11:42 额度优先、集中两组推进

- 用户进一步明确：优先用满账户额度，再集中完成一组，允许第二个 setting 补位。现以 MMSI/Qwen3.5-9B 为主、MindCube/Qwen3.5-27B 为第二组，不再沿用上一轮“只有9B可新增”的限制，也不恢复四组分散补位。
- 11:41实查 daai_qos 为 MaxJobsPU=5、MaxSubmitJobsPU=10，用户/QOS未显示独立GPU张数上限。兼容A100 srv11/12/15与H20 srv16均8/8卡已分配；4/5运行名额尚未满是可用GPU不足，不能靠多提交立刻保证第5个启动。原Run的A100硬件指纹不变。
- 11:42核对已完成和所有活动数组后，9B剩余6–9均已活动，不重复提交；实际新增 MindCube/27B chunk3/4/5 为 `67605_[3,4,5]`，各2×A10080GB，即时PENDING。该setting已有chunk0/2 `67579_0/2` RUNNING，合计活动5片；9B已有chunk6/7 `67550_6` / `67560_7` RUNNING，chunk8/9 `67600_8/9` PENDING Resources，合计活动4片。
- 即时共4个P1运行（8×A100）、5个P1排队；含无关55278共10/10提交槽已满。两组各跨数组活动cap5，账户运行上限仍5；Slurm分配资源后启动候补，自动监控完成即归档并补位。实际命令、资源/配额输出和前后队列见[两组集中提交审计](./scheduling/20260909T034249Z-two-setting-quota-first.json)。
- 9B先争取全量，完成并合并归档后以MindCube/27B为主，第二组选择MindCube/72B补位，尽量只推进两组。无作业取消或重启，无环境复查或重装，所有Run/r8、BF16/no-thinking/65536、官方图像顺序和SVC设置不变，所有既有产物保留。共享存储风险仍未证实根治，排队时间未知，不能给出可靠绝对完成时刻；9B最后两片实际启动后参考约4–5小时。

## 历史进展：2026-09-09 11:36 改为单 setting 集中推进

- 按用户最新要求，停止四组合同时补位，先集中 MMSI/Qwen3.5-9B：已严格归档 chunk0–5（600/1000题），剩余 chunk6–9 全部已提交。chunk6 `67550_6`、chunk7 `67560_7` 在 srv15 RUNNING；新增 chunk8/9 为 `67600_[8,9]`，即时 PENDING Resources，每片2×A10080GB。跨所有数组的当前 setting 活动合计上限5，仍受账户5运行/10提交限制；不等待前片完成才交后片。
- 撤销其他 setting 的5个未启动排队片：MindCube/27B `67579_3`、MindCube/72B `67580_1/2`、MMSI/3.8 `67581_1/3`。逐片限定 PENDING 状态执行，旧结果、断点和日志全部保留。操作前 MindCube/27B `67579_0/2` 已变为 RUNNING（srv12），为遵守不打断已启动任务的要求保留，不取消或重启。因此过渡期仍有两个 setting 活动，后续不再给非当前 setting 新增分片。
- 11:36队列：4个P1 RUNNING、2个P1 PENDING；运行共8×A100，新增两片各申请2×A100。含无关55278共7/10提交槽，不为填剩余槽位打破单 setting 策略。实际操作、提交命令及前后队列见[切换审计](./scheduling/20260909T033604Z-single-setting-focus.json)。
- 自动监控已切换：9B全10片严格验证、合并归档并push后，依次集中 MindCube/27B、MindCube/72B、MMSI/3.8；每个 setting 内并行补齐未完成且未活动的分片，每片完成立即归档。保留原 Run ID、冻结r8、现成本地环境、BF16/no-thinking/65536、官方图片顺序和论文SVC设置，72B之后续提仍须TP2+独占SVC1共3H20且实际export显式0.93。
- 单 setting 可能减少不同模型同时加载的共享存储压力，但并非已经验证的 EIO/ENOSPC 修复；相同模型多片仍会访问共享权重并写视频。以9B近期完整分片约3.4–4.3小时估算，最后两片从实际启动到结束约需4–5小时，排队与故障时间另计，不保证当天固定完成时刻。

## 历史进展：2026-09-09 11:21 按用户新授权补满提交额度

- 用户要求增加并行、尽量用满账户额度，覆盖此前故障组合全部暂缓新增的策略。11:20实查账号仍MaxJobsPU=5、MaxSubmitJobsPU=10；现有9B两片运行，兼容A100节点srv11/12/15与H20 srv16均8/8卡已分配，当前无法立即新增运行，但可以提前排队。
- 11:21真实提交7片：MindCube/27B `67579_[0,2,3]`（每片2A100）；MindCube/72B `67580_[1,2]`（每片3H20，TP2+SVC1，显式export 0.93）；MMSI/3.8 `67581_[1,3]`（每片2A100）。9B既有 `67550_6` / `67560_7`保留运行不动。实际命令和去重记录见[提交审计](./scheduling/20260909T032134Z-user-full-queue.json)。跨全部数组上限为3/2/2/2（MC27B/MC72B/MMSI3.8/MMSI9B），已排除完成和活动片。
- 即时队列共9个P1活动分片：2运行、7排队；加无关55278共10/10提交槽已满。运行名额尚为2/5，原因是兼容GPU已分配完，不把排队当运行，不声称已满5个运行槽。空闲资源释放后由Slurm启动，后续完成则核验归档并按合计上限补位；不再沿用“只有9B可以提交”的旧限制。
- 这次恢复其他组合是按用户新授权进行，不代表共享存储已修复。若同片再次报存储错误，保留日志和进度、避免该片无限重试，同时推进其他可运行分片。原Run ID、固定r8源码、BF16/no-thinking/65536、官方图像顺序和论文SVC设置不变，无环境重检、权重重扫或主动中断任务。

## 历史进展：2026-09-09 10:49 MMSI/9B 已完成6片

- chunk5 `67459_5` 已 COMPLETED 0:0，用时04:19:49；严格核验100/100题、27对73错、0 skip。原始[结果](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_5/results.json)、COMPLETE与验证摘要已归档，SHA `aaf4e81c76221ee5540bb8d3d1663f2f12cdc49b9dde1d7d97cb60489ec79870`。9B已完成0–5共600/1000题，172对428错，部分准确率28.67%；非全量成绩。P1累计归档10片。
- 10:49实查chunk6 `67550_6` RUNNING，去重及配额检查后补交chunk7为 `67560_7`，即时队列已分配srv15；两片各2×A10080GB、合计4卡，chunk7刚启动不等同已推理。[续提审计](./scheduling/20260909T024911Z-mmsi9b-next-shard.json)保留实际sbatch参数。沿用原Run、r8源码、本地环境与论文设置，不重启活动片；其他存储故障组合新增继续暂缓。

## 历史进展：2026-09-09 10:35 MMSI/9B 完成一半分片

- chunk4 `67459_4` 已 COMPLETED 0:0，用时03:46:18，100/100题、32对68错、0 skip，严格验证及COMPLETE哈希一致。原始[结果](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_4/results.json)、完成标记和验证摘要已归档，SHA `bc91d242f6550a6db98f8df0617a63e4448dcefac72572edb5dfc891f8a12280`。9B正式完成chunk0–4共500/1000题，145对355错，部分准确率29.00%；不是全量成绩。P1累计归档9片。
- 10:35确认chunk5 `67459_5`仍RUNNING，无重复/完成片冲突，按9B合计上限2续提chunk6为 `67550_6`（即时PENDING），每片2×A10080GB；[实际续提命令](./scheduling/20260909T023528Z-mmsi9b-next-shard.json)。QOS仍5运行/10提交；同Run/r8/原环境与论文设置不变，其他存储故障组合继续暂缓新增，未中断任何运行任务。

## 历史进展：2026-09-09 10:01 新增四片完成，9B 分片4/5继续运行

以下四片均已 COMPLETED 0:0，严格题目覆盖、零 skip、运行指纹和 COMPLETE 结果哈希验证通过；原始 results.json、COMPLETE 与 validation_summary 已逐片归档，原始结果无尾换行的字节格式保持不变。表中用时是本次作业时长，含断点续跑的片不是全部尝试累计用时。

| 实验 | 分片 / 作业 | 正确 / 总数 | 单片准确率 | 本次用时 | 完成标记时间（HKT） |
|---|---|---|---|---|---|
| MMSI / Qwen3.5-9B | 2 / `67300_2` | 31 / 100 | 31.00% | 03:24:27 | 03:50:03 |
| MMSI / Qwen3.5-9B | 3 / `67377_3` | 28 / 100 | 28.00% | 03:31:43 | 06:03:57 |
| MMSI / Qwen3.8-27B | 2 / `67292_2` | 21 / 100 | 21.00% | 06:01:52 | 06:23:54 |
| MindCube / Qwen3.5-27B | 1 / `67220_1` | 42 / 95 | 44.21% | 10:05:27 | 09:16:51 |

- 归档结果：[9B chunk2](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_2/results.json)、[9B chunk3](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_3/results.json)、[3.8 chunk2](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_2/results.json)、[MindCube/27B chunk1](./mindcube/qwen3.5-27b/svc/mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908/chunks/question_chunk_1/results.json)。MindCube/27B 新增运行清单，run-group `2878daf0a74e8eb106dc44bf2e02f54a593888278bec99017b21418493147738`；其他片均与各自既有归档 run-group 一致。详细逐文件哈希见 SHA256SUMS。
- P1 现正式归档 8 片：9B chunk0–3 共 400 题，113 对 / 287 错（28.25%）；MMSI/3.8 chunk0/2 共 200 题，40 对 / 160 错（20.00%）；MindCube/27B chunk1 共 95 题（44.21%）；MindCube/72B chunk0 共95题（40.00%）。这些均为已完成分片的部分指标，不是全量成绩。
- 06:26 刷新配额及队列后，9B 完成0–3且无活动片，在合计上限2内续提 chunk4/5 为 `67459_[4,5]`，每片2×A10080GB；原始命令见[续提审计](./scheduling/20260908T222642Z-mmsi9b-next-shards.json)。10:01 两片均在 srv15 RUNNING，随后题数读取分别93/100和82/100，没有新 COMPLETE，不能提前计入正式完成。其他存活旧任务均正常完成，没有主动中断。
- 当前仅两片9B使用4×A100；MindCube与MMSI/3.8新增/失败片仍按已有共享存储故障保护暂缓，9B上限2已满，不重复提交。连接曾被远端关闭，后改为自动响应用户已授权密码以避免交互等待；未改服务器认证配置。没有重新配环境、扫描权重或修改 BF16/no-thinking/65536/图片顺序/SVC 设置。所有旧失败产物与日志继续保留。

## 历史进展：2026-09-09 02:32 MMSI/9B 第二片完成并续提

- MMSI/Qwen3.5-9B chunk1 作业 `67293_1` 已 COMPLETED 0:0，本次续跑用时 01:08:27，完成标记时间 01:30:33 HKT（包含此前失败尝试保存的进度，不是该片总累计 GPU 用时）。严格验证通过：100/100 题，29 对 / 71 错，0 skip，单片准确率 29.00%；run-group 与已归档 chunk0 一致。原始[结果](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_1/results.json)、COMPLETE 与校验摘要已归档，结果 SHA256 `17d5dd7965bbc5d55e7bc5451c992f5d7ff1df8b92707c4dda4da73dbf57488d`。9B 已正式完成 2/10 片，共 200 题、54 对 / 146 错，27.00% 仅为已完成两片，不是全量成绩。P1 累计归档 4 个完成片。
- 02:32 刷新 GPU 与账号限制后，确认9B仅 chunk2 `67300_2` 活动，按跨数组上限2补交未完成且未活动的 chunk3，作业 `67377_3`；即时队列 PENDING，不能记为已开始推理。实际 sbatch 审计见[续提记录](./scheduling/20260908T183211Z-mmsi9b-next-shard.json)。同 Run ID/r8/2×A10080GB，所有设置不变，不重复环境检查、不重启其他任务。
- 同期仍 RUNNING：MindCube/27B `67220_1`、MMSI/3.8 `67292_2`、MMSI/9B `67300_2`。共享存储故障没有稳定恢复证据，MindCube及MMSI/3.8新增片继续暂缓；健康9B保持两片活动上限，后续每片完成即归档并续提。

## 历史进展：2026-09-09 00:40 MMSI/3.8 新片存储失败，保留四个推理作业

- `67292_1`（MMSI/3.8 chunk1，srv15）于约 00:33:40 FAILED 1:0，Elapsed 00:11:38；已保存 3 题（2 对 / 1 错，0 skip）。正式推理生成第 170 题视频时，`question_chunk_1/170/step_1/turn-left_18_degrees_turn-left_27.00_degrees/pred.mp4` 报 No space left on device，继发 BrokenPipe。原完整日志保留于 `attempts/question_chunk_1/67296-20260908T162204Z/pipeline.log`。不是环境导入或显存问题；按重试保护规则暂停 MMSI/3.8 新增/失败片重提，存活 chunk2 不动。
- 00:40 队列剩 4 个 RUNNING、8×A10080GB：MindCube/27B `67220_1`、MMSI/3.8 `67292_2`、MMSI/9B `67293_1` / `67300_2`。四片都有实际 SVC Sampling / 模型回答记录；9B 两片已分别推进到 75 / 7 题，不再只是加载模型。9B 当前跨数组上限 2 已满，MindCube 和 MMSI/3.8 新增提交均受存储故障保护，本轮没有盲重试以填空槽。
- 最新题目累计：MindCube/27B 83/1050（55+24+4），72B 123/1050（95+18+10），MMSI/9B 182/1000（100+75+7），MMSI/3.8 109/1000（100+3+6）；均 0 skip，没有新 COMPLETE，正式归档仍 3 片。结果、日志与既有任务保留，设置未变，继续监控健康组合和逐片归档。

## 历史进展：2026-09-09 00:25 用户授权重试，已补满 5 个运行名额

- 用户明确要求再次尝试并尽量用满账户额度。00:21 登录节点 1 MiB 写入/fsync/回读成功后，核对全部活动数组与完成片，实交 `67290_[0,2]`（MindCube/27B）、`67291_[1,2]`（MindCube/72B）、`67292_[1,2]`（MMSI/3.8）及 `67293_1`（MMSI/9B），共 7 片。既有 `67220_1` 未中断；旧 `67221_1` 和 `67223_1` 在提交前已自行 FAILED，均为输出 pred.mp4 报 ENOSPC，分别保留 18 题和 66 题。实际命令见[重试审计](./scheduling/20260908T162112Z-user-authorized-retry.json)。
- 新一轮 MindCube 四片又在加载权重阶段失败：`67290_0/2` 均 46 秒，Qwen3.5-27B 第 5/11 权重文件报 FileNotFoundError；`67291_1/2` 分别 57/51 秒，72B 多个权重文件报 EIO，随后 safe_open 报文件不存在。00:25 在登录节点对四个确切错误文件 stat + 仅读取 16 字节均成功，不能据此断言权重被删除/损坏或存储恢复。当前不再盲重提这些 MindCube 片，也不重新下载或扫描权重。
- 为利用空位，依据用户允许动态调整并发的授权，将 MMSI/9B 跨数组合计上限暂由 1 调至 2，仅补交未完成且未活动的 chunk2 为 `67300_2`。00:25:35 队列确认下面 5 个 P1 作业 RUNNING，合计 10×A10080GB，已用满实查 MaxJobsPU=5；含无关 `55278` 排队任务共 6/10 提交槽。H20 srv16 当时 8 卡空闲，但 72B 读权重失败，当前瓶颈不是排不到卡。原 A100 Run 不混改硬件指纹。审计与错误摘录见[动态补位记录](./scheduling/20260908T162534Z-capacity-refill.json)。

| 实验 | 运行分片 / 作业 | 每片 GPU | 00:25 状态 |
|---|---|---|---|
| MindCube / Qwen3.5-27B | 1 / `67220_1` | 2×A10080GB（srv15） | 既有任务继续推理；0/2 本轮重试失败 |
| MindCube / Qwen2.5-VL-72B | 无 | 原配置 3×H20 | 1/2 本轮重试失败，保留进度 |
| MMSI / Qwen3.5-9B | 1 / `67293_1`；2 / `67300_2` | 2×A10080GB（srv11 / srv12） | chunk1 已加载权重；chunk2 刚获分配，不等同已推理 |
| MMSI / Qwen3.8-27B | 1 / `67292_1`；2 / `67292_2` | 2×A10080GB（srv15） | 模型服务就绪，正式流水线已启动 |

- 00:22 结果快照：MindCube/27B 81/1050（55+22+4），MindCube/72B 123/1050（95+18+10），MMSI/9B 166/1000（100+66），MMSI/3.8 100/1000。未新增 COMPLETE；正式归档仍为 3 片，不发布全量准确率。共享存储稳定性未知，旧全量 ETA 暂不可用。
- 所有片复用节点本地环境、原 Run ID、冻结 r8 源码及原题目进度。BF16、no-thinking、65536 上下文、官方图像顺序与论文 SVC 设置未改；72B 实际 export 仍显式 0.93。自动监控继续跟踪并逐片核验/归档/push；存储仍报错的组合不无限重试，健康组合可按更新后跨数组上限补充未完成片。没有删除结果、日志或主动终止任何运行任务。

## 历史进展：2026-09-09 00:02 共享存储故障复发，停止自动重试

- 存储定向读写恢复后的一轮重试仍失败：`67220_0`（00:39:58）读取生成图片 EIO；`67220_2`（00:39:58）及 `67221_2`（00:40:13）写 pred.mp4 报 ENOSPC 并触发 BrokenPipe；`67222_1` / `67222_2`（均 00:00:11）读取 `/home/datasets/chentao/models/Qwen3.8-27B/config.json` 报 EIO。说明不是仅输出目录或某个模型问题，也不能用短暂探测成功判断已恢复。
- 已停止新的自动补交和失败片重试，不重建环境、不修改论文设置、不删除结果。00:02 队列中 `67220_1`（MindCube/27B，srv15）、`67221_1`（MindCube/72B，srv16）、`67223_1`（MMSI/9B，srv15）仍 RUNNING，保持原状不主动中断。其余失败片保留已有进度，待存储管理员确认故障处理及稳定恢复证据后再继续。
- 最近结果快照：MindCube/27B chunk0=55题、chunk1=19题、chunk2=4题；72B chunk0已归档95题、chunk1=14题、chunk2=10题；MMSI/9B chunk0已归档100题、chunk1=62题；MMSI/3.8 chunk0已归档100题。均未发现 skip，部分片仍未完成，不能据此发布全量准确率。没有新增正式 COMPLETE。
- 需要集群管理员检查 `/home/datasets` 的 NFS 服务、后端存储与配额。23:05 的容量快照仍显示约 3.9 TB 可用，但 quota RPC 返回 Connection refused；未知是配额、单个后端容量还是其他存储异常，不能仅根据聚合 df 排除问题。完整失败日志留在各 Run 的 `attempts/question_chunk_N/`；后续自动监控继续保留结果、跟踪存活任务与故障状态，重复不变状态不打扰用户。原 ETA 暂不可用。

## 历史进展：2026-09-08 23:12 完成归档与共享存储异常

- 存储检查 `67219` 已于 23:11 COMPLETED 0:0，用时 2 秒；srv12 三个确切报错文件读取、1 MiB 写入/fsync/回读均成功。仅在通过后恢复提交，23:12 队列确认 MindCube/27B `67220_[0,1,2]` 在 srv15 RUNNING，MindCube/72B `67221_[1,2]` 在 srv16 RUNNING；共 6×A100 + 6×H20、5 个运行名额。MMSI/3.8 `67222_[1,2]` 与 MMSI/9B `67223_1` 已排队等待 QOSMaxJobsPerUserLimit。这是作业启动/恢复，不宣称新题已成功。旧失败 attempts 及题目进度全部保留，同 Run ID/r8/原配置续跑，无主动中断活动作业。提交审计见[存储恢复记录](./scheduling/20260908T151123Z-storage-recovery.json)。若此轮再次出现 EIO/ENOSPC，不持续盲重试，应报告共享存储需管理员处理。
- MindCube/Qwen2.5-VL-72B 首片 `66975_0` 已 COMPLETED 0:0（Elapsed 05:47:11，23:01:17 结束）。严格校验通过：95/95 题、38 对 / 57 错、0 skip，首片准确率 40.00%，不是全量成绩。原始[结果](./mindcube/qwen2.5-vl-72b/svc/mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908/chunks/question_chunk_0/results.json)、COMPLETE、运行清单和校验摘要均已归档，结果 SHA256 `dd1582fb4166d15a7a18d7d25fa3f3058156d36412b14fd22e114cfd0acd5fad`。
- MMSI/Qwen3.8-27B 首片 `66857_0` 已 COMPLETED 0:0（Elapsed 07:56:29，22:31:28 结束）。严格校验通过：100/100 题、19 对 / 81 错、0 skip，首片准确率 19.00%，不是全量成绩。原始[结果](./mmsi/qwen3.8-27b/svc/mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908/chunks/question_chunk_0/results.json)、COMPLETE、运行清单和校验摘要均已归档，结果 SHA256 `5759bc5859fe540f015e1bdfbf0aaed0a15c88c3138133eb6bc35a400140bee9`。
- 22:54 起多个节点出现共享 `/home/datasets` 存储错误：MindCube/27B `66856_0` 读取生成图像报 EIO，保留 52 题进度；`67122_2` 写 gpt.json 报 ENOSPC，随后 `67122_1` 也 FAILED（02:08:45）。MMSI/9B `67076_1`（03:28:20）和 MMSI/3.8 `67124_1`（00:09:50）读生成图像报 EIO；72B `67123_1`（00:00:44）读取模型 preprocessor_config.json / tokenizer_config.json 报 EIO，非此前 KV cache 显存错误。所有日志、已完成结果和未完成进度保留，没有主动重启活动任务。
- 登录节点容量显示 `/home/datasets` 使用 98%、仍余约 3.9 TB / 6400 万 inode；`/home` 余约 89 TB。quota RPC 查询被拒绝，尚不能确认是否另有配额或存储后端故障。五个确切出错文件的定向读取及 1 KiB 写入随后成功，说明登录节点已恢复，但不据此宣称集群故障彻底解决。
- 暂停盲目重试并提交不占 GPU 的短检查作业 `67219`（srv12、1 CPU、2 GiB、10 分钟上限）：仅读取三个此前错误的小文件并执行 1 MiB 临时文件写入/回读，临时文件自动清理；成功后才调用既有外部调度器补交，失败即退出不占用 GPU。日志位于 `/home/comp/24482277/shiyang/p1-storage-recovery-67219.out` 与 `.err`，避免检查日志依赖故障中的 datasets 盘。此项是存储诊断，不重新导入/检查模型环境。故障期间原完成时间估计暂不作为可靠 ETA。

## 历史进展：2026-09-08 20:59 并行调度（覆盖旧串行续提策略）

用户已授权首题/首片成功后直接并行提交未完成片，不再要求上一片完成才提交下一片。初始跨数组合计上限：MindCube/27B 3、MindCube/72B 2、MMSI/9B 1、MMSI/3.8-27B 2；排队、运行及收尾中的任务均计入，排队片不会被重复提交。

- 实查 `daai_qos` 为 MaxJobsPU=5、MaxSubmitJobsPU=10；查询到的用户/账户关联及该 QOS 未设置显式 GPU 张数上限，分区 QOS 另有共享 TRES 限额，不能理解为资源无限。提交前可用且已确认兼容的 A10080GB：srv11 余 1 张、srv12 余 0 张、srv15 余 5 张；H20 srv16 余 0 张。srv07/08 旧驱动、40GB DGX 与尚未确认兼容的 srv13/14 不用于新增片。
- 20:56 新增分片 `67122_[1,2]`（MindCube/27B，每片 2×A100）、`67123_1`（MindCube/72B，3×H20）、`67124_1`（MMSI/3.8-27B，2×A100）。20:58 确认 `67122_1` 在 srv15 RUNNING，账号已用满 5 个运行名额；另三片等待 `QOSMaxJobsPerUserLimit`，Slurm 未给可用的预计开始时间。总计 8 个 P1 活动任务，加既有无关待运行 `55278` 为 9/10 提交槽；无关作业未改动。
- 外部调度器 [p1_parallel_dispatch.py](../scripts/p1_parallel_dispatch.py) 使用共享排他锁，展开所有数组，先排除已完成和活动分片，再按实验合计上限及全账号提交槽位补交；每次提交写入追加式日志。6 项调度定向测试通过，覆盖跨数组/排队合计、重复片拒绝、完成片排除、提交限额和 72B 显式显存预算。它不在冻结 worker 的 source 文件列表中，现有 r8 源码没有变化。[本次原始提交审计](./scheduling/20260908T125634Z-parallel-dispatch.json)含实际 sbatch 命令和参数。
- 所有新增片使用原 Run ID、r8 source SHA、独立分片目录；72B 实际 `--export` 显式保留 `P1_GPU_MEMORY_UTILIZATION=0.93`、TP2 + SVC1。BF16、no-thinking、65536 上下文、官方图片顺序及 SVC 论文设置均未改动。没有取消/重启原活动模型，也没有重配环境或扫描未变的 SVC 权重。

| 实验 | 运行分片 / 作业 | 排队分片 / 作业 | 每片 GPU | 全量剩余时间粗估 |
|---|---|---|---|---|
| MindCube / Qwen3.5-27B | 0 / `66856_0`；1 / `67122_1`（新片正在启动） | 2 / `67122_2` | 2×A10080GB | 约 60–90 小时 |
| MindCube / Qwen2.5-VL-72B | 0 / `66975_0` | 1 / `67123_1` | 3×H20 | 约 40–75 小时 |
| MMSI / Qwen3.5-9B | 1 / `67076_1`；0 已完成归档 | 无 | 2×A10080GB | 约 35–45 小时 |
| MMSI / Qwen3.8-27B | 0 / `66857_0` | 1 / `67124_1` | 2×A10080GB | 约 40–75 小时 |

估计基于当前逐题吞吐与账号最多 5 个同时运行作业，而不是假定目标 8 片都立即开跑；后续资源重分配和题型耗时仍会影响结果。四项全量暂按约 3–4 天（9 月 11–12 日）规划，不是排队或完成时间承诺。每片完成即核验、归档、推送，不等待整项完成。

## 历史进展：2026-09-08 依赖本地化

- 19:36 HKT：MMSI/Qwen3.5-9B 首片 `66836_0` 已 COMPLETED 0:0，Elapsed 05:00:02，19:24:46 写出 COMPLETE；严格结果校验通过，100/100 题完整覆盖、25 对 / 75 错、0 skip，首片准确率 25.00%（不是全量结果）。结果 SHA256 `9520280d07945f7445326be17b365cc73eed523e51cc9dd025af372690e4082e`，run-group 指纹 `d0cce3a6ceef87aa5db856718e01167571a1b14b952d44e98d414b71760cd394`。已归档[首片结果](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_0/results.json)、[完成记录](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_0/COMPLETE)及[校验摘要](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/chunks/question_chunk_0/validation_summary.json)。
- 确认没有同组合活动作业且下一片未完成后，沿用原 r8 Run/source、2×A100、BF16/no-thinking/65536/全部图片及算法设置，仅把原 sbatch 的 `--array=0%1` 改为 `1%1`，续提成功为 `67076_1`。原始命令与提交记录见[续提记录](./mmsi/qwen3.5-9b/svc/mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908/submissions/20260908T1136Z-67076.txt)。未重启其他三个活动实验、未重新复制现成环境。19:32 其余进度为 MindCube/27B 30 题、MindCube/72B 31 题、MMSI/3.8-27B 65 题，均 0 skip。
- 17:31 HKT：四项 P1 均已进入真实推理。72B `66975_0` 在 srv16 使用 3×H20，17:22:56 模型服务就绪，17:28 起出现成功的 chat completions；结果已完成首题（1 对 / 0 错 / 0 skip），pipeline 持续 SVC Sampling。显存预算 0.93 已解决此前启动 KV cache 不足，当前只证明首题成功，不代表全部题型均已验证。其余三个活动作业保持不动：MindCube/27B 已完成 17 题（6 对 / 11 错），MMSI/9B 65 题（17 对 / 48 错），MMSI/3.8-27B 37 题（9 对 / 28 错），均 0 skip。当前各 chunk 0 尚无 COMPLETE，不发布全量指标，不重复提交活动片。
- 17:13 HKT 实际推理快照：`66856_0`（MindCube/Qwen3.5-27B，srv11）完成 16 题（5 对 / 11 错）；`66836_0`（MMSI/Qwen3.5-9B，srv15）完成 59 题（16 对 / 43 错）；`66857_0`（MMSI/Qwen3.8-27B，srv12）完成 32 题（6 对 / 26 错）。均为正在运行的 chunk 0，`skip_indices` 均为空；日志已出现真实 SVC Sampling 和模型回答，不能将这些部分结果记为全量准确率或分片完成。三个任务持续运行，未为启动优化重启。
- 上述进度来自各自 r8 Run root 下的 `results_spatial_beam_search_qc11/question_chunk_0/results.json`（MindCube）或 `results_spatial_beam_search_qc10/question_chunk_0/results.json`（MMSI），按 `progress` 中 correct/wrong 列表计数。原始逐题产物和失败 attempts 全部保留，正式归档仍等待完整覆盖与 COMPLETE。
- 72B 的 H20 首试 `66855_0` 已 FAILED（Elapsed 00:11:01）：权重已加载，65536 上下文需要 10.0 GiB KV cache，但默认 90% 显存预算只提供 8.42 GiB。17:14 HKT 已将唯一运行时改动 `P1_GPU_MEMORY_UTILIZATION=0.93` 显式加入原 sbatch 的 `--export`，同一 H20 r8 Run、同源码、同 chunk 0 续提成功为 `66975`（数组任务 `66975_0`），尚不宣称已推理成功。仍为 TP2 + SVC1 共 3×H20，BF16、no-thinking、65536 上下文、图片与 SVC 设置均不变。后续 72B 续提必须保留此显式 export；仅设置提交 shell 的父环境变量会被提交器显式 export 过滤。
- H20 srv16 已实际完成压缩包复制、解压和路径适配，耗时 156.42 秒（约 2.6 分钟）。这是新节点分发实测值，不是模型加载耗时。srv11/12/15/16 的现成 LOCAL_READY 环境优先复用，不重新逐文件复制、不重新安装，也不重复导入检查。
- 14:33 HKT 故障推进：`66827_0`（72B，3×A100）在模型权重成功加载后，于多模态编码器显存 profiling 阶段 OOM，Elapsed 00:10:16。每个模型卡权重占 68.59 GiB；OOM 时仅余约 1002 MiB，却需再分配 1.25 GiB。未擅自降低 BF16、65536 上下文或图像上限；改以现有 3×H20 资源方案（TP2 + SVC1）提交 `66853`，Run `mj-p1-mindcube-qwen25vl-72b-h20-fast-r8-20260908`，同 r8 source SHA。实际 H20 可运行性待真实启动确认，不宣称已解决显存问题。
- `66834_0`（MindCube/27B）和 `66835_0`（MMSI/3.8-27B）已完成 vLLM 服务启动，但 SVC 初始化因找不到本地固定资源失败，分别用时 00:10:04 / 00:06:54，无题目结果。定位到账号继承的 `HF_HOME=/home/comp/24482277/chentao/models` 与已校验的 `P1_CACHE_ROOT` 不一致。其 `hub` 目录此前仅有 `version.txt`；已新增三个同名仓库目录符号链接，分别指向 `/home/datasets/shiyang/daai_runtime/model_cache/huggingface/hub/` 下的 `models--stabilityai--stable-virtual-camera`、`models--sd2-community--stable-diffusion-2-1-base`、`models--laion--CLIP-ViT-H-14-laion2B-s32B-b79K`。不覆盖原文件、不复制权重，不改活动作业源码或环境。
- 该缓存路径修复也对仍运行的 `66836_0`（MMSI/9B，srv15）直接生效，无需重启其已加载模型。两项已失败作业用原 r8 Run ID 和原源码 `--resume` 续提，提交器 `66851`（MindCube/27B）、`66852`（MMSI/3.8-27B）；未重新复制本地环境。所有失败 attempts 保留，新任务不会覆盖旧结果。`66851`–`66853` 当前等待 CPU 提交器调度，后续 GPU ID 以对应提交日志为准。
- 打包作业 `66825` 已 `COMPLETED 0:0`，耗时 00:01:12；压缩包大小 7,407,950,231 bytes，SHA256 `721f10aa766dcdbe7ba6d4c5acf2db8645dc55d157b350fccd9d49bd7ff728d8`，旁置 `.tar.zst.json` 绑定源环境 COMPLETE 和四个元数据文件哈希。此处是打包耗时，不冒充新节点解压/启动耗时。72B 快速提交器 `66826` 耗时 18 秒。
- 其余失败组合已使用 r8 提交：`66831`（MindCube/27B）、`66832`（MMSI/9B）、`66833`（MMSI/3.8-27B）。Run ID 分别为 `mj-p1-mindcube-qwen35-27b-a100-fast-r8-20260908`、`mj-p1-mmsi-qwen35-9b-a100-fast-r8-20260908`、`mj-p1-mmsi-qwen38-27b-a100-fast-r8-20260908`，位于原 `/home/datasets/shiyang/daai_runtime/p1_runs/`。与 72B/r7 分开保持各自源码指纹，避免修改已加载中的作业。
- `63b4039` 进一步让 SVC 主权重、VAE、OpenCLIP 加载器复用同一已验证记录，避免入口检查后再次重复扫描权重；记录不匹配或非 P1 的未登记文件仍保留完整内容校验。78/78 本地代码测试通过。其余失败任务使用独立目录 `/home/comp/24482277/shiyang/MindJourney-p1-startup-r8-20260908`，source SHA256 `e6d08e5a782bbf8f2521d25637cb197f52b7d8dfc1edf7cd29d403b6ac123e64`。已开始加载的 72B 保留 r7，不为了该进一步优化改动其源目录或重启它。
- 72B 新首片 `66827_0`（提交器 `66826`）使用 3×A100，在 srv11 复用现成环境，14:09:18 已进入模型加载，读取 38 个权重分片。Run ID `mj-p1-mindcube-qwen25vl-72b-a100-fast-r7-20260908`；attempt `66827-20260908T060807Z`。日志已确认短 IPC 路径生效，TP=2、BF16、65536 上下文保持原值；显存可运行性及正式推理仍待后续结果确认。
- 压缩包构建 CPU 作业 `66825` 已打印 `Environment archive ready`，从 srv12 的完整本地环境生成单个共享压缩包，不重新扫描共享环境中的大量小文件。它不占 GPU，也未重新复制现成环境。9B 旧 `66751_0` 随后自行以相同 IPC 长路径错误失败（00:23:24），本次未主动中断；srv11 原复制作业 `66813` 已成功完成（00:21:49）。
- 用户随后明确授权：已完整校验且未变化的 SVC 资源在启动时只检查已有校验记录和必需文件；资源缺失、版本或文件元数据变化时才完整校验。commit `f345c50` 在提交器和计算节点加入 `validate --startup`：核对小清单哈希、固定身份、文件存在/大小/修改时间，不读取权重内容，也不导入 Hub；异常才进行离线完整校验并刷新记录。显式 `validate` 和预下载流程仍提供完整校验。
- 同一修复采用已验证 SAT 的 `tar.zst` 分发模式：从现成节点环境一次性打包，在其他节点顺序复制单个压缩包、校验传输并本地解压。完整的 `LOCAL_READY.json` 优先复用，甚至不要求访问压缩包，不重新复制 srv11/12/15 已准备的环境；已有部分副本和旧日志不删除。压缩包默认 `/home/datasets/shiyang/daai_runtime/envs/archives/4c3ccc5763b452719ee9564c6afbff63c9e13bfc1f0b6513ddfbfa0b4e5dec50.tar.zst`。
- `66748_0`、`66747_0`、`66750_0` 已先于本次修改 FAILED：旧 TMPDIR 包含完整环境哈希，vLLM 的 Unix socket 路径超过 107 字节，尚未进入模型推理。现改为短路径 `/dev/shm/mj-p1-1194/t.XXXXXX` 并显式设置 `VLLM_RPC_BASE_PATH`；旧作业不是被本次优化重启。9B/`66751_0` 在本次修改时刚启动旧版 vLLM，未主动中断；待真实状态决定是否只重提失败片。
- 本地代码测试 77/77 通过，覆盖快速路径不读取权重/不导入 Hub、缺失/内容/版本变化回退、压缩包往返、损坏包拒绝、完整本地环境不重复制，以及 IPC 短路径。新执行源码 SHA256 `1b5eb199f6726e1f6f9de0844d78c36cdab89f7d6b0530d5137d6ef0ee67bef8`，新固定执行目录 `/home/comp/24482277/shiyang/MindJourney-p1-startup-r7-20260908`。旧 r6 目录保持不动，BF16/no-thinking/上下文/图片顺序及 SVC 论文设置未修改。
- 13:45 HKT：srv12、srv15 已完成 `qwen` + `svc` 的本地依赖复制并发布完成标记，耗时分别 3790.96 秒、3694.05 秒（约 63.2 / 61.6 分钟，包含首次 NFS 复制成本）。72B 的 `66747_0` 日志已明确 `Reusing local dependencies`，复用 srv15 副本而非重新复制。此时还未出现正式题目 attempt/结果，不将依赖完成误记为推理完成。
- 13:42 HKT：四项 r6 已全部分配 GPU 节点，但仍处于本地依赖准备而非题目推理。`66748_0`（MindCube/27B）在 srv12；`66750_0`（MMSI/3.8-27B）及 `66747_0`（MindCube/72B）在 srv15；`66751_0`（MMSI/9B）在 srv11。同节点只允许一个复制者持锁，其余作业等待并复用副本，避免重复复制。
- srv11 的交互式预复制 step `66705.18`、`66705.21` 分别在 13:08、13:26 被 SIGKILL；与 SSH 断开同时发生，`nohup` 未能保护后一项。Slurm 记录为 CANCELLED，并非 OOM。现已改为独立 CPU 批处理 `66813`，固定 srv11，4 CPU / 64 GiB / 无 GPU，确认 RUNNING；日志 `/home/datasets/shiyang/daai_runtime/p1_runs/local-stage-batch-66813.err`（标准输出同前缀 `.out`）。该作业断点复用原副本，不重新安装或检查导入。
- 独立复制启动后，已恢复旧 vLLM 的 CONT 并取消旧 `66705_0`，释放其 2×A100；MMSI/9B 的既有 `66751_0` 随即在 srv11 启动，无重复提交正式分片。旧日志和本地断点均保留。不要再将旧交互复制日志或 `66705_0` 当作当前运行状态。
- 用户要求将已安装依赖复制到计算节点本地。`66705_0` 在 srv11 的旧 vLLM 进程停留于 NFS Python 导入，尚未提供模型服务或产生题目结果；短时系统调用跟踪观察到 torch 的单个 `.pyc` 打开耗时约 0.2–0.25 秒。这不是重新配环境或权重下载。
- 修复 commit `fdc7270`：复用已验证的共享 `qwen`/`svc` 环境，以受限并发复制到每个节点的私有 `/dev/shm/mj-p1-1194/env-4c3ccc5763b452719ee9564c6afbff63c9e13bfc1f0b6513ddfbfa0b4e5dec50`。完成后原子发布 `LOCAL_READY.json`，同节点后续作业复用副本；修正启动脚本中的绝对环境路径，包二进制不变。编译及临时缓存也使用节点本地目录，模型权重和结果仍保留共享目录。启动不增加重型导入或版本检查；SVC 原有完整资产校验保留。
- 安装来源仍为 `/home/datasets/shiyang/daai_runtime/envs/p1-01ef26c-v1`，`COMPLETE` SHA256 `4c3ccc5763b452719ee9564c6afbff63c9e13bfc1f0b6513ddfbfa0b4e5dec50`。新 worker source SHA256 `6bb1eed4483e9c8dac5f203e49ce57b16e1396d1864c4b042116303ef387ebd2`；实验清单 SHA256 `1b13b98fc39873515eb3794a4c417197ae222f844b6ae41402442103aa93f77f`。四项均使用固定执行目录 `/home/comp/24482277/shiyang/MindJourney-p1-72b-tp2-20260908`，不得在活动作业期间更新源码。
- 本地复制定向测试 3/3、原持久环境 prolog 测试 13/13 通过。BF16、no-thinking、图片顺序、65536 上下文及 SVC 搜索/生成设置不变；72B 仍试 TP=2 + SVC 1 卡，总计 3×A100，其他三项各 2×A100。少卡可运行性尚待实际推理确认。
- 12:37 HKT：srv11 已复制约 5.9 GiB，仍在复制中，尚无 `LOCAL_READY.json` 或新推理结果，不能据此宣称瓶颈已消除。旧 `66705_0` 的 vLLM 已暂停以减少读取争用，该 allocation 暂供本地复制；日志 `/home/datasets/shiyang/daai_runtime/p1_runs/local-stage-fast-66705.err`，复制完成后应释放旧 allocation，由新版正式作业运行。
- 已取消被替代的 `66706`、`66707`、`66716` 及临时 r5 `66733`–`66736`，日志和所有 Run root 保留。r6 提交器为 `66742`（MindCube/27B）、`66743`（MMSI/9B）、`66744`（MMSI/3.8-27B）、`66745`（MindCube/72B）；提交器运行不等于 GPU 推理开始。新 Run ID 分别为 `mj-p1-mindcube-qwen35-27b-a100-local-r6-20260908`、`mj-p1-mmsi-qwen35-9b-a100-local-r6-20260908`、`mj-p1-mmsi-qwen38-27b-a100-local-r6-20260908`、`mj-p1-mindcube-qwen25vl-72b-a100-local-r6-20260908`，均位于 `/home/datasets/shiyang/daai_runtime/p1_runs/`。不得混合新旧源码的结果。
- 已停止并清理同一次临时复制中误重复的三个无用副本（合计约 3.3 GiB），仅删除 srv11 上本任务拥有的 `.nFA3yC`、`.V0ohU1`、`.e53Knl` 临时目录；有效断点副本、共享原环境、权重和实验结果全部保留。
- 12:40 HKT 正式 GPU 队列：`66748_0`（MindCube/27B，srv12）和 `66750_0`（MMSI/3.8-27B，srv15）已分配节点，处于本地依赖复制阶段；`66751_0`（MMSI/9B）排队 Priority，`66747_0`（MindCube/72B）排队 Resources。srv11 预复制已处理约 16,954 个 Qwen 文件；文件计数包括复用断点，不代表题目数。所有复制完成后由 prolog 自动启动实际实验，无需重新配环境。

## 历史进展：2026-09-08 中午

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
| MindCube 1050 | P1 · 节点本地依赖复制中 | P1 · 三卡首片排队 | P3 · 待跑 | P3 · 待跑 |
| MMSI-Bench 1000 | P0 · 用户称此前已跑，产物待定位/验证 | P0 · 用户称此前已跑，产物待定位/验证 | P1 · 首片排队 | P1 · 节点本地依赖复制中 |
| SAT Real | P0 · **已验证完成** | P0 · 用户称此前已跑，产物待定位/验证 | P2 · 待跑 | P2 · 待跑 |
| SAT Syn (`rand42-500`) | P0 · **已验证完成** | P4 · 待跑 | P4 · 待跑 | P4 · 待跑 |

用户后续指令已确认第 1、2 行分别对应 MindCube 1050 与 MMSI-Bench 1000。`Qwen3.8-27B` 的规范模型 ID 已确认为 `Qwen/Qwen3.8-27B`。当前先完成四项 P1：MindCube 1050 的 Qwen3.5-27B、Qwen2.5-VL-72B-Instruct，以及 MMSI-Bench 1000 的 Qwen3.5-9B、Qwen3.8-27B；高优先级分片完成并验证后再进入 P2/P3/P4。

## P1 准备与运行状态（历史 r3 快照，现行队列见顶部）

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
