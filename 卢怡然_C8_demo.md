# 卢怡然 · C8 早期验证物（`姓名_C8_demo.*`）

> 平台说明：**「没有实际东西 = 不会入选」**，评分公式 `Proposal 文字质量 × 30% + 早期验证物质量 × 70%`。
> 因此本文件只是索引，**真正的验证物是 `demo/` 目录里可运行的系统 + `evidence/` 里可核验的输出**。

---

## 1. 它是什么

一个把微信群消息流变成「可查询、可追踪、可行动」结构化数据的四层系统，完整实现资料包下发的《微信群 → 班级管理子系统》L1–L4：

| 层 | 实现 | 入口 |
|---|---|---|
| L1 Channel Adapter | 3 种显式数据源（synthetic / jsonl / chatlog）→ 7 字段 JSONL | `demo/wechat_bridge.py` |
| L2 Cognitive | 7 类意图分类、挑战关联、提交检测（含附件完整性）、Q&A 提取 | `demo/classifier.py` 等 4 个 CLI |
| L3 Skill Domain | 7 个标准 `SKILL.md`、Property Graph CRUD、6 类自然语言查询 | `demo/wechat-class-manager/` |
| L4 Closed Loop | Watcher 增量去重、5 条预警规则、周报、8 维度离线看板 | `demo/wechat-class-manager/watcher.py` 等 |

## 2. 三步复现（评审可直接照做）

```bash
# 解释器：C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe（Python 3.13.14，零第三方依赖）
cd C:/Users/卢怡然/Desktop/C8

# ① 端到端：11 个独立 CLI 依次执行，产出 evidence/ 全部文件
"…/python.exe" demo/run_pipeline.py

# ② 单独跑测试：13 项
"…/python.exe" -m unittest discover -s demo/wechat-class-manager/tests -v

# ③ 打开看板（离线，无需服务器）
双击 demo/wechat-class-manager/dashboard/index.html
```

详细安装/使用/排错见 `demo/SETUP.md`，架构见 `demo/系统架构文档.md`，部署见 `demo/部署指南.md`。

> 说明：`*.yaml` 配置文件用 JSON 语法（YAML 1.2 合法子集），**不需要 PyYAML**；这条已在真缺依赖的解释器上验证，见 `evidence/environment.txt`。

## 3. 实测结果（2026-11-14，全部机器可核）

| 验收项 | 实测 | 证据文件 |
|---|---|---|
| 端到端可运行 | 11 个 CLI 步骤全部 `exit=0` | `evidence/pipeline_output.txt` |
| 测试通过 | `Ran 13 tests ... OK` | `evidence/test_output.txt` |
| 消息量 / schema | 150 条 / 100% 符合 7 字段 / 6 种类型全覆盖 | `evidence/sample_output.jsonl` |
| CLI 可重复 | 两次运行输出 sha256 一致 | `evidence/acceptance_matrix.json` L1-4 |
| 分类准确率 | 合成集 1.0000（150/150）；独立手写变体集 1.0000（20/20） | `evidence/classifier_metrics.json`、`test_output.txt` |
| 提交检测 | 8 个事件（4 完整 / 4 缺 AI 日志），4 个附件正确归并 | `evidence/submissions.json` |
| Q&A 提取 | 14 对，平均质量分 0.714 | `evidence/qa_pairs.json` |
| Property Graph | 22 学生 × 8 挑战，203 节点 / 291 边 / 7 类边 | `evidence/graph.json` |
| 自然语言查询 | 6 类意图全部可答 | `evidence/nl_query_answers.md` |
| Watcher 增量 | 12 条输入 → 跳过 4 条重复、处理 8 条新增；二次运行 0 新增 | `evidence/watcher_result.json` |
| 预警 | 4 类规则共 14 条（模拟时间点 2026-11-18） | `evidence/alerts.json` |
| 周报 / 看板 | 6 章节 / 8 维度 | `evidence/weekly_report.md`、`dashboard_data.json` |
| 验收矩阵 | 22 条：15 pass / 2 pass(合成数据) / 5 not_met | `evidence/acceptance_matrix.json` |

## 4. 文件地图（按任务书四级对应）

| 任务书要求的文件 | 本交付位置 |
|---|---|
| `wechat_bridge.py` / `sample_output.jsonl` / `SETUP.md` / L1 AI 日志 | `demo/wechat_bridge.py` / `evidence/sample_output.jsonl` / `demo/SETUP.md` / `卢怡然_C8_W1_AI日志.md` |
| `classifier.py` / `challenge_linker.py` / `submission_detector.py` / `qa_extractor.py` / 测试数据 / L2 AI 日志 | `demo/` 四个同名 CLI / `demo/data/` / `卢怡然_C8_W1_AI日志.md` |
| `wechat-class-manager/`（7 SKILL.md、4 schema、2 config、tests、Graph、NL 查询）/ L3 AI 日志 | `demo/wechat-class-manager/` / `卢怡然_C8_W2_AI日志.md` |
| Watcher + Alert + Report + Dashboard + 架构文档 + 部署指南 / L4 AI 日志 | `demo/wechat-class-manager/` / `demo/系统架构文档.md` / `demo/部署指南.md` / `卢怡然_C8_W3_AI日志.md` |
| 每个 Level 一份 AAR | `卢怡然_C8_AAR_W1.md` / `W2` / `W3` |

## 5. 这个验证物的边界（务必连同交付一起看）

1. **数据是合成的**：`demo/scripts/gen_fixture.py` 用固定种子 20261114 生成 150 条脱敏样本，姓名为「学生NN」占位。**本次未解密、未读取、未导出任何真实微信聊天记录**；本机虽检测到微信数据目录，但出于隐私与授权边界没有碰它。
2. 因此 L1「从真实本地微信数据提取 ≥100 条」、L4「≥1 周真实数据演示」**未满足**；`acceptance_matrix.json` 标为 `not_met`。
3. 分类器两个 1.0000 **不是泛化证据**：合成集标签与规则同源；手写变体集虽独立于模板，但只有 20 条且由本人设计。真实标注集上的准确率未知。
4. 未安装 OpenClaw / Claude Code（Skill 的 runtime 调用未实测）、未推送 GitHub、未实现 Wechaty 双向写回；预警中的 deadline 规则使用**模拟时间点** 2026-11-18，不是真实当天。
5. 看板与周报里的所有数字都来自合成样本，不得对外表述为真实班级数据。

> 完整逐条说明见 `evidence/验收记录.md`。把这些边界写清楚，是 C3 那次「未发出却写成已参与」被扣分之后我给自己定的规矩。
