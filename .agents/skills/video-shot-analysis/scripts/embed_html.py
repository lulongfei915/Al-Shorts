#!/usr/bin/env python3
"""embed_html.py — 把 HTML 同目录 assets/ 下的图片内嵌为 base64，产出自包含单文件。

Usage: embed_html.py <report.html>
原地改写：src="assets/x.jpg" 与 CSS url("assets/x") 都会被替换。
"""
import base64
import mimetypes
import os
import re
import sys


def main() -> None:
    html_path = sys.argv[1]
    root = os.path.dirname(os.path.abspath(html_path))
    html = open(html_path, encoding="utf-8").read()

    def data_uri(rel: str) -> str:
        path = os.path.join(root, rel)
        mime = mimetypes.guess_type(path)[0] or "image/jpeg"
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        return f"data:{mime};base64,{b64}"

    def repl_src(m: re.Match) -> str:
        return f'src="{data_uri(m.group(1))}"'

    def repl_css(m: re.Match) -> str:
        return f'url("{data_uri(m.group(1))}")'

    html = re.sub(r'src="(assets/[^"]+)"', repl_src, html)
    html = re.sub(r'url\("?(assets/[^")]+)"?\)', repl_css, html)

    open(html_path, "w", encoding="utf-8").write(html)
    left = len(re.findall(r'src="assets/|url\("?assets/', html))
    print(f"embedded; remaining relative refs={left}; size={os.path.getsize(html_path)//1024} KB")
    if left:
        sys.exit(1)


if __name__ == "__main__":
    main()
