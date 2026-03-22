# Deep Research Pro v4.3 — 架构设计

## 核心原则

Skill 是流程逻辑层，不是基础设施层。

- 搜索能力 → 系统 search 工具提供，Skill 只定义搜什么、怎么筛
- LLM 推理 → 系统主模型提供，Skill 只定义 prompt 和输出格式
- Python 脚本 → 只做不依赖外部 API 的纯计算任务

## 文件结构

```
deep-research-pro/
├── SKILL.md              # 入口：流程编排指令（含执行纪律）
├── config.yaml           # 阈值和权重配置（含动态阈值）
├── prompts/              # Prompt 模板（供系统 LLM 使用）
│   ├── 03a_craap_extract.md  # Tier 1-2 快速提取模式
│   ├── 03b_craap_batch.md    # Tier 3-5 批量评估模式
│   └── 09_analyze_and_write.md  # 分析+撰写合并 prompt
├── scripts/              # Python 脚本（纯计算，无外部 API）
├── templates/            # 渲染模板（HTML + CSS）
└── references/           # 信源域名分级数据库
```

## 执行流程

18 步（步骤 11 已合并到步骤 9），每步混合使用系统工具和脚本：

1. PLAN — 系统 LLM + prompt/01_plan.md → 研究计划 JSON
2. MECE CHECK — 系统 LLM + prompt/02_mece_check.md → 自检
3. SEARCH（并行）— 系统 search 工具 × 4 层同时发起 → 原始结果 JSON
4. CLASSIFY — scripts/classify_sources.py → 分级结果
5. CRAAP EVAL（分层批量）— 系统 LLM + prompt/03a + 03b → 评分
6. AGGREGATE — scripts/aggregate_craap.py → 过滤低质量
7. TRIANGULATE — 系统 LLM + prompt/04_triangulate.md → 验证
8. QUALITY GATE 1 — scripts/quality_gate.py（含动态阈值）→ 信源充分性检查
9. ANALYZE + WRITE（合并）— 系统 LLM + prompt/09_analyze_and_write.md → 章节分析 + HTML
10. EXEC SUMMARY — 系统 LLM + prompt/06_write_exec_summary.md → 执行摘要
11. （已合并到步骤 9，跳过）
12. METHODOLOGY — 系统 LLM + prompt/08_write_methodology.md → 研究方法
13. REFERENCES — 自动生成参考文献 HTML
14. MERGE — 合并所有 HTML 片段
15. SANITIZE — scripts/sanitize_html.py → 清理 Markdown 残留
16. QUALITY GATE 2 — scripts/quality_gate.py → 报告完整性检查
17. RENDER — scripts/render_pdf.py + render_docx.py → 双格式
18. DELIVER — 交付 PDF + DOCX
