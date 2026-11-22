# demo/ · C8 早期验证物（可运行系统）

> 这是 `卢怡然_C8_demo.md` 指向的实际代码目录。平台评分公式中「早期验证物质量」占 70%。

## 快速开始

```bash
cd C:/Users/卢怡然/Desktop/C8
"C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe" demo/run_pipeline.py
"C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe" -m unittest discover -s demo/wechat-class-manager/tests -v
```
双击 `wechat-class-manager/dashboard/index.html` 查看离线看板。

## 目录索引

| 路径 | 内容 |
|---|---|
| `run_pipeline.py` | 一键端到端：11 个 CLI 子进程 + 测试 + 验收矩阵 + 环境/sha256 |
| `wcm_common.py` | 公共基础：7 字段 schema 校验、IO、配置加载、sha256 |
| `wechat_bridge.py` | L1 · 3 种显式数据源 → 标准 JSONL |
| `classifier.py` / `challenge_linker.py` / `submission_detector.py` / `qa_extractor.py` | L2 · 四个可独立运行的信号模块 |
| `scripts/gen_fixture.py` | 固定种子合成脱敏样本生成器（150 条 + 增量批次 + 真值标签） |
| `data/` | 合成样本、标签、增量批次、`README.md`（含诚实声明） |
| `wechat-class-manager/SKILL.md` | L3 · 根技能说明（触发词 / IO / 依赖 / 一键运行） |
| `wechat-class-manager/skills/` | 6 个子技能，各含 `SKILL.md` + 薄封装 `.py` |
| `wechat-class-manager/schemas/` | 4 个契约（3 个 JSON Schema + 1 个领域图定义） |
| `wechat-class-manager/config/` | 挑战定义与群配置（JSON 语法的 `.yaml`） |
| `wechat-class-manager/graph_store.py` | L3 · Property Graph CRUD 与学生画像 |
| `wechat-class-manager/nl_query.py` | L3 · 6 类自然语言查询（规则路由，非 LLM） |
| `wechat-class-manager/watcher.py` | L4 · 按 msg_id + checkpoint 增量去重 |
| `wechat-class-manager/alert_engine.py` | L4 · 5 条预警规则（4 类触发） |
| `wechat-class-manager/report_engine.py` | L4 · 周报 + 看板数据 |
| `wechat-class-manager/dashboard/` | 离线静态看板（8 维度） |
| `wechat-class-manager/tests/` | 13 项 unittest + 20 条独立手写变体夹具 |
| `SETUP.md` / `系统架构文档.md` / `部署指南.md` | 安装配置 / 架构 / 部署 |

## 实测摘要

- 11 个 CLI `exit=0`；13 项测试 `OK`；验收矩阵 22 条 = 15 pass / 2 pass(合成数据) / 5 not_met。
- 150 条消息 · 22 学生 × 8 挑战 · 203 节点 / 291 边 · 8 个提交事件 · 14 对 Q&A · 6 类查询 · 4 类预警 · 8 维度看板。
- 全部数字见 `../evidence/acceptance_matrix.json`，运行环境见 `../evidence/environment.txt`。

## 边界（请连同交付一起阅读）

**本目录不含任何真实微信聊天记录。** 数据全部由 `scripts/gen_fixture.py` 合成；真实数据源、Agent Runtime 调用、GitHub 托管、跨周运行与双向写回均未在本次实测/实现。详见 `data/README.md` 与 `../evidence/验收记录.md`。
