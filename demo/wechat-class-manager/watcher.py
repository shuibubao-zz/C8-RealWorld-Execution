"""Level 4 (Platinum): Watcher Agent —— 增量处理新消息，按 msg_id 去重。

验收点：Watcher 能增量处理新消息，不重复处理（同一批次内重复 + 跨批次 checkpoint 去重）。

用法：
  python watcher.py --input data/synthetic_messages_increment.jsonl \
      --graph evidence/graph.json --checkpoint state/checkpoint.json \
      --output evidence/watcher_result.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from classifier import classify_stream  # noqa: E402
from wcm_common import EVIDENCE, ROOT, load_json, load_jsonl, save_json  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_store import PropertyGraph  # noqa: E402


def load_checkpoint(path):
    p = Path(path)
    if not p.exists():
        return {"processed_ids": [], "last_timestamp": None, "runs": 0}
    return load_json(path)


def process(graph, messages, checkpoint_path, classify=True):
    cp = load_checkpoint(checkpoint_path)
    seen = set(cp.get("processed_ids", []))
    fresh, duplicate = [], []
    for m in messages:
        if m["msg_id"] in seen:
            duplicate.append(m["msg_id"])
        else:
            seen.add(m["msg_id"])
            fresh.append(m)

    rows = classify_stream(fresh) if classify else fresh
    inserted = []
    for r in rows:
        mid = r["msg_id"]
        if graph.get_node("Message", mid):
            # checkpoint 未记录但图中已存在：仍算重复，不计入新处理
            duplicate.append(mid)
            continue
        inserted.append(r)
        sid = r["sender"]["wechat_id"]
        graph.add_node("Student", sid, {"nickname": r["sender"]["nickname"]})
        graph.add_node("Message", mid, {
            "timestamp": r["timestamp"], "content": r["content"],
            "type": r["type"], "wechat_msg_id": mid, "intent": r.get("intent"),
            "sender": sid,
        })
        graph.add_edge("SENT", "Student:" + sid, "Message:" + mid)
        node = graph.get_node("Student", sid)
        graph.update_node("Student", sid, {
            "message_count": node.get("message_count", 0) + 1,
            "last_active": r["timestamp"],
        })

    cp = {
        "processed_ids": sorted(seen),
        "last_timestamp": max((r["timestamp"] for r in inserted),
                              default=cp.get("last_timestamp")),
        "runs": cp.get("runs", 0) + 1,
        "last_new_count": len(inserted),
        "last_duplicate_count": len(duplicate),
    }
    save_json(checkpoint_path, cp)
    return {
        "input_count": len(messages),
        "new_processed": len(inserted),
        "duplicates_skipped": len(duplicate),
        "duplicate_ids": duplicate,
        "new_ids": [r["msg_id"] for r in inserted],
        "checkpoint_runs": cp["runs"],
        "graph_counts": graph.counts(),
        "intent_distribution": dict(Counter(r.get("intent") for r in inserted)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Watcher 增量消息处理")
    ap.add_argument("--input", default=str(ROOT / "data/synthetic_messages_increment.jsonl"))
    ap.add_argument("--graph", default=str(EVIDENCE / "graph.json"))
    ap.add_argument("--checkpoint", default=str(ROOT / "state/checkpoint.json"))
    ap.add_argument("--output", default=str(EVIDENCE / "watcher_result.json"))
    ap.add_argument("--save-graph", action="store_true")
    ap.add_argument("--group", default=None, help="兼容 Skill 转发")
    ap.add_argument("--days", type=int, default=None, help="兼容 Skill 转发")
    ap.add_argument("--wechat-id", default=None, help="兼容 Skill 转发")
    args = ap.parse_args(argv)

    g = PropertyGraph.load(args.graph)
    result = process(g, load_jsonl(args.input), args.checkpoint)
    result["graph"] = args.graph
    result["_note"] = "增量样本为合成数据；4 条重复 msg_id 用于验证去重。"
    save_json(args.output, result)
    if args.save_graph:
        g.save(args.graph)
    print("[watcher] input=%d new=%d duplicates=%d runs=%d"
          % (result["input_count"], result["new_processed"],
             result["duplicates_skipped"], result["checkpoint_runs"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
