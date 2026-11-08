#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 web 版打包成原生壳可直接加载的资源目录 apps/web/。

做三件事：
1. 复制运行期需要的静态资源（排除 backup / src 大文件）
2. 去掉 Google Fonts 外链，替换为本地子集化的印章书法体
3. 注入 native-shim.js（原生壳适配：视图状态上报、返回键、离线兜底）

每次改完 web 版重跑一次即可：
    python apps/scripts/prepare-web.py
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APPS = os.path.dirname(HERE)
ROOT = os.path.dirname(APPS)
OUT = os.path.join(APPS, "web")
FONT_SRC = os.path.join(APPS, "_build", "out", "seal.woff2")

# 运行期真正需要的文件（刻意不含 *.backup.html / *.src.html / _probe）
WEB_FILES = [
    "index.html",
    "jiangshan-atlas.html",
    "scroll.css",
    "view-switch.css",
    "atlas.css",
    "atlas-timeline-ui.css",
    "scroll-app.js",
    "atlas-app.js",
    "atlas-dynasty.js",
    "atlas-lore.js",
    "atlas-bridge.js",
    "atlas-ui.js",
    "emperor-data.js",
    "atlas-terrain.webp",
    "js/atlas_snapshots.js",
]

FONT_FACE = """  <!-- 原生包：书法体改为本地子集（仅「史」「舆」等印章用字），不再请求 Google Fonts -->
  <style>
    @font-face {
      font-family: 'Ma Shan Zheng';
      src: url('fonts/seal.woff2') format('woff2');
      font-weight: 400;
      font-display: swap;
    }
  </style>
"""

NATIVE_SHIM_TAG = '  <script src="native-shim.js"></script>\n</body>'


def copy_assets():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "fonts"), exist_ok=True)
    missing = []
    for name in WEB_FILES:
        src = os.path.join(ROOT, name)
        if not os.path.exists(src):
            missing.append(name)
            continue
        dst = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    if os.path.exists(FONT_SRC):
        shutil.copy2(FONT_SRC, os.path.join(OUT, "fonts", "seal.woff2"))
    else:
        print("[!] 缺少字体，请先运行字体子集化步骤", file=sys.stderr)

    shim = os.path.join(HERE, "native-shim.js")
    if os.path.exists(shim):
        shutil.copy2(shim, os.path.join(OUT, "native-shim.js"))
    else:
        print("[!] 缺少 native-shim.js", file=sys.stderr)
    return missing


def patch_index():
    path = os.path.join(OUT, "index.html")
    html = open(path, encoding="utf-8").read()
    original_len = len(html)

    # 1) 删掉 Google Fonts 的 <link>（含前面那行注释），避免离线首屏等待 / 外网请求
    html = re.sub(
        r'[ \t]*<!--[^>]*?字体[^>]*?-->\s*<link[^>]*fonts\.googleapis\.com[^>]*>\s*',
        FONT_FACE,
        html,
        count=1,
    )
    if "fonts.googleapis.com" in html:
        # 兜底：注释格式变了也要清掉
        html = re.sub(r'[ \t]*<link[^>]*fonts\.googleapis\.com[^>]*>\s*', "", html, count=1)
        if "@font-face" not in html:
            html = html.replace("</head>", FONT_FACE + "</head>", 1)

    # 2) 注入 native-shim.js
    if "native-shim.js" not in html:
        if "</body>" in html:
            html = html.replace("</body>", NATIVE_SHIM_TAG, 1)
        else:
            html += "\n" + NATIVE_SHIM_TAG

    open(path, "w", encoding="utf-8", newline="\n").write(html)
    print(f"  index.html  {original_len} -> {len(html)} bytes  "
          f"(google fonts removed: {'fonts.googleapis.com' not in html})")


def sync_native():
    """把 apps/web 同步到鸿蒙 rawfile 与 iOS Resources（先清后拷，避免残留旧文件）"""
    import shutil as _sh
    targets = [
        os.path.join(APPS, "harmony", "entry", "src", "main", "resources", "rawfile", "web"),
        os.path.join(APPS, "ios", "HistoryScroll", "Resources", "web"),
    ]
    for dst in targets:
        if os.path.exists(dst):
            _sh.rmtree(dst)
        shutil.copytree(OUT, dst)
        print("  ->", os.path.relpath(dst, ROOT))


def main():
    print("打包 web 资源 ->", OUT)
    missing = copy_assets()
    patch_index()
    sync_native()
    if missing:
        print("[!] 缺失文件:", ", ".join(missing))
    total = 0
    for dirpath, _, files in os.walk(OUT):
        for f in files:
            total += os.path.getsize(os.path.join(dirpath, f))
    print(f"完成：{total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
