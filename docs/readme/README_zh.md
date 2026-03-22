<div align="center">

# 🔬 Deep Research Pro

**AI 驱动的深度调研引擎 · OpenClaw 专用**

[English](README.md) | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-4.3.0-blue?style=flat-square)](https://github.com/Nimo1987/deep-research-pro)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-OpenClaw-orange?style=flat-square)](https://docs.openclaw.ai)

</div>

---

> 代码驱动的深度调研引擎。CRAAP 信源评估 × 交叉信源加权 × 自适应时效过滤，输出专业级 PDF/DOCX 研究报告。

## ⚡ 快速安装

```bash
git clone https://github.com/Nimo1987/deep-research-pro.git ~/.openclaw/skills/deep-research-pro
pip install weasyprint python-docx beautifulsoup4 pyyaml
```

## 🎯 核心能力

| 能力 | 说明 |
|---|---|
| 🔍 **四层搜索** | 背景层 · 权威层 · 时效层 · 学术层 — 60+ 关键词并行搜索 |
| 📊 **CRAAP 评估** | 五维度评分：时效性、相关性、权威性、准确性、目的性 |
| 🔗 **交叉信源加权** | 同一内容出现在 2+ 搜索层 → 自动加分（2层 +15%，3层 +25%） |
| ⏱️ **自适应时效过滤** | LLM 根据话题类型判断最佳时间窗口（7天 / 30天 / 90天 / 不限） |
| ⚖️ **时效权重调整** | 趋势型话题：Currency 维度 ×3 权重；稳定型话题：正常权重 |
| ✅ **三角验证** | 多信源交叉验证关键数据点 |
| 🚦 **质量门控** | 三级判定（PASS / WARN / FAIL），自动重试 + 优雅降级 |
| 📚 **学术信源** | arXiv + PubMed 自动论文检索 |
| 💹 **金融数据** | akshare A股 / 港股 / 美股数据（可选） |
| 📄 **PDF + DOCX 输出** | 专业格式研究报告 |

## 🏗️ 工作原理

```
┌─────────────────┐
│   用户调研主题    │
└────────┬────────┘
         ▼
┌─────────────────┐
│  LLM 生成研究计划 │  关键词 + 时效策略 + 时效权重
└────────┬────────┘
         ▼
┌─────────────────┐
│ 四层并行搜索     │  背景 / 权威 / 时效 / 学术
│                 │  60+ 关键词，带时间过滤
└────────┬────────┘
         ▼
┌─────────────────┐
│ 信源分类         │  → 交叉信源检测（URL + 标题相似度）
│ + CRAAP 评估     │  时效权重 × 交叉加权
└────────┬────────┘
         ▼
┌─────────────────┐
│ 三角验证         │  → 质量门控（PASS / WARN / FAIL）
└────────┬────────┘
         ▼
┌─────────────────┐
│ 逐章分析 + 撰写  │  分析与撰写合并执行
│                 │  → 质量门控（失败自动重试）
└────────┬────────┘
         ▼
┌─────────────────┐
│  PDF + DOCX      │  专业格式报告输出
└─────────────────┘
```

## 📁 目录结构

```
deep-research-pro/
├── SKILL.md                         # 流程编排入口
├── config.yaml                      # 阈值和权重配置
├── _meta.json                       # Skill 元数据
├── prompts/                         # LLM Prompt 模板
│   ├── 01_plan.md                   # 研究计划生成（含时效策略）
│   ├── 02_mece_check.md             # MECE 自检
│   ├── 03a_craap_extract.md         # Tier 1-2 快速提取
│   ├── 03b_craap_batch.md           # Tier 3-5 批量评估
│   ├── 04_triangulate.md            # 三角验证
│   ├── 06_write_exec_summary.md     # 执行摘要
│   ├── 08_write_methodology.md      # 研究方法与局限性
│   └── 09_analyze_and_write.md      # 分析 + 撰写合并
├── scripts/                         # Python 脚本（纯计算，无外部 API）
│   ├── classify_sources.py          # 信源分类
│   ├── cross_source_detect.py       # 交叉信源检测 ✨ v4.3 新增
│   ├── aggregate_craap.py           # CRAAP 聚合（时效权重 + 交叉加权）
│   ├── quality_gate.py              # 质量门控
│   ├── fetch_financial_data.py      # 金融数据拉取
│   ├── sanitize_html.py             # HTML 清理
│   ├── render_pdf.py                # PDF 渲染
│   └── render_docx.py               # DOCX 渲染
├── templates/                       # 渲染模板（HTML + CSS）
├── references/                      # 信源域名分级数据库
└── data/                            # 路由配置
```

## 🆕 v4.3 更新

- **自适应时效过滤** — LLM 分析话题类型，为每层搜索指定时间窗口
- **时效权重调整** — Currency 维度可配置 1-3 倍权重，区分趋势型与稳定型话题
- **交叉信源检测** — URL 匹配 + 标题 Jaccard 相似度，跨层内容自动加权
- **MECE 自检增强** — 新增时效策略字段校验

## 📦 依赖

| 包名 | 用途 |
|---|---|
| `weasyprint` | PDF 渲染 |
| `python-docx` | DOCX 生成 |
| `beautifulsoup4` | HTML 处理 |
| `pyyaml` | 配置解析 |

**系统能力**（由宿主平台提供）：
- 搜索工具（Brave Search 或同等）
- LLM 推理能力
- 文件读写

## 📜 License

MIT
