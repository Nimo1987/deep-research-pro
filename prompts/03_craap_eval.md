# CRAAP 信源评估 Prompt

你是信源质量评估专家。对以下信源进行 CRAAP 评估。

## 信源信息

- URL: {{URL}}
- 标题: {{TITLE}}
- 内容摘要: {{CONTENT}}
- 预分类层级: {{TIER_LABEL}}（权重: {{WEIGHT}}）

## 输出格式

严格按以下 JSON 格式输出（每项 0-10 分）：

```json
{
  "url": "该信源的URL",
  "currency": {
    "score": 0,
    "reason": "时效性评估理由"
  },
  "relevance": {
    "score": 0,
    "reason": "相关性评估理由"
  },
  "authority": {
    "score": 0,
    "reason": "权威性评估理由"
  },
  "accuracy": {
    "score": 0,
    "reason": "准确性评估理由"
  },
  "purpose": {
    "score": 0,
    "reason": "目的性评估理由（是否为软文/广告/有商业偏见）"
  },
  "bias_detected": false,
  "bias_description": "",
  "key_facts": ["从该信源提取的关键事实/数据点1", "数据点2"]
}
```

## 评分标准

- Currency: 近1年内容 8-10分，1-3年 5-7分，更早 1-4分
- Relevance: 直接相关 8-10分，间接相关 4-7分
- Authority: .gov/.edu/顶级期刊 9-10分，咨询公司 7-8分，主流媒体 5-7分，博客/社交 1-4分
- Accuracy: 有数据引用和参考文献 8-10分，有数据无引用 5-7分，纯观点 1-4分
- Purpose: 纯学术/教育 9-10分，新闻报道 6-8分，有商业目的但客观 4-6分，软文/广告 1-3分
