"""Level 2 (Silver): 提交检测器 —— 文件 + 命名规范 -> Submission 记录 + 完整性检查。

任务书要求「检查完整性：AI 日志是否提交？必要附件是否齐全？」：
- 主提交：姓名_C编号_描述.扩展名
- 配套附件：姓名_C编号_AI日志.md（按 学生×挑战 归并到主提交，不单独计一次提交）

输出 submissions.json（学生×挑战矩阵 + missing + alerts）。
用法：python submission_detector.py [--input classified.jsonl] [--refs challenge_refs.json]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcm_common import (EVIDENCE, SUBMISSION_RE, load_challenges,  # noqa: E402
                        load_json, load_jsonl, save_json)

ATTACH_MARKERS = ("AI日志", "AILog", "ai_log")
REQUIRED_ATTACHMENTS = ("AI日志",)


def detect(messages, refs=None, cfg=None):
    cfg = cfg or load_challenges()
    valid_ids = {c["id"] for c in cfg["challenges"]}
    ref_map = {}
    if refs:
        payload = load_json(refs) if not isinstance(refs, dict) else refs
        ref_map = {r["msg_id"]: r.get("challenge_ref")
                   for r in payload.get("refs", payload if isinstance(payload, list) else [])}

    records = {}
    attachments = {}
    skipped = []
    for m in messages:
        if m.get("type") != "file":
            continue
        name = Path(m.get("content") or m.get("media_ref") or "").name
        mt = SUBMISSION_RE.match(name)
        if not mt:
            skipped.append({"msg_id": m["msg_id"], "reason": "命名规范不匹配", "file": name})
            continue
        student = mt.group("name")
        cid = mt.group("challenge")
        desc = mt.group("desc")
        if cid not in valid_ids:
            skipped.append({"msg_id": m["msg_id"], "reason": "未知挑战编号", "file": name})
            continue
        key = (student, cid)
        if any(k in desc for k in ATTACH_MARKERS):
            attachments.setdefault(key, []).append(m)
            continue
        rec = records.get(key)
        if rec is None:
            rec = {
                "submission_id": "SUB-%03d" % (len(records) + 1),
                "student": student,
                "wechat_id": m["sender"]["wechat_id"],
                "challenge": cid,
                "challenge_ref_from_linker": ref_map.get(m["msg_id"]),
                "timestamp": m["timestamp"],
                "files": [],
                "level_claimed": None,
                "level_note": "样本文件名未声明等级，未做推断",
                "status": "received",
                "msg_ids": [],
            }
            records[key] = rec
        rec["files"].append({"name": name, "type": mt.group("ext"),
                             "path": m.get("media_ref")})
        rec["msg_ids"].append(m["msg_id"])

    missing, alerts, matrix = [], [], {}
    for (student, cid), rec in records.items():
        found = []
        for att in attachments.get((student, cid), []):
            found.append(Path(att.get("content") or "").name)
        rec["attachments_found"] = found
        absent = [r for r in REQUIRED_ATTACHMENTS
                  if not any(r in f for f in found)]
        rec["missing_items"] = absent
        rec["complete"] = not absent
        matrix.setdefault(student, {})[cid] = "complete" if not absent else "incomplete"
        for item in absent:
            missing.append({"student": student, "challenge": cid,
                            "item": item, "submission_id": rec["submission_id"]})
            alerts.append({"type": "missing_attachment", "student": student,
                           "challenge": cid, "item": item,
                           "message": "%s 的 %s 提交缺少 %s" % (student, cid, item)})

    submissions = sorted(records.values(), key=lambda r: r["submission_id"])
    stats = {
        "submission_events": len(submissions),
        "complete": sum(1 for r in submissions if r["complete"]),
        "incomplete": sum(1 for r in submissions if not r["complete"]),
        "students": len({r["student"] for r in submissions}),
        "challenges": len({r["challenge"] for r in submissions}),
        "attachments_merged": sum(len(v) for v in attachments.values()),
        "files_skipped": len(skipped),
        "by_challenge": dict(Counter(r["challenge"] for r in submissions)),
    }
    return {"submissions": submissions, "matrix": matrix, "missing": missing,
            "alerts": alerts, "skipped": skipped, "stats": stats}


def main(argv=None):
    ap = argparse.ArgumentParser(description="提交检测与完整性检查")
    ap.add_argument("--input", default=str(EVIDENCE / "classified.jsonl"))
    ap.add_argument("--refs", default=str(EVIDENCE / "challenge_refs.json"))
    ap.add_argument("--output", default=str(EVIDENCE / "submissions.json"))
    args = ap.parse_args(argv)
    result = detect(load_jsonl(args.input), refs=args.refs)
    save_json(args.output, result)
    print("[detector] events=%d complete=%d incomplete=%d skipped=%d output=%s"
          % (result["stats"]["submission_events"], result["stats"]["complete"],
             result["stats"]["incomplete"], result["stats"]["files_skipped"], args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
