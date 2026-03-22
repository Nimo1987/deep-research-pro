#!/usr/bin/env python3
"""
信源分类脚本 — 纯规则匹配，无外部 API 调用
包含空值防御：过滤 None 元素、空 URL、无效条目

用法：
  python classify_sources.py \
    --input raw_search_results.json \
    --config config.yaml \
    --tiers source_tiers.yaml \
    --output classified_sources.json
"""

import argparse
import json
import hashlib
from urllib.parse import urlparse

import yaml


def load_tiers(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data else {}


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data else {}


def classify_url(url: str, tiers_db: dict, weights: dict) -> dict:
    if not url:
        w = weights.get("4", weights.get(4, {}))
        return {
            "tier": 4,
            "weight": w.get("weight", 0.4) if isinstance(w, dict) else 0.4,
            "tier_label": w.get("label", "四级一般") if isinstance(w, dict) else "四级一般",
        }

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    full_url = url.lower()

    tier_map = [
        ("tier_1_authority", 1),
        ("tier_2_professional", 2),
        ("tier_3_news", 3),
        ("tier_5_social", 5),
    ]

    for tier_key, tier_num in tier_map:
        patterns = tiers_db.get(tier_key, [])
        if not patterns:
            continue
        for pattern in patterns:
            if not pattern:
                continue
            if pattern in domain or pattern in full_url:
                w = weights.get(str(tier_num), weights.get(tier_num, {}))
                return {
                    "tier": tier_num,
                    "weight": w.get("weight", 0.4) if isinstance(w, dict) else 0.4,
                    "tier_label": w.get("label", f"Tier {tier_num}") if isinstance(w, dict) else f"Tier {tier_num}",
                }

    w = weights.get("4", weights.get(4, {}))
    return {
        "tier": 4,
        "weight": w.get("weight", 0.4) if isinstance(w, dict) else 0.4,
        "tier_label": w.get("label", "四级一般") if isinstance(w, dict) else "四级一般",
    }


def deduplicate(sources: list) -> list:
    seen = set()
    result = []
    for s in sources:
        url = s.get("url", "")
        if not url:
            continue
        h = hashlib.md5(url.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            result.append(s)
    return result


def sanitize_sources(raw: list) -> list:
    """过滤 None、非 dict、缺少 url 的无效条目"""
    valid = []
    skipped = 0
    for item in raw:
        if item is None:
            skipped += 1
            continue
        if not isinstance(item, dict):
            skipped += 1
            continue
        url = item.get("url")
        if not url or not isinstance(url, str) or not url.startswith("http"):
            skipped += 1
            continue
        # 确保必要字段存在
        item.setdefault("title", "")
        item.setdefault("content", "")
        valid.append(item)
    if skipped > 0:
        print(f"[CLASSIFY] 跳过 {skipped} 个无效条目（None/空URL/非法格式）")
    return valid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--tiers", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 防御：raw 可能是 None 或非 list
    if not raw or not isinstance(raw, list):
        print("[CLASSIFY] 警告：输入为空或格式错误，输出空列表")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([], f)
        return

    config = load_config(args.config)
    tiers_db = load_tiers(args.tiers)
    weights = config.get("source_weights", {})

    print(f"[CLASSIFY] 原始输入: {len(raw)} 条")

    # 清洗
    sources = sanitize_sources(raw)
    print(f"[CLASSIFY] 有效条目: {len(sources)}")

    # 去重
    sources = deduplicate(sources)
    print(f"[CLASSIFY] 去重后: {len(sources)}")

    # 分类
    for s in sources:
        s.update(classify_url(s.get("url", ""), tiers_db, weights))

    # 排序
    sources.sort(key=lambda x: (-x.get("weight", 0), -x.get("score", 0)))

    # 统计
    tier_counts = {}
    for s in sources:
        t = s["tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1

    print("[CLASSIFY] 分布:")
    for t in sorted(tier_counts):
        label = weights.get(str(t), weights.get(t, {}))
        label = label.get("label", f"T{t}") if isinstance(label, dict) else f"T{t}"
        print(f"  T{t} ({label}): {tier_counts[t]}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)

    print(f"[CLASSIFY] 完成 → {args.output}")


if __name__ == "__main__":
    main()
