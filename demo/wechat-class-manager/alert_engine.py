"""Level 4 (Platinum): Alert Engine —— 基于规则的异常检测 + KSTAR ΔE 学习信号。

5 条规则（任务书要求 >= 3 种可正确触发）：
  A deadline_warning        距 deadline <= 3 天仍未提交
  B silent_student          最近 3 天零发言（此前有发言）
  C low_submission_rate     某挑战提交率 < 30%
  D activity_drop           前后半窗发言量下降 > 50%（ΔE 偏差）
  E missing_attachment      提交缺 AI 日志等必要附件

`--as-of` 允许指定模拟时间点以触发 deadline 规则；会在结果里明确标注 simulated，
不把它表述为真实当天。

用法：python alert_engine.py --as-of 2026-11-18 --output evidence/alerts.json
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wcm_common import (EVIDENCE, load_challenges, load_group_config,  # noqa: E402
                        load_json, load_jsonl, parse_ts, save_json)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_store import PropertyGraph  # noqa: E402

RULES = {
    "deadline_warning": "距 deadline <=3 天且该挑战仍有未提交学生",
    "silent_student": "最近 3 天零发言且此前有发言",
    "low_submission_rate": "挑战提交率 < 30%",
    "activity_drop": "后半窗发言量相对前半窗下降 > 50% (KSTAR ΔE)",
    "missing_attachment": "提交缺 AI 日志等必要附件",
}


def run_alerts(graph, messages, submissions_payload, as_of=None):
    cfg = load_challenges()
    group = load_group_config()
    rules_cfg = group.get("alert_rules", {})
    deadline_days = rules_cfg.get("deadline_days", 3)
    silent_days = rules_cfg.get("silent_days", 7)
    rate_threshold = rules_cfg.get("submission_rate_threshold", 0.30)

    stamps = [parse_ts(m["timestamp"]) for m in messages if m.get("timestamp")]
    if not stamps:
        raise SystemExit("无消息时间戳，无法计算预警")
    window_start, window_end = min(stamps), max(stamps)
    as_of_dt = datetime.fromisoformat(as_of) if as_of else window_end
    simulated = as_of is not None
    span = (window_end - window_start).total_seconds()
    mid = window_start.timestamp() + span / 2
    recent_cut = window_end.timestamp() - min(silent_days, 3) * 86400
    silent_cut = window_end.timestamp() - silent_days * 86400

    per_student = defaultdict(lambda: {"first": [], "second": [], "recent": 0,
                                       "total": 0, "name": ""})
    for m in messages:
        sid = m["sender"]["wechat_id"]
        t = parse_ts(m["timestamp"]).timestamp()
        p = per_student[sid]
        p["name"] = m["sender"]["nickname"]
        p["total"] += 1
        (p["first"] if t < mid else p["second"]).append(m["msg_id"])
        if t >= recent_cut:
            p["recent"] += 1

    students = graph.nodes["Student"]
    total_students = len(students)
    submitted_by_challenge = defaultdict(set)
    for s in submissions_payload.get("submissions", []):
        submitted_by_challenge[s["challenge"]].add(s.get("wechat_id", s["student"]))

    alerts = []

    def emit(rule, severity, message, data):
        alerts.append({"rule": rule, "severity": severity,
                       "message": message, "data": data})

    # A deadline_warning
    for c in cfg["challenges"]:
        due = datetime.fromisoformat(c["due_date"])
        days_left = (due - as_of_dt).days
        if 0 <= days_left <= deadline_days:
            done = submitted_by_challenge.get(c["id"], set())
            missing = [n.get("nickname", k) for k, n in students.items() if k not in done]
            emit("deadline_warning", "high",
                 "%s 距截止仅 %d 天，仍有 %d 人未提交" % (c["id"], days_left, len(missing)),
                 {"challenge": c["id"], "days_left": days_left,
                  "missing_count": len(missing), "missing_sample": missing[:5]})

    # B silent_student（最近 3 天零发言）
    for sid, p in per_student.items():
        if p["total"] >= 2 and p["recent"] == 0:
            emit("silent_student", "medium",
                 "%s 最近 3 天零发言，此前共 %d 条" % (p["name"], p["total"]),
                 {"wechat_id": sid, "total_messages": p["total"],
                  "last_window_days": 3})

    # C low_submission_rate
    for c in cfg["challenges"]:
        n = len(submitted_by_challenge.get(c["id"], set()))
        rate = n / total_students if total_students else 0
        if rate < rate_threshold:
            emit("low_submission_rate", "high",
                 "%s 提交率 %.1f%% 低于 %.0f%% 阈值" %
                 (c["id"], rate * 100, rate_threshold * 100),
                 {"challenge": c["id"], "submitted": n,
                  "total_students": total_students, "rate": round(rate, 4)})

    # D activity_drop (ΔE)
    for sid, p in per_student.items():
        f, s = len(p["first"]), len(p["second"])
        if f >= 4 and s < f * 0.5:
            emit("activity_drop", "medium",
                 "%s 活跃度下降：前半窗 %d 条 -> 后半窗 %d 条" % (p["name"], f, s),
                 {"wechat_id": sid, "first_half": f, "second_half": s,
                  "delta": s - f})

    # E missing_attachment
    for item in submissions_payload.get("missing", []):
        emit("missing_attachment", "medium",
             "%s 的 %s 提交缺少 %s" %
             (item["student"], item["challenge"], item["item"]), item)

    counts = Counter(a["rule"] for a in alerts)
    return {
        "as_of": as_of_dt.isoformat(),
        "simulated_as_of": simulated,
        "data_window": [window_start.isoformat(), window_end.isoformat()],
        "rules": RULES,
        "rule_counts": {r: counts.get(r, 0) for r in RULES},
        "triggered_rule_types": sum(1 for r in RULES if counts.get(r, 0) > 0),
        "total_alerts": len(alerts),
        "alerts": alerts,
        "_note": ("预警基于合成脱敏样本计算；deadline 规则使用模拟时间点，"
                  "不构成真实课程提醒。")
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="班级异常预警引擎")
    ap.add_argument("--input", default=str(EVIDENCE / "classified.jsonl"),
                    help="已分类消息 JSONL")
    ap.add_argument("--graph", default=str(EVIDENCE / "graph.json"))
    ap.add_argument("--submissions", default=str(EVIDENCE / "submissions.json"))
    ap.add_argument("--as-of", default=None, help="模拟时间点 YYYY-MM-DD")
    ap.add_argument("--output", default=str(EVIDENCE / "alerts.json"))
    ap.add_argument("--group", default=None, help="兼容 Skill 转发")
    ap.add_argument("--days", type=int, default=None, help="兼容 Skill 转发")
    ap.add_argument("--wechat-id", default=None, help="兼容 Skill 转发")
    args = ap.parse_args(argv)

    result = run_alerts(PropertyGraph.load(args.graph), load_jsonl(args.input),
                        load_json(args.submissions), args.as_of)
    save_json(args.output, result)
    print("[alert] types=%d total=%d counts=%s as_of=%s simulated=%s"
          % (result["triggered_rule_types"], result["total_alerts"],
             result["rule_counts"], result["as_of"], result["simulated_as_of"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
