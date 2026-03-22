# Deep Research Pro v4.3

代码驱动的深度调研引擎。流程由 SKILL.md 编排，Python 脚本做纯计算，搜索和 LLM 推理全部调用系统能力。

## 分发层（主 Session 必须先执行这一步）

> 这一步是主 session 唯一需要做的事。后续所有步骤由 subagent 自主完成。

当主 session 收到深度调研请求时：

1. 从用户输入中提取调研主题（`{TOPIC}`）
2. 获取当前时间戳（格式 `YYYYMMDD_HHmmss`），生成标签 `swan-r_{timestamp}`
3. 向用户发送一条启动确认消息：`"🦢 Swan 已启动，研究主题：{TOPIC}。预计 10-15 分钟，完成后自动通知你。"`
4. 立即 spawn subagent：
   - `label`: `swan-r_{timestamp}`
   - `mode`: `run`
   - `runtime`: `subagent`
   - `task`: 将以下内容作为 task 传入（替换 `{TOPIC}` 和 `{SKILL_DIR}`）：
     ```
     你是一个深度研究 agent（swan）。请完整执行 deep-research-pro skill 的全部流程。

     调研主题：{TOPIC}
     Skill 目录：/root/.openclaw/workspace/skills/deep-research-pro

     执行前请先 read {SKILL_DIR}/SKILL.md，从"执行流程"部分开始执行（跳过"分发层"）。

     执行完成后，通过 message 工具将 PDF 和 DOCX 文件发送到 Telegram（channel: telegram, to: 697273061）。
     ```
5. 主 session **立即结束**，不等待 subagent 返回结果。

## CRITICAL — 执行纪律

> 以下规则优先级高于所有流程步骤。违反任何一条都会导致严重的时间浪费。

### 禁止行为（NEVER）

1. **NEVER 等待汇报**：等待 subagent 完成或 shell 命令返回时，禁止发送任何"正在等待…""已运行 X 秒…""进度更新"之类的消息。保持沉默直到结果返回。
2. **NEVER 过渡消息**：阶段完成后，禁止发送"XX 已完成，现在进入 YY 阶段"的过渡性消息。直接执行下一阶段的第一个动作。
3. **NEVER 上下文堆积**：禁止将超过 500 tokens 的中间结果（搜索结果、CRAAP 评分、HTML 片段）保留在对话上下文中。

### 必须行为（ALWAYS）

4. **ALWAYS 结果直写**：所有中间结果立即写入文件（约定路径），后续步骤通过 `read` 工具按需读取。
5. **ALWAYS 一步到位**：每个阶段完成后，立即执行下一阶段的第一个工具调用，中间不插入任何纯文本输出。
6. **ALWAYS 静默执行**：仅在以下 3 个时机向用户发消息：
   - 任务启动时（1 条，说明研究主题和预计耗时 10-15 分钟）
   - 任务完成时（1 条，附带 PDF 和 DOCX 交付物）
   - 遇到需要用户决策的错误时

### Subagent 使用原则

7. **只在以下条件全部满足时使用 subagent**：任务完全独立、不需要主 agent 中间数据、预计耗时 > 2 分钟。
8. **以下任务禁止使用 subagent**（直接在主 agent 中执行）：CRAAP 评估、三角验证、执行摘要撰写、研究方法章节撰写。
9. **章节分析与撰写（步骤 9）**：如果内容章节数 ≥ 4，可以 spawn subagent 并行处理多个章节；否则串行执行。
10. **spawn subagent 后**：主 agent 继续执行不依赖该 subagent 结果的后续步骤（如准备下一阶段的 prompt 模板），禁止空等。

### 上下文管理规则

11. **搜索结果**：保存到 `raw_search_results.json` 后，后续步骤不得将完整搜索结果放入 prompt。需要引用时，通过 `read` 工具读取文件。
12. **CRAAP 评分**：保存后，后续步骤只引用 `eval_stats.json` 的统计摘要（总数、通过数、平均分），不引用逐条评分。
13. **章节 HTML**：每个章节撰写完成后，只在上下文中保留 `{章节标题: 文件路径}` 的索引，不保留完整 HTML。
14. **目标**：主 agent 上下文在整个流程中保持在 30K tokens 以内。

## 触发条件

当用户要求进行深度调研、行业分析、市场研究、技术评估或任何需要多信源交叉验证的研究任务时，使用此 Skill。

## 环境准备（仅首次）

```bash
pip install weasyprint python-docx beautifulsoup4 pyyaml
```

## 执行流程

> 以下每一步必须严格按顺序执行。标注"系统LLM"的步骤，将对应 prompt 文件的内容作为 system/user message 发送给系统主模型；标注"系统搜索"的步骤，使用系统的 search 工具；标注"脚本"的步骤，用 shell 执行对应 Python 脚本。

### 准备工作

1. 创建工作目录：`{workspace}/deep-research-{topic_slug}/`，下设 `sources/`、`analysis/`、`output/` 三个子目录
2. 将用户的调研主题记录到 `{workspace}/deep-research-{topic_slug}/topic.txt`
3. 初始化重试计数器：`search_retry=0`, `report_retry=0`

---

### 阶段一：研究计划（PLAN）

**步骤 1 — 生成研究计划**
- 读取 `{SKILL_DIR}/prompts/01_plan.md`
- 将其中的 `{{TOPIC}}` 替换为用户的调研主题
- 将替换后的内容作为 prompt 发送给系统 LLM
- 要求系统 LLM 以 JSON 格式输出
- 将输出保存到 `{workspace}/sources/research_plan.json`

**步骤 2 — MECE 自检**
- 读取 `{SKILL_DIR}/prompts/02_mece_check.md`
- 将 `{{PLAN_JSON}}` 替换为步骤 1 的输出
- 发送给系统 LLM，要求 JSON 输出
- 如果 `is_mece` 为 false，回到步骤 1 重新生成（最多重试 2 次）

---

**步骤 2.5 — 金融数据拉取（条件执行）**

> ⚠️ 此步骤完全可选。akshare 未安装时自动跳过，不影响后续流程。

**触发条件**：topic 中包含以下任意关键词时执行：
- A股：A股、沪深、上证、深证、创业板、科创板、港股、香港、恒生、恒指、H股
- 美股：美股、纳斯达克、NYSE、NASDAQ、标普、道琼斯
- 个股代码特征：6位数字（A股）、2-5位英文字母（美股）、5位数字含前缀00/06（港股）

**执行步骤：**

1. **生成路由参数**（系统 LLM）：  
   根据 topic 和 `research_plan.json` 生成一个路由 hint JSON，格式：
   ```json
   {
     "market": "A股 | 美股 | 港股",
     "scenarios": ["场景1", "场景2"],
     "symbol": "股票代码（如有）",
     "start": "YYYYMMDD",
     "end": "YYYYMMDD",
     "industry": "行业名（如有）",
     "index": "指数代码（如有）"
   }
   ```
   可用场景参考 `{SKILL_DIR}/data/akshare_router.json`

2. **执行脚本**：
   ```bash
   python {SKILL_DIR}/scripts/fetch_financial_data.py \
     --topic "{TOPIC}" \
     --routing-hint '{ROUTING_HINT_JSON}' \
     --output {workspace}/sources/financial_data.json \
     --router {SKILL_DIR}/data/akshare_router.json
   ```

3. **处理结果**：
   - 脚本退出码 0 且 `status=success`：金融数据已就绪，阶段三报告中可直接引用 `financial_data.json`
   - 脚本退出码 0 且 `status=skipped`：akshare 未安装或 topic 不涉及金融，**静默继续**，不报错不提示
   - 脚本退出码非 0：记录警告，继续执行（金融数据非必需）

4. **在报告中使用金融数据**（仅 status=success 时）：
   - 数据引用章节标注来源：`数据来源：akshare / {API名}`
   - 结构化数据优先于搜索引擎结果（数据更准确）
   - 保留原始数值，不自行推算未出现在数据中的指标

---

**步骤 2.6 — 学术文献拉取（条件执行）**

> ⚠️ 此步骤完全可选。未配置相关环境变量时自动跳过，不影响后续流程。

**触发条件**：topic 中包含以下任意类型关键词时执行：
- 学术/研究类：论文、研究、综述、meta分析、clinical trial、study、paper、research、review
- 生物医学类：药物、基因、疾病、临床、医学、cancer、drug、genome、protein、病理、治疗
- AI/技术类：LLM、transformer、diffusion、neural network、deep learning、机器学习、强化学习

**数据源 A：arXiv（无需安装，直接调用 API）**

适用场景：AI、物理、数学、计算机科学、经济学等领域

**前置检测（跳过条件）**：
```bash
# 测试 arXiv API 连通性，失败则跳过（超时 5 秒）
curl -s --max-time 5 "https://export.arxiv.org/api/query?search_query=all:test&max_results=1" -o /dev/null
# 退出码非 0 → 静默跳过，不报错
```

执行方式（直接 exec）：
```bash
# 搜索最近 30 天的相关论文（最多 10 篇）
curl -s "https://export.arxiv.org/api/query?search_query=all:{TOPIC_EN}&sortBy=submittedDate&sortOrder=descending&max_results=10" \
  -o {workspace}/sources/arxiv_results.xml

# 提取标题、摘要、链接
python3 -c "
import xml.etree.ElementTree as ET
import json

tree = ET.parse('{workspace}/sources/arxiv_results.xml')
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}
papers = []
for entry in root.findall('atom:entry', ns):
    papers.append({
        'title': entry.find('atom:title', ns).text.strip(),
        'summary': entry.find('atom:summary', ns).text.strip()[:500],
        'url': entry.find('atom:id', ns).text.strip(),
        'published': entry.find('atom:published', ns).text[:10],
        'search_layer': 'academic',
        'search_keyword': '{TOPIC_EN}',
        'source': 'arxiv'
    })
print(json.dumps(papers, ensure_ascii=False, indent=2))
" > {workspace}/sources/arxiv_papers.json
```

结果处理：
- 成功拿到论文：将 `arxiv_papers.json` 内容合并进 `raw_search_results.json`（作为学术层补充）
- curl 失败或结果为空：静默跳过，不报错

**数据源 B：PubMed EDirect（需手动安装 esearch/efetch）**

适用场景：生物医学、临床研究、药学等领域

**前置检测（跳过条件）**：以下任意一项不满足时静默跳过：
- `NCBI_API_KEY` 环境变量已设置
- `CF_PROXY_URL` 环境变量已设置（或 NCBI API 本机可直连）

```bash
# 检测是否具备 PubMed 访问条件
python3 -c "
import os, sys
api_key = os.environ.get('NCBI_API_KEY', '')
proxy = os.environ.get('CF_PROXY_URL', '')
if not api_key:
    print('SKIP: NCBI_API_KEY not set')
    sys.exit(0)
if not proxy:
    print('SKIP: CF_PROXY_URL not set')
    sys.exit(0)
print('OK')
" | grep -q "OK" || { echo "PubMed 跳过（环境变量未配置）"; exit 0; }
```

若检测通过，执行（通过 CF 代理绕过 IP 封锁）：
```bash

python3 -c "
import requests, urllib.parse, json, os

proxy = os.environ.get('CF_PROXY_URL', '')
secret = os.environ.get('CF_PROXY_SECRET', '')
api_key = os.environ.get('NCBI_API_KEY', '')
topic = '{TOPIC_EN}'
ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

params = urllib.parse.urlencode({'db': 'pubmed', 'term': topic + '[Title/Abstract]', 'retmax': '20', 'retmode': 'json', 'api_key': api_key})
target = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}'

hdrs = {'User-Agent': ua}
if proxy:
    hdrs.update({'X-Proxy-Url': target, 'X-Proxy-Secret': secret})
    r = requests.get(proxy, headers=hdrs, timeout=15)
else:
    r = requests.get(target, headers=hdrs, timeout=15)

ids = r.json()['esearchresult']['idlist']
print('\n'.join(ids))
" > {workspace}/sources/pubmed_ids.txt

# 批量拉取摘要
python3 -c "
import requests, urllib.parse, os

proxy = os.environ.get('CF_PROXY_URL', '')
secret = os.environ.get('CF_PROXY_SECRET', '')
api_key = os.environ.get('NCBI_API_KEY', '')
ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

ids = open('{workspace}/sources/pubmed_ids.txt').read().strip()
if not ids: exit()

params = urllib.parse.urlencode({'db': 'pubmed', 'id': ids.replace('\n', ','), 'retmode': 'xml', 'api_key': api_key})
target = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}'

hdrs = {'User-Agent': ua}
if proxy:
    hdrs.update({'X-Proxy-Url': target, 'X-Proxy-Secret': secret})
    r = requests.get(proxy, headers=hdrs, timeout=30)
else:
    r = requests.get(target, headers=hdrs, timeout=30)

open('{workspace}/sources/pubmed_fetch.xml', 'wb').write(r.content)
"

# 解析 XML → JSON
python3 -c "
import xml.etree.ElementTree as ET, json
tree = ET.parse('{workspace}/sources/pubmed_fetch.xml')
papers = []
for art in tree.getroot().findall('.//PubmedArticle'):
    pmid = art.findtext('.//PMID', '')
    title = art.findtext('.//ArticleTitle', '')
    abstract = art.findtext('.//AbstractText', '')
    if title:
        papers.append({'title': title, 'summary': abstract[:500], 'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/', 'search_layer': 'academic', 'source': 'pubmed'})
print(json.dumps(papers, ensure_ascii=False, indent=2))
" > {workspace}/sources/pubmed_papers.json

# 格式化为 JSON
python3 -c "
import json, sys
papers = []
for line in open('{workspace}/sources/pubmed_raw.txt'):
    parts = line.strip().split('\t')
    if len(parts) >= 3:
        pmid, title, abstract = parts[0], parts[1], parts[2]
        papers.append({
            'title': title,
            'summary': abstract[:500],
            'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
            'search_layer': 'academic',
            'search_keyword': '{TOPIC_EN}',
            'source': 'pubmed'
        })
print(json.dumps(papers, ensure_ascii=False, indent=2))
" > {workspace}/sources/pubmed_papers.json
```

结果处理：
- 成功拿到论文：将 `pubmed_papers.json` 内容合并进 `raw_search_results.json`
- esearch 未安装或失败：静默跳过，不报错

**在报告中使用学术数据**（仅有结果时）：
- 论文引用格式：`[标题](链接) — arXiv {日期}` 或 `[标题](PubMed链接)`
- 学术层来源优先用于"研究现状"、"技术背景"章节
- 摘要超过 500 字时，用 `web_fetch` 抓取原文 PDF 链接补充细节

---

### 阶段二：多层搜索（SEARCH）

**步骤 3 — 执行四层搜索（并行）**

从 `research_plan.json` 中提取 `search_keywords` 和 `freshness_policy`，**同时**对四层的所有关键词发起 search 调用：

| 层 | 关键词来源 | 搜索目的 |
|---|-----------|---------|
| 背景层 | search_keywords.background | 建立基础认知 |
| 权威层 | search_keywords.authority | 获取权威信源 |
| 时效层 | search_keywords.timeliness | 获取最新动态 |
| 学术层 | search_keywords.academic | 获取学术/研究信源 |

**时效过滤（freshness 参数透传）：**

从 `research_plan.json` 中读取 `freshness_policy`，为每层搜索指定 `freshness` 参数：

| freshness_policy 值 | search 工具 freshness 参数 | 含义 |
|---|---|---|
| `null` | 不传 freshness 参数 | 不限时间 |
| 1-6 | `"week"` | 最近 1 周 |
| 7-30 | `"month"` | 最近 1 个月 |
| 31-90 | `"quarter"` | 最近 3 个月 |
| 91-365 | `"year"` | 最近 1 年 |
| >365 | 不传 freshness，在关键词末尾加年月限定 | 用关键词限定时间 |

**执行规则：** 搜索每个关键词时，根据该关键词所属层的 freshness_policy 值，决定是否传入 freshness 参数。例如 timeliness 层 freshness_policy=30，则该层所有关键词搜索时传入 `freshness: "month"`。

**并行执行规则：**
- 将四层的所有关键词（通常 60-80 个）**一次性全部发起搜索**，不需要等某一层完成再搜下一层
- 如果系统支持批量工具调用，在一条消息中发起多个 search 调用
- 如果系统不支持批量调用，则按关键词逐个发起，但不按层分组等待

**搜索数量目标（重要）：**
- 原始搜索结果总量目标：**不少于 60 条**（去重前）
- 如果所有关键词搜完后总结果不足 60 条，必须追加搜索：
  1. 将现有关键词的同义词、英文翻译、缩写形式作为新关键词
  2. 去掉 site: 限定符重新搜索（限定符可能过滤了有效结果）
  3. 拆分复合关键词为更细粒度的单独搜索
- 每个关键词搜索应期望返回 3-10 条结果。如果某个关键词只返回 1-2 条，尝试简化关键词重搜

**搜索容错规则（重要）：**
- 每个关键词单独搜索。如果某个关键词搜索返回空结果或报错，**跳过该关键词继续下一个**，不要中断整个流程
- 搜索结果中的每一条必须包含 `url`、`title`、`content` 三个字段。如果某条结果缺少 `url`，丢弃该条
- 将所有有效搜索结果汇总保存到 `{workspace}/sources/raw_search_results.json`，格式为 JSON 数组
- **保存后立即从上下文中卸载搜索结果**（后续步骤通过 `read` 工具读取文件）

```json
[
  {
    "url": "...",
    "title": "...",
    "content": "...",
    "search_layer": "background|authority|timeliness|academic",
    "search_keyword": "..."
  }
]
```

**步骤 4 — 信源分类**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/classify_sources.py \
    --input {workspace}/sources/raw_search_results.json \
    --config {SKILL_DIR}/config.yaml \
    --tiers {SKILL_DIR}/references/source_tiers.yaml \
    --output {workspace}/sources/classified_sources.json
  ```
- 脚本内置空值防御，会自动跳过 None、空 URL、非法格式的条目

**步骤 4.5 — 交叉信源检测**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/cross_source_detect.py \
    --input {workspace}/sources/raw_search_results.json \
    --output {workspace}/sources/cross_source_map.json
  ```
- 该脚本检测同一 URL（或高度相似标题）出现在多个搜索层的情况
- 同一内容出现在 2+ 个搜索层 → `cross_source: true`，CRAAP 总分 +15%
- 出现在 3+ 个搜索层 → CRAAP 总分 +25%
- 输出的 `cross_source_map.json` 将在步骤 6 聚合时使用
- 脚本内置空值防御，搜索结果为空或格式异常时输出空映射，不中断流程

---

### 阶段三：信源评估（EVALUATE）

**步骤 5 — CRAAP 分层评估**

将 `classified_sources.json` 中的信源按层级分组，采用不同评估策略以减少 LLM 调用次数：

**Tier 1-2（权威信源）— 快速提取模式：**
- 自动赋予基准 CRAAP 分数：authority=9, accuracy=8, purpose=9（域名已证明权威性）
- 将所有 Tier 1-2 信源合并为一批
- 读取 `{SKILL_DIR}/prompts/03a_craap_extract.md`
- 将 `{{SOURCES_BATCH}}` 替换为该批信源的 JSON 数组（每条包含 url、title、content）
- 发送给系统 LLM，要求 JSON 输出
- LLM 只需评估 currency 和 relevance，并提取 key_facts
- 将基准分与 LLM 返回的分数合并为完整 CRAAP 记录
- **1 次 LLM 调用完成所有 Tier 1-2 信源**

**Tier 3（主流媒体）— 批量完整评估：**
- 每 5 条信源为一批
- 读取 `{SKILL_DIR}/prompts/03b_craap_batch.md`
- 将 `{{SOURCES_BATCH}}` 替换为该批信源的 JSON 数组
- 发送给系统 LLM，要求 JSON 输出（一次返回该批所有信源的完整 CRAAP 评分）
- **通常 2-3 次 LLM 调用**

**Tier 4-5（一般/社交）— 精简批量评估：**
- 仅取 top 10 条（按 content 长度排序，优先评估内容丰富的）
- 每 10 条为一批
- 读取 `{SKILL_DIR}/prompts/03b_craap_batch.md`
- 将 `{{SOURCES_BATCH}}` 替换为该批信源的 JSON 数组
- 发送给系统 LLM，要求 JSON 输出
- **1 次 LLM 调用**

**容错规则**：任何批次的 LLM 评估失败或返回异常格式，**跳过该批次继续下一批**，不中断流程。
将所有成功评估的结果保存到 `{workspace}/sources/craap_scores.json`。

**步骤 6 — 聚合与过滤**
- 从 `research_plan.json` 中读取 `currency_weight`（1-3，如不存在则默认为 1）
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/aggregate_craap.py \
    --sources {workspace}/sources/classified_sources.json \
    --scores {workspace}/sources/craap_scores.json \
    --config {SKILL_DIR}/config.yaml \
    --output {workspace}/sources/filtered_sources.json \
    --stats {workspace}/sources/eval_stats.json \
    --cross-source-map {workspace}/sources/cross_source_map.json \
    --currency-weight {currency_weight}
  ```
- 该脚本会：
  - 根据 `currency_weight` 调整 CRAAP 五维度中 Currency 的权重占比
  - 对交叉信源（cross_source_map.json 中标记的）自动加权
  - 输出 `eval_stats.json` 中包含 `cross_source_count`、`currency_weight`、`adjusted_weights` 字段

**步骤 7 — 三角验证**
- 读取 `{SKILL_DIR}/prompts/04_triangulate.md`
- 将 `{{TOPIC}}` 和 `{{FACTS_JSON}}` 替换（FACTS_JSON 来自 craap_scores.json 中各信源的 key_facts）
- 发送给系统 LLM，要求 JSON 输出
- 保存到 `{workspace}/analysis/triangulation.json`

**步骤 8 — 质量门控 1（信源充分性）**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/quality_gate.py check_sources \
    --filtered {workspace}/sources/filtered_sources.json \
    --stats {workspace}/sources/eval_stats.json \
    --triangulation {workspace}/analysis/triangulation.json \
    --config {SKILL_DIR}/config.yaml \
    --retry-count {search_retry} \
    --warnings-output {workspace}/sources/quality_warnings.json
  ```
- **三级判定逻辑：**
  - `PASS`（退出码 0，输出 PASS）→ 继续下一步
  - `WARN`（退出码 0，输出 WARN）→ 继续下一步，但将 warnings.json 中的问题记录下来，在步骤 12 写入"研究方法与局限性"章节
  - `FAIL`（退出码 1）→ 需要重试，执行以下操作：
    1. `search_retry += 1`
    2. 如果 `search_retry > 2`，**强制降级为 WARN 继续**（不再重试）
    3. 如果 `search_retry <= 2`，回到步骤 3，但**必须变换搜索策略**：
       - 阅读 FAIL 输出中的建议（如"建议搜索关键词加上 site:.gov"）
       - 在原关键词基础上添加 site: 限定符、同义词、英文翻译等
       - 新关键词必须与上一轮不同，禁止用完全相同的关键词重试
       - 新搜索结果追加到已有的 raw_search_results.json 中（不覆盖）

---

### 阶段四：结构化分析与撰写（ANALYZE + WRITE 合并）

**步骤 9 — 逐章分析与撰写（合并）**

对 `research_plan.json` 中的每个内容章节（跳过"执行摘要"、"研究方法与局限性"、"参考文献"章节）：
- 读取 `{SKILL_DIR}/prompts/09_analyze_and_write.md`
- 替换 `{{TOPIC}}`、`{{CORE_QUESTION}}`、`{{SECTION_TITLE}}`、`{{SECTION_PURPOSE}}`、`{{KEY_DATA_POINTS}}`
  - `{{SOURCE_MATERIALS}}`：通过 `read` 工具读取 `filtered_sources.json` 中 top 30 信源的摘要
  - `{{TRIANGULATION}}`：通过 `read` 工具读取 `triangulation.json`
- 发送给系统 LLM，要求 JSON 输出（包含 `analysis` 和 `html` 两个字段）
- 将返回的 `analysis` 字段保存到 `{workspace}/analysis/section_{n}_analysis.json`
- 将返回的 `html` 字段保存到 `{workspace}/analysis/section_{n}.html`
- **字数后置检查（必须执行）**：保存后，统计 html 字段的纯文本字数（去除所有 HTML 标签后的字符数）。如果少于 1500 字，立即重新发送该章节的 prompt 给系统 LLM，并在 prompt 开头追加：`"注意：你上次输出的章节只有 X 字，远低于 1500 字的最低要求。这次你必须写到 1500 字以上，包含至少 2 个子标题和 1 个数据表格。展开论述每个论点，加入数据对比、原因分析和影响推演。"` 最多重试 1 次。
- **保存后仅在上下文中保留 `{"章节标题": "section_{n}.html"}` 索引，不保留完整内容**

**并行处理注意事项（当使用 subagent 时）：**
- `filtered_sources.json` 和 `triangulation.json` 是只读文件，多个 subagent 可安全并行读取
- 每个 subagent 必须写入不同的文件（`section_{n}_analysis.json` 和 `section_{n}.html`，其中 n 是该章节在 research_plan 中的 id），禁止多个 subagent 写同一个文件
- 主 agent 负责在所有 subagent 完成后收集各章节的文件路径索引

---

### 阶段五：报告撰写（WRITE）

**步骤 10 — 撰写执行摘要**
- 读取 `{SKILL_DIR}/prompts/06_write_exec_summary.md`
- 替换 `{{TOPIC}}`、`{{CORE_QUESTION}}`、`{{SECTION_SUMMARIES}}`（通过 `read` 工具从各 `section_{n}_analysis.json` 中提取 core_argument）
- 发送给系统 LLM
- 输出为 HTML 片段，保存到 `{workspace}/analysis/exec_summary.html`

**步骤 11 — 已合并到步骤 9，跳过**

> 原逐章撰写逻辑已合并到步骤 9（分析与撰写一步完成），此步骤不再执行。

**步骤 12 — 撰写研究方法与局限性**
- 读取 `{SKILL_DIR}/prompts/08_write_methodology.md`
- 替换 `{{TOPIC}}`、`{{SEARCH_STATS}}`、`{{PASSED_SOURCES}}`、`{{REJECTED_SOURCES}}`、`{{VERIFIED_POINTS}}`、`{{CONFLICTING_POINTS}}`、`{{TIER_DISTRIBUTION}}`
- **如果存在 `quality_warnings.json`，读取其中的 `warnings` 数组，将每条 warning 格式化为无序列表文本后替换 prompt 中的 `{{QUALITY_WARNINGS}}`。格式示例：**
  ```
  - 信源数量偏少: 8/10（可继续但报告深度受限）
  - 一级权威信源不足: 0/1（已重试2次，降级继续）
  ```
  **如果不存在 `quality_warnings.json`，则将 `{{QUALITY_WARNINGS}}` 替换为"无"**
- 发送给系统 LLM
- 输出为 HTML 片段

**步骤 13 — 生成参考文献**

从 filtered_sources.json 中按权重排序，生成 HTML 格式的参考文献列表：
```html
<h2>参考文献</h2>
<ol class="references">
  <li><a href="URL">标题</a> <span class="ref-meta">[层级, CRAAP: X.X]</span></li>
</ol>
```

**步骤 14 — 合并所有 HTML 片段**

按以下顺序合并：
1. `<h1 class="report-title">{主题}</h1>`
2. `<div class="report-meta">深度调研报告</div>`
3. 执行摘要 HTML
4. 各章节 HTML
5. 研究方法与局限性 HTML
6. 参考文献 HTML

保存到 `{workspace}/analysis/full_report.html`

---

### 阶段六：清理与渲染（RENDER）

**步骤 15 — 清理 Markdown 残留**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/sanitize_html.py \
    --input {workspace}/analysis/full_report.html \
    --output {workspace}/analysis/clean_report.html
  ```

**步骤 16 — 质量门控 2（报告完整性）**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/quality_gate.py check_report \
    --report {workspace}/analysis/clean_report.html \
    --config {SKILL_DIR}/config.yaml \
    --retry-count {report_retry} \
    --warnings-output {workspace}/analysis/report_warnings.json
  ```
- 判定逻辑同步骤 8：PASS/WARN 继续，FAIL 且 `report_retry <= 1` 则 `report_retry += 1` 并回到对应撰写步骤补充，超过重试次数则强制降级继续

**步骤 17 — 渲染 PDF**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/render_pdf.py \
    --input {workspace}/analysis/clean_report.html \
    --template {SKILL_DIR}/templates/report.html \
    --css {SKILL_DIR}/templates/styles.css \
    --output {workspace}/output/
  ```

**步骤 18 — 渲染 DOCX**
- 运行脚本：
  ```bash
  python {SKILL_DIR}/scripts/render_docx.py \
    --input {workspace}/analysis/clean_report.html \
    --output {workspace}/output/
  ```

---

### 阶段七：交付（DELIVER）

将 `{workspace}/output/` 下的 PDF 和 DOCX 文件交付给用户。

## 重要约束

1. **禁止在脚本中调用任何外部 API**（包括 LLM API、搜索 API）
2. **所有 LLM 交互必须通过系统主模型**，Skill 只提供 prompt 模板
3. **所有搜索必须通过系统 search 工具**，Skill 只提供关键词
4. **输出中禁止 Markdown 表格语法**，所有表格必须是 HTML `<table>`
5. **搜索返回空结果时跳过继续**，不中断流程
6. **质量门控超过重试次数后强制降级继续**，不陷入死循环
7. **重试搜索时必须变换关键词**，禁止用完全相同的关键词重试
8. **上下文卸载规则**：搜索结果、CRAAP 逐条评分、章节 HTML 片段保存到文件后，禁止在后续 prompt 中内联引用完整内容。必须通过 `read` 工具按需读取。主 agent 对话上下文全程不超过 30K tokens。
