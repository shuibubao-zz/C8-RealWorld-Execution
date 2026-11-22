---
name: wechat-bridge
description: 数据桥接：把群消息规范化为 7 字段 JSON Lines
triggers:
  - "wechat bridge"
parent_skill: wechat-class-manager
version: 1.0.0
---

# wechat-bridge

## 职责
数据桥接：把群消息规范化为 7 字段 JSON Lines

## 输入
`group, days, source`

## 输出
`messages.jsonl`

## 依赖
- Python 3.9+ 标准库；无第三方包
- 上游实现：`demo/wechat_bridge.py`（本 Skill 只做薄封装，不复制逻辑）

## 调用
```bash
python demo/wechat-class-manager/skills/wechat-bridge/bridge.py --help
```
或在 Agent Runtime 中按 parent SKILL.md 的 IO 表路由。

## 边界
不访问真实微信数据库；默认数据源为合成脱敏样本。真实数据源需在 wechat-bridge 显式指定。
