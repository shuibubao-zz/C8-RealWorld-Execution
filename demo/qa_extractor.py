"""Level 2 (Silver): Q&A 提取器 —— 从消息流沉淀课程 FAQ。

两种配对策略（先精确后兜底）：
  1) reply_to 精确指向某条 question 消息（matched_by=reply_to）
  2) 同一时间窗（30 分钟）内、未配对的 answer 消息，按挑战标签最近匹配（matched_by=time_window）

quality_score 是启发式可解释打分，不是模型评分，公式写明在 result 里。
用法：python qa_extractor.py --input classified.jsonl --output qa_pairs.json
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcm_common import EVIDENCE, load_jsonl, parse_ts, save_json  # noqa: E402

TOKEN_RE = re.compile(r"(C\d+[A-Z]?H?)", re.I)
EXPLAIN_RE = re.compile(r"因为|原因是|要|建议|可以|按模板|先|对不上", re.I)
WINDOW_MINUTES = 30

QUALITY_FORMULA = (
    "0.35 基础 + 0.25(答案长度>=15) + 0.20(含解释性措辞) "
    "+ 0.20(问答共享挑战标签)；上限 1.0。启发式打分，非模型评分。"
)


def _score(q, a, qtags, atags):
    s = 0.35
    if len(a) >= 15:
        s += 0.25
    if EXPLAIN_RE.search(a):
        s += 0.20
    if set(qtags) & set(atags):
        s += 0.20
    return round(min(s, 1.0), 2)


def extract(messages):
    by_id = {m["msg_id"]: m for m in messages}
    questions = [m for m in messages if m.get("intent") == "question"]
    answers = [m for m in messages if m.get("intent") == "answer"]
    used = set()
    pairs = []

    # 策略 1：reply_to 精确配对
    for q in questions:
        for a in answers:
            if a["msg_id"] in used:
                continue
            if a.get("reply_to") == q["msg_id"]:
                used.add(a["msg_id"])
                qtags = TOKEN_RE.findall(q["content"])
                atags = TOKEN_RE.findall(a["content"])
                pairs.append(_make(q, a, qtags, atags, "reply_to"))
                break

    # 策略 2：时间窗兜底
    unmatched_q = [q for q in questions
                   if q["msg_id"] not in {p["question_id"] for p in pairs}]
    for q in unmatched_q:
        qt = parse_ts(q["timestamp"])
        qtags = TOKEN_RE.findall(q["content"])
        candidates = []
        for a in answers:
            if a["msg_id"] in used:
                continue
            delta = (parse_ts(a["timestamp"]) - qt).total_seconds() / 60
            if 0 <= delta <= WINDOW_MINUTES:
                atags = TOKEN_RE.findall(a["content"])
                candidates.append((len(set(qtags) & set(atags)), -abs(delta), a, atags))
        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            _, _, a, atags = candidates[0]
            used.add(a["msg_id"])
            pairs.append(_make(q, a, qtags, atags, "time_window"))

    pairs.sort(key=lambda p: p["timestamp"])
    stats = {
        "pairs": len(pairs),
        "questions": len(questions),
        "answers": len(answers),
        "matched_by": dict(Counter(p["matched_by"] for p in pairs)),
        "avg_quality": round(sum(p["quality_score"] for p in pairs) / len(pairs), 3)
        if pairs else 0,
        "topics": dict(Counter(t for p in pairs for t in p["topic_tags"])),
        "window_minutes": WINDOW_MINUTES,
    }
    return {"pairs": pairs, "stats": stats, "quality_formula": QUALITY_FORMULA}


def _make(q, a, qtags, atags, matched_by):
    return {
        "question_id": q["msg_id"],
        "question": q["content"],
        "asked_by": q["sender"]["nickname"],
        "answer_id": a["msg_id"],
        "answer": a["content"],
        "answered_by": a["sender"]["nickname"],
        "timestamp": q["timestamp"],
        "topic_tags": sorted(set(qtags) | set(atags)),
        "quality_score": _score(q["content"], a["content"], qtags, atags),
        "matched_by": matched_by,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Q&A 对提取")
    ap.add_argument("--input", default=str(EVIDENCE / "classified.jsonl"))
    ap.add_argument("--output", default=str(EVIDENCE / "qa_pairs.json"))
    args = ap.parse_args(argv)
    result = extract(load_jsonl(args.input))
    save_json(args.output, result)
    print("[qa_extractor] pairs=%d avg_quality=%s matched=%s output=%s"
          % (result["stats"]["pairs"], result["stats"]["avg_quality"],
             result["stats"]["matched_by"], args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
