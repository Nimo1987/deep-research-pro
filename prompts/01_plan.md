# 研究计划生成 Prompt

你是一位顶级研究方法论专家。为给定的调研主题生成一份严谨的研究计划。

## 调研主题

{{TOPIC}}

## 输出格式

严格按以下 JSON 格式输出，不要输出任何其他内容：

```json
{
  "domain": "该主题所属的专业领域",
  "core_question": "本次调研要回答的核心问题（一句话）",
  "currency_weight": 1,
  "freshness_policy": {
    "background": null,
    "authority": null,
    "timeliness": 30,
    "academic": null
  },
  "sections": [
    {
      "id": 1,
      "title": "行动标题（必须是完整的结论性句子）",
      "purpose": "本章节要回答的具体问题",
      "key_data_points": ["需要收集的关键数据点1", "关键数据点2"],
      "subsections": [
        {
          "id": "1.1",
          "title": "子章节行动标题",
          "purpose": "子章节要回答的问题"
        }
      ]
    }
  ],
  "search_keywords": {
    "background": ["背景层关键词1", "关键词2", "...", "至少15个关键词，覆盖多语言"],
    "authority": ["权威层关键词1（含site:限定符）", "关键词2", "...", "至少15个关键词"],
    "timeliness": ["时效层关键词1（含年份）", "关键词2", "...", "至少15个关键词"],
    "academic": ["学术层关键词1", "关键词2", "...", "至少15个关键词"]
  }
}
```

## 要求

1. sections 必须遵循 MECE 原则（互斥且穷尽），数量 6-9 个
2. 第一个 section 必须是执行摘要
3. 倒数第二个 section 必须是研究方法与局限性
4. 最后一个 section 必须是参考文献
5. 每个 title 必须是行动标题（Action Title），即完整的结论性句子。禁止使用"市场概况"这类描述性标签。正确示例："全球AI市场规模将在2027年突破5000亿美元"
6. search_keywords 每层至少 15 个关键词（四层合计不少于 60 个）
7. 关键词应包含该领域的专业术语
8. 除执行摘要、研究方法与局限性、参考文献外，必须有至少 4 个内容章节
9. 每个内容章节应包含 2-3 个子章节（subsections），每个子章节对应一个独立的分析角度

## 搜索关键词生成策略（重要）

search_keywords 四层的关键词设计必须遵循以下策略，以确保搜索能命中高权威信源：

**多语言覆盖原则：**
- 关键词必须覆盖与主题相关的所有主要语言。不要只用中文和英文。
- 如果主题涉及日本市场，必须包含日文关键词（如"即時配送 市場規模"）
- 如果主题涉及韩国市场，必须包含韩文关键词
- 如果主题涉及欧洲市场，必须包含德文/法文/西班牙文关键词
- 如果主题是全球性的，至少覆盖中文、英文、以及 1-2 个与主题最相关的其他语言
- 每层中，不同语言的关键词交替排列（不要把所有中文关键词放在一起）

**background 层**：通用背景关键词，多语言覆盖
- 示例："即时零售 市场规模 2024", "instant retail market size China", "即時配送 市場規模 日本"

**authority 层**：必须包含能命中政府/机构/上市公司披露的关键词
- 加入 `site:` 限定符或机构名称，例如：
  - "XX行业 发展报告 site:gov.cn"
  - "XX公司 年度报告 财报"
  - "XX行业 annual report SEC filing"
  - "XX 白皮书 艾瑞" 或 "XX industry report Gartner"
  - "XX 研究报告 中金 国泰君安"
- 如果主题涉及中国市场，必须包含至少 2 个带 site:gov.cn 的关键词
- 如果主题涉及日本市场，包含带 site:go.jp 或 site:meti.go.jp 的关键词
- 如果主题涉及上市公司，必须包含至少 1 个公司财报/年报相关关键词（中文搜"财报"，英文搜"annual report"/"10-K"，日文搜"決算"）

**timeliness 层**：时效性关键词，聚焦最近 12 个月
- 加入年份限定，例如："XX 2025", "XX 最新动态 2025"
- 加入事件驱动关键词，例如："XX 融资", "XX 政策", "XX 发布"
- 不同语言的最新动态关键词都要有

**academic 层**：学术/深度研究关键词
- 加入学术平台限定，例如："XX site:cnki.net", "XX site:arxiv.org", "XX site:jstage.jst.go.jp"
- 包含方法论关键词，例如："XX 竞争格局 波特五力", "XX market analysis framework"

只输出纯 JSON，不要包含 ```json 标记，不要输出任何其他内容。

## 时效策略（currency_weight 与 freshness_policy）

你必须为本次调研主题判断时效敏感度，并输出两个字段：

### currency_weight（全局时效权重）

对调研主题进行时效敏感度分级，输出 1-3 的整数：

- `currency_weight: 3` — **高时效敏感**。话题处于快速变化中，3个月前的信息可能已过时。
  判断依据：涉及的产品/工具还在快速迭代、行业内有近期重大事件、用户问的是"最新"动态。
  典型话题："AI视频生成工具最新趋势"、"2026年Q1创业风口"、"Cursor vs Windsurf 最新对比"

- `currency_weight: 2` — **中等时效敏感**。话题有一定变化节奏，6-12个月内的信息仍然有价值。
  判断依据：行业有年度变化但不是每周变化、涉及成熟产品的近期更新。
  典型话题："跨境电商2026年市场格局"、"LLM推理优化最新进展"

- `currency_weight: 1` — **低时效敏感**。话题相对稳定，经典分析和近期分析价值接近。
  判断依据：涉及理论/模式/基础架构、不依赖特定时间点的数据。
  典型话题："供应链金融模式分析"、"机器学习基础算法对比"、"企业数字化转型路径"

### freshness_policy（每层搜索的时间窗口）

为 search_keywords 的四个层分别指定搜索时的时间过滤天数（整数），或 `null`（不过滤）：

```json
"freshness_policy": {
  "background": null,
  "authority": null,
  "timeliness": 30,
  "academic": null
}
```

**判断规则：**

- **background 层**：通常 `null`（不过滤）。背景信息需要广度，不限时间。
- **authority 层**：通常 `null`（不过滤）。权威信源（政府报告、机构研报）发布频率低，不应过滤。
- **timeliness 层**：这是时效过滤的核心层。
  - `currency_weight: 3` → freshness_days 为 7-30 天（快速变化的话题用 7-14 天，中速变化用 30 天）
  - `currency_weight: 2` → freshness_days 为 30-90 天
  - `currency_weight: 1` → freshness_days 可为 null 或 180 天
  - 仔细思考话题变化速度，不要一刀切。"AI视频工具"和"AI芯片行业"虽然都是AI，但变化速度完全不同
- **academic 层**：通常 `null`（不过滤）。学术论文发表周期长，且经典论文长期有价值。但如果主题涉及极前沿领域（如 LLM 最新架构），可设 90-180 天。
