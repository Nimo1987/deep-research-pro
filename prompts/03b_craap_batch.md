# CRAAP 信源评估 — 批量完整评估模式

你是信源质量评估专家。对以下一批信源进行完整的 CRAAP 评估。

## 信源列表

{{SOURCES_BATCH}}

## 输出格式

输出纯 JSON 数组，每条信源一个对象：

[
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
]

## 评分标准

- Currency: 近1年内容 8-10分，1-3年 5-7分，更早 1-4分
- Relevance: 直接相关 8-10分，间接相关 4-7分
- Authority: .gov/.edu/顶级期刊 9-10分，咨询公司 7-8分，主流媒体 5-7分，博客/社交 1-4分
- Accuracy: 有数据引用和参考文献 8-10分，有数据无引用 5-7分，纯观点 1-4分
- Purpose: 纯学术/教育 9-10分，新闻报道 6-8分，有商业目的但客观 4-6分，软文/广告 1-3分

## 重要

- key_facts 必须是具体的事实或数据，不要写模糊概述
- 每条信源提取 2-5 个 key_facts
- 对每条信源的 5 个维度都必须给出评分和理由

只输出纯 JSON 数组，不要包含 ```json 标记，不要输出任何其他内容。
