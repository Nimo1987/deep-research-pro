# MECE 自检 Prompt

你是 MECE 原则检查专家。检查以下研究大纲是否满足 MECE 原则（互斥且穷尽）。

## 大纲

{{PLAN_JSON}}

## 输出格式

严格按以下 JSON 格式输出：

```json
{
  "is_mece": true,
  "overlaps": ["重叠描述1"],
  "gaps": ["遗漏描述1"],
  "suggestions": ["修改建议1"]
}
```

## 检查标准

1. 各章节之间是否存在内容重叠
2. 是否有重要维度被遗漏
3. 章节划分的逻辑是否一致（按时间、按维度、按因果等）
4. 是否包含执行摘要、研究方法与局限性、参考文献三个必要章节
5. `currency_weight` 是否为 1-3 的整数，且与调研主题的时效敏感度匹配
   - 如果主题明显是快速变化领域（如AI工具、社交媒体趋势），currency_weight 不应为 1
   - 如果主题明显是稳定领域（如基础理论、经典模式），currency_weight 不应为 3
6. `freshness_policy` 是否包含四个层（background、authority、timeliness、academic），值是否为正整数或 null
   - timeliness 层在 currency_weight ≥ 2 时不应为 null（时效敏感主题必须有时间过滤）
   - background 和 authority 层通常应为 null（不应过度过滤）
   - academic 层通常应为 null
7. freshness_policy 中的天数是否合理
   - timeliness 层：currency_weight=3 时应在 7-90 天之间；currency_weight=2 时应在 30-180 天之间
   - 不允许出现 0 或负数

只输出纯 JSON，不要包含 ```json 标记，不要输出任何其他内容。
