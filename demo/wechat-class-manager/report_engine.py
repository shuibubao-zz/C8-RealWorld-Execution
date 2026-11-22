"""Level 4 (Platinum): Report Engine —— 周报 Markdown + Dashboard 数据（>=5 维度）。

产出：
  weekly_report.md        可直接发群 / 转公众号
  dashboard_data.json     机器可读
  dashboard/dashboard_data.js  （window.C8_DASHBOARD，令 index.html 双击即可离线打开）

用法：python report_engine.py --output evidence/weekly_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wcm_common import EVIDENCE, PKG, load_json, load_jsonl, save_json  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_store import PropertyGraph  # noqa: E402

DASH_DIR = PKG / "dashboard"


def _bar(rate, width=20):
    n = max(0, min(width, int(round(rate * width))))
    return "█" * n + "░" * (width - n)


def build_report(graph, messages, submissions_payload, qa_payload, alerts_payload):
    students = graph.nodes["Student"]
    challenges = graph.nodes["Challenge"]
    total_students = len(students)
    intent_dist = Counter(m.get("intent") for m in messages)
    daily = Counter(m["timestamp"][:10] for m in messages)

    submitted = defaultdict(set)
    for s in submissions_payload.get("submissions", []):
        submitted[s["challenge"]].add(s.get("wechat_id", s["student"]))
    completion = []
    for cid, node in challenges.items():
        n = len(submitted.get(cid, set()))
        rate = n / total_students if total_students else 0
        completion.append({"challenge": cid, "name": node.get("name_cn", ""),
                           "submitted": n, "total": total_students, "rate": round(rate, 4)})
    completion.sort(key=lambda x: x["challenge"])

    top_active = [
        {"name": n.get("nickname", k), "messages": n.get("message_count", 0),
         "questions": n.get("question_count", 0), "answers": n.get("answer_count", 0),
         "submissions": n.get("submission_count", 0)}
        for k, n in sorted(students.items(),
                           key=lambda kv: kv[1].get("message_count", 0), reverse=True)[:5]
    ]
    qa_topics = Counter(t for p in qa_payload.get("pairs", [])
                        for t in p.get("topic_tags", []))
    best_qa = sorted(qa_payload.get("pairs", []),
                     key=lambda p: p.get("quality_score", 0), reverse=True)[:3]
    alert_counts = alerts_payload.get("rule_counts", {})

    # ---------- Markdown 周报 ----------
    lines = [
        "# Elite20 班级周报（C8 Level 4 Report Engine 自动生成）", "",
        "> **数据来源：合成脱敏样本，非真实微信群数据。** 本机未解密/未读取真实聊天记录。",
        "> 生成方式：`python demo/wechat-class-manager/report_engine.py`，规则统计，无 LLM 参与。",
        "> 统计窗口：%s ~ %s" % (min(daily) if daily else "-", max(daily) if daily else "-"),
        "", "## 一、本周概览", "",
        "| 指标 | 数值 |", "|---|---|",
        "| 学生数 | %d |" % total_students,
        "| 挑战数 | %d |" % len(challenges),
        "| 消息数 | %d |" % len(messages),
        "| 新增提交 | %d 件，涉及 %d 个挑战 |" %
        (len(submissions_payload.get("submissions", [])), len(submitted)),
        "| 完整提交 / 缺附件 | %d / %d |" %
        (submissions_payload.get("stats", {}).get("complete", 0),
         submissions_payload.get("stats", {}).get("incomplete", 0)),
        "| Q&A 沉淀 | %d 对 |" % len(qa_payload.get("pairs", [])),
        "| 触发预警 | %d 条（%d 类规则） |" %
        (alerts_payload.get("total_alerts", 0),
         alerts_payload.get("triggered_rule_types", 0)),
        "",
        "## 二、最活跃学生 Top 5（发言量 + 回答量）", "",
        "| 排名 | 学生 | 发言 | 提问 | 回答 | 提交 |", "|---|---|---|---|---|---|",
    ]
    for i, s in enumerate(top_active, 1):
        lines.append("| %d | %s | %d | %d | %d | %d |" %
                     (i, s["name"], s["messages"], s["questions"],
                      s["answers"], s["submissions"]))
    lines += ["", "## 三、各挑战完成率", "", "```"]
    for c in completion:
        lines.append("%-5s %s %5.1f%%  (%d/%d)  %s" %
                     (c["challenge"], _bar(c["rate"]), c["rate"] * 100,
                      c["submitted"], c["total"], c["name"]))
    lines += ["```", "", "## 四、最佳 Q&A 对（启发式质量分 Top 3）", ""]
    if best_qa:
        for i, p in enumerate(best_qa, 1):
            lines += ["%d. **Q**（%s）：%s" % (i, p["asked_by"], p["question"]),
                      "   - **A**（%s）：%s" % (p["answered_by"], p["answer"]),
                      "   - 质量分 %.2f ｜ 标签 %s ｜ 匹配方式 %s" %
                      (p["quality_score"], "、".join(p["topic_tags"]) or "-", p["matched_by"]),
                      ""]
    else:
        lines += ["（无 Q&A 数据）", ""]
    lines += ["## 五、消息意图分布", "", "| 意图 | 条数 |", "|---|---|"]
    for k, v in sorted(intent_dist.items(), key=lambda kv: -kv[1]):
        lines.append("| %s | %d |" % (k, v))
    lines += ["", "## 六、预警摘要", "", "| 规则 | 条数 |", "|---|---|"]
    for k, v in alert_counts.items():
        lines.append("| %s | %d |" % (k, v))
    lines += ["", "## 七、每日消息趋势", "", "```"]
    for day in sorted(daily):
        lines.append("%s  %-3d %s" % (day, daily[day], "█" * min(30, daily[day])))
    lines += ["```", "", "---", "",
              "*报告由代码生成，所有数字均来自 evidence/ 下的机器可读文件，可用 sha256 复核。*"]

    data = {
        "meta": {"synthetic": True, "generated_by": "report_engine.py",
                 "_note": "合成脱敏样本，非真实班级数据"},
        "dimensions": {
            "kpi": {"students": total_students, "challenges": len(challenges),
                    "messages": len(messages),
                    "submissions": len(submissions_payload.get("submissions", [])),
                    "qa_pairs": len(qa_payload.get("pairs", [])),
                    "alerts": alerts_payload.get("total_alerts", 0)},
            "intent_distribution": dict(intent_dist),
            "challenge_completion": completion,
            "top_active_students": top_active,
            "daily_message_trend": dict(sorted(daily.items())),
            "qa_topic_distribution": dict(qa_topics),
            "alert_rule_counts": alert_counts,
            "student_profiles": [
                {"name": n.get("nickname", k), "messages": n.get("message_count", 0),
                 "answers": n.get("answer_count", 0),
                 "submissions": n.get("submission_count", 0),
                 "skill_tags": n.get("skill_tags", [])}
                for k, n in sorted(students.items(),
                                   key=lambda kv: kv[1].get("message_count", 0),
                                   reverse=True)[:10]
            ],
        },
        "dimension_count": 8,
    }
    return "\n".join(lines) + "\n", data


def main(argv=None):
    ap = argparse.ArgumentParser(description="周报与看板数据生成")
    ap.add_argument("--input", default=str(EVIDENCE / "classified.jsonl"))
    ap.add_argument("--graph", default=str(EVIDENCE / "graph.json"))
    ap.add_argument("--submissions", default=str(EVIDENCE / "submissions.json"))
    ap.add_argument("--qa", default=str(EVIDENCE / "qa_pairs.json"))
    ap.add_argument("--alerts", default=str(EVIDENCE / "alerts.json"))
    ap.add_argument("--output", default=str(EVIDENCE / "weekly_report.md"))
    ap.add_argument("--data-output", default=str(EVIDENCE / "dashboard_data.json"))
    ap.add_argument("--group", default=None, help="兼容 Skill 转发")
    ap.add_argument("--days", type=int, default=None, help="兼容 Skill 转发")
    ap.add_argument("--wechat-id", default=None, help="兼容 Skill 转发")
    args = ap.parse_args(argv)

    md, data = build_report(PropertyGraph.load(args.graph),
                            load_jsonl(args.input), load_json(args.submissions),
                            load_json(args.qa), load_json(args.alerts))
    Path(args.output).write_text(md, encoding="utf-8")
    save_json(args.data_output, data)
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    (DASH_DIR / "dashboard_data.js").write_text(
        "window.C8_DASHBOARD = " +
        json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    print("[report] dimensions=%d report=%s data=%s dashboard_js=%s"
          % (data["dimension_count"], args.output, args.data_output,
             DASH_DIR / "dashboard_data.js"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
