---
name: class-report
description: 自动生成周报与看板数据
triggers:
  - "class report"
parent_skill: wechat-class-manager
version: 1.0.0
---

# class-report

## 职责
自动生成周报与看板数据

## 输入
`graph.json, submissions.json, qa_pairs.json`

## 输出
`weekly_report.md, dashboard_data.json`

## 依赖
- Python 3.9+ 标准库；无第三方包
- 上游实现：`demo/report_engine.py`（本 Skill 只做薄封装，不复制逻辑）

## 调用
```bash
python demo/wechat-class-manager/skills/class-report/reporter.py --help
```
或在 Agent Runtime 中按 parent SKILL.md 的 IO 表路由。

## 边界
不访问真实微信数据库；默认数据源为合成脱敏样本。真实数据源需在 wechat-bridge 显式指定。
