# 卢怡然 · C8 项目申请书（C8 Proposal）

| 项 | 内容 |
|---|---|
| 申请人 | 卢怡然（郑州西亚斯学院 · 大数据应用开发专业 · 2024 级本科在读，学号 2024105480202） |
| 申请日期 | 2026-11-14 |
| 挑战 | C8 Real-World Project Execution（`ch-20260717031544-7vw0rn`，平台截止 2026-12-31T23:59） |
| 申请项目 | **Project C：课程生产体系**（服从导师最终分配，可迁移性见附录 B） |
| 本次实现载体 | 资料包下发的《微信群 → 班级管理子系统》L1–L4 任务书 |
| 早期验证物 | `demo/`（可运行系统 + 13 项测试 + 逐条验收记录），说明见 `卢怡然_C8_demo.md` |

---

## 1. 项目选择

### 我选择的项目：**C（课程生产体系）**

一句话理由：Project C 考的是「端到端生产系统 + 自动化 + 可复用到不同课程」，而我在 C1–C7 反复练的正是**把一次性产出变成可复跑的流水线**；资料包里下发的具体任务《微信群 → 班级管理子系统》恰好是这条流水线在「课程运营数据」侧的一个完整实例：

```
群消息流(Channel) → 结构化(Schema) → 意图理解(Signal) → 可复用 Skill(Domain)
                  → 交付(Dashboard/Report) → 归档(Graph/Evidence) → 闭环(AAR/ΔR)
```

它与 Project C 的 `Syllabus → Content → Agent → Delivery → Portfolio` 是同构的：都是把非结构化教学材料转成 Agent 可调用的结构化资产，并让整条链路能换一门课直接复用。

### 为什么适合我（不写「我很感兴趣」，只列已存在的产出）

**A. 我的相关经验 —— 真实客户项目 P27**

- 项目：**P27 城市配送网络动态看板**，甲方为**辽宁省聚思达供应链管理有限公司**，郑州西亚斯学院 AI+X Vibe Coding 实验班（二期）；我任 **Project lead**，组员**王艺然、靖雪晴**。
- 原始依据：桌面 `卢怡然_P27_真实项目需求书_AI+X导入版.md`（含 10 大章节 / 40 检查点映射，明确「【待确认】字段不填具体数值」的诚实约束）。
- 可核验的迭代留痕：桌面 `V1.1` → `V1.6.3` 共 9 个「三端合一」版本包（约 81 MB/版）、`V1.4/V1.5/V1.6.3` 的 `.sha256` 校验文件、`聚思达TMS三端使用指导说明书` 多个版本、`V1.6.3-数据库升级-102-109.sql`、`卢怡然_20261110汇报讲稿_带箭头标注.html`。
- 我在其中的职责（需求书原文）：企业需求对接与 12 项关键问题确认、3 周实施方案与第一周执行手册、系统架构设计与 AI 辅助开发（大屏端 + 司机 H5 + 数据导入工具）、测试组织与交付物归档。
- **诚实边界**：这些材料证明我做过真实客户项目，但**不能证明客户已签字验收**（桌面未找到客户验收文件），也不冒充本次 C8 的技术交付物。详见 `附录_真实项目证据/卢怡然_C8_真实项目证据索引.md`。

**B. 我在 C1–C7 中展示的相关能力（均为桌面上真实存在的目录/文件）**

| 挑战 | 具体产出 | 与 Project C 的关系 |
|---|---|---|
| C1 | 课程资料获取与翻译管线 | 输入侧：非结构化材料 → 结构化 |
| C2 / C2A | AI for Math 论文；ΔE-Bench（AGI 认知能力基准提案，Track 2 元认知） | 定义可测量的成功标准与「预期 vs 实际」差值 |
| C2G | 参数高尔夫 eval stride 拐点标定（本机**无 GPU**是当时的硬约束） | 约束下做可复现的消融实验 |
| C3 | 群内高质量参与（平台初评 77，**因「未发出」被扣分**） | 教训：**没真正发出/做到的事，绝不写成已完成**——直接决定本 Proposal 的诚实边界写法 |
| C4 / C4A / C4B / C4C / C4D | 技能分享、技能提交自动评审器（v4 双环境自检 16/16）、公众号文章生成技能（7 坑逐条标注依据级别）、作业自动求解、本地大模型 Agent 技能 | 把能力封装成**别人能调用的 Skill**，并给 Skill 配可执行检查器 |
| C5 / C5A | GitHub repo（`https://github.com/shuibubao--zz/wechat-publisher`）、GitHub 入门 | 开源协作与可移交性 |
| C6 / C6A | Web App、提交数据仪表盘（repo + 周报 + 截图 + demo.mp4） | 交付系统与可视化看板（本次 L4 Dashboard 直接承接） |
| C7 | 内容传播（articles / site / 文章链接汇总 / Elite20 复盘） | 把结果变成别人看得懂、用得上的表达 |

**C. 我对这个领域的理解**

1. 端到端系统的难点不是某个模块，而是**接口契约**：所以我在 L1 先把消息固定成 7 字段 schema，L2/L3/L4 全部只认这份契约，换数据源只需换 adapter。
2. 「可复用」要靠**配置与实现分离**：挑战定义、群配置、节点/边 schema 全部外置到 `config/` 与 `schemas/`，换一门课改配置即可。
3. 「自动化」必须配**可核验的验收**：所以写了 `run_pipeline.py` 一键复跑 + 13 项 unittest + `acceptance_matrix.json` 逐条现算数字，而不是靠文档自述。
4. 真实项目和练习最大的差别是**约束不能被忽略**：隐私授权、依赖环境、他人背书、真实时间跨度，都不能用「模拟一下」糊过去（见 §5 与 `evidence/验收记录.md`）。

### 为什么不是 A / B（对比分析，不是自我劝退）

| 项目 | 匹配度 | 判断依据 |
|---|---|---|
| A · AI+X 高校落地扩展 | 中 | 核心工作是课程适配、招生机制、面向校领导的方案包与 ROI 谈判；我的实证集中在**系统交付**而非 BD/谈判，缺少可出示的合作洽谈记录 |
| B · 企业本体 Agent 系统 | 中 | 需要电信运营商的真实业务数据与 Neo4j/pgvector 生产环境，本次未获得；但它的 **Property Graph 建模方法（T-box/A-box → 节点+边）被我用在 L3**，是我主动拿来的部分 |
| **C · 课程生产体系** | **高** | 下发任务书本身就是「消息流 → 结构化 → Agent Skill → 交付 → 归档」的端到端流水线，且明确要求复用到不同课程/挑战；与我的 Skill 化、pipeline 化、看板化经验完全对齐 |

> 说明：`CHALLENGE.md` §3 写明 C8 项目由**导师筛选进入**，因此以上为申请意向，最终以导师分配为准；附录 B 给出 A/B 分配下的可迁移清单。

---

## 2. 拿来主义分析（Reference + Adaptation）

> 这是本挑战标注的**最重要评分项**。下面每个来源都给出：出处、核心思想、adopted（直接复用）、removed（去掉及原因）、improved（重构/新增及原因）。权威性排序与版本冲突处理见 `卢怡然_C8_拿来说明.md` §1。

### 2.1 参考来源总表（7 个，全部可核）

| # | 来源 | 出处 / 链接 | 核心思想 |
|---|---|---|---|
| S1 | 平台 `challenge.json` / `CHALLENGE.md` / `rubric.json` | 资料包根目录（已全文读取） | 交付物命名规范、KSTAR、AAR（R̂ vs R）、5 维度 rubric |
| S2 | 《C8 WeChat Class Management Challenge》任务书 | `materials/…pdf` p.1–15（已提取 13035 字符） | 三层架构、Domain Model First、L1–L4 分级与验收标准、技术选型速查表 |
| S3 | sjzar/chatlog | `https://github.com/sjzar/chatlog`（2026-11-14 联网核实） | 本地解密微信 DB → HTTP API（默认 `127.0.0.1:5030/api/v1/chatlog`）+ MCP SSE，Windows/macOS，完全本地运行 |
| S4 | wechat-cli / wetrace / PyWxDump 选型清单 | 任务书 p.12「Layer 1 技术选型速查」 | 按平台与取证级别选择 Channel Adapter，CLI-first、JSON 输出、AI-friendly |
| S5 | 本人 C4A 技能提交自动评审器 | 桌面 `C4A/`（`c4-skill-evaluator/`、evidence、README） | 把检查清单写成**可执行检查器**；v4 修复「无 PyYAML 时 mini-YAML 行内注释崩溃」 |
| S6 | 本人 C6A 提交数据仪表盘 | 桌面 `C6A/`（`卢怡然_C6A_dashboard/`、周报、report.xlsx） | KPI 卡 + 完成率可视化的看板形态 |
| S7 | 《AI+X 实验班真实项目执行方案 v3.1》 | `materials/真实项目执行方案0511.pdf` p.7–8 | G1 提案 7 要素、G2 六件套 + 验证报告 APPROVE、G3 30 分钟复现、AI_LOG.md 过程留痕 |

### 2.2 逐来源的取舍（adopted / removed / improved）

**S1 平台规范（权威性最高）**
- adopted：四类必需文件的命名通配、Proposal 5 部分、AAR 的 `R̂ vs R → 失败分析 → 下周计划` 结构、每 Level 一份 AI 日志。
- removed：不加任何「平台没要求」的额外格式，避免偏离需求。
- improved：把 rubric 的「有验收记录」「有验证」落成机器可核验的 `acceptance_matrix.json`（22 条逐条现算），而不是自评表。

**S2 下发任务书（实现主线）**
- adopted：三层架构（Channel / Cognitive / Skill Domain）、Property Graph 领域模型（6 类节点、7 类边）、KSTAR Episode 编码思想、L1–L4 全部交付物名称与验收口径。
- removed：**不实现**「Neo4j / Memgraph / NetworkX」等需额外安装的存储（本机无这些依赖）；**不读取**真实微信数据库（隐私与授权边界）。
- improved：① 用标准库 dict + JSON 实现图 CRUD，换机器零安装即可跑；② 把单一的 `wechat-cli` 起点改造成 **3 种显式数据源**（synthetic / jsonl / chatlog），且真实源失败时**直接报错、不静默回退假数据**；③ 每级交付物补一份可复跑的验收记录。

**S3 chatlog**
- adopted：HTTP API 契约形状（`talker` / `format=json` / `limit`）、「数据只在本地、不上传」的隐私原则。
- removed：去掉 Go 二进制与 MCP SSE 依赖（本次未安装、未实测），不把「支持 MCP」写成已实现能力。
- improved：在 `wechat_bridge.py` 里把它做成**可插拔 adapter**，并明确标注「未连接真实服务、未实测」；这样将来接真实数据时不用改 L2–L4 任何一行。

**S4 选型清单**
- adopted：「Channel Adapter 与上层解耦」「JSON Lines 输出」两个判断。
- removed：不做工具之间的功能对比实验（没有真实数据可测，做了就是编）。
- improved：把选型结论固化为 `config/group_config.yaml` 的 `data_source` 字段 + `SETUP.md` 的三种数据源使用说明。

**S5 C4A 评审器（含我踩过的坑）**
- adopted：「检查器必须可执行」「双环境自检」「evidence 留档 + sha256 复核」三套做法。
- removed：**去掉 PyYAML 依赖**。C4A v4 的教训是「无 PyYAML 环境下 mini-YAML 行内注释会崩」，所以本次 `config/*.yaml` 与 `schemas/domain-graph.yaml` 全部用 **JSON 语法**（JSON 是 YAML 1.2 的合法子集），用 `json.load` 读，无需任何第三方包。
- improved：把「零依赖」宣称真正验证一遍——用本机 `Python 3.13.14`（`importlib` 检查 pypdf/PyPDF2/pdfplumber/fitz/pdfminer **全部为 False** 的解释器）跑通 11 个 CLI + 13 项测试，环境写入 `evidence/environment.txt`。

**S6 C6A 仪表盘**
- adopted：KPI 卡、完成率条形、周报结构。
- removed：去掉在线服务 / 构建工具 / CDN 依赖。
- improved：改成**双击即可离线打开**的静态 `dashboard/index.html`，数据由 `report_engine.py` 生成 `dashboard_data.js` 注入（规避 `file://` 下 fetch 的跨域限制），维度从 C6A 的若干项扩展为 8 个。

**S7 实验班执行方案**
- adopted：「过程留痕（AI_LOG）」「30 分钟复现核心结果」「验证报告」的工程要求。
- removed：**不采用其 6/17 截止日期**（与平台 `challenge.json` 的 2026-12-31 冲突，以平台为准）；不虚构 G1 老师/同伴书面背书、G2 `APPROVE`、G3 定级。
- improved：把「30 分钟复现」变成 `run_pipeline.py` 一键复跑 + `sha256` 清单，把「验证报告」变成 `acceptance_matrix.json` + `evidence/验收记录.md`。

### 2.3 创造性组合（为什么不是简单拼装）

把 S5 的「检查器可执行化」装在 S1 的「验收记录」上，把 S3/S4 的「可插拔数据源」装在 S2 的「三层架构」上，再用 S7 的「过程留痕」串起 S6 的「可视化交付」——得到的是一条**从数据入口到验收出口都能被机器复核**的链路：换数据源不改上层、换课程不改代码、换机器不装依赖、换评审能逐条对齐验收标准。这正是 Project C 要求的「不需要每次从头搭建」。

---

## 3. 执行方案（KSTAR）

### K（Knowledge）：我已有的知识和资源

- **相关技能**：Python 标准库工程化、规则引擎与 schema 设计、Skill 封装（C4 系列）、静态看板（C6A）、技术文档与 evidence 留档（C1–C7 全程）。
- **可用工具**：本机 `C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe`（Python 3.13.14，**无第三方包**）、WorkBuddy（AI 协作）、pypdf 7.1.0（仅临时用于读资料 PDF，不进入交付系统）。
- **团队 / 协作资源**：P27 项目组（王艺然、靖雪晴）的协作经验；C1–C7 全部历史交付目录；资料包 8 份文件。
- **已知约束**：无真实微信数据授权、无 OpenClaw/Claude Code runtime、无本次 GitHub 仓库、无外部 LLM 预算、无老师/同伴签字背书。

### S（Situation）：当前问题是什么

- **现状**：Elite20 的班级管理靠人工翻群消息——提交追踪靠老师手动找文件，活跃度全凭感觉，好问题淹没在聊天流，通知发出后不知道谁看了（任务书 p.1 问题表）。
- **痛点**：消息流不可查询、不可追踪、不可行动；已有工具（chatlog 等）只解决「导出」，不解决「结构化 + 复用」。
- **约束条件**：① 隐私：真实聊天记录不能未经授权读取/落盘；② 环境：换机器必须零依赖可跑；③ 口径：平台规范与下发任务书要同时满足；④ 时间：本次为集中执行，无法提供真实跨周运行记录；⑤ 验证：所有数字必须可复跑、可复核。

### T（Task）：我要解决什么

**核心目标**：交付一个「Channel → 结构化 → Skill → 交付 → 归档 → 复盘」的端到端可复用系统，并让每条验收标准都有机器可核验的证据。

| 子任务 | 周期 | 目标产出 |
|---|---|---|
| T1 · 数据桥接与信号提取（L1–L2） | W1–W2 | 7 字段消息契约、3 种显式数据源、7 类意图分类、挑战关联、提交检测、Q&A 提取 |
| T2 · Skill 封装与领域模型（L3） | W3–W4 | 7 个 SKILL.md、4 schema + 2 config、Property Graph CRUD、≥5 类自然语言查询、测试 |
| T3 · 闭环系统（L4） | W5–W6 | Watcher 增量去重、≥3 类预警、周报、≥5 维度 Dashboard、架构与部署文档 |
| T4 · 验收与复盘固化 | W7–W8 | 一键流水线、逐条验收矩阵、AI 日志、拿来更新、AAR（R̂ vs R）、交付包整理 |

### Â（Action Plan）：怎么做

| 步骤 | 使用的 AI / 工具 | 输入 | 输出 |
|---|---|---|---|
| A1 读全资料、定双轨口径 | AI 辅助提取 3 份 PDF 文本并对照 5 份元数据 | 资料包 8 文件 | `卢怡然_C8_目标与验收标准对照.md` |
| A2 核实事实与隐私边界 | 本机只读探测 + 联网核实 chatlog | 桌面历史交付、P27 材料 | 事实清单（写入本 Proposal §1 与拿来说明） |
| A3 写 L1/L2 模块 | AI 生成初版 → 我逐条核对 schema 与规则 | 合成样本生成器 | `wechat_bridge.py` 等 5 个可独立运行 CLI |
| A4 批量生成 Skill 包 | 生成脚本一次产出结构化资产 | 任务书目录规范 | 7 SKILL.md + 4 schema + 2 config + 手写变体集 |
| A5 写 L3/L4 引擎 | AI 辅助 + 我确定图模型与预警规则 | L1/L2 产物 | graph/nl_query/watcher/alert/report + dashboard |
| A6 一键流水线 + 测试 | `unittest` 与 subprocess 真跑 | 全部模块 | `evidence/` 全部产物 + 13 项测试结果 |
| A7 依据实测数字反写文档 | AI 整理，我逐项核对数字出处 | `acceptance_matrix.json` | Proposal / AAR / 验收记录 / 自检清单 |
| A8 整理与 sha256 复核 | 脚本全量哈希 | C8/ 全部文件 | `sha256_清单.txt`、`卢怡然_C8_交付清单.md` |

> 迭代真实发生过：A3–A6 期间修复了 4 个真实缺陷（生成器标签容器类型、README 模板 `%` 未转义、Watcher 把重复消息计入新处理数、导师被计入 Student 节点），全部记录在 `卢怡然_C8_AI日志.md` 与 `AAR_W1–W3.md`，没有把失败藏起来。

### R̂（Expected Result）：预计产出什么

**可交付物清单**
1. `卢怡然_C8_proposal.md`（本文件）+ `卢怡然_C8_demo.md` + AI 日志 + 拿来说明（申请四件套）。
2. `demo/` 可运行系统：L1–L4 全部模块 + 7 个 Skill + 4 schema + 2 config + 13 项测试 + 4 份文档。
3. `evidence/` 可核验产物：验收矩阵、测试输出、流水线输出、环境信息、sha256 清单。
4. 执行阶段周次文件与 3 份 AAR。

**成功标准（全部可量化，便于 AAR 对比 ΔR）**

| 指标 | R̂ 目标 | 验证方法（机器可核验文件） |
|---|---|---|
| 消息样本量 / schema 合规 | ≥100 条 / 100% 符合 7 字段 | `evidence/sample_output.jsonl` + `test_output.txt` |
| 消息类型覆盖 | 6 种全覆盖 | `sample_output.meta.json` |
| 分类器准确率 | >0.70（另报独立手写变体集） | `classifier_metrics.json` / `test_output.txt` |
| 提交事件 / Q&A 对 | ≥5 / ≥10 | `submissions.json` / `qa_pairs.json` |
| 图规模 | ≥20 学生 × 8 挑战 | `graph.json` counts |
| NL 查询类型 | ≥5 类 | `nl_query_answers.json` |
| 预警类型 | ≥3 类 | `alerts.json` |
| Dashboard 维度 | ≥5 个 | `dashboard_data.json` |
| 测试与端到端 | 全部通过、11 个 CLI exit=0 | `test_output.txt` / `pipeline_output.txt` |
| 验收记录完整度 | 每条标准有 measured + status + evidence | `acceptance_matrix.json` |

> R̂ 里**故意包含无法用模拟达成的项**（真实微信数据、真实 1 周运行、runtime 实测、GitHub 托管），AAR 会对它们诚实地给出 `not_met`，而不是事后把目标改小。

---

## 4. 我的角色

- **主角色：Builder**（动手写代码、搭系统、产出可运行交付物）；**兼任 Architect**（定义 schema、图模型、三层架构与接口契约）。
- **我负责的具体模块**：L1 数据桥接与 schema；L2 四个信号模块；L3 Property Graph、NL 查询、全部 SKILL.md；L4 Watcher / Alert / Report / Dashboard；一键流水线、测试、验收矩阵与全部交付文档。
- **我的边界（我不负责什么）**：
  - 不负责真实微信数据库的解密、导出与合规授权（需数据所有者授权）；
  - 不负责 OpenClaw / Claude Code 的部署与 hook 配置（本机未安装）；
  - 不负责 Wechaty 双向写回、群发提醒等**对外动作**（未经允许不向群里发消息）；
  - 不负责 GitHub 仓库创建/推送与 G1/G2/G3 背书（需账号凭据与他人参与）；
  - 不负责学生画像的心理学解释——画像只是群互动统计，不是能力测评结论。
- **我需要的支持**：① 若入选真实项目，需导师/客户明确数据授权范围与目标群；② 若分配 Project B，需企业侧本体术语表与脱敏样本；③ 若需 GitHub 托管，需确认归属账号；④ G1/G2/G3 需要 ≥1 老师 + ≥1 同伴的书面背书。

---

## 5. 早期验证（Proof of Capability）

> 「没有实际东西 = 不会入选」。本次提供**可运行的系统**（不只是文档），评分权重 70% 的部分在这里。

**验证物**：`卢怡然_C8_demo.md`（说明）+ `demo/`（可运行代码）+ `evidence/`（可核验输出）。

**2026-11-14 实测结果**（解释器 `Python 3.13.14`，零第三方依赖，详见 `evidence/environment.txt`）：

| 项 | 实测 |
|---|---|
| 端到端 | `run_pipeline.py` 11 个独立 CLI 步骤全部 `exit=0` |
| 测试 | `unittest` **13 项全部通过**（`Ran 13 tests ... OK`） |
| 消息 | 150 条，6 种类型，100% 符合 7 字段 schema，两次运行输出 sha256 一致 |
| 分类 | 合成集 1.0000（150/150）；独立手写变体集 1.0000（20/20） |
| 提交 | 8 个事件（4 完整 / 4 缺 AI 日志），4 个附件正确归并 |
| Q&A | 14 对，平均质量分 0.714，全部 reply_to 精确配对 |
| 图 | 22 学生 × 8 挑战，203 节点 / 291 边，7 类边 |
| 自然语言查询 | 6 类意图全部可答 |
| 闭环 | Watcher 12 条输入中跳过 4 条重复、处理 8 条新增；预警 4 类共 14 条；周报 6 章节；看板 8 维度 |
| 验收 | `acceptance_matrix.json` 22 条：**15 pass / 2 pass(合成数据) / 5 not_met** |

**这个验证物证明了什么、没证明什么**

- ✅ 证明：我能把一份 15 页任务书拆成可运行的四层系统，能定义接口契约、写出测试、把验收标准变成机器可核验的数字，并诚实记录失败与迭代。
- ❌ **不证明**：系统在真实微信群上有效。所有数据为合成脱敏样本；分类器两个 1.0000 都不等于真实人工标注集上的泛化能力；未接真实数据源、未跨周运行、未被 Agent Runtime 调用过、未托管 GitHub。
- 上述 5 项 `not_met` 已在 `evidence/验收记录.md` 与三份 AAR 中逐条列明，**不用模拟结果冒充真实结果**——这是我从 C3「未发出却写成已参与」被扣分里学到的规矩。

---

## 附录 A：与真实项目 P27 的关系

P27 是我在**真实客户、真实需求、真实团队**下的项目经历，用来支撑 §1 的「相关经验」；本次 C8 的技术交付物是 `demo/` 中的班级管理子系统，**两者不是同一个项目**，P27 材料也不复制进交付包（只留一份路径索引，避免把 81 MB × 9 个版本包塞进提交目录）。它带来的可迁移做法：需求书字段化、版本包 + sha256 留痕、按周迭代、面向客户的使用说明书、验收要有复现步骤。

## 附录 B：服从导师分配与可迁移性

| 若分配 | 可直接复用 | 需要补做 |
|---|---|---|
| A · AI+X 高校落地扩展 | 配置与实现分离、一键复跑流水线、验收矩阵、文档与 evidence 体系 | 课程适配包、招生机制、面向校领导的方案包与 ROI 分析 |
| B · 企业本体 Agent 系统 | `domain-graph.yaml` 的 T-box/A-box 思路、图 CRUD、可插拔数据源、Skill IO 规范 | 企业术语表、OWL/RDF/SKOS 表达、真实脱敏数据、Neo4j/pgvector 生产环境 |
| C · 课程生产体系 | **本次全部交付物** | 接入真实课程大纲与真实消息源、跨周 AAR、GitHub 托管 |

---

*本 Proposal 中所有数字均来自 `evidence/` 下可复跑的机器产物；所有引用的历史交付与项目材料均为本机真实存在的文件。未做到的事在 §5 与 `evidence/验收记录.md` 中明确列为未满足。*
