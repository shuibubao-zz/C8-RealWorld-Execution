"""C8 微信群 -> 班级管理子系统：公共基础模块。

设计约束（可复核）：
1. 零第三方依赖，仅使用 Python 标准库；配置文件 .yaml 采用 JSON 语法
   （JSON 是 YAML 1.2 的合法子集），因此不需要 PyYAML，避免无依赖环境崩溃。
2. 消息体严格遵循任务书 Level 1 的 7 字段 schema，额外字段一律不写入消息体。
3. 本模块不接触真实微信数据库；真实数据源只能由 wechat_bridge.py 显式指定。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent                 # demo/
PKG = ROOT / "wechat-class-manager"
CONFIG = PKG / "config"
DATA = ROOT / "data"
EVIDENCE = ROOT.parent / "evidence"

MESSAGE_TYPES = ("text", "image", "file", "voice", "link", "system")
INTENTS = ("submission", "question", "answer", "discussion",
           "announcement", "resource", "social")
MESSAGE_FIELDS = ("msg_id", "timestamp", "sender", "type",
                  "content", "media_ref", "reply_to")

# 提交命名规范：姓名_C编号_描述.扩展名，如 卢怡然_C8_proposal.md
SUBMISSION_RE = re.compile(
    r"^(?P<name>[^_\\/]+)_(?P<challenge>C\d+[A-Z]?H?)_(?P<desc>.+)\.(?P<ext>[A-Za-z0-9]+)$"
)

DEFAULT_CHALLENGES = {
    "version": 1,
    "challenges": [
        {"id": "C1", "name_cn": "课程资料获取与翻译", "signal_keywords": ["翻译", "C1"], "signal_extensions": [".md", ".pdf"], "due_date": "2026-11-20"},
        {"id": "C2", "name_cn": "AI for Math 论文", "signal_keywords": ["论文", "C2"], "signal_extensions": [".md", ".pdf"], "due_date": "2026-11-22"},
        {"id": "C3", "name_cn": "群内高质量参与", "signal_keywords": ["群内", "参与", "C3"], "signal_extensions": [".md"], "due_date": "2026-11-25"},
        {"id": "C4B", "name_cn": "公众号文章生成技能", "signal_keywords": ["技能", "公众号", "C4B"], "signal_extensions": [".skill", ".md"], "due_date": "2026-11-28"},
        {"id": "C5", "name_cn": "GitHub Repository", "signal_keywords": ["GitHub", "repo", "C5"], "signal_extensions": [".md", ".zip"], "due_date": "2026-12-01"},
        {"id": "C6A", "name_cn": "提交数据仪表盘", "signal_keywords": ["仪表盘", "看板", "C6A"], "signal_extensions": [".html", ".xlsx"], "due_date": "2026-12-04"},
        {"id": "C7", "name_cn": "内容传播", "signal_keywords": ["传播", "文章", "C7"], "signal_extensions": [".md", ".html"], "due_date": "2026-12-07"},
        {"id": "C8", "name_cn": "真实项目落地", "signal_keywords": ["真实项目", "proposal", "C8"], "signal_extensions": [".md", ".zip"], "due_date": "2026-12-31"},
    ],
}


def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        if default is not None:
            return default
        raise FileNotFoundError(p)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return p


def load_jsonl(path):
    out = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def save_jsonl(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return p


def load_challenges():
    return load_json(CONFIG / "challenges.yaml", DEFAULT_CHALLENGES)


def load_group_config():
    return load_json(CONFIG / "group_config.yaml", {
        "group_name": "Elite20-示例群（合成）",
        "synthetic": True,
        "mentors": ["t01"],
        "students": [],
    })


def parse_ts(value):
    return datetime.fromisoformat(value)


def validate_message(msg):
    """校验 Level 1 schema；返回 (bool, 错误说明)。"""
    if not isinstance(msg, dict):
        return False, "not a dict"
    missing = [k for k in MESSAGE_FIELDS if k not in msg]
    if missing:
        return False, "missing fields: " + ",".join(missing)
    extra = [k for k in msg if k not in MESSAGE_FIELDS]
    if extra:
        return False, "unexpected fields: " + ",".join(extra)
    if not isinstance(msg["msg_id"], str) or not msg["msg_id"]:
        return False, "bad msg_id"
    try:
        parse_ts(msg["timestamp"])
    except (ValueError, TypeError):
        return False, "bad timestamp"
    s = msg["sender"]
    if not isinstance(s, dict) or "wechat_id" not in s or "nickname" not in s:
        return False, "bad sender"
    if msg["type"] not in MESSAGE_TYPES:
        return False, "bad type"
    if not isinstance(msg["content"], str):
        return False, "bad content"
    if msg["media_ref"] is not None and not isinstance(msg["media_ref"], str):
        return False, "bad media_ref"
    if msg["reply_to"] is not None and not isinstance(msg["reply_to"], str):
        return False, "bad reply_to"
    return True, "ok"


def normalize_message(raw):
    """把任意上游（chatlog / wechat-cli / 合成）记录规范化为 7 字段消息。"""
    sender = raw.get("sender") or {}
    if isinstance(sender, str):
        sender = {"wechat_id": sender, "nickname": raw.get("nickname", sender)}
    msg_type = raw.get("type", "text")
    if msg_type not in MESSAGE_TYPES:
        msg_type = "text"
    out = {
        "msg_id": str(raw.get("msg_id") or raw.get("id") or ""),
        "timestamp": raw.get("timestamp") or raw.get("time") or "",
        "sender": {
            "wechat_id": str(sender.get("wechat_id", "unknown")),
            "nickname": str(sender.get("nickname", "unknown")),
        },
        "type": msg_type,
        "content": str(raw.get("content") or raw.get("message") or ""),
        "media_ref": raw.get("media_ref") or raw.get("file") or None,
        "reply_to": raw.get("reply_to") or None,
    }
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")
