# Weekly AAR — Week 2（L3 Skill 封装 + 领域模型）

> **时间口径诚实声明**：W2 是 2026-11-14 集中执行的第二个迭代轮次，非真实跨周记录。
> 对应任务书：Level 3 Gold ｜ 对应 Proposal §3 的 T2

---

## 预期（R̂）

| 指标 | 本轮计划 |
|---|---|
| Skill 包 | 完整 `wechat-class-manager/` 目录，7 个标准 `SKILL.md` |
| Schema / 配置 | 4 个 schema + 2 个 config |
| Property Graph | 能存 ≥20 学生 × 8 挑战，具备 CRUD |
| 自然语言查询 | ≥5 种不同类型的问题 |
| 其它 | 至少 3 个可演示场景、代码有测试且通过、Skill 可被 Agent Runtime 识别调用、代码托管 GitHub |

## 实际（R）

- 目录齐全：根 `SKILL.md` + 6 个子技能 `SKILL.md`（共 7 个），每个子技能配一个只做转发的薄封装 `.py`（不复制业务逻辑）；`schemas/` 4 个、`config/` 2 个、`tests/` 含 13 项测试与 20 条手写变体夹具。
- Property Graph：**22 学生 × 8 挑战**，203 节点 / 291 边，7 类边（SUBMITTED / SENT / ASKED / ANSWERED / MENTORED / PROGRESSED_TO / TAGGED_WITH）；CRUD 与 JSON 持久化有专门测试。
- 自然语言查询：**6 类**意图全部可答（`student_submissions` / `missing_by_challenge` / `top_active` / `faq` / `student_profile` / `class_summary`），演示问答写入 `evidence/nl_query_answers.md`。
- 13 项单元测试中，L3 相关 5 项全部通过。
- **未被 Agent Runtime 识别调用：未实测（本机无 OpenClaw / Claude Code）**；**GitHub 托管：未做（本次未创建/推送仓库）**。

## 差值（ΔR = R̂ − R）

**完成了什么**：目录规范、图规模、查询类型、测试——任务书 L3 的可工程验证部分全部达成。

**没完成什么**：`L3-4` runtime 实测、`L3-5` GitHub 托管。这两项都需要外部条件（安装 runtime / 账号凭据），本次不具备，我不把「SKILL.md 写好了」等同于「被调用过」，也不拿历史 C5/C6A 仓库冒充本次交付。

**意外发现**：第一版图里 `Student` 节点是 **23** 个，比配置里的 22 名学生多 1。查下来是导师 `t01` 发的公告也被建成了 Student 节点。这个「多出来的人」不会让任何测试失败，却会让「22 名学生」这个口径变成假的——**不会报错的口径错误最容易被写进报告**。

## 失败分析

| 失败 | 根本原因 | 不是根本原因但看起来像的 |
|---|---|---|
| 学生数 23 ≠ 22 | 领域模型把所有 `sender` 一律建成 `Student` 节点，没有 Mentor 主体 | 不是样本里混进了第 23 个人，也不是 `group_config.yaml` 配错（配置里是 22 个 `s01..s22`） |
| 生成 Skill 资产时报错 | 模板字符串 `%s` 个数与参数个数不一致 | 不是目录权限或中文路径问题 |
| 配置读取可能在别的机器上崩 | C4A v4 的真实教训：无 PyYAML 时 mini-YAML 解析器会崩 | 不是「YAML 文件写得不对」——本交付的 `.yaml` 用 JSON 语法，`json.load` 直读，任何解释器行为一致 |

**修复**：`graph_store.py` 引入 `Mentor:` 主体，导师消息仍产生 `SENT` 边、仍能作为 `ANSWERED` / `MENTORED` 的参与方，但不占 `Student` 节点；重跑后 `students=22, challenges=8`。同时把「零依赖」宣称放到真缺依赖的解释器上验证（pypdf/PyPDF2/pdfplumber/fitz/pdfminer 全部 `find_spec=False`），结果写入 `evidence/environment.txt`。

## 本周我发现了什么（拿来主义条目）

> 本周我发现了 **「JSON 是 YAML 1.2 的合法子集」** 这一做法，它比 C4A 里自写 mini-YAML 解析器更好，因为：既保留任务书要求的 `challenges.yaml` / `group_config.yaml` 文件名与目录结构，又不需要 PyYAML，用标准库 `json.load` 就能在任何解释器读，直接消除「行内注释崩溃」整类缺陷。
> 代价是配置文件不能写 YAML 注释——我把注释改成 `_format_note` / `_privacy_note` 字段，让说明本身也成为可读取的数据。
> 同时评估了 Neo4j / Memgraph / NetworkX：**现有「标准库 dict + JSON」仍是最优**，因为本机无这些依赖、任务书也允许「快速原型」档位；若将来进 Project B 的企业环境，再换原生图库也不影响上层 Skill IO 契约。

## 下周计划（→ W3）

- **R̂ 调整**：W3 做 L4 闭环（Watcher / Alert / Report / Dashboard）+ 验收固化，目标：增量不重复、≥3 类预警、结构完整周报、≥5 维度看板、一键流水线、22 条验收矩阵、13 项测试全绿；**R̂ 继续保留「真实 1 周运行」与「双向写回」两项，预期失败也如实记录**。
- **需要改变的做法**：① 把「节点口径」这类不会让测试失败的约束，主动写成断言（如学生数精确等于配置人数）；② 验收矩阵由代码现算，不许手写数字；③ 预警规则的模拟时间点必须在结果里标注 `simulated_as_of`。
- **需要的支持**：真实数据源授权、目标 Agent Runtime 的安装与调用规范、GitHub 归属账号。
