<div align="center">

# 🔬 Deep Research Pro

**AI-Powered Deep Research Engine for OpenClaw**

[English](README.md) | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-4.3.0-blue?style=flat-square)](https://github.com/Nimo1987/deep-research-pro)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-OpenClaw-orange?style=flat-square)](https://docs.openclaw.ai)

</div>

---

> A code-driven deep research engine. CRAAP source evaluation × cross-source weighting × adaptive timeliness filtering. Produces professional PDF/DOCX research reports.

## ⚡ Quick Start

```bash
git clone https://github.com/Nimo1987/deep-research-pro.git ~/.openclaw/skills/deep-research-pro
pip install weasyprint python-docx beautifulsoup4 pyyaml
```

## 🎯 Core Capabilities

| Capability | Description |
|---|---|
| 🔍 **Four-Layer Search** | Background · Authority · Timeliness · Academic — 60+ keywords searched in parallel |
| 📊 **CRAAP Evaluation** | Five-dimension scoring: Currency, Relevance, Authority, Accuracy, Purpose |
| 🔗 **Cross-Source Weighting** | Same content across 2+ search layers → auto bonus (+15% for 2 layers, +25% for 3) |
| ⏱️ **Adaptive Timeliness** | LLM determines optimal time window per topic type (7d / 30d / 90d / unrestricted) |
| ⚖️ **Currency Weight** | Trending topics: Currency ×3 weight; stable topics: normal weight |
| ✅ **Triangulation** | Cross-verify key data points across multiple independent sources |
| 🚦 **Quality Gate** | Three-tier decision (PASS / WARN / FAIL) with auto-retry + graceful degradation |
| 📚 **Academic Sources** | arXiv + PubMed automatic paper retrieval |
| 💹 **Financial Data** | akshare A-share / HK / US stock data (optional) |
| 📄 **PDF + DOCX Output** | Professional research reports in both formats |

## 🏗️ How It Works

```
┌─────────────────┐
│   User Topic    │
└────────┬────────┘
         ▼
┌─────────────────┐
│  LLM generates  │  Keywords + timeliness policy + currency weight
│  research plan  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Four-layer      │  Background / Authority / Timeliness / Academic
│ parallel search │  60+ keywords, freshness-filtered
└────────┬────────┘
         ▼
┌─────────────────┐
│ Source classify  │  → Cross-source detection (URL + title similarity)
│ + CRAAP eval    │  Currency weight × cross-source bonus
└────────┬────────┘
         ▼
┌─────────────────┐
│ Triangulation   │  → Quality gate (PASS / WARN / FAIL)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Chapter-by-     │  Analysis + writing merged per section
│ chapter writing │  → Quality gate (retry on FAIL)
└────────┬────────┘
         ▼
┌─────────────────┐
│  PDF + DOCX     │  Professional report output
└─────────────────┘
```

## 📁 Directory Structure

```
deep-research-pro/
├── SKILL.md                         # Workflow orchestration entry
├── config.yaml                      # Thresholds & weights
├── _meta.json                       # Skill metadata
├── prompts/                         # LLM prompt templates
│   ├── 01_plan.md                   # Research plan (incl. timeliness strategy)
│   ├── 02_mece_check.md             # MECE self-check
│   ├── 03a_craap_extract.md         # Tier 1-2 fast extraction
│   ├── 03b_craap_batch.md           # Tier 3-5 batch evaluation
│   ├── 04_triangulate.md            # Triangulation
│   ├── 06_write_exec_summary.md     # Executive summary
│   ├── 08_write_methodology.md      # Methodology & limitations
│   └── 09_analyze_and_write.md      # Analysis + writing merged
├── scripts/                         # Python scripts (pure computation, no external APIs)
│   ├── classify_sources.py          # Source classification
│   ├── cross_source_detect.py       # Cross-source detection ✨ New in v4.3
│   ├── aggregate_craap.py           # CRAAP aggregation (timeliness + cross-source)
│   ├── quality_gate.py              # Quality gate
│   ├── fetch_financial_data.py      # Financial data fetcher
│   ├── sanitize_html.py             # HTML cleanup
│   ├── render_pdf.py                # PDF rendering
│   └── render_docx.py               # DOCX rendering
├── templates/                       # Report templates (HTML + CSS)
├── references/                      # Source domain tier database
└── data/                            # Router configs
```

## 🆕 What's New in v4.3

- **Adaptive Timeliness Filtering** — LLM analyzes topic type and assigns per-layer time windows
- **Currency Weight Adjustment** — Currency dimension configurable 1-3× weight for trending vs stable topics
- **Cross-Source Detection** — URL matching + title Jaccard similarity for multi-layer source weighting
- **Enhanced MECE Check** — Validates timeliness strategy fields

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `weasyprint` | PDF rendering |
| `python-docx` | DOCX generation |
| `beautifulsoup4` | HTML processing |
| `pyyaml` | Config parsing |

**System capabilities** (provided by host platform):
- Search tool (Brave Search or equivalent)
- LLM inference
- File I/O

## 📜 License

MIT
