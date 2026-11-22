"""Level 2 (Silver): 挑战关联器 —— 给每条消息打 challenge_ref。

两级匹配：
  1) 编号精确匹配（C1 / C4B / C8 ... 必须存在于 config/challenges.yaml）
  2) signal_keywords 关键词兜底（如「仪表盘」-> C6A）
未命中则为 null，不强行归类。

用法：python challenge_linker.py --input classified.jsonl --output challenge_refs.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcm_common import EVIDENCE, load_challenges, load_jsonl, save_json  # noqa: E402

TOKEN_RE = re.compile(r"(C\d+[A-Z]?H?)", re.I)


def load_config():
    cfg = load_challenges()
    return {c["id"].upper(): c for c in cfg["challenges"]}


def link_one(msg, cfg):
    text = (msg.get("content") or "") + " " + (msg.get("media_ref") or "")
    for token in TOKEN_RE.findall(text):
        key = token.upper()
        if key in cfg:
            return key, 0.95, "编号精确匹配"
    low = text.lower()
    for cid, c in cfg.items():
        for kw in c.get("signal_keywords", []):
            if kw.lower() in low:
                return cid, 0.70, "关键词匹配:%s" % kw
    return None, 0.0, "未命中"


def link_stream(messages, cfg=None):
    cfg = cfg or load_config()
    out = []
    for m in messages:
        cid, conf, reason = link_one(m, cfg)
        out.append({"msg_id": m["msg_id"], "challenge_ref": cid,
                    "confidence": conf, "reason": reason})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="消息 -> 挑战关联")
    ap.add_argument("--input", default=str(EVIDENCE / "classified.jsonl"))
    ap.add_argument("--output", default=str(EVIDENCE / "challenge_refs.json"))
    args = ap.parse_args(argv)
    rows = link_stream(load_jsonl(args.input))
    dist = Counter(r["challenge_ref"] or "(none)" for r in rows)
    save_json(args.output, {
        "rows": len(rows),
        "distribution": dict(dist),
        "refs": rows,
    })
    print("[linker] rows=%d dist=%s output=%s" % (len(rows), dict(dist), args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
