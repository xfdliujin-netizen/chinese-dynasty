# -*- coding: utf-8 -*-
"""
把地图（jiangshan-atlas）的「史志事件（milestones）+ 人物（PERSON_PROFILES）」映射到长卷
index.html 时间轴，覆盖长卷原有事件、人物数据（盛世/文豪不动），一一对应。

策略：
  - 事件：地图 milestones（重大事件）为唯一来源，替换长卷战国（前403）及以后的事件；
          战国前的 6 条（夏商西周春秋）长卷原事件保留（地图无此时期数据）。
  - 人物：地图 PERSON_PROFILES（123 真人）覆盖长卷「人物」图层（FIGURE_AXIS）。
  - 盛世（GOLDEN_AGES）、文豪（LITERATI）不动。
  - UI 完全不动，只改数据层。
"""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
IDX = os.path.join(ROOT, 'index.html')
DYNASTY_JS = os.path.join(ROOT, 'atlas-dynasty.js')
LORE_JS = os.path.join(ROOT, 'atlas-lore.js')

# ---------- 读取地图数据 ----------
s = open(DYNASTY_JS, encoding='utf-8').read()
i = s.index('window.DYNASTY_DATA = ')
rest = s[i + len('window.DYNASTY_DATA = '):].strip()
dynasties = json.loads(rest[:rest.index('];') + 1])

s2 = open(LORE_JS, encoding='utf-8').read()
i2 = s2.index('window.ATLAS_LORE_DATA = {')
lore = json.loads(s2[i2 + len('window.ATLAS_LORE_DATA = '):].rstrip().rstrip(';'))
persons = lore['PERSON_PROFILES']

# ---------- 映射表 ----------
# 地图 dynastyKey -> (长卷 arc id, 朝代中文名)
KEY_TO_ARC = {
    'zhanguo': ('dzhou', '东周'), 'qin': ('qin', '秦朝'),
    'xihan': ('han', '西汉'), 'donghan': ('han', '东汉'),
    'sanguo': ('sanguo', '三国'), 'xijin': ('jin16', '西晋'),
    'dongjin': ('jin16', '东晋'), 'nanbei': ('nanbeichao', '南北朝'),
    'sui': ('sui', '隋朝'), 'tang': ('tang', '唐朝'),
    'wudai': ('wudai', '五代十国'), 'beisong': ('song', '北宋'),
    'nansong': ('song', '南宋'), 'yuan': ('yuan', '元朝'),
    'ming': ('ming', '明朝'), 'qing': ('qing', '清朝'),
}

def esc(s):
    return str(s or '').replace('\\', '\\\\').replace("'", "\\'").replace('\n', '').replace('\r', '')

def format_year(y):
    y = int(y)
    return ('前' + str(-y)) if y < 0 else str(y)

def classify(h):
    h = str(h or '')
    if any(k in h for k in ('变法', '改革', '建制', '称帝', '即位', '迁都', '立', '建', '统一', '册', '禅让', '称制', '改元', '称王')):
        return '政治变革'
    if any(k in h for k in ('战', '攻', '灭', '伐', '征', '叛', '起义', '军', '兵', '破', '陷', '屠', '围')):
        return '军事风云'
    if any(k in h for k in ('丝路', '遣', '下西洋', '朝贡', '和亲', '出使', '贸易', '凿空', '通西域', '北击')):
        return '对外开拓'
    if any(k in h for k in ('文', '书', '经', '诗', '赋', '学', '佛', '道', '科', '术', '纸', '印', '历', '医', '著', '编', '筑', '渠', '仓', '均田', '科举')):
        return '文明盛世'
    return '政治变革'

def short_title(h):
    h = re.sub(r'[（(][^）)]*[）)]', '', str(h or '')).strip()
    return h[:6] if h else '历史纪事'

# ---------- 生成事件 ----------
def build_events():
    events = []
    for di, d in enumerate(dynasties):
        key = d.get('key', '')
        arc, period = KEY_TO_ARC.get(key, (None, ''))
        if arc is None:
            continue
        for m in d.get('milestones', []):
            y = int(m.get('year', 0))
            hl = str(m.get('headline', '')).strip()
            if not hl:
                continue
            site = m.get('site', '')
            persons = m.get('persons', [])
            fig = ''
            if isinstance(persons, list) and persons:
                key_to_name = {p.get('key'): p.get('zh', p.get('key', '')) for p in persons if isinstance(p, dict)}
                fig = '、'.join([key_to_name.get(str(p), str(p) if not isinstance(p, dict) else p.get('zh', '')) for p in persons])
            events.append({
                'id': f'm{di:02d}-{len(events)}', 'year': y, 'period': period,
                'shortTitle': short_title(hl), 'title': hl, 'category': classify(hl),
                'figure': fig, 'desc': hl,
                'detail': (hl + ('；地点：' + site if site else '')),
                'impact': '', 'bk': hl,
            })
    events.sort(key=lambda e: (e['year'], e['id']))
    return events

# ---------- 生成人物 ----------
def build_figures():
    real = [p for p in persons if not p.get('isRelic')]
    figures = []
    for p in real:
        key = p.get('key', '')
        zh = p.get('zh', '')
        courtesy = p.get('courtesyZh', '')
        dkey = p.get('dynastyKey', '')
        span = p.get('span', [])
        arc, dyn = KEY_TO_ARC.get(dkey, (None, ''))
        if arc is None:
            continue
        y0 = int(span[0]) if isinstance(span, list) and len(span) >= 1 else 0
        y1 = int(span[1]) if isinstance(span, list) and len(span) >= 2 else y0
        life = f'{format_year(y0)}—{format_year(y1)}'
        figures.append({
            'id': f'at-{key}', 'kind': 'figure', 'n': zh, 'year': y0,
            'life': life, 'role': courtesy or '历史人物', 'd': courtesy or '',
            'dyn': dyn, 'arcId': arc, 'src': '',
        })
    figures.sort(key=lambda f: f['year'])
    return figures

def emit_event(e):
    return (f"      {{ id: '{e['id']}', year: {e['year']}, period: '{esc(e['period'])}', "
            f"shortTitle: '{esc(e['shortTitle'])}', title: '{esc(e['title'])}', "
            f"category: '{esc(e['category'])}', figure: '{esc(e['figure'])}',\n"
            f"        desc: '{esc(e['desc'])}',\n"
            f"        detail: '{esc(e['detail'])}',\n"
            f"        impact: '{esc(e['impact'])}', bk: '{esc(e['bk'])}' }},")

def emit_figure(f):
    return (f"      {{ id: '{f['id']}', kind: 'figure', n: '{esc(f['n'])}', year: {f['year']}, "
            f"life: '{esc(f['life'])}', role: '{esc(f['role'])}', d: '{esc(f['d'])}', "
            f"dyn: '{esc(f['dyn'])}', arcId: '{esc(f['arcId'])}', src: '{esc(f['src'])}' }}")

def main():
    events = build_events()
    figures = build_figures()
    print(f'生成事件 {len(events)} 条, 人物 {len(figures)} 条')

    s = open(IDX, encoding='utf-8').read()

    # === 1) 提取战国前原事件（e1~e6，year < -403）===
    i_start = s.index('const HISTORICAL_EVENTS = [')
    i_e7 = s.index("{ id: 'e7'")  # 战国从 e7（三家分晋 -403）开始
    keep_pre = s[i_start:i_e7]  # 含 "const HISTORICAL_EVENTS = [" 和 e1~e6
    # 去掉末尾可能多余的空白/逗号，保持原样（e1~e6 每条以 ' }, 结尾）

    # === 2) 组装新 HISTORICAL_EVENTS ===
    new_events = [keep_pre]
    for e in events:
        new_events.append(emit_event(e))
    new_events.append('    ];')
    new_events_block = '\n'.join(new_events)

    # === 3) 替换：从 const HISTORICAL_EVENTS = [ 到 push 行结束 ===
    i_extra = s.index('const EXTRA_EVENTS = [')
    i_push = s.index('HISTORICAL_EVENTS.push(...EXTRA_EVENTS, ...WAR_EVENTS, ...COMPAT_EVENTS);')
    i_push_end = s.index('\n', i_push) + 1

    new_seg = new_events_block + '\n\n' + \
        '    const EXTRA_EVENTS = [];\n    const WAR_EVENTS = [];\n    const COMPAT_EVENTS = [];\n'
    s = s[:i_start] + new_seg + s[i_push_end:]
    print('事件区已替换')

    # === 4) 重建 FIGURE_AXIS ===
    fa_start = s.index('const FIGURE_AXIS = [];')
    fa_end_marker = 'FIGURE_AXIS.sort((a, b) => a.year - b.year);'
    fa_end = s.index(fa_end_marker, fa_start) + len(fa_end_marker)

    fig_lines = ['    const FIGURE_AXIS = ['] + [emit_figure(f) + ',' for f in figures]
    fig_lines.append('    ];')
    fig_lines.append('    FIGURE_AXIS.sort((a, b) => a.year - b.year);')
    fig_block = '\n'.join(fig_lines)

    s = s[:fa_start] + fig_block + s[fa_end:]
    print('人物区已替换')

    open(IDX, 'w', encoding='utf-8', newline='\n').write(s)
    print('已写入 index.html')

if __name__ == '__main__':
    main()
