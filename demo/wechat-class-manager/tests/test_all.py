"""C8 测试套件：零第三方依赖，python -m unittest discover -s <tests> -v 即可运行。

覆盖：schema / 分类 / 挑战关联 / 提交检测 / Q&A / 图 CRUD 与规模 /
      自然语言查询 / Watcher 去重 / 预警 / 报告 / 端到端产物。

诚实说明：分类器在「同源合成集」与「独立手写变体集」上分别给出准确率，
两者都不等同于真实微信群人工标注集。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parents[2]
WCM = DEMO / "wechat-class-manager"
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(WCM))

from classifier import classify_stream, evaluate  # noqa: E402
from challenge_linker import link_stream  # noqa: E402
from qa_extractor import extract as extract_qa  # noqa: E402
from submission_detector import detect  # noqa: E402
from wcm_common import validate_message  # noqa: E402
from graph_store import PropertyGraph, build_graph  # noqa: E402
from nl_query import DEMO_QUERIES, answer_query  # noqa: E402
from alert_engine import run_alerts  # noqa: E402
from watcher import process as watch_process  # noqa: E402
from report_engine import build_report  # noqa: E402

from scripts.gen_fixture import build as build_fixture  # noqa: E402


class C8TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.msgs, cls.labels, cls.increment = build_fixture()
        cls.classified = classify_stream(cls.msgs)
        cls.refs = link_stream(cls.classified)
        cls.ref_payload = {"refs": cls.refs}
        cls.subs = detect(cls.classified, refs=cls.ref_payload)
        cls.qa = extract_qa(cls.classified)
        cls.graph = build_graph(cls.classified, cls.subs, cls.qa, cls.ref_payload)

    # ---------- Level 1 ----------
    def test_01_schema_and_volume(self):
        self.assertGreaterEqual(len(self.msgs), 100)
        for m in self.msgs:
            ok, err = validate_message(m)
            self.assertTrue(ok, "%s: %s" % (m["msg_id"], err))
        types = {m["type"] for m in self.msgs}
        self.assertEqual(types, {"text", "image", "file", "voice", "link", "system"})

    def test_02_fixture_deterministic(self):
        again, _, _ = build_fixture()
        self.assertEqual(self.msgs, again, "固定种子下样本必须逐字节一致")

    # ---------- Level 2 ----------
    def test_03_classifier_accuracy_synthetic(self):
        ev = evaluate(self.classified, self.labels)
        self.assertGreater(ev["accuracy"], 0.70)
        self.assertEqual(ev["total"], len(self.classified))

    def test_04_classifier_accuracy_holdout(self):
        """独立于生成模板的 20 条手工变体，结果打印到测试输出，不隐藏。"""
        fx = json.loads((WCM / "tests/fixtures/holdout_variants.json").read_text(encoding="utf-8"))
        stream = classify_stream(fx["anchor_questions"] + fx["messages"])
        rows = [r for r in stream if r["msg_id"].startswith("v")]
        ev = evaluate(rows, fx["labels"])
        print("\n[HOLDOUT] 手写变体集 accuracy=%.4f (%d/%d) confusion=%s"
              % (ev["accuracy"], ev["correct"], ev["total"], ev["confusion"]))
        self.assertEqual(ev["total"], 20)
        self.assertGreaterEqual(ev["accuracy"], 0.60)

    def test_05_challenge_linker(self):
        hit = [r for r in self.refs if r["challenge_ref"]]
        self.assertGreater(len(hit), 50)
        self.assertTrue(all(r["challenge_ref"] in
                            {c["id"] for c in
                             __import__("wcm_common").load_challenges()["challenges"]}
                            for r in hit))

    def test_06_submission_detector(self):
        self.assertGreaterEqual(self.subs["stats"]["submission_events"], 5)
        self.assertEqual(self.subs["stats"]["submission_events"], 8)
        self.assertEqual(self.subs["stats"]["complete"], 4)
        self.assertEqual(self.subs["stats"]["incomplete"], 4)
        self.assertEqual(self.subs["stats"]["attachments_merged"], 4)
        self.assertGreaterEqual(len(self.subs["missing"]), 4)
        self.assertIn("学生01", self.subs["matrix"])

    def test_07_qa_extractor(self):
        self.assertGreaterEqual(self.qa["stats"]["pairs"], 10)
        self.assertIn("reply_to", self.qa["stats"]["matched_by"])
        for p in self.qa["pairs"]:
            self.assertGreater(p["quality_score"], 0)
            self.assertIn(p["matched_by"], ("reply_to", "time_window"))

    # ---------- Level 3 ----------
    def test_08_graph_scale_and_crud(self):
        c = self.graph.counts()
        self.assertGreaterEqual(c["nodes"]["Student"], 20)
        self.assertGreaterEqual(c["nodes"]["Challenge"], 8)
        self.assertGreaterEqual(c["total_edges"], 100)
        g = PropertyGraph()
        g.add_node("Student", "x1", {"nickname": "测试"})
        g.add_node("Challenge", "C9", {"name_cn": "测试挑战"})
        g.add_edge("SENT", "Student:x1", "Message:m1")
        self.assertEqual(g.get_node("Student", "x1")["nickname"], "测试")
        g.update_node("Student", "x1", {"message_count": 3})
        self.assertEqual(g.get_node("Student", "x1")["message_count"], 3)
        self.assertEqual(len(g.query_edges("SENT", src="Student:x1")), 1)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "g.json"
            g.save(p)
            g2 = PropertyGraph.load(p)
            self.assertEqual(g2.counts(), g.counts())

    def test_09_nl_query_coverage(self):
        intents = {answer_query(self.graph, q)["intent"] for q in DEMO_QUERIES}
        self.assertGreaterEqual(len(intents), 5)
        self.assertEqual(len(intents), 6)

    def test_10_skill_assets_complete(self):
        for name in ("wechat-bridge", "msg-classifier", "submission-tracker",
                     "qa-sink", "student-profile", "class-report"):
            self.assertTrue((WCM / "skills" / name / "SKILL.md").exists(), name)
            self.assertEqual(len(list((WCM / "skills" / name).glob("*.py"))), 1, name)
        for f in ("message.schema.json", "submission.schema.json",
                  "student.schema.json", "domain-graph.yaml"):
            self.assertTrue((WCM / "schemas" / f).exists(), f)
        for f in ("challenges.yaml", "group_config.yaml"):
            c = json.loads((WCM / "config" / f).read_text(encoding="utf-8"))
            self.assertIsInstance(c, dict)

    # ---------- Level 4 ----------
    def test_11_watcher_incremental_dedup(self):
        with tempfile.TemporaryDirectory() as td:
            cp = Path(td) / "checkpoint.json"
            g = PropertyGraph.from_dict(self.graph.to_dict())
            r1 = watch_process(g, self.increment, cp)
            self.assertEqual(r1["duplicates_skipped"], 4)
            self.assertEqual(r1["new_processed"], 8)
            r2 = watch_process(g, self.increment, cp)
            self.assertEqual(r2["new_processed"], 0)
            self.assertEqual(r2["duplicates_skipped"], 12)
            self.assertEqual(r2["checkpoint_runs"], 2)

    def test_12_alert_rules(self):
        res = run_alerts(self.graph, self.classified, self.subs, as_of="2026-11-18")
        self.assertGreaterEqual(res["triggered_rule_types"], 3)
        self.assertTrue(res["simulated_as_of"])
        self.assertGreater(res["rule_counts"]["low_submission_rate"], 0)
        self.assertGreater(res["rule_counts"]["missing_attachment"], 0)

    def test_13_report_and_dashboard_dimensions(self):
        alerts = run_alerts(self.graph, self.classified, self.subs, as_of="2026-11-18")
        md, data = build_report(self.graph, self.classified, self.subs, self.qa, alerts)
        for section in ("本周概览", "最活跃学生", "完成率", "Q&A", "预警摘要", "每日消息趋势"):
            self.assertIn(section, md)
        self.assertGreaterEqual(data["dimension_count"], 5)
        self.assertEqual(len(data["dimensions"]), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
