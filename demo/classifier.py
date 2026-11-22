"""Level 2 (Silver): 消息意图分类器（规则引擎 / Bronze-Silver 实现）。

7 类意图：submission / question / answer / discussion / announcement / resource / social
零第三方依赖；可独立运行，也可作为 pipeline 的一站。

取舍说明（见 卢怡然_C8_拿来说明.md）：
- 采用规则引擎而非 LLM 分类：本机无稳定 LLM API 预算，且规则可复现、可审计、可离线。
- 预留 `llm_classify` 接口位，但**不实现、不假装调用过 LLM**。

用法：
  python classifier.py --input messages.jsonl --output classified.jsonl \
      [--labels data/synthetic_labels.json --metrics metrics.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcm_common import (EVIDENCE, INTENTS, SUBMISSION_RE, load_json,  # noqa: E402
                        load_jsonl, save_json, save_jsonl)

QUESTION_RE = re.compile(r"[?？]|请问|怎么|为什么|如何|能不能|是不是|吗[？?]?$|求问|该不该")
ANNOUNCE_RE = re.compile(r"@全体|通知|截止|deadline|请于|务必", re.I)
RESOURCE_RE = re.compile(r"https?://|www\.|推荐|分享|资料|链接|模板", re.I)
CHALLENGE_TOKEN_RE = re.compile(r"C\d+[A-Z]?H?", re.I)
EXPLAIN_RE = re.compile(r"因为|原因是|要先|建议|可以|按模板|对不上|常见问题", re.I)


def classify(msg, question_ids=None):
    """返回 (intent, confidence, reason)。question_ids 用于 reply_to 精判。"""
    content = msg.get("content", "") or ""
    mtype = msg.get("type", "text")
    media = msg.get("media_ref") or ""
    reply_to = msg.get("reply_to")

    # 1) 提交：文件 + 命名规范
    if mtype == "file":
        candidate = Path(content or media).name
        if SUBMISSION_RE.match(candidate):
            return "submission", 0.95, "file + 命名规范匹配"

    # 2) 公告：老师 + 通知信号
    if ANNOUNCE_RE.search(content) and msg.get("sender", {}).get("wechat_id", "").startswith("t"):
        return "announcement", 0.90, "导师 + 公告关键词"

    # 3) 回答：回复链指向 question，或有明确解释性结构
    if reply_to and (question_ids is None or reply_to in question_ids):
        return "answer", 0.88, "reply_to 指向提问消息"
    if reply_to and EXPLAIN_RE.search(content):
        return "answer", 0.75, "回复 + 解释性措辞"

    # 4) 提问
    if QUESTION_RE.search(content):
        return "question", 0.85, "疑问词/问号"

    # 5) 资源
    if mtype == "link" or RESOURCE_RE.search(content):
        return "resource", 0.80, "链接或资源关键词"

    # 6) 讨论：提及挑战且有一定长度
    if CHALLENGE_TOKEN_RE.search(content) and len(content) >= 12:
        return "discussion", 0.65, "挑战编号 + 长文本"
    if len(content) >= 24:
        return "discussion", 0.55, "长文本讨论"

    return "social", 0.60, "默认闲聊"


def classify_stream(messages):
    question_ids = {m["msg_id"] for m in messages
                    if QUESTION_RE.search(m.get("content", "") or "")}
    out = []
    for m in messages:
        intent, conf, reason = classify(m, question_ids)
        out.append({
            "msg_id": m["msg_id"],
            "timestamp": m["timestamp"],
            "sender": m["sender"],
            "type": m["type"],
            "content": m["content"],
            "media_ref": m["media_ref"],
            "reply_to": m["reply_to"],
            "intent": intent,
            "confidence": conf,
            "reason": reason,
        })
    return out


def evaluate(rows, labels):
    """labels: {msg_id: intent}。返回逐类与总体准确率。"""
    correct = 0
    total = 0
    per = {}
    confusion = {}
    for r in rows:
        gold = labels.get(r["msg_id"])
        if gold is None:
            continue
        total += 1
        hit = gold == r["intent"]
        correct += int(hit)
        per.setdefault(gold, [0, 0])
        per[gold][1] += 1
        per[gold][0] += int(hit)
        if not hit:
            key = "%s->%s" % (gold, r["intent"])
            confusion[key] = confusion.get(key, 0) + 1
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "per_intent": {k: {"correct": v[0], "total": v[1],
                           "accuracy": round(v[0] / v[1], 4)}
                       for k, v in sorted(per.items())},
        "confusion": confusion,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="群消息意图分类")
    ap.add_argument("--input", default=str(EVIDENCE / "sample_output.jsonl"))
    ap.add_argument("--output", default=str(EVIDENCE / "classified.jsonl"))
    ap.add_argument("--labels", default=None)
    ap.add_argument("--metrics", default=str(EVIDENCE / "classifier_metrics.json"))
    args = ap.parse_args(argv)

    msgs = load_jsonl(args.input)
    rows = classify_stream(msgs)
    save_jsonl(args.output, rows)
    result = {"rows": len(rows), "intent_distribution": {}}
    for i in INTENTS:
        result["intent_distribution"][i] = sum(1 for r in rows if r["intent"] == i)
    if args.labels:
        payload = load_json(args.labels)
        labels = payload.get("labels", payload)
        ev = evaluate(rows, labels)
        result["evaluation"] = ev
        result["evaluation_note"] = (
            "合成集标签与规则同源，此准确率仅证明实现自洽；"
            "手写变体集结果见 tests/test_all.py 与 evidence/验收记录.md"
        )
        print("[classifier] accuracy=%.4f (%d/%d)" %
              (ev["accuracy"], ev["correct"], ev["total"]))
    save_json(args.metrics, result)
    print("[classifier] rows=%d dist=%s" % (len(rows), result["intent_distribution"]))
    print("[classifier] output=%s metrics=%s" % (args.output, args.metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
