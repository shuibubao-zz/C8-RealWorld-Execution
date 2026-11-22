# 卢怡然 · C8 真实项目落地 —— 交付包（先看我）

> 挑战：C8 Real-World Project Execution ｜ ID `ch-20260717031544-7vw0rn` ｜ 平台截止 2026-12-31
> 整理日期：2026-11-14 ｜ 交付形态：Proposal 申请阶段全套 + 可运行早期验证物 + 逐条验收记录

---

## 30 秒上手

```bash
# 1) 端到端复现（零第三方依赖，Python 3.9+）
"C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe" demo/run_pipeline.py

# 2) 单独跑测试
"C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe" -m unittest discover -s demo/wechat-class-manager/tests -v

# 3) 打开看板：双击 demo/wechat-class-manager/dashboard/index.html（离线可用）
```

预期输出：`11 个 CLI 步骤 exit=0`、`Ran 13 tests ... OK`、验收矩阵 `15 pass / 2 pass(合成数据) / 5 not_met`。

---

## 先读哪三份

| 顺序 | 文件 | 用途 |
|---|---|---|
| 1 | `卢怡然_C8_目标与验收标准对照.md` | 挑战目标、三套口径、验收标准、优先级、未满足项 |
| 2 | `卢怡然_C8_proposal.md` | 正式申请书（5 部分、KSTAR、角色、早期验证） |
| 3 | `evidence/验收记录.md` | 每条验收标准 vs 实测数字，含诚实边界 |

---

## 目录结构

```
C8/
├── README.md                                 本文件：入口与运行方式
├── 卢怡然_C8_目标与验收标准对照.md            目标/验收/交付清单/优先级
├── 卢怡然_C8_proposal.md                     ★ 项目申请书（5 部分）
├── 卢怡然_C8_demo.md                         ★ 早期验证物说明（指向 demo/）
├── 卢怡然_C8_AI日志.md                       ★ 申请阶段 AI 协作日志
├── 卢怡然_C8_拿来说明.md                     ★ 7 个来源 + adopted/removed/improved
├── 卢怡然_C8_AAR_W1.md / W2 / W3             三轮迭代 AAR（R̂ vs R + 失败分析）
├── 卢怡然_C8_W1_产出说明.md / W2 / W3        执行阶段周产出索引
├── 卢怡然_C8_W1_AI日志.md / W2 / W3          执行阶段周 AI 日志
├── 卢怡然_C8_W1_拿来更新.md / W2 / W3        执行阶段每周新参考来源
├── 卢怡然_C8_提交自检清单.md                 平台检查清单逐条勾验
├── 卢怡然_C8_交付清单.md                     全部文件及用途（含 sha256 索引）
├── sha256_清单.txt                           全部交付文件的 SHA-256
├── demo/                                     ★ 可运行早期验证物
│   ├── README.md / SETUP.md / 系统架构文档.md / 部署指南.md
│   ├── run_pipeline.py                       一键端到端
│   ├── wechat_bridge.py                      L1 数据桥接（3 种显式数据源）
│   ├── classifier.py / challenge_linker.py
│   ├── submission_detector.py / qa_extractor.py   L2 四个模块
│   ├── wcm_common.py                         公共基础（零依赖）
│   ├── scripts/gen_fixture.py                合成脱敏样本生成器
│   ├── data/                                 合成样本、真值标签、增量批次
│   └── wechat-class-manager/                 L3/L4 Skill 包
│       ├── SKILL.md + skills/*/SKILL.md      7 个标准技能说明
│       ├── schemas/ (4) / config/ (2)
│       ├── graph_store.py / nl_query.py
│       ├── watcher.py / alert_engine.py / report_engine.py
│       ├── dashboard/index.html              离线看板（8 维度）
│       └── tests/test_all.py                 13 项测试 + 手写变体集
├── evidence/                                 可核验产物
│   ├── acceptance_matrix.json                22 条验收标准逐条实测
│   ├── 验收记录.md                           人工版验收记录
│   ├── test_output.txt / pipeline_output.txt / environment.txt
│   ├── sample_output.jsonl / classified.jsonl / challenge_refs.json
│   ├── submissions.json / qa_pairs.json / graph.json
│   ├── nl_query_answers.md / alerts.json / watcher_result.json
│   ├── weekly_report.md / dashboard_data.json / classifier_metrics.json
│   └── evidence_sha256.txt
└── 附录_真实项目证据/
    └── 卢怡然_C8_真实项目证据索引.md         P27 真实客户项目能力证据索引
```

---

## 诚实声明（重要，请勿略过）

1. **本次没有使用任何真实微信聊天数据。** 本机检测到微信数据目录，但未解密、未读取、未导出。系统全部由固定种子 20261114 生成的合成脱敏样本驱动，姓名均为「学生NN」占位。
2. 因此任务书 L1「提取 ≥100 条**真实**群消息」、L4「≥1 周**真实数据**演示」**未满足**；`evidence/acceptance_matrix.json` 中相关条目标记为 `not_met`，不用合成数据冒充。
3. 分类器准确率在「同源合成集」和「20 条独立手写变体集」上均为 1.0000；两者都**不是真实微信群人工标注集**，不能作为真实泛化证据。
4. 未安装 OpenClaw / Claude Code、未推送 GitHub、未实现双向写回微信；AAR 的 W1–W3 是同日完成的三个迭代轮次，**不是真实跨周记录**。
5. 未获得 G1/G2/G3 的老师或同伴书面背书，不宣称已通过实验班评审。
6. 所有 `xx/xx 通过` 类数字均绑定了解释器与依赖状态，见 `evidence/environment.txt`。

---

## 提交建议

申请阶段四件套（命名严格按平台要求）：
`卢怡然_C8_proposal.md`、`卢怡然_C8_demo.md`（+ `demo/` 目录）、`卢怡然_C8_AI日志.md`、`卢怡然_C8_拿来说明.md`。

执行阶段补充：`卢怡然_C8_AAR_W*.md`、`卢怡然_C8_W*_*.md`。
若提交系统只收单文件，可打包整个 `C8/` 目录；`sha256_清单.txt` 用于评审复核文件未被改动。
