# SETUP · 安装与配置（Level 1 交付物之一）

## 1. 环境要求

| 项 | 要求 |
|---|---|
| Python | 3.9+（本次实测：`C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe`，Python 3.13.14） |
| 第三方包 | **无**。全部使用标准库（json / re / argparse / datetime / unittest / urllib / http.server / hashlib） |
| 配置文件 | `wechat-class-manager/config/*.yaml`、`schemas/domain-graph.yaml` 采用 **JSON 语法**（JSON 是 YAML 1.2 的合法子集），用 `json.load` 读取，**不需要 PyYAML** |
| 操作系统 | Windows / macOS / Linux 均可（路径用 `pathlib`，无平台专属调用） |
| 网络 | 不需要。`chatlog` 数据源是可选的本机 `127.0.0.1` 调用 |

> 「零依赖」不是宣称：已在 `importlib.util.find_spec` 检查 pypdf / PyPDF2 / pdfplumber / fitz / pdfminer **全部为 False** 的解释器上，跑通 11 个 CLI 与 13 项测试，见 `../evidence/environment.txt`。

## 2. 三步快速开始

在本文件所在目录的上一级（`C8/`）执行：

```bash
set PY=C:/Users/卢怡然/.workbuddy/binaries/python/versions/3.13.12/python.exe

%PY% demo/run_pipeline.py                       # 端到端，产出 ../evidence/ 全部文件
%PY% -m unittest discover -s demo/wechat-class-manager/tests -v   # 13 项测试
```

然后双击 `wechat-class-manager/dashboard/index.html` 打开看板（离线，无需服务器）。

预期：11 个 CLI 步骤 `exit=0`、`Ran 13 tests ... OK`、验收矩阵 `15 pass / 2 pass(合成数据) / 5 not_met`。

## 3. 数据源配置（重要）

`wechat_bridge.py` 必须用 `--source` **显式**选择数据源，没有隐式默认兜底到真实数据：

| `--source` | 用途 | 命令 |
|---|---|---|
| `synthetic`（默认值） | 固定种子 20261114 生成 150 条合成脱敏样本，**本次交付使用** | `python wechat_bridge.py --group "Elite20" --days 7 --output out.jsonl` |
| `jsonl` | 规范化 wechat-cli / 其它工具导出的 JSONL | `python wechat_bridge.py --source jsonl --input export.jsonl --days 7 --output out.jsonl` |
| `chatlog` | 调用本机 chatlog HTTP API（默认 `127.0.0.1:5030`） | `python wechat_bridge.py --source chatlog --chatlog-url http://127.0.0.1:5030 --group <群ID> --output out.jsonl` |

**合规性前置条件**：接真实数据前必须获得数据所有者授权，并自行完成脱敏。`chatlog` 分支在本次交付中**未连接真实服务、未实测**；连接失败会抛错退出，**不会静默回退到合成数据**，以免把假数据当成真结果。

`--days N` 以样本内最大时间戳为基准（而非系统时钟），因此重复运行结果逐字节一致，可用 sha256 复核。

## 4. 逐个模块单独运行

```bash
# L1
python wechat_bridge.py --group "Elite20" --days 7 --output ../evidence/sample_output.jsonl

# L2（每个都可独立运行）
python classifier.py --input ../evidence/sample_output.jsonl --output ../evidence/classified.jsonl --labels data/synthetic_labels.json
python challenge_linker.py --input ../evidence/classified.jsonl --output ../evidence/challenge_refs.json
python submission_detector.py --input ../evidence/classified.jsonl --refs ../evidence/challenge_refs.json --output ../evidence/submissions.json
python qa_extractor.py --input ../evidence/classified.jsonl --output ../evidence/qa_pairs.json

# L3
python wechat-class-manager/graph_store.py --build
python wechat-class-manager/graph_store.py --action profile --wechat-id s01 --input ../evidence/graph.json
python wechat-class-manager/nl_query.py --demo

# L4
python wechat-class-manager/watcher.py --input data/synthetic_messages_increment.jsonl
python wechat-class-manager/alert_engine.py --as-of 2026-11-18
python wechat-class-manager/report_engine.py
```

Skill 入口（薄封装，只转发到唯一实现）：

```bash
python wechat-class-manager/skills/wechat-bridge/bridge.py --days 7 --output out.jsonl
python wechat-class-manager/skills/class-report/reporter.py
```

## 5. 配置说明

| 文件 | 内容 |
|---|---|
| `wechat-class-manager/config/challenges.yaml` | 8 个挑战定义（id / 名称 / signal_keywords / signal_extensions / due_date）+ 4 个 Level |
| `wechat-class-manager/config/group_config.yaml` | 群名、`synthetic: true`、导师列表、22 名学生映射、预警阈值、`_privacy_note` |
| `wechat-class-manager/schemas/message.schema.json` | 7 字段消息契约（draft-07，`additionalProperties: false`） |
| `wechat-class-manager/schemas/submission.schema.json` / `student.schema.json` | 提交与学生画像契约 |
| `wechat-class-manager/schemas/domain-graph.yaml` | 6 类节点 + 7 类边的领域模型 |

换一门课/换一个群：只改 `config/` 两个文件，不改任何 Python 代码。

## 6. 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 看板打开是空白 | 先跑 `report_engine.py` 生成 `dashboard/dashboard_data.js`；看板用 `<script src>` 注入数据，避免 `file://` 下 fetch 跨域 |
| `ModuleNotFoundError: yaml` | 不会发生：配置用 JSON 语法，`json.load` 读取。若你自己改成了带注释的 YAML，需自行安装 PyYAML |
| Watcher 第二次跑显示 0 条新增 | 正常：`state/checkpoint.json` 按 msg_id 去重。删掉该文件即可从干净状态复跑；`run_pipeline.py` 会自动清理 |
| 预警里 `deadline_warning` 为 0 | 默认按数据窗末日计算；用 `--as-of YYYY-MM-DD` 指定模拟时间点，结果会标 `simulated_as_of: true` |
| 想接真实微信数据 | 先取得授权 → 用 `chatlog` 或导出 JSONL → 检查 `sample_output.meta.json` 里 `synthetic` 字段为 `false` → 重跑 pipeline |

## 7. 诚实边界

本目录**不含**任何真实微信聊天记录。`data/` 全部为合成脱敏样本（`data/README.md` 有完整声明）；真实数据源、跨周运行、Agent Runtime hook 与双向写回均未在本次交付中实测，详见 `../evidence/验收记录.md`。
