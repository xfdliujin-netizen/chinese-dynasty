#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 5MB 单文件地图拆成「骨架 + 外链数据 + 外链控制器 + 独立地形图」。
   幂等：每次都从 jiangshan-atlas.src.html（首次自动备份）重新生成。
   产物：
     jiangshan-atlas.html   骨架（CSS + DOM + seed + 桥接）
     atlas-dynasty.js       朝代数据
     atlas-lore.js          人物志文本
     atlas-app.js           控制器
     js/atlas_snapshots.js  完整疆域快照（由控制器按需异步拉取）
     atlas-terrain.webp     地形浮雕图
"""
import base64
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'jiangshan-atlas.html')
KEEP = os.path.join(ROOT, 'jiangshan-atlas.src.html')

MARKERS = {
    'lore': '/* Auto-bundled Lore Data',
    'dynasty': 'window.DYNASTY_DATA = ',
    'snapshots': 'Historical Atlas Snapshots',
    'controller': 'Historical Atlas Controller',
}


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)
    print('  %-28s %7.1f KB' % (os.path.relpath(p, ROOT), len(s.encode('utf-8')) / 1024))


def locate(src, marker):
    i = src.find(marker)
    if i < 0:
        raise SystemExit('找不到标记: ' + marker)
    tag_start = src.rfind('<script', 0, i)
    if tag_start < 0:
        raise SystemExit('标记前没有 <script>: ' + marker)
    tag_end = src.find('>', tag_start) + 1
    body_end = src.find('</script>', tag_end)
    close_end = body_end + len('</script>')
    return tag_start, tag_end, body_end, close_end


def is_full_source(path):
    if not os.path.isfile(path):
        return False
    text = read(path)
    return ('data:image/webp;base64,' in text and
            all(MARKERS[key] in text for key in ('lore', 'dynasty', 'snapshots')))


def main():
    # 优先读取刚构建的完整单文件，避免旧 src 备份覆盖新构建；
    # 只有当前文件已是拆分后的骨架时，才回退到完整源备份。
    if is_full_source(SRC):
        src = read(SRC)
        with open(KEEP, 'w', encoding='utf-8', newline='') as f:
            f.write(src)
        print('已从最新构建读取并更新源备份')
    elif is_full_source(KEEP):
        print('从源备份读取：jiangshan-atlas.src.html')
        src = read(KEEP)
    else:
        raise SystemExit('请先运行 python _probe/build_atlas.py 生成完整地图文件')

    spans = {k: locate(src, m) for k, m in MARKERS.items() if m in src}

    # ---------- 1. 抽出各段脚本 ----------
    bodies = {k: src[v[1]:v[2]] for k, v in spans.items()}
    write(os.path.join(ROOT, 'atlas-dynasty.js'), bodies['dynasty'].strip() + '\n')
    write(os.path.join(ROOT, 'atlas-lore.js'), bodies['lore'].strip() + '\n')
    if 'controller' in bodies:
        write(os.path.join(ROOT, 'atlas-app.js'), bodies['controller'].strip() + '\n')
    elif not os.path.isfile(os.path.join(ROOT, 'atlas-app.js')):
        raise SystemExit('缺少共享控制器 atlas-app.js')
    write(os.path.join(ROOT, 'js', 'atlas_snapshots.js'), bodies['snapshots'].strip() + '\n')

    # ---------- 2. 地形图：base64 → webp ----------
    m = re.search(r'(<image\b[^>]*id="terrain-relief-img"[^>]*?)href="data:image/webp;base64,([A-Za-z0-9+/=]+)"', src)
    if not m:
        raise SystemExit('找不到地形图 base64')
    raw = base64.b64decode(m.group(2) + '==')
    with open(os.path.join(ROOT, 'atlas-terrain.webp'), 'wb') as f:
        f.write(raw)
    print('  %-28s %7.1f KB' % ('atlas-terrain.webp', len(raw) / 1024))

    # ---------- 3. 组装新 HTML ----------
    subs = [
        (spans['snapshots'][0], spans['snapshots'][3], ''),          # 交给控制器异步加载
        (spans['lore'][0], spans['lore'][3], '<script src="atlas-lore.js" defer></script>'),
        (spans['dynasty'][0], spans['dynasty'][3], '<script src="atlas-dynasty.js" defer></script>'),
    ]
    if 'controller' in spans:
        subs.append((spans['controller'][0], spans['controller'][3],
                     '<script id="atlas-app-script" src="atlas-app.js" defer data-v-snapshots="20261031"></script>'))
    for a, b, rep in sorted(subs, key=lambda x: -x[0]):
        src = src[:a] + rep + src[b:]

    src = src.replace(
        'href="data:image/webp;base64,' + m.group(2) + '"',
        'href="atlas-terrain.webp"', 1)

    # 让关键脚本尽早开始下载
    if 'rel="preload" href="atlas-app.js"' not in src:
        src = src.replace('</head>',
                          '  <link rel="preload" href="atlas-app.js" as="script" />\n'
                          '  <link rel="preload" href="atlas-dynasty.js" as="script" />\n'
                          '</head>', 1)

    write(SRC, src)

    html_kb = len(src.encode('utf-8')) / 1024
    total = html_kb + sum(os.path.getsize(os.path.join(ROOT, p)) for p in
                          ['atlas-dynasty.js', 'atlas-lore.js', 'atlas-app.js',
                           'js/atlas_snapshots.js', 'atlas-terrain.webp']) / 1024
    print('\n骨架 %.0f KB（原 4890 KB），首屏关键脚本约 %.0f KB，总量 %.0f KB'
          % (html_kb, html_kb + 247 + 584, total))


if __name__ == '__main__':
    main()
