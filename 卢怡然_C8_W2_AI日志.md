# 卢怡然 · C8 Week 2 AI 日志

> 平台执行阶段必需文件 ｜ 主题：L3 Skill 封装 + Property Graph + 自然语言查询
> **诚实声明**：由 AI 依据本次会话真实操作整理，非逐字 prompt 存档；未执行的环节不写。

## 本轮 AI 协作记录

1. 用一次性生成脚本批量产出 7 个 SKILL.md + 6 个薄封装 + 4 schema + 2 config，避免十几次逐文件往返。
2. 生成脚本首次因模板 %s 个数与参数不一致失败 → 修正占位符，重跑成功。
3. AI 生成 graph_store.py 初版把导师也建成 Student 节点（学生数 23）；我核对口径后要求改成 Mentor 主体，重跑得 22。
4. AI 建议用 PyYAML 读 .yaml；我依据 C4A v4 的真实踩坑改为 JSON 语法 + json.load，并在真缺依赖环境验证。
5. AI 起草 SKILL.md 时想把「支持 MCP / 已被 runtime 调用」写进能力清单，我要求删除——本机未安装、未实测。

## 本轮迭代与失败

详见 `卢怡然_C8_AAR_W2.md`「失败分析」与 `卢怡然_C8_AI日志.md` §1 的 R7–R10。所有失败都改了**实现或事实口径**，没有为通过而放宽验收标准。

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
