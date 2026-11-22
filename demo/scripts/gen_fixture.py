"""生成可复现的合成脱敏群消息样本（Level 1/2 测试数据）。

重要声明：
- 本脚本不读取任何真实微信数据。所有姓名均为「学生NN」占位，内容全部由模板生成。
- 固定随机种子 20261114；重复运行结果逐字节一致，可用 sha256 复核。
- 标签与分类规则由同一批模板设计，因此在合成集上测得的准确率
  只证明「实现自洽」，不构成对真实群消息的泛化证据。此限制写入验收记录。

用法：python scripts/gen_fixture.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wcm_common import DATA, iso, save_json, save_jsonl, validate_message  # noqa: E402

SEED = 20261114
N_STUDENTS = 22
START = datetime(2026, 11, 2, 9, 0, 0)

CHALLENGE_TAGS = ["C1", "C2", "C3", "C4B", "C5", "C6A", "C7", "C8"]
DISCUSS_TOPICS = [
    "关于 {tag} 的评分标准，我把检查清单又核了一遍，发现有几条容易漏。",
    "{tag} 这个任务里，README 和复现说明最好分开写，不然接手的人会卡住。",
    "我试了下 {tag} 的做法，数据口径统一之后结果稳定很多，大家可以参考。",
    "讨论一下 {tag}：先做最小闭环再补功能，比一次做全更省时间。",
    "{tag} 的 evidence 目录建议按日期归档，方便后面 AAR 对比预期和实际。",
]
QUESTION_TOPICS = [
    "请问 {tag} 的提交文件命名必须严格按模板吗？",
    "{tag} 的 AI 日志要写到什么颗粒度才算合格？",
    "为什么我的 {tag} 自检器跑出来和示例数字对不上？",
    "怎么在 {tag} 里复现别人的实验结果？",
    "{tag} 的拿来说明至少要列几个参考来源？",
]
ANSWER_TOPICS = [
    "命名要严格按模板，文件通配匹配不上会被判缺失。",
    "AI 日志写清楚每轮指令、改了什么、为什么改，最好附上失败尝试。",
    "先核对解释器和依赖版本，数字口径不一致最常见的原因就是这个。",
    "从 README 的安装步骤开始，一步步跑，把输出和预期逐条对。",
    "检查清单写的是至少 3 个来源，而且每个要有取舍分析。",
]
RESOURCE_TOPICS = [
    "分享一份 {tag} 的复现笔记 https://example.org/notes/{tag}",
    "推荐这个资料，讲 {tag} 的检查清单挺清楚 https://example.org/ref/{tag}",
    "把 {tag} 的模板整理成文档了，链接在这里 https://example.org/tpl/{tag}",
]
SOCIAL_TOPICS = [
    "早上好，今天继续推进。", "收到，谢谢！", "哈哈这个梗我记住了。",
    "晚上还有个会，先撤一下。", "大家辛苦了。", "周末加油～",
    "刚吃完饭，回来继续看。", "好的没问题。",
]


def build():
    rnd = random.Random(SEED)
    students = [{"wechat_id": "s%02d" % i, "nickname": "学生%02d" % i}
                for i in range(1, N_STUDENTS + 1)]
    mentor = {"wechat_id": "t01", "nickname": "导师"}
    msgs, labels = [], {}
    counter = [0]
    clock = [START]

    def add(sender, mtype, content, intent, media_ref=None, reply_to=None,
            advance_min=7):
        counter[0] += 1
        clock[0] = clock[0] + timedelta(minutes=rnd.randint(1, max(1, advance_min)))
        mid = "m%04d" % counter[0]
        msg = {
            "msg_id": mid,
            "timestamp": iso(clock[0]),
            "sender": {"wechat_id": sender["wechat_id"], "nickname": sender["nickname"]},
            "type": mtype,
            "content": content,
            "media_ref": media_ref,
            "reply_to": reply_to,
        }
        ok, err = validate_message(msg)
        assert ok, (mid, err)
        msgs.append(msg)
        labels[mid] = intent
        return mid

    # 1) 公告（老师发出，含 @全体 / 截止 / deadline）
    for tag, day in [("C1", "11月20日"), ("C4B", "11月28日"), ("C6A", "12月4日"),
                     ("C7", "12月7日"), ("C8", "12月31日"), ("C5", "12月1日")]:
        add(mentor, "text", "@全体 通知：%s 的截止时间是 %s，请提前提交并附 AI 日志。" % (tag, day),
            "announcement")

    # 2) 提交事件 8 个（file + 命名规范），其中 3 个故意缺 AI 日志
    submit_pairs = [("C1", "proposal"), ("C2", "论文"), ("C3", "参与记录"),
                    ("C4B", "wechat-publisher"), ("C5", "repo链接"),
                    ("C6A", "dashboard"), ("C7", "文章链接汇总"), ("C8", "proposal")]
    for i, (tag, desc) in enumerate(submit_pairs):
        st = students[i]
        fname = "%s_%s_%s.md" % (st["nickname"], tag, desc)
        add(st, "file", fname, "submission", media_ref="attachments/" + fname)

    # 2b) 前 4 个提交附带 AI 日志（用于演示完整性检查：4 完整 / 4 缺失）
    for i in range(4):
        tag, _ = submit_pairs[i]
        st = students[i]
        fname = "%s_%s_AI日志.md" % (st["nickname"], tag)
        add(st, "file", fname, "submission", media_ref="attachments/" + fname)

    # 3) Q&A 14 对（question -> answer 通过 reply_to 关联）
    for i in range(14):
        tag = CHALLENGE_TAGS[i % len(CHALLENGE_TAGS)]
        q_student = students[(i * 3) % N_STUDENTS]
        a_student = mentor if i % 4 == 0 else students[(i * 3 + 5) % N_STUDENTS]
        q = QUESTION_TOPICS[i % len(QUESTION_TOPICS)].format(tag=tag)
        qid = add(q_student, "text", q, "question")
        ans = ANSWER_TOPICS[i % len(ANSWER_TOPICS)]
        add(a_student, "text", ans, "answer", reply_to=qid)

    # 4) 资源分享（link）
    for i in range(9):
        tag = CHALLENGE_TAGS[i % len(CHALLENGE_TAGS)]
        add(students[(i * 2 + 1) % N_STUDENTS], "link",
            RESOURCE_TOPICS[i % len(RESOURCE_TOPICS)].format(tag=tag), "resource")

    # 5) 讨论
    for i in range(34):
        tag = CHALLENGE_TAGS[i % len(CHALLENGE_TAGS)]
        add(students[(i * 5 + 2) % N_STUDENTS], "text",
            DISCUSS_TOPICS[i % len(DISCUSS_TOPICS)].format(tag=tag), "discussion")

    # 6) 多媒体与系统消息（保证类型可区分）
    for i in range(6):
        add(students[i], "image", "[图片]", "social", media_ref="images/p%02d.png" % i)
    for i in range(4):
        add(students[i + 6], "voice", "[语音]", "social", media_ref="voice/v%02d.silk" % i)
    for i in range(3):
        add(mentor, "system", "成员 学生%02d 加入了群聊" % (i + 1), "social")

    # 7) 闲聊补足到 >= 150 条
    while len(msgs) < 150:
        add(students[rnd.randrange(N_STUDENTS)], "text",
            rnd.choice(SOCIAL_TOPICS), "social", advance_min=4)

    # 8) 增量批次：4 条重复（用于验证 watcher 去重）+ 8 条新消息
    increment = [msgs[10], msgs[40], msgs[80], msgs[120]]
    for k in range(8):
        counter[0] += 1
        clock[0] = clock[0] + timedelta(minutes=11)
        mid = "m%04d" % counter[0]
        tag = CHALLENGE_TAGS[k % len(CHALLENGE_TAGS)]
        msg = {
            "msg_id": mid,
            "timestamp": iso(clock[0]),
            "sender": students[k],
            "type": "text",
            "content": DISCUSS_TOPICS[k % len(DISCUSS_TOPICS)].format(tag=tag),
            "media_ref": None,
            "reply_to": None,
        }
        ok, err = validate_message(msg)
        assert ok, (mid, err)
        increment.append(msg)
        labels[mid] = "discussion"

    return msgs, labels, increment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DATA))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    msgs, labels, increment = build()
    save_jsonl(out / "synthetic_messages.jsonl", msgs)
    save_json(out / "synthetic_labels.json", {
        "_note": "合成数据真值标签；与分类规则同源于模板设计，仅用于实现自洽性验证。",
        "seed": SEED,
        "count": len(labels),
        "labels": labels,
    })
    save_jsonl(out / "synthetic_messages_increment.jsonl", increment)
    readme = """# 合成脱敏样本说明（必读）

| 项 | 值 |
|---|---|
| 数据来源 | **完全合成**，由 `scripts/gen_fixture.py` 用固定种子 20261114 生成 |
| 真实微信数据 | **未使用**。本机虽检测到微信数据目录，本次未解密、未读取、未导出任何真实聊天记录 |
| 姓名 | 全部为「学生NN」占位，无真实个人信息 |
| 消息条数 | %d 条主样本 + %d 条增量批次（含 4 条重复 msg_id，用于验证 Watcher 去重） |
| 覆盖类型 | text / image / file / voice / link / system |
| 覆盖意图 | submission / question / answer / discussion / announcement / resource / social |
| 覆盖挑战 | C1 C2 C3 C4B C5 C6A C7 C8（8 个） |
| 覆盖学生 | 22 名（> 任务书要求的 20 名） |
| 时间窗 | 2026-11-02 ~ 2026-11-08（7 天，合成时间戳） |

## 诚实边界

1. 真实标签 `synthetic_labels.json` 与分类器规则出自同一批模板，因此在合成集上测得的
   准确率**只能证明实现自洽**，不能作为「真实群消息上准确率 > 70%%」的证据。
2. 任务书 Level 1「从本地微信数据中提取至少 100 条群消息」与 Level 4「至少运行 1 周
   真实数据演示」因隐私与授权边界**未满足**，详见 `../evidence/验收记录.md`。
3. 因此本目录数据仅用于端到端功能验证，不得对外表述为真实班级数据。
""" % (len(msgs), len(increment))
    (out / "README.md").write_text(readme, encoding="utf-8")
    print("synthetic messages: %d, labels: %d, increment: %d, out: %s"
          % (len(msgs), len(labels), len(increment), out))


if __name__ == "__main__":
    main()
