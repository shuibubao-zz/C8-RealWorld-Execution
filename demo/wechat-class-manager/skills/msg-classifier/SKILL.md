---
name: msg-classifier
description: 消息意图分类（7 类规则引擎）
triggers:
  - "msg classifier"
parent_skill: wechat-class-manager
version: 1.0.0
---

# msg-classifier

## 职责
消息意图分类（7 类规则引擎）

## 输入
`messages.jsonl`

## 输出
`classified.jsonl`

## 依赖
- Python 3.9+ 标准库；无第三方包
- 上游实现：`demo/classifier.py`（本 Skill 只做薄封装，不复制逻辑）

## 调用
```bash
python demo/wechat-class-manager/skills/msg-classifier/classifier.py --help
```
或在 Agent Runtime 中按 parent SKILL.md 的 IO 表路由。

## 边界
不访问真实微信数据库；默认数据源为合成脱敏样本。真实数据源需在 wechat-bridge 显式指定。
