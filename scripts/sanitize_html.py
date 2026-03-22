#!/usr/bin/env python3
"""
HTML 清理脚本 — 移除所有 Markdown 残留，确保纯 HTML 输出

用法：
  python sanitize_html.py \
    --input full_report.html \
    --output clean_report.html
"""

import argparse
import re


def sanitize(html: str) -> str:
    """清理 HTML 中的 Markdown 残留"""

    # 1. 移除 Markdown 表格（|---|---|）
    lines = html.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测 Markdown 表格分隔行
        if re.match(r'^\|[\s\-:|]+\|$', line):
            # 回溯删除上一行（表头行）
            if cleaned and cleaned[-1].strip().startswith("|"):
                cleaned.pop()
            # 跳过分隔行和后续表格行
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            continue

        # 单独的 Markdown 表格行（没有分隔行的情况）
        if line.startswith("|") and line.endswith("|") and line.count("|") >= 3:
            # 检查是否在 HTML 标签内（如 <table> 中的内容不应被清理）
            context = "\n".join(cleaned[-5:]) if len(cleaned) >= 5 else "\n".join(cleaned)
            if "<table" not in context:
                i += 1
                continue

        cleaned.append(lines[i])
        i += 1

    html = "\n".join(cleaned)

    # 2. 移除 Markdown 代码块
    html = re.sub(r'```[\w]*\n(.*?)\n```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)

    # 3. 移除 Markdown 粗体（**text**）如果不在 HTML 标签内
    # 只处理不在标签属性中的情况
    html = re.sub(r'(?<![<\w])\*\*([^*]+)\*\*(?![>\w])', r'<strong>\1</strong>', html)

    # 4. 移除 Markdown 斜体（*text*）
    html = re.sub(r'(?<![<\w*])\*([^*]+)\*(?![>\w*])', r'<em>\1</em>', html)

    # 5. 移除 Markdown 标题语法（# ## ###）
    html = re.sub(r'^#{1,6}\s+(.+)$', r'\1', html, flags=re.MULTILINE)

    # 6. 移除 Markdown 链接语法 [text](url) → <a href="url">text</a>
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # 7. 清理多余空行（保留最多 2 个连续空行）
    html = re.sub(r'\n{4,}', '\n\n\n', html)

    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        html = f.read()

    original_len = len(html)
    html = sanitize(html)
    cleaned_len = len(html)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    diff = original_len - cleaned_len
    print(f"[SANITIZE] 原始: {original_len} 字符, 清理后: {cleaned_len} 字符, 移除: {diff}")
    print(f"[SANITIZE] 完成 → {args.output}")


if __name__ == "__main__":
    main()
