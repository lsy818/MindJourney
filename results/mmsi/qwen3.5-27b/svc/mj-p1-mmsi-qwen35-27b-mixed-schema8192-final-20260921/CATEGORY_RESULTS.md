# MMSI-Bench / Qwen3.5-27B

Mixed-protocol source-aware aggregate, NOT a uniform strict-schema benchmark. 542 repaired + 329 previously unfinished strict-schema answers; 129 retained old-protocol answers. User explicitly retained scoring-parse-affected IDs 776 (wrong) and 992 (correct) without rerun. All outputs use 8192; not all answers are newly generated.

| 类别 | 正确 / 总数 | 准确率 |
|---|---:|---:|
| Motion (Cam.) | 18 / 74 | 24.32% |
| Positional Relationship (Cam.–Obj.) | 25 / 86 | 29.07% |
| Attribute (Meas.) | 31 / 64 | 48.44% |
| Positional Relationship (Reg.–Reg.) | 23 / 81 | 28.40% |
| MSR | 70 / 198 | 35.35% |
| Motion (Obj.) | 21 / 76 | 27.63% |
| Positional Relationship (Cam.–Cam.) | 26 / 93 | 27.96% |
| Positional Relationship (Cam.–Reg.) | 35 / 83 | 42.17% |
| Attribute (Appr.) | 19 / 66 | 28.79% |
| Positional Relationship (Obj.–Reg.) | 34 / 85 | 40.00% |
| Positional Relationship (Obj.–Obj.) | 28 / 94 | 29.79% |
| **总体** | **330 / 1000** | **33.00%** |
