"""class-report — Skill 薄封装。

只负责把 SKILL.md 约定的调用转发到唯一实现（demo/report_engine.py），
不复制业务逻辑，避免多处实现漂移。
"""
import argparse
import subprocess
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parents[3]
TARGET = DEMO / "report_engine.py"


def main(argv=None):
    ap = argparse.ArgumentParser(description="自动生成周报与看板数据")
    ap.add_argument("--input", default=None, help="输入文件路径")
    ap.add_argument("--output", default=None, help="输出文件路径")
    ap.add_argument("--group", default=None)
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--wechat-id", default=None, help="student-profile 专用")
    ap.add_argument("--pass-through", nargs=argparse.REMAINDER, default=[],
                    help="其余参数原样转发给底层实现")
    args = ap.parse_args(argv)
    cmd = [sys.executable, str(TARGET)]
    if args.input:
        cmd += ["--input", args.input]
    if args.output:
        cmd += ["--output", args.output]
    if args.group:
        cmd += ["--group", args.group]
    if args.days is not None:
        cmd += ["--days", str(args.days)]
    if args.wechat_id:
        cmd += ["--wechat-id", args.wechat_id]
    cmd += args.pass_through
    print("[class-report] -> " + " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
