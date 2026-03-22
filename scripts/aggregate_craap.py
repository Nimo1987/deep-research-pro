#!/usr/bin/env python3
"""
CRAAP 评分聚合与过滤脚本 — 纯数值计算，无外部 API
包含空值防御：处理空文件、None 值、格式异常

支持交叉信源加权和时效权重调整。

用法：
  python aggregate_craap.py \
    --sources classified_sources.json \
    --scores craap_scores.json \
    --config config.yaml \
    --output filtered_sources.json \
    --stats eval_stats.json \
    [--cross-source-map cross_source_map.json] \
    [--currency-weight 1]
"""

import argparse
import json

import yaml


def safe_load_json(path: str, default=None):
    """安全加载 JSON，处理空文件和格式错误"""
    if default is None:
        default = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            print(f"[AGGREGATE] 警告：{path} 为空文件，使用默认值")
            return default
        data = json.loads(content)
        if data is None:
            return default
        return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[AGGREGATE] 警告：加载 {path} 失败 ({e})，使用默认值")
        return default


def safe_score(dim_data, fallback=5) -> float:
    """安全提取评分，处理各种异常格式"""
    if dim_data is None:
        return fallback
    if isinstance(dim_data, (int, float)):
        return float(dim_data)
    if isinstance(dim_data, dict):
        score = dim_data.get("score", fallback)
        if score is None:
            return fallback
        try:
            return float(score)
        except (ValueError, TypeError):
            return fallback
    return fallback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--scores", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stats", required=True)
    parser.add_argument("--cross-source-map", default=None,
                        help="交叉信源映射文件路径（可选）")
    parser.add_argument("--currency-weight", type=int, default=1,
                        help="时效权重倍数 1-3（默认 1）")
    args = parser.parse_args()

    sources = safe_load_json(args.sources, [])
    scores = safe_load_json(args.scores, [])

    # 加载交叉信源映射（可选）
    cross_map = {}
    if args.cross_source_map:
        cross_map = safe_load_json(args.cross_source_map, {})
        if not isinstance(cross_map, dict):
            cross_map = {}
        print(f"[AGGREGATE] 交叉信源映射: {len(cross_map)} 条")

    # 时效权重
    currency_weight = max(1, min(3, args.currency_weight))
    print(f"[AGGREGATE] 时效权重: {currency_weight}x")

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    eval_config = config.get("evaluation", {})
    threshold = eval_config.get("craap_threshold", 6.0)
    craap_weights = eval_config.get("craap_weights", {
        "currency": 0.167, "relevance": 0.167,
        "authority": 0.25, "accuracy": 0.25, "purpose": 0.167,
    })

    # 应用时效权重：currency 维度乘以 currency_weight，然后归一化
    adjusted_weights = dict(craap_weights)
    if currency_weight > 1:
        adjusted_weights["currency"] = adjusted_weights.get("currency", 0.2) * currency_weight
        total_w = sum(adjusted_weights.values())
        if total_w > 0:
            adjusted_weights = {k: v / total_w for k, v in adjusted_weights.items()}
        print(f"[AGGREGATE] 调整后权重: { {k: round(v, 3) for k, v in adjusted_weights.items()} }")

    # 过滤无效 scores 条目
    valid_scores = [s for s in scores if isinstance(s, dict) and s.get("url")]

    # 建立 URL → 评分 映射
    score_map = {}
    for entry in valid_scores:
        url = entry.get("url", "")
        if url:
            score_map[url] = entry

    print(f"[AGGREGATE] 信源: {len(sources)}, 评分: {len(valid_scores)}, 匹配映射: {len(score_map)}")

    # 合并评分到信源
    matched = 0
    for s in sources:
        if not isinstance(s, dict):
            continue
        url = s.get("url", "")
        eval_data = score_map.get(url, {})

        if eval_data:
            matched += 1
            dims = ["currency", "relevance", "authority", "accuracy", "purpose"]
            weighted_sum = 0
            for dim in dims:
                dim_data = eval_data.get(dim)
                dim_score = safe_score(dim_data, 5)
                dim_weight = adjusted_weights.get(dim, 0.2)
                weighted_sum += dim_score * dim_weight

            # 应用交叉信源加成
            cross_info = cross_map.get(url, {})
            bonus_pct = cross_info.get("bonus_pct", 0) if isinstance(cross_info, dict) else 0
            if bonus_pct > 0:
                weighted_sum = weighted_sum * (1 + bonus_pct)
                s["cross_source"] = True
                s["cross_layers"] = cross_info.get("layers", [])
                s["cross_bonus"] = bonus_pct
            else:
                s["cross_source"] = False
                s["cross_layers"] = []
                s["cross_bonus"] = 0

            s["craap_score"] = round(weighted_sum, 2)
            s["craap_detail"] = {d: eval_data.get(d, {}) for d in dims}
            s["key_facts"] = eval_data.get("key_facts") or []
            s["bias_detected"] = bool(eval_data.get("bias_detected", False))
            s["bias_description"] = eval_data.get("bias_description") or ""
        else:
            # 无评分但可能有交叉信源信息
            cross_info = cross_map.get(url, {})
            bonus_pct = cross_info.get("bonus_pct", 0) if isinstance(cross_info, dict) else 0
            s["craap_score"] = 0
            s["craap_detail"] = {}
            s["key_facts"] = []
            s["bias_detected"] = False
            s["bias_description"] = ""
            s["cross_source"] = bonus_pct > 0
            s["cross_layers"] = cross_info.get("layers", []) if isinstance(cross_info, dict) else []
            s["cross_bonus"] = bonus_pct

    print(f"[AGGREGATE] 匹配到评分: {matched}/{len(sources)}")

    # 过滤
    passed = [s for s in sources if isinstance(s, dict) and s.get("craap_score", 0) >= threshold]
    rejected = [s for s in sources if isinstance(s, dict) and s.get("craap_score", 0) < threshold]

    # 排序
    passed.sort(key=lambda x: -(x.get("weight", 0.4) * x.get("craap_score", 0)))

    # 统计
    avg_craap = sum(s.get("craap_score", 0) for s in passed) / len(passed) if passed else 0
    tier_dist = {}
    for s in passed:
        t = s.get("tier", 4)
        tier_dist[f"T{t}"] = tier_dist.get(f"T{t}", 0) + 1

    stats = {
        "total_evaluated": len(sources),
        "passed": len(passed),
        "rejected": len(rejected),
        "avg_craap_score": round(avg_craap, 2),
        "tier_distribution": tier_dist,
        "threshold_used": threshold,
        "bias_detected_count": sum(1 for s in sources if isinstance(s, dict) and s.get("bias_detected")),
        "cross_source_count": sum(1 for s in passed if s.get("cross_source")),
        "currency_weight": currency_weight,
        "adjusted_weights": {k: round(v, 3) for k, v in adjusted_weights.items()},
    }

    print(f"[AGGREGATE] 通过: {len(passed)}, 过滤: {len(rejected)}, 平均CRAAP: {avg_craap:.2f}")
    print(f"[AGGREGATE] 分布: {tier_dist}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(passed, f, ensure_ascii=False, indent=2)

    with open(args.stats, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"[AGGREGATE] 完成 → {args.output}, {args.stats}")


if __name__ == "__main__":
    main()
