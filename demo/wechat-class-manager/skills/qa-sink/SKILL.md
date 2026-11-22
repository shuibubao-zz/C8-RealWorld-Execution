---
name: qa-sink
description: Q&A 对提取与课程 FAQ 沉淀
triggers:
  - "qa sink"
parent_skill: wechat-class-manager
version: 1.0.0
---

# qa-sink

## 职责
Q&A 对提取与课程 FAQ 沉淀

## 输入
`classified.jsonl`

## 输出
`qa_pairs.json`

## 依赖
- Python 3.9+ 标准库；无第三方包
- 上游实现：`demo/qa_extractor.py`（本 Skill 只做薄封装，不复制逻辑）

## 调用
```bash
python demo/wechat-class-manager/skills/qa-sink/sink.py --help
```
或在 Agent Runtime 中按 parent SKILL.md 的 IO 表路由。

## 边界
不访问真实微信数据库；默认数据源为合成脱敏样本。真实数据源需在 wechat-bridge 显式指定。
