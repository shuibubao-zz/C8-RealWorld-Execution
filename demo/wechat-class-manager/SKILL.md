---
name: wechat-class-manager
description: 把一个微信群的消息流变成可查询、可追踪、可行动的班级管理 Agent Skill 集合。覆盖提交追踪、考勤活跃度、Q&A 沉淀、学生画像、周报与预警。
triggers:
  - "这周班级状态如何"
  - "谁还没交 C4B"
  - "帮我生成本周班级周报"
  - "查一下张三提交了哪些挑战"
version: 1.0.0
runtime: "Python 3.9+ / 零第三方依赖 / 任意可读 SKILL.md 的 Agent Runtime"
---

# wechat-class-manager

## 层次
| 层 | 职责 | 目录 |
|---|---|---|
| L1 Channel Adapter | 群消息 -> 标准 JSONL | `../wechat_bridge.py` / `skills/wechat-bridge/` |
| L2 Cognitive | 分类、挑战关联、提交检测、Q&A 提取 | `../*.py` / `skills/msg-classifier/` 等 |
| L3 Skill Domain | 图存储、自然语言查询、画像、报告 | `graph_store.py` / `nl_query.py` / `skills/*/` |
| L4 Closed Loop | 增量监控、预警、周报、看板 | `watcher.py` / `alert_engine.py` / `report_engine.py` / `dashboard/` |

## 依赖
- Python 3.9+ 标准库（json / re / argparse / datetime / unittest / http.server）
- 配置文件 `config/*.yaml` 采用 JSON 语法，无需 PyYAML
- 数据：默认合成脱敏样本；真实微信数据须经 `wechat_bridge.py` 显式指定数据源

## 输入 / 输出
| Skill | 输入 | 输出 |
|---|---|---|
| wechat-bridge | group, days, source | messages.jsonl |
| msg-classifier | messages.jsonl | classified.jsonl |
| submission-tracker | classified.jsonl + challenge_refs.json | submissions.json |
| qa-sink | classified.jsonl | qa_pairs.json |
| student-profile | graph.json + wechat_id | profile JSON |
| class-report | graph.json + submissions.json + qa_pairs.json | weekly_report.md + dashboard_data.json |

## 一键运行
```bash
python demo/run_pipeline.py            # 端到端，输出到 evidence/
python -m unittest discover -s demo/wechat-class-manager/tests -v
```

## 诚实边界
- 本次未连接真实微信数据源、未接入 OpenClaw / Claude Code hook、未推送 GitHub。
- Skill 以「标准 SKILL.md + 可独立运行 CLI」形式提供；"被特定 runtime 自动识别并调用" 未实测。
- 详见 `../evidence/验收记录.md`。
