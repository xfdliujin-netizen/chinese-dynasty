# -*- coding: utf-8 -*-
"""
把 jiangshan-map 核心包内联为单文件「疆域图谱 · 内嵌版」（L2 深度融合）

处理清单
1) 全量恢复 DYNASTY_DATA（18 个时期，前 403 — 1912），不再做清朝试点裁剪
2) 剔除与本应用无关的功能：
   - 古琴雅乐（音乐模块 + Audio 初始化）
   - 繁简 / 英文语言切换（锁定简体）
   - GitHub Star 入口
   - 科举「舆图寻址」挑战（入口在初次到访指引中，整体关闭）
   - 初次到访指引 / 鼠标手势提示 / SEO 目录外链
   - Google Fonts / 统计脚本 / PWA manifest
3) 顶部工具条改为「‹ 长卷 + 图层 + 搜索」极简形态，视觉与主程序一致
4) 注入双向联动桥（__atlasReady / __atlasAck / __atlasState / __atlasExit）
"""
import base64
import json
import os
import re

AT = '_probe/atlas'


def read(p):
    return open(os.path.join(AT, p), encoding='utf-8').read()


def must_replace(text, old, new, label, count=1):
    n = text.count(old)
    assert n == count, '[%s] 期望 %d 处，实际 %d 处' % (label, count, n)
    return text.replace(old, new)


def must_sub(text, pattern, repl, label, flags=0):
    out, n = re.subn(pattern, repl, text, flags=flags)
    assert n == 1, '[%s] 正则命中 %d 次' % (label, n)
    return out


idx = read('index.html')
css = read('style.css')

# ---------------------------------------------------------------- 1. 清 head
for pat in [
    r'<link rel="preconnect" href="https://fonts\.googleapis\.com" />\s*',
    r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin />\s*',
    r'<link href="https://fonts\.googleapis\.com/css2\?family=Noto\+Serif[^"]*" rel="stylesheet" />\s*',
    r'<link href="https://fonts\.googleapis\.com/css2\?family=Ma\+Shan[^"]*" rel="stylesheet" />\s*',
    r'<script[^>]*events\.vercount\.one[^>]*>\s*</script>\s*',
    r'<script[^>]*cloudflareinsights[^>]*></script>\s*',
    r'<script type="application/ld\+json">.*?</script>\s*',
    r'<link rel="manifest"[^>]*>\s*',
    r'<link rel="icon"[^>]*>\s*',
    r'<link rel="apple-touch-icon"[^>]*>\s*',
]:
    idx = re.sub(pat, '', idx, flags=re.S)

# ------------------------------------------------------- 2. 外链 SEO 目录整块删
i = idx.find('<nav id="seo-atlas-directory"')
assert i > 0, '未找到 SEO 目录'
j = idx.find('</nav>', i)
assert j > 0
idx = idx[:i] + idx[j + 6:]

# ------------------------------------------------ 3. body 标记（内嵌模式样式钩子）
idx = must_replace(idx, '<body>', '<body class="atlas-embed">', 'body class')

# -------------------------------------------- 4. 品牌区 → 「‹ 长卷」返回按钮
idx = must_replace(
    idx,
    '<a class="home-link" id="act-home" href="./" title="回到首页"><span class="seal-mark" id="txt-seal">江山时序</span></a>',
    '<button class="home-link" id="act-home" type="button" title="回到长卷并定位到当前年份">'
    '<span class="seal-mark" id="txt-seal">长卷</span></button>',
    'home link',
)

# ------------------------------------- 5. 工具条：移除音乐 / 语言 / GitHub 入口
for _ in range(3):
    for start, end in [
        ('<div class="music-pill-group"', '</div>'),
        ('<div class="locale-pill-group"', '</div>'),
        ('<a id="act-github-star"', '</a>'),
    ]:
        k = idx.find(start)
        if k < 0:
            continue
        e = idx.find(end, k + len(start))
        assert e > 0
        idx = idx[:k] + idx[e + len(end):]

# 工具条上遗留的分隔线（音乐组前那条）
idx = re.sub(
    r'(<button id="act-layers-menu".*?</button>)\s*<span class="toolbar-divider" aria-hidden="true"></span>\s*',
    r'\1\n        ',
    idx,
    count=1,
    flags=re.S,
)

# ------------------------------------------------ 6. 挑战卡片（科举小试）整体删
i = idx.find('<div id="challenge-card"')
if i > 0:
    j = idx.find('<div id="genealogy-card"', i)
    assert j > i
    idx = idx[:i] + idx[j:]

# ------------------------------------------------ 7. CSS 内联 + 地形底图 base64
idx = re.sub(r'<link rel="stylesheet" href="css/style\.css[^>]*>',
             '<style>\n' + css + '\n</style>', idx)
terr = base64.b64encode(open(os.path.join(AT, 'terrain_relief.webp'), 'rb').read()).decode()
idx = idx.replace('href="assets/terrain_relief.webp"', 'href="data:image/webp;base64,%s"' % terr)

# ---------------------------------------- 8. 内嵌模式外观统一（追加在 </head> 前）
EMBED_CSS = r'''
<style id="atlas-embed-unify">
/* ================= 内嵌模式：与主程序统一的克制外观 ================= */
body.atlas-embed {
  -webkit-tap-highlight-color: transparent;
}
/* 顶部工具条压成一条细工具栏 */
body.atlas-embed #nav-bar {
  padding: calc(3px + env(safe-area-inset-top, 0px)) 10px 3px;
  gap: 8px;
  background: rgba(247, 243, 235, 0.9);
  -webkit-backdrop-filter: blur(18px) saturate(1.7);
  backdrop-filter: blur(18px) saturate(1.7);
  border-bottom: 1px solid rgba(120, 100, 70, 0.13);
  box-shadow: none;
}
body.atlas-embed .brand-group h1 { gap: 6px; align-items: center; }
body.atlas-embed .brand-group .home-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  min-height: 28px;
  padding: 0 11px 0 8px;
  border: none;
  border-radius: 14px;
  background: rgba(120, 100, 70, 0.10);
  color: #5C4630;
  text-decoration: none;
  transition: transform .16s ease, background .16s ease;
}
body.atlas-embed .brand-group .home-link:active {
  transform: scale(.95);
  background: rgba(120, 100, 70, 0.18);
}
body.atlas-embed .brand-group .home-link::before {
  content: '‹';
  font-size: 17px;
  line-height: 1;
  opacity: .55;
  margin-right: 1px;
}
body.atlas-embed .brand-group .seal-mark {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: .02em;
  color: #5C4630;
  line-height: 1;
}
body.atlas-embed .brand-group .subtitle-mark { display: none; }
body.atlas-embed .control-strip .action-btn { border-radius: 14px; }
/* 去掉与主程序重复/无关的浮层 */
body.atlas-embed #gesture-guide,
body.atlas-embed #start-guide,
body.atlas-embed #seo-atlas-directory { display: none !important; }
body.atlas-embed #scrubber-dock { border-top: 1px solid rgba(120, 100, 70, 0.13); }
/* 底部时间轴：按钮圆角统一 */
body.atlas-embed .round-btn,
body.atlas-embed .play-speed-btn,
body.atlas-embed .step-nav-btn { border-radius: 10px; }

/* ================= 沉浸版式：地图铺满，其余全部悬浮玻璃卡 ================= */
body.atlas-embed { overflow: hidden; overscroll-behavior: none; }
body.atlas-embed #atlas-shell { display: block; height: 100vh; height: 100dvh; }
body.atlas-embed #workspace-body {
  display: grid;
  height: 100%;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr);
}
body.atlas-embed #viewport-frame { border-right: none; }

/* 顶部工具条 → 悬浮胶囊 */
body.atlas-embed #nav-bar {
  position: fixed;
  top: calc(env(safe-area-inset-top, 0px) + 8px);
  left: 50%;
  right: auto;
  transform: translateX(-50%);
  z-index: 72;
  width: auto;
  max-width: calc(100vw - 24px);
  padding: 5px 9px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: linear-gradient(180deg, rgba(252, 249, 242, 0.72), rgba(246, 240, 229, 0.60));
  -webkit-backdrop-filter: blur(28px) saturate(1.9);
  backdrop-filter: blur(28px) saturate(1.9);
  box-shadow: 0 10px 28px rgba(30, 27, 24, 0.16), 0 1px 0 rgba(255, 255, 255, 0.7) inset;
  transition: opacity 0.35s ease;
}

/* 详情面板：宽屏悬浮右侧玻璃卡 */
@media (min-width: 901px) {
  body.atlas-embed #chronicle-pane {
    position: fixed;
    top: calc(env(safe-area-inset-top, 0px) + 62px);
    right: 12px;
    bottom: calc(env(safe-area-inset-bottom, 0px) + 132px);
    width: min(330px, 30vw);
    z-index: 62;
    margin: 0;
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.6);
    background: linear-gradient(180deg, rgba(252, 249, 242, 0.80), rgba(246, 240, 229, 0.70));
    -webkit-backdrop-filter: blur(26px) saturate(1.8);
    backdrop-filter: blur(26px) saturate(1.8);
    box-shadow: 0 14px 36px rgba(30, 27, 24, 0.18);
    overflow-y: auto;
    overscroll-behavior: contain;
    transition: opacity 0.35s ease, transform 0.35s ease;
  }
}
/* 窄屏：详情面板变底部悬浮卡，整体叠在地图之上（不再占布局空间） */
@media (max-width: 900px) {
  body.atlas-embed #workspace-body,
  body.atlas-embed #workspace-body.is-pane-collapsed,
  body.atlas-embed #workspace-body.is-mobile-chronicle-open {
    grid-template-columns: 1fr !important;
    grid-template-rows: 1fr 0px !important;
  }
  body.atlas-embed #chronicle-pane {
    position: fixed;
    left: 10px;
    right: 10px;
    top: auto;
    bottom: calc(env(safe-area-inset-bottom, 0px) + 128px);
    height: auto !important;
    max-height: min(46vh, 340px);
    z-index: 62;
    border-radius: 16px;
    overflow-y: auto;
    overscroll-behavior: contain;
    border: 1px solid rgba(255, 255, 255, 0.6);
    background: linear-gradient(180deg, rgba(252, 249, 242, 0.86), rgba(246, 240, 229, 0.76));
    -webkit-backdrop-filter: blur(26px) saturate(1.8);
    backdrop-filter: blur(26px) saturate(1.8);
    box-shadow: 0 12px 30px rgba(30, 27, 24, 0.18);
    opacity: 1;
    transition: opacity 0.35s ease, transform 0.35s ease;
  }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane { max-height: none; }
  /* 竖屏：图例叠在朝代横幅上方，互不压叠；展开史志卡时隐藏图例 */
  body.atlas-embed #map-key {
    bottom: calc(env(safe-area-inset-bottom, 0px) + 188px);
    max-height: 40vh;
    overflow-y: auto;
    overscroll-behavior: contain;
  }
  body.atlas-embed #workspace-body.is-mobile-chronicle-open #map-key { display: none; }
}

/* 时间轴：直接贴屏幕底部，仅保留 8px 安全间隙 */
body.atlas-embed #scrubber-dock {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: calc(env(safe-area-inset-bottom, 0px) + 8px);
  z-index: 66;
  width: min(880px, calc(100vw - 20px));
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(252, 249, 242, 0.74), rgba(246, 240, 229, 0.62));
  -webkit-backdrop-filter: blur(26px) saturate(1.8);
  backdrop-filter: blur(26px) saturate(1.8);
  box-shadow: 0 12px 32px rgba(30, 27, 24, 0.2);
  transition: opacity 0.35s ease;
}
/* 时间轴触摸拖动：交给指针事件，避免被浏览器手势抢走 */
body.atlas-embed #scrubber-track { touch-action: none; }

/* 触碰地图：悬浮面板淡到 75%；拖动/滚轮缩放地图：全部降到 15%，松手恢复 */
body.atlas-embed.ui-recede #nav-bar,
body.atlas-embed.ui-recede #scrubber-dock,
body.atlas-embed.ui-recede #chronicle-pane,
body.atlas-embed.ui-recede #map-key,
body.atlas-embed.ui-recede #canvas-br-dock,
body.atlas-embed.ui-recede #act-toggle-pane { opacity: 0.75; }

body.atlas-embed #map-key,
body.atlas-embed #canvas-br-dock { transition: opacity 0.3s ease, transform 0.28s ease; }

body.atlas-embed.ui-move #nav-bar,
body.atlas-embed.ui-move #scrubber-dock,
body.atlas-embed.ui-move #chronicle-pane,
body.atlas-embed.ui-move #map-key,
body.atlas-embed.ui-move #canvas-br-dock,
body.atlas-embed.ui-move #act-toggle-pane {
  opacity: 0.15;
  transition-duration: 0.18s;
}

/* 详情卡收起/展开手柄：贴在卡片左缘，收起后滑到屏幕右缘 */
body.atlas-embed #act-toggle-pane {
  position: fixed;
  top: 50%;
  right: calc(min(330px, 30vw) + 20px);
  transform: translateY(-50%);
  z-index: 64;
  width: auto;
  min-height: 0;
  flex-direction: row;
  align-items: center;
  gap: 4px;
  padding: 9px 10px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 15px;
  background: linear-gradient(180deg, rgba(252, 249, 242, 0.84), rgba(246, 240, 229, 0.72));
  -webkit-backdrop-filter: blur(22px) saturate(1.8);
  backdrop-filter: blur(22px) saturate(1.8);
  box-shadow: 0 8px 22px rgba(30, 27, 24, 0.18), 0 1px 0 rgba(255, 255, 255, 0.7) inset;
  transition: right 0.32s ease, opacity 0.3s ease, background 0.15s ease;
}
body.atlas-embed #act-toggle-pane .tp-arrow { font-size: 15px; line-height: 1; }
body.atlas-embed #act-toggle-pane .tp-label {
  writing-mode: horizontal-tb;
  font-size: 12px;
  letter-spacing: 0.04em;
}
body.atlas-embed #workspace-body.is-pane-collapsed #act-toggle-pane { right: 14px; }
body.atlas-embed #act-toggle-pane:hover {
  width: auto;
  background: linear-gradient(180deg, rgba(255, 253, 248, 0.95), rgba(250, 246, 238, 0.88));
}

/* 左下角图例：抬到时间轴胶囊上方，避免重叠；禁原生拖拽/选区（防 dragstart 劫持滑动手势） */
@media (min-width: 901px) {
  body.atlas-embed #map-key {
    bottom: calc(env(safe-area-inset-bottom, 0px) + 132px);
    max-height: calc(100vh - 268px);
    overflow-y: auto;
    overscroll-behavior: contain;
  }
}
body.atlas-embed #map-key {
  user-select: none;
  -webkit-user-select: none;
}
body.atlas-embed #map-key * { -webkit-user-drag: none; user-drag: none; }

/* 左下角图例：底部提示左右滑动 */
body.atlas-embed #map-key::after {
  content: '‹ 左右滑动 · 同步时间轴 ›';
  margin-top: 3px;
  padding-top: 3px;
  border-top: 1px dashed rgba(120, 100, 70, 0.22);
  font-size: 10px;
  letter-spacing: 0.06em;
  text-align: center;
  color: #9A8A74;
}

/* ================= 响应式档案夹 + 实测时间轴避让（v13） ================= */
/* 复位视图与比例尺：固定在地图右上角，纵向紧凑排列 */
body.atlas-embed #canvas-br-dock {
  position: fixed;
  top: calc(env(safe-area-inset-top, 0px) + 6px);
  right: calc(env(safe-area-inset-right, 0px) + 6px);
  bottom: auto;
  z-index: 74;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}
body.atlas-embed #canvas-br-dock .canvas-reset-btn {
  padding: 5px 8px;
  border-radius: 9px;
  background: rgba(247, 242, 232, 0.88);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}
body.atlas-embed #scale-bar-box { padding-right: 2px; }

/* 所有底部浮卡共用时间轴实测留白，JS 在尺寸变化时更新 --dock-clearance */
@media (min-width: 768px) {
  body.atlas-embed #map-key {
    bottom: var(--dock-clearance, calc(env(safe-area-inset-bottom, 0px) + 132px));
    max-height: min(42vh, 360px);
    overflow-y: auto;
    overscroll-behavior: contain;
  }
}

/* 手机：史志条贴时间轴上缘，图例再贴史志条上缘；位置全部由实际矩形计算 */
@media (max-width: 767px) {
  body.atlas-embed #chronicle-pane {
    bottom: var(--dock-clearance, calc(env(safe-area-inset-bottom, 0px) + 128px));
    max-height: min(43vh, 340px);
  }
  body.atlas-embed #map-key {
    bottom: var(--phone-pane-clearance, calc(env(safe-area-inset-bottom, 0px) + 188px));
    max-height: min(30vh, 230px);
    overflow-y: auto;
    overscroll-behavior: contain;
  }
  body.atlas-embed #map-key::after { display: none; }
}

/* 平板 / 电脑：史志与事件共用右侧美式马尼拉档案夹，顶部索引签切换 */
body.atlas-embed .archive-folder-tabs { display: none; }
@media (min-width: 768px) {
  body.atlas-embed .archive-folder-tabs {
    position: fixed;
    top: calc(env(safe-area-inset-top, 0px) + 62px);
    right: calc(env(safe-area-inset-right, 0px) + 14px);
    z-index: 65;
    display: flex;
    align-items: flex-end;
    gap: 5px;
    height: 34px;
    pointer-events: auto;
  }
  body.atlas-embed .archive-folder-tab {
    position: relative;
    min-width: 106px;
    height: 29px;
    padding: 0 18px 3px;
    border: 1px solid rgba(105, 82, 45, 0.34);
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    clip-path: polygon(0 100%, 0 10px, 11px 0, calc(100% - 11px) 0, 100% 10px, 100% 100%);
    background: #cbb887;
    color: #665433;
    font-family: var(--serif-stack);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .08em;
    cursor: pointer;
    box-shadow: 0 -3px 9px rgba(65, 48, 25, 0.10);
    transition: height .16s ease, background .16s ease, color .16s ease;
  }
  body.atlas-embed .archive-folder-tab small {
    margin-left: 5px;
    font-family: var(--sans-stack);
    font-size: 8px;
    font-weight: 600;
    letter-spacing: .05em;
    opacity: .64;
  }
  body.atlas-embed .archive-folder-tab.is-active {
    height: 34px;
    background: #ead9ae;
    color: #4f3c20;
    z-index: 2;
  }
  body.atlas-embed .archive-folder-tab:active { transform: translateY(1px); }

  body.atlas-embed #chronicle-pane,
  body.atlas-embed #milestone-balloon {
    box-sizing: border-box;
    position: fixed;
    top: calc(env(safe-area-inset-top, 0px) + 96px) !important;
    right: calc(env(safe-area-inset-right, 0px) + 14px) !important;
    bottom: var(--dock-clearance, calc(env(safe-area-inset-bottom, 0px) + 132px));
    left: auto !important;
    width: min(340px, 34vw);
    max-width: min(340px, 34vw);
    max-height: none;
    margin: 0;
    padding: 20px 20px 16px;
    border: 1px solid rgba(105, 82, 45, 0.34);
    border-top: 2px solid rgba(105, 82, 45, 0.42);
    border-radius: 4px 4px 12px 12px;
    background-color: rgba(234, 217, 174, 0.95);
    background-image: linear-gradient(rgba(255,255,255,.16), rgba(255,255,255,0)),
      repeating-linear-gradient(0deg, transparent 0, transparent 27px, rgba(113,91,50,.055) 28px);
    -webkit-backdrop-filter: blur(20px) saturate(1.25);
    backdrop-filter: blur(20px) saturate(1.25);
    box-shadow: 0 15px 34px rgba(54, 40, 20, 0.23), inset 0 0 0 5px rgba(255, 250, 230, 0.16);
    color: #44351f;
    overflow-y: auto;
    overscroll-behavior: contain;
  }
  body.atlas-embed #chronicle-pane::after,
  body.atlas-embed #milestone-balloon::after {
    content: 'HISTORICAL ARCHIVE';
    display: block;
    margin-top: 14px;
    padding-top: 8px;
    border-top: 1px solid rgba(105, 82, 45, 0.25);
    color: rgba(91, 69, 35, 0.58);
    font-family: var(--sans-stack);
    font-size: 8px;
    font-weight: 700;
    letter-spacing: .22em;
    text-align: right;
  }
  body.atlas-embed #milestone-balloon {
    bottom: auto !important;
    height: auto;
    min-height: 150px;
    max-height: calc(100dvh - 102px - var(--dock-clearance, 132px));
    font-size: 13px;
    line-height: 1.75;
    transition: opacity .2s ease;
  }
  body.atlas-embed #milestone-balloon::before { display: none; }
  body.atlas-embed #milestone-balloon .ep-head { padding-right: 24px; }
  body.atlas-embed #milestone-balloon .ep-year { font-size: 13px; color: #87422d; }
  body.atlas-embed #milestone-balloon .ep-text { margin-top: 10px; }
  body.atlas-embed #milestone-balloon .archive-empty {
    color: #75613e;
    font-family: var(--serif-stack);
    line-height: 1.9;
  }
  body.atlas-embed #milestone-balloon .archive-empty strong {
    display: block;
    margin-bottom: 8px;
    color: #513d20;
    font-size: 18px;
    font-weight: 600;
  }

  /* 档案夹互斥显示：保留原应用状态，只切换可见性 */
  body.atlas-embed[data-archive-tab="chronicle"] #milestone-balloon {
    visibility: hidden;
    opacity: 0;
    pointer-events: none;
  }
  body.atlas-embed[data-archive-tab="event"] #chronicle-pane {
    visibility: hidden;
    opacity: 0;
    pointer-events: none;
  }
  body.atlas-embed[data-archive-tab="event"] #act-toggle-pane { opacity: 0; pointer-events: none; }

  /* iPad 竖屏原本落入 <=900px 手机紧凑规则，这里恢复完整档案内容 */
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane {
    display: flex;
    height: auto !important;
    min-height: 0 !important;
    padding: 20px 20px 16px !important;
    border: 1px solid rgba(105, 82, 45, 0.34) !important;
    overflow-y: auto !important;
    opacity: 1;
    pointer-events: auto;
    gap: 14px;
  }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane .dynasty-banner {
    display: block;
    width: 100%;
    margin: 0;
    padding: 0;
    border-bottom: none;
    cursor: default;
  }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane .dynasty-title-row {
    display: flex;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--dynasty-accent);
    overflow: visible;
  }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane #dynasty-title {
    font-size: 32px;
    overflow: visible;
    text-overflow: clip;
  }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane #dynasty-span { font-size: 12px; }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane .seat-row {
    display: flex;
    width: auto;
    margin-top: 8px;
    font-size: 12.5px;
  }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane #dynasty-summary { display: block; }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane .milestone-section { display: block; }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane .disclaimer-box { display: block; }
  body.atlas-embed #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane .mobile-chronicle-btn { display: none; }
  body.atlas-embed[data-archive-tab="event"] #workspace-body:not(.is-mobile-chronicle-open) #chronicle-pane {
    visibility: hidden;
    opacity: 0;
    pointer-events: none;
  }
  body.atlas-embed #workspace-body.is-pane-collapsed:not(.is-mobile-chronicle-open) #chronicle-pane {
    width: min(340px, 34vw);
  }
}

/* ================= 不透明界面（v14）：取消所有背景透明度与淡出效果 ================= */
body.atlas-embed,
body.atlas-embed * {
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
}
body.atlas-embed #nav-bar,
body.atlas-embed #scrubber-dock,
body.atlas-embed #map-key,
body.atlas-embed #chronicle-pane,
body.atlas-embed #milestone-balloon,
body.atlas-embed #act-toggle-pane {
  opacity: 1;
  background-color: #F7F2E8;
  background-image: none;
}
body.atlas-embed #nav-bar { border-color: #D8CBB6; }
body.atlas-embed .brand-group .home-link {
  background: #E9DFCE;
}
body.atlas-embed #nav-bar .action-btn.subtle,
body.atlas-embed .locale-pill-group,
body.atlas-embed .music-pill-group,
body.atlas-embed .search-input-wrap {
  background: #FCF8F0;
}
body.atlas-embed #layers-popover {
  background: #FBF8F1;
}
body.atlas-embed .play-speed-btn {
  background: #FFFFFF;
}
body.atlas-embed #act-toggle-pane:hover {
  background: #FFFDF8;
}
body.atlas-embed #canvas-br-dock .canvas-reset-btn {
  background: #F7F2E8;
  border-color: #D8CBB6;
}
body.atlas-embed #scale-bar-box {
  padding: 4px 6px;
  border: 1px solid #D8CBB6;
  border-radius: 8px;
  background: #F7F2E8;
}
body.atlas-embed .scale-label { text-shadow: none; }
body.atlas-embed .archive-folder-tab small { opacity: 1; }

/* 触碰或拖动地图时不再把任何面板变淡 */
body.atlas-embed.ui-recede #nav-bar,
body.atlas-embed.ui-recede #scrubber-dock,
body.atlas-embed.ui-recede #chronicle-pane,
body.atlas-embed.ui-recede #map-key,
body.atlas-embed.ui-recede #canvas-br-dock,
body.atlas-embed.ui-recede #act-toggle-pane,
body.atlas-embed.ui-move #nav-bar,
body.atlas-embed.ui-move #scrubber-dock,
body.atlas-embed.ui-move #chronicle-pane,
body.atlas-embed.ui-move #map-key,
body.atlas-embed.ui-move #canvas-br-dock,
body.atlas-embed.ui-move #act-toggle-pane {
  opacity: 1;
}

/* 平板 / 电脑的档案夹同样使用不透明马尼拉纸色 */
@media (min-width: 768px) {
  body.atlas-embed #chronicle-pane,
  body.atlas-embed #milestone-balloon {
    background-color: #EAD9AE;
    background-image: repeating-linear-gradient(
      0deg,
      #EAD9AE 0,
      #EAD9AE 27px,
      #E2CF9E 28px
    );
  }
}

/* 文字光晕：用描边代替 SVG 滤镜（iPad 上省掉大量 filter 重绘） */
body.atlas-embed #atlas-svg text[filter] {
  filter: none !important;
  paint-order: stroke fill;
  stroke: #F7F2E6;
  stroke-width: 2.4px;
  stroke-linejoin: round;
}
</style>
'''
idx = must_replace(idx, '</head>', EMBED_CSS + '</head>', 'head unify css')

# ------------------------------------------------------------ 9. app.js 裁剪
app = read('app.js')

# 9.1 语言：锁定简体
app = must_sub(
    app,
    r"      const rawLang = \(new URLSearchParams\(location\.search\)\.get\('lang'\) \|\| ''\)\.toLowerCase\(\);\n"
    r"      this\.locale =\n"
    r"        rawLang === 'en'\n"
    r"          \? 'en'\n"
    r"          : /\^\(zh-tw\|zh_tw\|tw\|hk\|zh-hk\|zh_hk\|zh-hant\|zh_hant\|hant\)\$/\.test\(rawLang\)\n"
    r"            \? 'zh-tw'\n"
    r"            : 'zh';",
    "      /* 内嵌版：锁定简体中文（语言切换已移除） */\n      this.locale = 'zh';",
    'locale lock',
)

# 9.2 品牌文案：seal=长卷，副标题=疆域图谱
app = must_sub(
    app,
    r"      this\._id\('txt-seal'\)\.textContent = this\.uiStr\('brand_seal', '江山时序'\);\n"
    r"      const homeLink = this\._id\('act-home'\);\n"
    r"      if \(homeLink\) \{\n"
    r".*?\n      \}\n",
    "      this._id('txt-seal').textContent = '长卷';\n"
    "      const homeLink = this._id('act-home');\n"
    "      if (homeLink) homeLink.title = '回到长卷并定位到当前年份';\n",
    'brand text',
    re.S,
)
app = must_replace(
    app,
    "this._id('txt-subtitle').textContent = this.uiStr('brand_sub', '中国历史地图 · 战国 → 今');",
    "this._id('txt-subtitle').textContent = '疆域图谱';",
    'subtitle',
)

# 9.3 删除古琴雅乐模块
i = app.find('    // ---------------- Classical Guqin Music Player ----------------')
assert i > 0, 'music block not found'
j = app.find('    // ---------------- Camera Pan & Zoom ----------------', i)
assert j > i
app = app[:i] + app[j:]
app = must_replace(app, '      this._updateMusicUi();\n', '', 'music ui call')

# 9.4 关闭初次到访指引（含科举挑战入口）
app = must_replace(
    app,
    '    _maybeShowStartGuide() {\n',
    '    _maybeShowStartGuide() {\n      return; // 内嵌版：不弹「初次到访 / 舆图寻址」指引\n',
    'start guide off',
)
# 挑战卡片已从 DOM 移除，两处绑定补空安全
app = must_replace(
    app,
    "      this._id('act-close-challenge').addEventListener('click', () => this.stopChallenge());\n"
    "      this._id('act-next-round').addEventListener('click', () => {",
    "      const _chalClose = this._id('act-close-challenge');\n"
    "      if (_chalClose) _chalClose.addEventListener('click', () => this.stopChallenge());\n"
    "      const _chalNext = this._id('act-next-round');\n"
    "      if (_chalNext) _chalNext.addEventListener('click', () => {",
    'challenge bind guard',
)

# 9.5 状态回传钩子（年份 / 人物）
app = must_replace(
    app,
    '      this.year = y;\n      this._scheduleUrlSync();',
    '      this.year = y;\n      if (window.__atlasSync) window.__atlasSync();\n      this._scheduleUrlSync();',
    'year sync hook',
)
app = must_replace(
    app,
    '      this.activePerson = state;\n      this.activePersonEventIdx =',
    '      this.activePerson = state;\n      if (window.__atlasSync) window.__atlasSync();\n      this.activePersonEventIdx =',
    'person sync hook',
)
app = must_replace(
    app,
    '      this.activePerson = null;\n      this.activePersonEventIdx = -1;',
    '      this.activePerson = null;\n      if (window.__atlasSync) window.__atlasSync();\n      this.activePersonEventIdx = -1;',
    'person clear sync hook',
    2,   # 构造器初始化 + _clearActivePerson
)

# 9.6 locale 绑定节点已移除，补空安全（act-locale 直接绑定的那一处）
app = app.replace(
    "      this._id('act-locale').addEventListener('click', () => {",
    "      const _actLocEl = this._id('act-locale');\n      if (_actLocEl) _actLocEl.addEventListener('click', () => {",
)

# ---------------------------------------- 10. 全量 DYNASTY_DATA（不再裁剪）
md = read('map_data.js')
m = re.search(r'(window\.DYNASTY_DATA\s*=\s*)(\[.*?\n\])', md, re.S)
assert m, 'DYNASTY_DATA not found'
D = json.loads(m.group(2))
assert len(D) >= 18, len(D)
new_md = md[:m.start(2)] + json.dumps(D, ensure_ascii=False) + md[m.end(2):]

# --------------------------------------------------- 11. 按原顺序内联各脚本
scripts = [
    ('js/china_geo_data.js?v=5c8bd520', read('china_geo_data.js')),
    ('__snapshots__', read('atlas_snapshots.js')),
    ('js/atlas_boot.js?v=9074be71', read('atlas_boot.js')),
    ('js/map_data.js?v=22d13b6b', new_md),          # 全量版
    ('js/lore_data.js?v=7bcd66a3', read('lore_data.js')),
    ('js/app.js?v=2c51b2f8', app),                  # 裁剪版
    # zh_hant.js / atlas_quiz.js 不再内联（语言切换与科举挑战已移除）
]
for src, body in scripts:
    if src == '__snapshots__':
        safe = body.replace('</script', '<\\/script')
        idx = idx.replace('<script id="atlas-app-script"',
                          '<script>\n' + safe + '\n</script>\n<script id="atlas-app-script"')
        continue
    tag = re.search(r'<script[^>]*src="%s"[^>]*>\s*</script>' % re.escape(src), idx)
    assert tag, 'script tag not found: %s' % src
    safe = body.replace('</script', '<\\/script')
    idx = idx.replace(tag.group(0), '<script>\n' + safe + '\n</script>')

# 已移除的脚本标签清理（避免 404）
for gone in ['zh_hant.js', 'atlas_quiz.js']:
    idx = re.sub(r'<script[^>]*src="js/%s[^"]*"[^>]*>\s*</script>\s*' % gone.replace('.', r'\.'), '', idx)

# ---------------------------------------------------- 12. 标题与副标题文案
idx = idx.replace('</title>', ' · 疆域图谱</title>')
idx = idx.replace('中国历史地图 · 战国 → 今', '疆域图谱 · 前 403 — 1912')

# ------------------------------------------- 13. 双向联动桥（含返回长卷按钮）
BRIDGE = r'''
<script>
/* ============ 内嵌联动桥 v2（与「华夏千年历史长卷」双向同步）============
   上行：__atlasReady / __atlasAck / __atlasState / __atlasExit
   下行：{ __atlas:1, year, person, token } / { __atlas:1, __atlasQuery:1 }
   原则：只发消息，绝不重载文档，保证地图内部状态连续 */
/* iOS：锁整页上下滑动（overflow:hidden 在 iOS Safari 上仍会出现橡皮筋滚动）。
   触摸落在真实可滚动的容器（面板内容、史志窗格等）内时放行，其余一律拦截。 */
(function () {
  var isScrollable = function (el, axis) {
    var s = getComputedStyle(el);
    var ov = axis === 'x' ? s.overflowX : s.overflowY;
    return (ov === 'auto' || ov === 'scroll') &&
      (axis === 'x' ? el.scrollWidth : el.scrollHeight) >
      (axis === 'x' ? el.clientWidth : el.clientHeight) + 1;
  };
  document.addEventListener('touchmove', function (e) {
    var t = e.target;
    while (t && t.nodeType === 1 && t !== document.documentElement) {
      if (isScrollable(t, 'y') || isScrollable(t, 'x')) return;
      t = t.parentElement;
    }
    e.preventDefault();
  }, { passive: false });
})();
(function () {
  var EMBED = false;
  try { EMBED = !!(window.parent && window.parent !== window); } catch (e) { EMBED = false; }

  function post(msg) {
    if (!EMBED) return;
    try { window.parent.postMessage(msg, '*'); } catch (e) {}
  }
  function app() { return window.atlasApp || null; }

  function snap() {
    var a = app();
    if (!a) return null;
    var p = (a.activePerson && a.activePerson.profiles && a.activePerson.profiles[0]) || null;
    var d = (a.dynasties && a.dynasties[a.dynastyIdx]) || null;
    return {
      __atlasState: 1,
      year: typeof a.year === 'number' ? a.year : null,
      person: p ? p.key : null,
      personName: p ? (p.zh || p.nameZh || '') : null,
      dyn: d ? (d.nameZh || d.name || '') : '',
      playing: !!a.playing
    };
  }

  var lastSig = '';
  var syncTimer = 0;
  function sync(force) {
    var s = snap();
    if (!s) return;
    var sig = s.year + '|' + s.person;
    if (!force && sig === lastSig) return;
    lastSig = sig;
    post(s);
  }
  window.__atlasSync = function () {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(function () { sync(false); }, 120);
  };

  function apply(d) {
    var a = app();
    if (!a) return false;
    try {
      if (a.stopAutoplay) a.stopAutoplay();
      if (d.person) {
        a.openPersonChronicle(d.person, -1);
      } else {
        if (a.activePerson && a.closeGenealogyCard) a.closeGenealogyCard();
        if (typeof d.year === 'number' && isFinite(d.year) && a.jumpToYear) a.jumpToYear(d.year);
      }
      return true;
    } catch (e) { return false; }
  }

  var pending = null;

  window.addEventListener('message', function (e) {
    var d = e.data;
    if (typeof d === 'string') { try { d = JSON.parse(d); } catch (err) { return; } }
    if (!d || d.__atlas !== 1) return;
    if (d.__atlasQuery) {
      var s0 = snap() || {};
      post({ __atlasAck: 1, token: d.token || null, year: s0.year, person: s0.person, personName: s0.personName });
      return;
    }
    if (apply(d)) {
      post({ __atlasAck: 1, token: d.token || null, year: d.year, person: d.person || null });
      sync(true);
    } else {
      pending = d;
    }
  });

  function bindBack() {
    var b = document.getElementById('act-home');
    if (!b || b.__atlasBound) return;
    b.__atlasBound = 1;
    b.addEventListener('click', function (ev) {
      ev.preventDefault();
      var s = snap() || {};
      post({
        __atlasExit: 1,
        year: s.year, person: s.person, personName: s.personName, dyn: s.dyn
      });
    });
  }

  var tries = 0;
  var timer = setInterval(function () {
    tries += 1;
    if (app()) {
      clearInterval(timer);
      bindBack();
      post({ __atlasReady: 1 });
      if (pending) {
        var p = pending; pending = null;
        if (apply(p)) post({ __atlasAck: 1, token: p.token || null, year: p.year, person: p.person || null });
        sync(true);
      } else {
        sync(true);
      }
    } else if (tries > 500) {
      clearInterval(timer);
    }
  }, 60);
})();
</script>
<script id="atlas-float-ui">
/* 悬浮 UI 状态：触碰地图 → 75%；拖动 / 滚轮缩放地图 → 15%；松手恢复 */
(function () {
  function boot() {
    var body = document.body;
    var viewport = document.getElementById('viewport-frame');
    var dock = document.getElementById('scrubber-dock');
    if (!viewport || !dock) { setTimeout(boot, 120); return; }
    var restoreTimer = 0;
    var moveTimer = 0;
    function recede(on) {
      clearTimeout(restoreTimer);
      if (on) body.classList.add('ui-recede');
      else restoreTimer = setTimeout(function () { body.classList.remove('ui-recede'); }, 160);
    }
    function moving(on) {
      clearTimeout(moveTimer);
      if (on) body.classList.add('ui-move');
      else moveTimer = setTimeout(function () { body.classList.remove('ui-move'); }, 220);
    }
    var dragging = false;
    viewport.addEventListener('pointerdown', function () {
      dragging = true; recede(true); moving(false);
    }, { passive: true });
    window.addEventListener('pointermove', function (e) {
      if (dragging && ((e.buttons && e.buttons > 0) || (e.touches && e.touches.length > 0))) moving(true);
    }, { passive: true });
    window.addEventListener('wheel', function () { moving(true); }, { passive: true });
    function endDrag() { dragging = false; moving(false); recede(false); }
    window.addEventListener('pointerup', endDrag, { passive: true });
    window.addEventListener('pointercancel', endDrag, { passive: true });

    ['nav-bar', 'scrubber-dock', 'chronicle-pane', 'map-key', 'canvas-br-dock', 'milestone-balloon'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('pointerdown', function () { recede(false); moving(false); dragging = false; }, { passive: true });
    });

    /* 左下角图例：左右滑动 = 时间轴上一站 / 下一站 */
    var key = document.getElementById('map-key');
    if (key) {
      key.addEventListener('dragstart', function (e) { e.preventDefault(); });
      var sx = 0, sy = 0, dx = 0, active = false, horiz = false;
      key.addEventListener('pointerdown', function (e) {
        if (e.button && e.button !== 0) return;
        e.stopPropagation();               /* 不当作地图触摸，也不触发地图拖拽 */
        active = true; horiz = false; dx = 0;
        sx = e.clientX; sy = e.clientY;
      }, { passive: true });
      window.addEventListener('pointermove', function (e) {
        if (!active) return;
        if (e.pointerType === 'mouse' && e.buttons === 0) { settle(); return; }  /* 兜底：pointerup 丢失 */
        dx = e.clientX - sx;
        var dy = e.clientY - sy;
        if (!horiz) {
          if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
          horiz = Math.abs(dx) > Math.abs(dy);
          if (!horiz) { active = false; return; }
        }
        var off = Math.max(-44, Math.min(44, dx / 2.4));
        key.style.transition = 'none';
        key.style.transform = 'translateX(' + off.toFixed(1) + 'px)';
      }, { passive: true });
      function settle() {
        if (!active) return;
        active = false;
        key.style.transition = '';
        key.style.transform = '';
        if (horiz && Math.abs(dx) > 36) {
          var btn = document.getElementById(dx < 0 ? 'act-step-next' : 'act-step-prev');
          if (btn) btn.click();
        }
        horiz = false;
      }
      window.addEventListener('pointerup', settle, { passive: true });
      window.addEventListener('pointercancel', settle, { passive: true });
    }

    /* ===== v13：档案夹双标签 + 浮卡对时间轴的实测避让 ===== */
    var pane = document.getElementById('chronicle-pane');
    var balloon = document.getElementById('milestone-balloon');
    var root = document.documentElement;
    var archivePlaceholder = false;
    var layoutRaf = 0;

    function archiveMode() { return window.innerWidth >= 768; }
    function setVar(name, value) {
      if (root.style.getPropertyValue(name) !== value) root.style.setProperty(name, value);
    }
    function scheduleLayout() {
      if (layoutRaf) return;
      layoutRaf = requestAnimationFrame(function () {
        layoutRaf = 0;
        var dr = dock.getBoundingClientRect();
        var dockClear = 0;
        if (dr.height > 0) {
          dockClear = Math.max(72, Math.round(window.innerHeight - dr.top + 6));
          setVar('--dock-clearance', dockClear + 'px');
        }
        if (pane && window.innerWidth < 768) {
          var pr = pane.getBoundingClientRect();
          if (pr.height > 0 && dockClear) {
            /* 面板底边贴时间轴上方；图例再贴面板上缘，全部按实测高度推算 */
            setVar('--phone-pane-clearance', Math.round(dockClear + pr.height + 6) + 'px');
          }
        }
      });
    }

    if (pane && balloon) {
      var tabs = document.createElement('div');
      tabs.className = 'archive-folder-tabs';
      tabs.setAttribute('role', 'tablist');
      tabs.setAttribute('aria-label', '历史档案分类');
      tabs.innerHTML =
        '<button type="button" class="archive-folder-tab is-active" data-tab="chronicle" role="tab" aria-selected="true">史志<small>CHRONICLE</small></button>' +
        '<button type="button" class="archive-folder-tab" data-tab="event" role="tab" aria-selected="false">事件<small>EVENT</small></button>';
      body.appendChild(tabs);
      body.setAttribute('data-archive-tab', 'chronicle');

      function paintTabs(name) {
        tabs.querySelectorAll('.archive-folder-tab').forEach(function (btn) {
          var on = btn.getAttribute('data-tab') === name;
          btn.classList.toggle('is-active', on);
          btn.setAttribute('aria-selected', on ? 'true' : 'false');
        });
      }
      function showEventPlaceholder() {
        archivePlaceholder = true;
        balloon.innerHTML = '<div class="archive-empty"><strong>事件档案</strong>点击地图上的事件圆点，或切换到「史志」签点击重大事件，这里就会展开对应的年份、地点与史事。</div>';
        balloon.classList.remove('is-hidden', 'is-offscreen');
      }
      function selectArchive(name) {
        if (!archiveMode()) return;
        if (name === 'chronicle') {
          var workspace = document.getElementById('workspace-body');
          if (workspace && workspace.classList.contains('is-pane-collapsed')) {
            var toggle = document.getElementById('act-toggle-pane');
            if (toggle) toggle.click();
          }
          if (archivePlaceholder) {
            archivePlaceholder = false;
            balloon.classList.add('is-hidden');
          }
        } else if (!balloon.querySelector('.ep-text')) {
          showEventPlaceholder();
        }
        body.setAttribute('data-archive-tab', name);
        paintTabs(name);
        recede(false);
        moving(false);
        scheduleLayout();
      }
      tabs.addEventListener('pointerdown', function (e) {
        e.stopPropagation();
        recede(false); moving(false); dragging = false;
      }, { passive: true });
      tabs.querySelectorAll('.archive-folder-tab').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault(); e.stopPropagation();
          selectArchive(btn.getAttribute('data-tab'));
        });
      });

      /* 点击地图事件后自动翻到「事件」签；关闭事件后回到「史志」签 */
      var balloonObserver = new MutationObserver(function () {
        if (!archiveMode()) return;
        var hidden = balloon.classList.contains('is-hidden');
        if (!hidden && balloon.querySelector('.ep-text')) {
          archivePlaceholder = false;
          var atlas = window.atlasApp;
          var automatic = atlas && atlas.activeMilestone && atlas.activeMilestone.isAuto;
          if (!automatic) {
            body.setAttribute('data-archive-tab', 'event');
            paintTabs('event');
          }
        } else if (hidden && !archivePlaceholder && body.getAttribute('data-archive-tab') === 'event') {
          body.setAttribute('data-archive-tab', 'chronicle');
          paintTabs('chronicle');
        }
        scheduleLayout();
      });
      balloonObserver.observe(balloon, { attributes: true, attributeFilter: ['class'], childList: true });

      function onResize() {
        if (!archiveMode()) {
          if (archivePlaceholder) {
            archivePlaceholder = false;
            balloon.classList.add('is-hidden');
          }
          body.setAttribute('data-archive-tab', 'chronicle');
          paintTabs('chronicle');
        }
        scheduleLayout();
      }
      window.addEventListener('resize', onResize, { passive: true });
      window.addEventListener('orientationchange', function () { setTimeout(scheduleLayout, 260); }, { passive: true });
      if (window.ResizeObserver) {
        var layoutObserver = new ResizeObserver(scheduleLayout);
        layoutObserver.observe(dock);
        layoutObserver.observe(pane);
        if (key) layoutObserver.observe(key);
      }
      scheduleLayout();
      setTimeout(scheduleLayout, 350);
      setTimeout(scheduleLayout, 1100);
    }
  }
  boot();
})();
</script>
'''
assert '</body>' in idx
idx = idx.replace('</body>', BRIDGE + '</body>')

out = 'jiangshan-atlas.html'
open(out, 'w', encoding='utf-8').write(idx)

# --------------------------------------------------------------- 自检输出
checks = {
    'github 链接': idx.count('github.com/DeanChensj'),
    'music 节点': idx.count('music-pill-group'),
    'locale 节点': idx.count('locale-pill-group'),
    'act-music': idx.count('act-music'),
    'act-locale': idx.count('act-locale'),
    'challenge-card': idx.count('challenge-card'),
    'seo-atlas-directory': idx.count('seo-atlas-directory'),
    'googleapis': idx.count('googleapis.com'),
    'vercount': idx.count('vercount'),
    'zh_hant.js': idx.count('zh_hant.js'),
    'atlas_quiz.js': idx.count('atlas_quiz.js'),
    'GUQIN': idx.count('GUQIN_TRACKS'),
    '联动桥': idx.count('__atlasExit'),
}
print(out, '%.2f MB' % (len(idx.encode('utf-8')) / 1048576))
print('朝代数据 %d 个：%s' % (len(D), ','.join(d['key'] for d in D)))
for k, v in checks.items():
    print('  %-22s %d' % (k, v))
