---
name: student-profile
description: 从群互动构建学生能力画像
triggers:
  - "student profile"
parent_skill: wechat-class-manager
version: 1.0.0
---

# student-profile

## 职责
从群互动构建学生能力画像

## 输入
`graph.json, wechat_id`

## 输出
`profile JSON`

## 依赖
- Python 3.9+ 标准库；无第三方包
- 上游实现：`demo/graph_store.py`（本 Skill 只做薄封装，不复制逻辑）

## 调用
```bash
python demo/wechat-class-manager/skills/student-profile/profiler.py --help
```
或在 Agent Runtime 中按 parent SKILL.md 的 IO 表路由。

## 边界
不访问真实微信数据库；默认数据源为合成脱敏样本。真实数据源需在 wechat-bridge 显式指定。
