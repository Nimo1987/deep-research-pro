#!/usr/bin/env python3
"""
Step 2.5: Financial Data Fetcher for Deep Research Pro
======================================================
数据源优先级：
  1. tushare（检测 TUSHARE_TOKEN 环境变量）
  2. 两者都没有 → 静默跳过（退出码 0，不中断流程）

任何用户都可以跑 deep-research-pro，没有 tushare token 只是不附加金融数据。

Usage:
    python fetch_financial_data.py \
        --topic "分析腾讯控股2024年财务表现" \
        --routing-hint '{"market": "港股", "scenarios": ["个股行情"], "symbol": "00700.HK", "start": "20240101", "end": "20241231"}' \
        --output ./sources/financial_data.json \
        --router ./data/tushare_router.json
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta


def get_tushare_pro():
    """获取 tushare pro 实例，未配置 token 返回 None（静默）"""
    token = os.getenv("TUSHARE_TOKEN", "").strip()
    if not token:
        return None
    try:
        import tushare as ts
        pro = ts.pro_api(token)
        return pro
    except Exception:
        return None


def detect_market(topic: str, router: dict) -> str | None:
    """根据 topic 关键词判断市场"""
    topic_lower = topic.lower()
    for market, config in router["markets"].items():
        for kw in config.get("keywords", []):
            if kw.lower() in topic_lower:
                return market
    return None


def fetch_single_tushare(pro, api_name: str, params: dict):
    """调用单个 tushare 接口，返回 DataFrame 或 None"""
    func = getattr(pro, api_name, None)
    if func is None:
        print(f"  [WARN] tushare 中未找到接口: {api_name}", file=sys.stderr)
        return None
    try:
        df = func(**params)
        return df
    except Exception as e:
        print(f"  [WARN] {api_name} 调用失败: {e}", file=sys.stderr)
        return None


def df_to_records(df, max_rows: int = 100) -> list:
    """DataFrame → JSON-serializable list，限制行数防止上下文爆炸"""
    if df is None or len(df) == 0:
        return []
    try:
        df_trimmed = df.tail(max_rows) if len(df) > max_rows else df
        return json.loads(df_trimmed.to_json(orient="records", force_ascii=False, date_format="iso"))
    except Exception as e:
        print(f"  [WARN] 数据序列化失败: {e}", file=sys.stderr)
        return []


def fill_params(params: dict, symbol: str, start: str, end: str, year: str, industry: str, index: str) -> dict:
    """替换路由模板中的占位符"""
    result = {}
    for k, v in params.items():
        if isinstance(v, str):
            v = v.replace("{SYMBOL}", symbol)
            v = v.replace("{START}", start)
            v = v.replace("{END}", end)
            v = v.replace("{YEAR}", year)
            v = v.replace("{INDUSTRY}", industry)
            v = v.replace("{INDEX}", index)
        result[k] = v
    return result


def write_skip(output_path: Path, reason: str):
    """写空占位文件，让后续步骤正常检测"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({
        "status": "skipped",
        "reason": reason,
        "data": []
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="调研主题")
    parser.add_argument("--routing-hint", default="{}", help="LLM 提供的路由参数 JSON 字符串")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--router", required=True, help="路由表 JSON 路径（tushare_router.json 或 akshare_router.json）")
    parser.add_argument("--max-rows", type=int, default=100, help="每个接口最多返回行数")
    args = parser.parse_args()

    output_path = Path(args.output)

    # ─── 数据源检测 ───────────────────────────────────────────────
    pro = get_tushare_pro()
    if pro is None:
        print("[SKIP] 未检测到 TUSHARE_TOKEN，跳过金融数据拉取步骤。")
        print("       如需启用，请配置环境变量: export TUSHARE_TOKEN=your_token")
        write_skip(output_path, "TUSHARE_TOKEN not set")
        sys.exit(0)

    print("[INFO] 数据源: tushare")

    # ─── 加载路由表 ───────────────────────────────────────────────
    router_path = Path(args.router)
    # 兼容旧配置：如果传的是 akshare_router.json，自动寻找 tushare_router.json
    if "akshare" in router_path.name:
        ts_router = router_path.parent / "tushare_router.json"
        if ts_router.exists():
            router_path = ts_router
            print(f"[INFO] 自动切换路由表: {router_path.name}")

    if not router_path.exists():
        print(f"[ERROR] 路由文件不存在: {router_path}", file=sys.stderr)
        write_skip(output_path, f"router not found: {router_path}")
        sys.exit(0)

    with open(router_path, encoding="utf-8") as f:
        router = json.load(f)

    # ─── 解析路由参数 ─────────────────────────────────────────────
    try:
        hint = json.loads(args.routing_hint)
    except json.JSONDecodeError:
        hint = {}

    market = hint.get("market") or detect_market(args.topic, router)
    if not market:
        print(f"[SKIP] topic 未匹配任何市场，跳过。topic: {args.topic}")
        write_skip(output_path, "no market matched")
        sys.exit(0)

    print(f"[INFO] 匹配市场: {market}")

    today = datetime.now()
    symbol   = hint.get("symbol", "")
    start    = hint.get("start", (today - timedelta(days=365)).strftime("%Y%m%d"))
    end      = hint.get("end", today.strftime("%Y%m%d"))
    year     = hint.get("year", str(today.year - 1))
    industry = hint.get("industry", "")
    index    = hint.get("index", "")

    requested_scenarios = hint.get("scenarios", [])
    market_config = router["markets"].get(market, {})
    all_scenarios = market_config.get("scenarios", {})

    if not requested_scenarios:
        requested_scenarios = list(all_scenarios.keys())[:3]

    print(f"[INFO] 将调用以下场景: {requested_scenarios}")

    # ─── 批量调用 ─────────────────────────────────────────────────
    import time
    results = []
    for i, scenario_name in enumerate(requested_scenarios):
        scenario = all_scenarios.get(scenario_name)
        if not scenario:
            print(f"  [WARN] 未知场景: {scenario_name}，跳过")
            continue

        api_name = scenario["api"]
        raw_params = scenario.get("params", {})
        filled_params = fill_params(raw_params, symbol, start, end, year, industry, index)

        print(f"  [FETCH] {scenario_name} → {api_name}({filled_params})")
        df = fetch_single_tushare(pro, api_name, filled_params)
        records = df_to_records(df, args.max_rows)

        results.append({
            "market": market,
            "scenario": scenario_name,
            "api": api_name,
            "description": scenario.get("description", ""),
            "params_used": filled_params,
            "record_count": len(records),
            "data": records
        })

        # 限速：2000 积分每分钟 2 次，场景间 sleep
        if i < len(requested_scenarios) - 1:
            time.sleep(31)

    # ─── 写出结果 ─────────────────────────────────────────────────
    output = {
        "status": "success",
        "topic": args.topic,
        "market": market,
        "source": "tushare",
        "fetched_at": datetime.now().isoformat(),
        "total_records": sum(r["record_count"] for r in results),
        "data": results
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    print(f"[DONE] 金融数据已保存: {output_path}")
    print(f"       市场: {market} | 场景数: {len(results)} | 总记录: {output['total_records']}")


if __name__ == "__main__":
    main()
