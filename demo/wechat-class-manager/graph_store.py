"""Level 3 (Gold): Property Graph 存储与学生画像。

零第三方依赖实现（对应任务书技术选型表里的 "NetworkX -> JSON export / 快速原型"，
但连 NetworkX 也不装，直接用 dict + JSON，换机器即可跑）。

节点：Student / Challenge / Submission / Message / QAPair / Report
边  ：SUBMITTED / SENT / ASKED / ANSWERED / MENTORED / PROGRESSED_TO / TAGGED_WITH

用法：
  python graph_store.py --build --output graph.json
  python graph_store.py --action profile --wechat-id s01 --input graph.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wcm_common import (EVIDENCE, load_challenges, load_group_config,  # noqa: E402
                        load_json, load_jsonl, save_json)

NODE_TYPES = ("Student", "Challenge", "Submission", "Message", "QAPair", "Report")
EDGE_TYPES = ("SUBMITTED", "SENT", "ASKED", "ANSWERED", "MENTORED",
              "PROGRESSED_TO", "TAGGED_WITH")


class PropertyGraph:
    def __init__(self):
        self.nodes = {t: {} for t in NODE_TYPES}
        self.edges = []
        self.meta = {}

    def add_node(self, ntype, key, props=None):
        assert ntype in self.nodes, ntype
        props = dict(props or {})
        props.setdefault("_key", key)
        if key in self.nodes[ntype]:
            self.nodes[ntype][key].update(props)
        else:
            self.nodes[ntype][key] = props
        return self.nodes[ntype][key]

    def get_node(self, ntype, key):
        return self.nodes[ntype].get(key)

    def update_node(self, ntype, key, patch):
        n = self.nodes[ntype].get(key)
        if n is None:
            return None
        n.update(patch)
        return n

    def add_edge(self, etype, src, dst, props=None):
        assert etype in EDGE_TYPES, etype
        e = {"type": etype, "src": src, "dst": dst, "props": props or {}}
        self.edges.append(e)
        return e

    def query_edges(self, etype=None, src=None, dst=None):
        return [e for e in self.edges
                if (etype is None or e["type"] == etype)
                and (src is None or e["src"] == src)
                and (dst is None or e["dst"] == dst)]

    def counts(self):
        return {"nodes": {t: len(v) for t, v in self.nodes.items()},
                "edges": dict(Counter(e["type"] for e in self.edges)),
                "total_nodes": sum(len(v) for v in self.nodes.values()),
                "total_edges": len(self.edges)}

    def to_dict(self):
        return {"meta": self.meta, "nodes": self.nodes, "edges": self.edges,
                "counts": self.counts()}

    @classmethod
    def from_dict(cls, d):
        g = cls()
        g.meta = d.get("meta", {})
        for t, nodes in d.get("nodes", {}).items():
            g.nodes.setdefault(t, {}).update(nodes)
        g.edges = d.get("edges", [])
        return g

    def save(self, path):
        return save_json(path, self.to_dict())

    @classmethod
    def load(cls, path):
        return cls.from_dict(load_json(path))


def build_graph(messages, submissions_payload, qa_payload, refs_payload=None,
                meta=None):
    cfg = load_challenges()
    group = load_group_config()
    g = PropertyGraph()
    g.meta = {
        "title": "Class Management Property Graph",
        "backend": "stdlib dict + JSON",
        "synthetic": True,
        "_note": "节点与边全部来自合成脱敏样本，未接入真实微信数据。",
    }
    if meta:
        g.meta.update(meta)

    for c in cfg["challenges"]:
        g.add_node("Challenge", c["id"], dict(c, levels=cfg.get("levels", [])))

    for s in group["students"]:
        g.add_node("Student", s["wechat_id"], {
            "wechat_id": s["wechat_id"], "nickname": s["nickname"],
            "major": "", "enrollment_date": None, "skill_tags": [],
            "message_count": 0, "question_count": 0, "answer_count": 0,
            "submission_count": 0, "last_active": None,
            "_profile_note": "画像由群互动统计推断，不是心理测评；仅用于教学管理辅助。",
        })

    ref_map = {}
    if refs_payload:
        ref_map = {r["msg_id"]: r.get("challenge_ref")
                   for r in refs_payload.get("refs", [])}

    mentor_ids = set(group.get("mentors", []))
    per_student = defaultdict(lambda: {"msgs": 0, "q": 0, "a": 0, "tags": []})
    for m in messages:
        sid = m["sender"]["wechat_id"]
        intent = m.get("intent")
        cref = m.get("challenge_ref") or ref_map.get(m["msg_id"])
        # 导师不是 Student 节点：单独作为 Mentor 主体，避免把老师计入学生数
        is_mentor = sid in mentor_ids
        principal = ("Mentor:" if is_mentor else "Student:") + sid
        if not is_mentor:
            g.add_node("Student", sid, {"nickname": m["sender"]["nickname"]})
        g.add_node("Message", m["msg_id"], {
            "timestamp": m["timestamp"], "content": m["content"],
            "type": m["type"], "wechat_msg_id": m["msg_id"], "intent": intent,
            "sender": sid, "challenge_ref": cref,
        })
        g.add_edge("SENT", principal, "Message:" + m["msg_id"])
        if cref and g.get_node("Challenge", cref):
            g.add_edge("TAGGED_WITH", "Message:" + m["msg_id"], "Challenge:" + cref)
        if is_mentor:
            continue
        if cref and g.get_node("Challenge", cref):
            per_student[sid]["tags"].append(cref)
        p = per_student[sid]
        p["msgs"] += 1
        p["q"] += int(intent == "question")
        p["a"] += int(intent == "answer")
        if p.get("last") is None or m["timestamp"] > p["last"]:
            p["last"] = m["timestamp"]

    for sid, p in per_student.items():
        g.update_node("Student", sid, {
            "message_count": p["msgs"], "question_count": p["q"],
            "answer_count": p["a"], "last_active": p.get("last"),
            "skill_tags": sorted(set(p["tags"]))[:5],
        })

    subs = submissions_payload.get("submissions", []) if submissions_payload else []
    for s in subs:
        sid = s.get("wechat_id", "unknown")
        cid = s["challenge"]
        g.add_node("Submission", s["submission_id"], {
            "timestamp": s["timestamp"], "files": s["files"],
            "level_claimed": s.get("level_claimed"), "status": s["status"],
            "complete": s.get("complete"), "missing_items": s.get("missing_items", []),
        })
        g.add_edge("SUBMITTED", "Student:" + sid, "Submission:" + s["submission_id"])
        g.add_edge("SUBMITTED", "Submission:" + s["submission_id"], "Challenge:" + cid)
        g.add_edge("PROGRESSED_TO", "Student:" + sid, "Challenge:" + cid,
                   {"level": "received"})
        g.update_node("Student", sid, {"submission_count":
                      g.get_node("Student", sid).get("submission_count", 0) + 1})

    qa_pairs = qa_payload.get("pairs", []) if qa_payload else []
    for i, p in enumerate(qa_pairs, 1):
        key = "QA-%03d" % i
        g.add_node("QAPair", key, {
            "question": p["question"], "answer": p["answer"],
            "topic_tags": p["topic_tags"], "quality_score": p["quality_score"],
            "question_id": p["question_id"], "answer_id": p["answer_id"],
        })
        qmsg = next((m for m in messages if m["msg_id"] == p["question_id"]), None)
        amsg = next((m for m in messages if m["msg_id"] == p["answer_id"]), None)
        if qmsg:
            g.add_edge("ASKED", "Student:" + qmsg["sender"]["wechat_id"], "QAPair:" + key)
        if amsg:
            a_sid = amsg["sender"]["wechat_id"]
            a_principal = ("Mentor:" if a_sid in mentor_ids else "Student:") + a_sid
            g.add_edge("ANSWERED", a_principal, "QAPair:" + key)
            if qmsg and a_sid != qmsg["sender"]["wechat_id"]:
                q_sid = qmsg["sender"]["wechat_id"]
                q_principal = ("Mentor:" if q_sid in mentor_ids else "Student:") + q_sid
                g.add_edge("MENTORED", a_principal, q_principal, {"via": key})

    g.meta["counts"] = g.counts()
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(description="Property Graph 构建与查询")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--action", default="build", choices=("build", "profile", "counts"))
    ap.add_argument("--messages", default=str(EVIDENCE / "classified.jsonl"))
    ap.add_argument("--submissions", default=str(EVIDENCE / "submissions.json"))
    ap.add_argument("--qa", default=str(EVIDENCE / "qa_pairs.json"))
    ap.add_argument("--refs", default=str(EVIDENCE / "challenge_refs.json"))
    ap.add_argument("--input", default=str(EVIDENCE / "graph.json"),
                    help="profile/counts 动作的图文件；也兼容 Skill 转发的 --input")
    ap.add_argument("--output", default=str(EVIDENCE / "graph.json"))
    ap.add_argument("--wechat-id", default=None)
    ap.add_argument("--group", default=None, help="兼容 Skill 转发，本模块不消费")
    ap.add_argument("--days", type=int, default=None, help="兼容 Skill 转发，本模块不消费")
    args = ap.parse_args(argv)

    if args.action == "build" or args.build:
        g = build_graph(load_jsonl(args.messages), load_json(args.submissions),
                        load_json(args.qa), load_json(args.refs))
        g.save(args.output)
        print("[graph] %s" % json.dumps(g.counts(), ensure_ascii=False))
        print("[graph] output=%s" % args.output)
        return 0

    g = PropertyGraph.load(args.input)
    if args.action == "counts":
        print(json.dumps(g.counts(), ensure_ascii=False, indent=2))
        return 0
    prof = g.get_node("Student", args.wechat_id or "s01")
    print(json.dumps(prof, ensure_ascii=False, indent=2))
    if args.output and args.output != args.input:
        save_json(args.output, prof)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
