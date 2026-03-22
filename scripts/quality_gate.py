#!/usr/bin/env python3
"""
质量门控脚本 — 三级判定：PASS / WARN / FAIL

PASS: 全部达标，继续
WARN: 部分未达标但可继续（附带降级说明写入 warnings.json）
FAIL: 严重不足，必须重试

退出码：0=PASS, 0=WARN（都可继续）, 1=FAIL（必须重试）

用法：
  python quality_gate.py check_sources \
    --filtered filtered_sources.json \
    --stats eval_stats.json \
    --triangulation triangulation.json \
    --config config.yaml \
    --retry-count 0 \
    --warnings-output warnings.json

  python quality_gate.py check_report \
    --report clean_report.html \
    --config config.yaml \
    --retry-count 0 \
    --warnings-output warnings.json
"""

import argparse
import json
import os
import re
import sys

import yaml


def safe_load_json(path, default=None):
    """安全加载 JSON 文件"""
    if default is None:
        default = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return default
        data = json.loads(content)
        return data if data is not None else default
    except (json.JSONDecodeError, FileNotFoundError, Exception):
        return default


def check_sources(args):
    sources = safe_load_json(args.filtered, [])
    stats = safe_load_json(args.stats, {})

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    gates = config.get("quality_gates", {}).get("sources", {})
    retry_count = args.retry_count
    max_retries = 2

    hard_fails = []  # 必须重试
    warnings = []  # 可降级继续

    # ===== 加载阈值 =====
    min_total = gates.get("min_total_sources", 15)
    min_t1 = gates.get("min_tier1_sources", 2)
    min_t2 = gates.get("min_tier2_sources", 3)
    min_avg = gates.get("min_avg_craap", 6.5)
    min_verified = gates.get("min_verified_points", 3)
    hard_min_total = gates.get("hard_min_total_sources", 5)
    hard_min_craap = gates.get("hard_min_avg_craap", 4.0)

    # ===== 动态阈值：信源稀少时自动降低 =====
    adaptive = gates.get("adaptive_threshold", False)
    reduction = gates.get("adaptive_reduction", 0.3)

    raw_results_path = os.path.join(
        os.path.dirname(args.filtered), "raw_search_results.json"
    )
    raw_count = 0
    if os.path.exists(raw_results_path):
        try:
            with open(raw_results_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                raw_count = len(raw_data) if isinstance(raw_data, list) else 0
        except Exception:
            raw_count = 0

    if adaptive and raw_count > 0 and raw_count < 40:
        factor = 1.0 - reduction  # 0.7
        min_total = max(hard_min_total, int(min_total * factor))
        min_t1 = max(0, int(min_t1 * factor))
        min_t2 = max(0, int(min_t2 * factor))
        min_avg = max(hard_min_craap, min_avg * factor)
        min_verified = max(1, int(min_verified * factor))
        warnings.append(
            f"信源稀少（原始搜索结果仅 {raw_count} 条），已自动降低质量阈值 {int(reduction * 100)}%"
        )

    # ===== 总信源数 =====
    total = len(sources)
    if total < hard_min_total:
        hard_fails.append(f"信源严重不足: {total}/{hard_min_total}（最低要求）")
    elif total < min_total:
        warnings.append(f"信源数量偏少: {total}/{min_total}（可继续但报告深度受限）")

    # ===== 一级权威 =====
    t1 = sum(1 for s in sources if s.get("tier") == 1)
    if t1 < min_t1:
        if retry_count < max_retries:
            hard_fails.append(
                f"一级权威信源不足: {t1}/{min_t1}，"
                f"建议搜索关键词加上 site:.gov OR site:.edu OR site:nature.com"
            )
        else:
            warnings.append(
                f"一级权威信源不足: {t1}/{min_t1}（已重试{retry_count}次，降级继续，"
                f"报告中将标注：部分结论缺少权威信源支撑）"
            )

    # ===== 二级专业 =====
    t2 = sum(1 for s in sources if s.get("tier") == 2)
    if t2 < min_t2:
        if retry_count < max_retries:
            hard_fails.append(
                f"二级专业信源不足: {t2}/{min_t2}，"
                f"建议搜索关键词加上 site:mckinsey.com OR site:gartner.com OR site:hbr.org"
            )
        else:
            warnings.append(
                f"二级专业信源不足: {t2}/{min_t2}（已重试{retry_count}次，降级继续）"
            )

    # ===== 平均 CRAAP =====
    avg = stats.get("avg_craap_score", 0)
    if avg < min_avg and avg > 0:
        if avg < hard_min_craap:
            hard_fails.append(f"平均 CRAAP 分数过低: {avg:.2f}/{min_avg}")
        else:
            warnings.append(
                f"平均 CRAAP 分数偏低: {avg:.2f}/{min_avg}（可继续但需注意信源质量）"
            )

    # ===== 三角验证 =====
    if args.triangulation:
        try:
            with open(args.triangulation, "r", encoding="utf-8") as f:
                content = f.read().strip()
            tri = json.loads(content) if content else {}
        except (json.JSONDecodeError, FileNotFoundError):
            tri = {}
        verified = len(tri.get("verified_data_points", []))
        if verified < min_verified:
            warnings.append(
                f"已验证数据点偏少: {verified}/{min_verified}（可继续，"
                f"报告中将标注低置信度数据点）"
            )

    # ===== 判定 =====
    result = {
        "hard_fails": hard_fails,
        "warnings": warnings,
        "retry_count": retry_count,
    }

    if args.warnings_output:
        with open(args.warnings_output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    if hard_fails:
        print("FAIL")
        for item in hard_fails:
            print(f"  [FAIL] {item}")
        for item in warnings:
            print(f"  [WARN] {item}")
        sys.exit(1)
    elif warnings:
        print("WARN")
        for item in warnings:
            print(f"  [WARN] {item}")
        print("  → 降级继续，上述问题将在报告「研究方法与局限性」章节中披露")
        sys.exit(0)
    else:
        print("PASS")
        print(f"  信源: {total}, T1: {t1}, T2: {t2}, 平均CRAAP: {avg:.2f}")
        sys.exit(0)


def check_report(args):
    try:
        with open(args.report, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print("FAIL")
        print(f"  [FAIL] 报告文件不存在: {args.report}")
        sys.exit(1)

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    gates = config.get("quality_gates", {}).get("report", {})
    retry_count = args.retry_count

    hard_fails = []
    warnings = []

    # 字符数
    text_only = re.sub(r"<[^>]+>", "", html)
    char_count = len(text_only.strip())
    min_chars = gates.get("min_char_count", 3000)
    if char_count < 500:
        hard_fails.append(f"报告字数严重不足: {char_count}/500（最低要求）")
    elif char_count < min_chars:
        if retry_count < 1:
            hard_fails.append(f"报告字数不足: {char_count}/{min_chars}")
        else:
            warnings.append(
                f"报告字数偏少: {char_count}/{min_chars}（已重试，降级继续）"
            )

    # 必要章节
    required = gates.get("required_sections", [])
    missing = [s for s in required if s not in html]
    if missing:
        if retry_count < 1:
            hard_fails.append(f"缺少必要章节: {', '.join(missing)}")
        else:
            warnings.append(f"缺少章节: {', '.join(missing)}（已重试，降级继续）")

    # 表格检查
    if gates.get("must_have_tables", True):
        if "<table" not in html:
            warnings.append("报告中没有表格（建议但不强制）")

    # Markdown 残留
    if gates.get("no_markdown_tables", True):
        md_table_pattern = r"\|[\s\-:]+\|"
        if re.search(md_table_pattern, html):
            hard_fails.append(
                "检测到 Markdown 表格语法残留，需重新运行 sanitize_html.py"
            )

    if "```" in html:
        hard_fails.append("检测到 Markdown 代码块残留，需重新运行 sanitize_html.py")

    # 判定
    result = {
        "hard_fails": hard_fails,
        "warnings": warnings,
        "retry_count": retry_count,
    }

    if args.warnings_output:
        with open(args.warnings_output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    if hard_fails:
        print("FAIL")
        for item in hard_fails:
            print(f"  [FAIL] {item}")
        for item in warnings:
            print(f"  [WARN] {item}")
        sys.exit(1)
    elif warnings:
        print("WARN")
        for item in warnings:
            print(f"  [WARN] {item}")
        sys.exit(0)
    else:
        print("PASS")
        print(f"  字符数: {char_count}, 含表格: {'<table' in html}")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    sp1 = subparsers.add_parser("check_sources")
    sp1.add_argument("--filtered", required=True)
    sp1.add_argument("--stats", required=True)
    sp1.add_argument("--triangulation", default=None)
    sp1.add_argument("--config", required=True)
    sp1.add_argument("--retry-count", type=int, default=0)
    sp1.add_argument("--warnings-output", default=None)

    sp2 = subparsers.add_parser("check_report")
    sp2.add_argument("--report", required=True)
    sp2.add_argument("--config", required=True)
    sp2.add_argument("--retry-count", type=int, default=0)
    sp2.add_argument("--warnings-output", default=None)

    args = parser.parse_args()

    if args.command == "check_sources":
        check_sources(args)
    elif args.command == "check_report":
        check_report(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
