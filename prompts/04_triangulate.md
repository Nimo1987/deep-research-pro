# 三角验证 Prompt

你是数据验证专家。对以下从多个信源提取的关键事实进行三角验证。

## 调研主题

{{TOPIC}}

## 各信源提取的关键事实

{{FACTS_JSON}}

## 输出格式

严格按以下 JSON 格式输出：

```json
{
  "verified_data_points": [
    {
      "claim": "经验证的数据点/事实",
      "supporting_sources": ["信源URL1", "信源URL2"],
      "confidence": "high",
      "note": "验证说明"
    }
  ],
  "conflicting_data_points": [
    {
      "claim": "存在冲突的数据点",
      "versions": [
        {"source": "信源URL", "value": "该信源的说法"},
        {"source": "信源URL", "value": "另一信源的说法"}
      ],
      "recommended_value": "基于信源权重推荐采纳的值",
      "reason": "推荐理由"
    }
  ],
  "unverified_claims": [
    {
      "claim": "仅单一来源的数据点",
      "source": "信源URL",
      "confidence": "low"
    }
  ]
}
```

## 验证规则

1. 同一数据点被 2 个以上独立信源确认 → verified, confidence=high
2. 被 2 个信源确认但有细微差异 → verified, confidence=medium
3. 多源冲突 → conflicting，推荐采纳信源权重更高的版本
4. 仅单一来源 → unverified, confidence=low

只输出纯 JSON，不要包含 ```json 标记，不要输出任何其他内容。
