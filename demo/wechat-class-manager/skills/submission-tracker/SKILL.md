---
name: submission-tracker
description: 提交检测 + 附件完整性检查 + 学生×挑战矩阵
triggers:
  - "submission tracker"
parent_skill: wechat-class-manager
version: 1.0.0
---

# submission-tracker

## 职责
提交检测 + 附件完整性检查 + 学生×挑战矩阵

## 输入
`classified.jsonl, challenge_refs.json`

## 输出
`submissions.json`

## 依赖
- Python 3.9+ 标准库；无第三方包
- 上游实现：`demo/submission_detector.py`（本 Skill 只做薄封装，不复制逻辑）

## 调用
```bash
python demo/wechat-class-manager/skills/submission-tracker/tracker.py --help
```
或在 Agent Runtime 中按 parent SKILL.md 的 IO 表路由。

## 边界
不访问真实微信数据库；默认数据源为合成脱敏样本。真实数据源需在 wechat-bridge 显式指定。
