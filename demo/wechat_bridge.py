"""Level 1 (Bronze): WeChat Channel Adapter —— 把群消息变成 Agent 可消费的 JSON Lines。

设计原则：**不伪造真实数据**。三种数据源必须显式选择：

  --source synthetic   合成脱敏样本（默认；固定种子，可复现；绝不代表真实群消息）
  --source jsonl       读取 wechat-cli 等工具导出的 JSONL，做 schema 规范化
  --source chatlog     调用 chatlog 本地 HTTP API（默认 127.0.0.1:5030）

chatlog 数据源在本次交付中**未连接真实服务、未实测**（无授权、且需本机解密密钥）；
连接失败会直接报错退出，不会静默回退到合成数据。

用法：
  python wechat_bridge.py --group "Elite20" --days 7 --output messages.jsonl
  python wechat_bridge.py --source jsonl --input export.jsonl --days 3 --output out.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wcm_common import (DATA, EVIDENCE, MESSAGE_TYPES, iso, load_jsonl,  # noqa: E402
                        normalize_message, parse_ts, save_json, save_jsonl,
                        validate_message)


def _synthetic_source():
    from scripts.gen_fixture import build
    msgs, _, _ = build()
    return msgs, {"source": "synthetic", "synthetic": True,
                  "note": "固定种子 20261114 生成的合成脱敏样本，非真实微信数据"}


def _jsonl_source(input_path):
    raw = load_jsonl(input_path)
    return [normalize_message(r) for r in raw], {
        "source": "jsonl", "synthetic": False, "input": str(input_path),
        "note": "由外部工具导出的 JSONL 规范化得到；真实性取决于输入文件",
    }


def _chatlog_source(url, talker, days, limit):
    """调用 chatlog HTTP API。未实测：保留可插拔接口，失败即显式报错。"""
    params = {"talker": talker, "format": "json", "limit": str(limit)}
    full = url.rstrip("/") + "/api/v1/chatlog?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(full, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - 明确暴露失败，不做假数据兜底
        raise RuntimeError(
            "chatlog 数据源连接失败（本次交付未实测真实数据源）：%s；"
            "请求地址 %s。请确认已启动 chatlog server 并完成本机解密。"
            % (exc, full)
        ) from exc
    items = payload.get("data", payload) if isinstance(payload, dict) else payload
    return [normalize_message(r) for r in items], {
        "source": "chatlog", "synthetic": False, "url": full,
        "note": "来自本地 chatlog HTTP API；需自行确认数据合规与授权",
    }


def filter_by_days(msgs, days):
    """以样本内最大时间戳为基准（而非系统时钟），保证重复运行结果一致。"""
    if not msgs or days is None:
        return msgs
    parsed = [(m, parse_ts(m["timestamp"])) for m in msgs if m.get("timestamp")]
    if not parsed:
        return msgs
    end = max(t for _, t in parsed)
    start = end - timedelta(days=days)
    return [m for m, t in parsed if start <= t <= end]


def main(argv=None):
    ap = argparse.ArgumentParser(description="微信群消息 -> 标准 JSONL 桥接")
    ap.add_argument("--group", default="Elite20-示例群（合成）", help="目标群名称/ID")
    ap.add_argument("--days", type=int, default=7, help="提取最近 N 天（默认 7）")
    ap.add_argument("--output", default=str(EVIDENCE / "sample_output.jsonl"))
    ap.add_argument("--meta", default=None, help="元数据 JSON 输出路径")
    ap.add_argument("--source", choices=("synthetic", "jsonl", "chatlog"),
                    default="synthetic")
    ap.add_argument("--input", help="--source jsonl 时的输入 JSONL")
    ap.add_argument("--chatlog-url", default="http://127.0.0.1:5030")
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args(argv)

    if args.source == "synthetic":
        msgs, meta = _synthetic_source()
    elif args.source == "jsonl":
        if not args.input:
            ap.error("--source jsonl 需要 --input")
        msgs, meta = _jsonl_source(args.input)
    else:
        msgs, meta = _chatlog_source(args.chatlog_url, args.group, args.days, args.limit)

    msgs = filter_by_days(msgs, args.days)
    bad = [(m.get("msg_id"), validate_message(m)[1]) for m in msgs
           if not validate_message(m)[0]]
    if bad:
        raise SystemExit("schema 校验失败 %d 条：%s" % (len(bad), bad[:5]))

    save_jsonl(args.output, msgs)
    meta.update({
        "group": args.group,
        "days": args.days,
        "count": len(msgs),
        "type_distribution": dict(Counter(m["type"] for m in msgs)),
        "time_range": [min(m["timestamp"] for m in msgs),
                       max(m["timestamp"] for m in msgs)] if msgs else [],
        "generated_by": "wechat_bridge.py",
    })
    meta_path = args.meta or str(Path(args.output).with_suffix(".meta.json"))
    save_json(meta_path, meta)

    print("[wechat_bridge] source=%s synthetic=%s group=%s days=%s count=%d"
          % (meta["source"], meta["synthetic"], args.group, args.days, len(msgs)))
    print("[wechat_bridge] types=%s" % meta["type_distribution"])
    print("[wechat_bridge] output=%s meta=%s" % (args.output, meta_path))
    if meta["synthetic"]:
        print("[wechat_bridge] 注意：输出为合成脱敏样本，不是真实群消息。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
