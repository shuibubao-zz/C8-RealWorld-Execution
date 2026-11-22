# 卢怡然 · C8 Week 3 AI 日志

> 平台执行阶段必需文件 ｜ 主题：L4 闭环系统 + 验收固化 + 交付整理
> **诚实声明**：由 AI 依据本次会话真实操作整理，非逐字 prompt 存档；未执行的环节不写。

## 本轮 AI 协作记录

1. AI 设计 run_pipeline.py：用 subprocess 逐模块调用而非 import 串联，让「模块可独立运行」被真实执行验证。
2. unittest 报 test_11 FAIL（12 ≠ 8）；AI 先建议放宽断言，我判断是 watcher 统计口径说谎，改为引入 inserted 列表修实现。
3. AI 起草验收矩阵时想用静态表格；我要求 measured/status/evidence 全部由代码现算，禁止手填数字。
4. AI 帮我把 22 条验收标准映射到 evidence 文件路径与解释器环境；我逐条核对 5 项 not_met 没有被美化。
5. 文档阶段：AI 依据实测数字反写 Proposal / AAR / 验收记录，我核对每个数字的出处文件。

## 本轮迭代与失败

详见 `卢怡然_C8_AAR_W3.md`「失败分析」与 `卢怡然_C8_AI日志.md` §1 的 R7–R10。所有失败都改了**实现或事实口径**，没有为通过而放宽验收标准。

## 人 / AI 分工

- AI：代码生成、批量资产、报错定位、文档整理；
- 我（卢怡然）：确定隐私边界与权威性排序、核对每个数字出处、决定哪些能力不能写成「已实现」。

## 可追溯

| 想核实 | 文件 |
|---|---|
| 端到端执行 | `evidence/pipeline_output.txt` |
| 测试结果 | `evidence/test_output.txt` |
| 运行环境与依赖 | `evidence/environment.txt` |
| 验收数字是否现算 | `demo/run_pipeline.py` + `evidence/acceptance_matrix.json` |
