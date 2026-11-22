"""Level 3 (Gold): 自然语言查询接口（老师用中文问，路由到图查询）。

支持的 6 类问题（任务书要求 >= 5 类）：
  1. student_submissions  「学生03 提交了哪些挑战？」
  2. missing_by_challenge 「C4B 还有谁没交？」
  3. top_active           「最近一周谁最活跃？」
  4. faq                  「关于 GitHub 的常见问题有哪些？」
  5. student_profile      「学生01 的画像是什么？」
  6. class_summary        「这周班级状态如何？」

规则路由（非 LLM）：可复现、可审计、零依赖、离线可跑。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_store import PropertyGraph  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wcm_common import EVIDENCE, save_json  # noqa: E402

CID_RE = re.compile(r"C\d+[A-Z]?H?", re.I)

DEMO_QUERIES = [
    "学生03 提交了哪些挑战？",
    "C4B 还有谁没交？",
    "最近一周谁最活跃？",
    "关于 C5 的常见问题有哪些？",
    "学生01 的画像是什么？",
    "这周班级状态如何？",
]


def _find_student(g, query):
    for key, node in g.nodes["Student"].items():
        if node.get("nickname") and node["nickname"] in query:
            return key, node
    m = re.search(r"\bs\d{2}\b", query, re.I)
    if m and g.get_node("Student", m.group(0).lower()):
        k = m.group(0).lower()
        return k, g.get_node("Student", k)
    return None, None


def _find_challenge(g, query):
    m = CID_RE.search(query)
    if m and g.get_node("Challenge", m.group(0).upper()):
        return m.group(0).upper()
    return None


def answer_query(g, query):
    q = query.strip()
    sid, snode = _find_student(g, q)
    cid = _find_challenge(g, q)

    # 1 学生提交
    if re.search(r"提交|交了|交过", q) and sid and not re.search(r"还有谁|没交|未提交", q):
        subs = [e for e in g.query_edges("SUBMITTED")
                if e["src"] == "Student:" + sid and e["dst"].startswith("Submission:")]
        rows = []
        for e in subs:
            s = g.get_node("Submission", e["dst"].split(":", 1)[1])
            to = g.query_edges("SUBMITTED", src=e["dst"])
            c = to[0]["dst"].split(":", 1)[1] if to else "?"
            rows.append({"challenge": c, "status": s.get("status"),
                         "complete": s.get("complete"), "files": [f["name"] for f in s.get("files", [])]})
        return {"query": q, "intent": "student_submissions", "data": rows,
                "answer": "%s 共提交 %d 项：%s" % (
                    snode["nickname"], len(rows),
                    "、".join("%s(%s)" % (r["challenge"], "完整" if r["complete"] else "缺附件")
                             for r in rows) or "无")}

    # 2 某挑战未交名单
    if re.search(r"还有谁|没交|未提交|缺交", q) and cid:
        submitted = {e["src"].split(":", 1)[1] for e in g.query_edges("SUBMITTED")
                     if e["dst"] == "Challenge:" + cid}
        missing = [n["nickname"] for k, n in g.nodes["Student"].items()
                   if k not in submitted]
        return {"query": q, "intent": "missing_by_challenge",
                "data": {"challenge": cid, "submitted_count": len(submitted),
                         "missing_count": len(missing), "missing": missing[:30]},
                "answer": "%s 已提交 %d 人，未提交 %d 人。未提交名单（前 30）：%s" % (
                    cid, len(submitted), len(missing), "、".join(missing[:30]))}

    # 3 活跃 Top5
    if re.search(r"最活跃|活跃度|发言最多", q):
        ranked = sorted(g.nodes["Student"].items(),
                        key=lambda kv: (kv[1].get("message_count", 0),
                                        kv[1].get("answer_count", 0)), reverse=True)[:5]
        rows = [{"name": n["nickname"], "messages": n.get("message_count", 0),
                 "answers": n.get("answer_count", 0)} for _, n in ranked]
        return {"query": q, "intent": "top_active", "data": rows,
                "answer": "发言量 Top5：" + "；".join(
                    "%s %d 条" % (r["name"], r["messages"]) for r in rows)}

    # 4 FAQ
    if re.search(r"常见问题|FAQ|问答|关于.*问题", q, re.I):
        kw = CID_RE.search(q)
        token = kw.group(0).upper() if kw else None
        pairs = []
        for key, p in g.nodes["QAPair"].items():
            if token is None or token in [t.upper() for t in p.get("topic_tags", [])]:
                pairs.append({"id": key, "question": p["question"],
                              "answer": p["answer"], "score": p["quality_score"]})
        pairs.sort(key=lambda x: x["score"], reverse=True)
        return {"query": q, "intent": "faq", "data": pairs[:10],
                "answer": "检索到 %d 条相关 Q&A，质量最高的 3 条：\n%s" % (
                    len(pairs), "\n".join("- Q: %s\n  A: %s" % (p["question"], p["answer"])
                                          for p in pairs[:3]))}

    # 5 学生画像
    if re.search(r"画像|强项|能力|表现", q) and sid:
        n = snode
        return {"query": q, "intent": "student_profile", "data": n,
                "answer": "%s：发言 %d 条，提问 %d 次，回答 %d 次，提交 %d 项，"
                          "关联挑战标签 %s。%s" % (
                              n["nickname"], n.get("message_count", 0),
                              n.get("question_count", 0), n.get("answer_count", 0),
                              n.get("submission_count", 0),
                              "、".join(n.get("skill_tags", [])) or "无",
                              n.get("_profile_note", ""))}

    # 6 班级总览（兜底）
    intents = Counter(m.get("intent") for m in g.nodes["Message"].values())
    sub_count = len(g.nodes["Submission"])
    student_count = len(g.nodes["Student"])
    challenge_count = len(g.nodes["Challenge"])
    return {"query": q, "intent": "class_summary",
            "data": {"students": student_count, "challenges": challenge_count,
                     "submissions": sub_count, "qa_pairs": len(g.nodes["QAPair"]),
                     "messages": len(g.nodes["Message"]),
                     "intent_distribution": dict(intents)},
            "answer": "班级状态：%d 名学生、%d 个挑战、%d 条消息、%d 次提交、%d 条 Q&A；"
                      "消息意图分布 %s。（数据为合成脱敏样本）" % (
                          student_count, challenge_count, len(g.nodes["Message"]),
                          sub_count, len(g.nodes["QAPair"]), dict(intents))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="班级管理自然语言查询")
    ap.add_argument("--input", default=str(EVIDENCE / "graph.json"))
    ap.add_argument("--output", default=str(EVIDENCE / "nl_query_answers.json"))
    ap.add_argument("--markdown", default=str(EVIDENCE / "nl_query_answers.md"))
    ap.add_argument("--query", default=None)
    ap.add_argument("--demo", action="store_true", help="跑 6 个演示场景")
    ap.add_argument("--group", default=None, help="兼容 Skill 转发")
    ap.add_argument("--days", type=int, default=None, help="兼容 Skill 转发")
    ap.add_argument("--wechat-id", default=None, help="兼容 Skill 转发")
    args = ap.parse_args(argv)

    g = PropertyGraph.load(args.input)
    queries = DEMO_QUERIES if (args.demo or not args.query) else [args.query]
    results = [answer_query(g, q) for q in queries]
    save_json(args.output, {
        "graph": args.input, "query_count": len(results),
        "intent_coverage": sorted({r["intent"] for r in results}),
        "results": results,
    })
    lines = ["# 自然语言查询演示（Level 3）", "",
             "> 数据源：合成脱敏样本；查询为规则路由，未调用 LLM。", ""]
    for i, r in enumerate(results, 1):
        lines += ["## %d. %s" % (i, r["query"]), "",
                  "- 路由意图：`%s`" % r["intent"], "",
                  "**回答：** " + r["answer"].replace("\n", "\n\n"), ""]
    Path(args.markdown).write_text("\n".join(lines), encoding="utf-8")
    print("[nl_query] queries=%d intents=%s output=%s"
          % (len(results), sorted({r["intent"] for r in results}), args.output))
    for r in results:
        print("  - [%s] %s -> %s" % (r["intent"], r["query"], r["answer"][:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
