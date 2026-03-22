#!/usr/bin/env python3
"""
交叉信源检测脚本 — 检测同一内容出现在多个搜索层的情况

同一 URL 或高度相似标题出现在 2+ 个搜索层 → cross_source 标记
交叉出现越多，可信度越高，CRAAP 加成越大。

用法：
  python cross_source_detect.py \
    --input raw_search_results.json \
    --output cross_source_map.json
"""

import argparse
import json
import re
from collections import defaultdict
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """标准化 URL 用于匹配"""
    if not url:
        return ""
    try:
        parsed = urlparse(url.lower().strip())
        # 移除 tracking 参数，保留有意义的查询参数
        # 移除 fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/"),
            "",  # params
            "",  # query（简化：去掉所有查询参数以提高匹配率）
            "",  # fragment
        ))
        return normalized
    except Exception:
        return url.lower().strip()


def normalize_title(title: str) -> str:
    """标准化标题用于相似度计算"""
    if not title:
        return ""
    # 去除标点、多余空格
    title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title.lower())
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def title_similarity(t1: str, t2: str) -> float:
    """基于词集合的 Jaccard 相似度"""
    if not t1 or not t2:
        return 0.0
    # 按字符或空格分词（兼容中英文）
    words1 = set(re.findall(r'[\w\u4e00-\u9fff]+', t1.lower()))
    words2 = set(re.findall(r'[\w\u4e00-\u9fff]+', t2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="raw_search_results.json 路径")
    parser.add_argument("--output", required=True, help="输出交叉信源映射")
    parser.add_argument("--similarity-threshold", type=float, default=0.7,
                        help="标题相似度阈值（默认 0.7）")
    args = parser.parse_args()

    # 加载搜索结果
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            print("[CROSS] 输入文件为空，输出空映射")
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return
        sources = json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[CROSS] 加载失败: {e}，输出空映射")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    if not isinstance(sources, list):
        sources = []

    print(f"[CROSS] 输入: {len(sources)} 条搜索结果")

    # 第一轮：按标准化 URL 分组
    url_layers = defaultdict(set)  # normalized_url -> set of layers
    url_items = defaultdict(list)   # normalized_url -> list of items
    norm_to_orig = {}               # normalized_url -> original_url

    for item in sources:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        layer = item.get("search_layer", "unknown")
        norm = normalize_url(url)
        if not norm:
            continue
        url_layers[norm].add(layer)
        url_items[norm].append(item)
        if norm not in norm_to_orig:
            norm_to_orig[norm] = url

    # 第二轮：标题相似度匹配（对 URL 不同但标题相似的条目）
    # 构建标题索引
    title_index = []  # [(normalized_title, url_norm, layer), ...]
    for item in sources:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        layer = item.get("search_layer", "unknown")
        title = normalize_title(item.get("title", ""))
        if not title or not url:
            continue
        norm_url = normalize_url(url)
        title_index.append((title, norm_url, layer))

    # 比较标题相似度（O(n²) 但在搜索结果规模下可接受）
    THRESHOLD = args.similarity_threshold
    title_matches = defaultdict(set)  # url_norm -> set of additional layers from title match

    for i in range(len(title_index)):
        t1, u1, l1 = title_index[i]
        if len(t1) < 10:  # 太短的标题容易误匹配
            continue
        for j in range(i + 1, len(title_index)):
            t2, u2, l2 = title_index[j]
            if u1 == u2:  # 同 URL 已在第一轮处理
                continue
            if l1 == l2:  # 同层不需要交叉检测
                continue
            if len(t2) < 10:
                continue
            sim = title_similarity(t1, t2)
            if sim >= THRESHOLD:
                title_matches[u1].add(l2)
                title_matches[u2].add(l1)

    # 合并结果
    cross_map = {}
    all_urls = set(url_layers.keys()) | set(title_matches.keys())

    for url_norm in all_urls:
        layers = url_layers.get(url_norm, set()) | title_matches.get(url_norm, set())
        layer_list = sorted(layers)
        cross_count = len(layer_list)
        is_cross = cross_count >= 2

        # 加成比例
        if cross_count >= 3:
            bonus_pct = 0.25
        elif cross_count == 2:
            bonus_pct = 0.15
        else:
            bonus_pct = 0.0

        cross_map[norm_to_orig.get(url_norm, url_norm)] = {
            "cross_source": is_cross,
            "layers": layer_list,
            "cross_count": cross_count,
            "bonus_pct": bonus_pct,
        }

    # 统计
    cross_count = sum(1 for v in cross_map.values() if v["cross_source"])
    print(f"[CROSS] 检测到交叉信源: {cross_count}/{len(cross_map)}")
    for url, info in sorted(cross_map.items(), key=lambda x: -x[1]["cross_count"]):
        if info["cross_source"]:
            print(f"  [{info['cross_count']}层] {info['layers']} ← {url[:80]}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(cross_map, f, ensure_ascii=False, indent=2)

    print(f"[CROSS] 完成 → {args.output}")


if __name__ == "__main__":
    main()
