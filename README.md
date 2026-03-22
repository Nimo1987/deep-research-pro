<div align="center">

# 🔬 Deep Research Pro

**AI-Powered Deep Research Engine for OpenClaw**

[![Version](https://img.shields.io/badge/version-4.3.0-blue?style=flat-square)](https://github.com/Nimo1987/deep-research-pro)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-OpenClaw-orange?style=flat-square)](https://docs.openclaw.ai)

---

**📖 Read this in other languages:**

### [🇺🇸 English](docs/readme/README.md) · [🇨🇳 简体中文](docs/readme/README_zh.md)

---

</div>

> 代码驱动的深度调研引擎。CRAAP 信源评估 × 交叉信源加权 × 自适应时效过滤，输出专业级 PDF/DOCX 研究报告。

## ⚡ Quick Install

```bash
git clone https://github.com/Nimo1987/deep-research-pro.git ~/.openclaw/skills/deep-research-pro
pip install weasyprint python-docx beautifulsoup4 pyyaml
```

## 🎯 Features

- 🔍 **Four-Layer Search** — Background · Authority · Timeliness · Academic (60+ parallel keywords)
- 📊 **CRAAP Evaluation** — Five-dimension scoring with tiered assessment
- 🔗 **Cross-Source Weighting** — Auto bonus for multi-layer sources (+15% / +25%)
- ⏱️ **Adaptive Timeliness** — LLM-determined time windows (7d / 30d / 90d)
- ⚖️ **Currency Weight** — Configurable 1-3× weight per topic type
- ✅ **Triangulation** — Multi-source data verification
- 🚦 **Quality Gate** — Auto-retry with graceful degradation
- 📄 **PDF + DOCX** — Professional report output

## 📁 Structure

```
deep-research-pro/
├── SKILL.md                    # Workflow entry
├── config.yaml                 # Config
├── prompts/                    # LLM templates
├── scripts/                    # Pure-computation Python
├── templates/                  # Report rendering
├── references/                 # Source tier database
└── data/                       # Router configs
```

👉 **[Full Documentation (English)](docs/readme/README.md)** · **[完整文档（中文）](docs/readme/README_zh.md)**

## 📜 License

MIT
