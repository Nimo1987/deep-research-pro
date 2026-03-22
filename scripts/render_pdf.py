#!/usr/bin/env python3
"""
PDF 渲染脚本 — 将 HTML 报告嵌入模板，用 WeasyPrint 渲染为 PDF

用法：
  python render_pdf.py \
    --input clean_report.html \
    --template report.html \
    --css styles.css \
    --output output_dir/
"""

import argparse
import re
from pathlib import Path

from weasyprint import HTML, CSS


def safe_filename(text: str, max_len: int = 30) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', '', text)
    return safe[:max_len].strip()


def extract_title(html: str) -> str:
    """从 HTML 中提取报告标题"""
    import re
    match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if match:
        return match.group(1).strip()
    return "深度调研报告"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="清理后的 HTML 报告")
    parser.add_argument("--template", required=True, help="HTML 模板文件")
    parser.add_argument("--css", required=True, help="CSS 样式文件")
    parser.add_argument("--output", required=True, help="输出目录")
    args = parser.parse_args()

    # 读取内容
    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()

    with open(args.template, "r", encoding="utf-8") as f:
        template = f.read()

    title = extract_title(content)

    # 嵌入模板
    full_html = template.replace("{{title}}", title).replace("{{content}}", content)

    # 渲染
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"深度调研报告_{safe_filename(title)}.pdf"

    template_dir = str(Path(args.template).parent)
    html_doc = HTML(string=full_html, base_url=template_dir)
    css = CSS(filename=args.css)
    html_doc.write_pdf(str(pdf_path), stylesheets=[css])

    print(f"[RENDER-PDF] 完成 → {pdf_path}")


if __name__ == "__main__":
    main()
