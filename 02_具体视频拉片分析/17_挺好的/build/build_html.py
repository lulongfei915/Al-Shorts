# -*- coding: utf-8 -*-
"""合并《挺好的》前2分钟 + 尾段73秒 HTML 拉片档案为全片版（0-193s）。
所有 base64 关键帧原样保留，不丢图、不丢数据。"""
import re, pickle, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE, 'build', 'assets.pkl'), 'rb') as f:
    A = pickle.load(f)

front = open(os.path.join(BASE, 'report', '拉片档案_挺好的_前2分钟.html'), encoding='utf-8').read()
tail  = open(os.path.join(BASE, 'report_tail', '拉片档案_挺好的_尾段73秒.html'), encoding='utf-8').read()

# ---------- 提取 1s 归一化数组（保留原始细粒度数据） ----------
def energy_arrays(html):
    t = re.search(r'const ENERGY_T=\[([^\]]+)\]', html).group(1)
    v = re.search(r'const ENERGY_V=\[([^\]]+)\]', html).group(1)
    T = [float(x) for x in t.split(',')]
    V = [float(x) for x in v.split(',')]
    return T, V
Tf, Vf = energy_arrays(front)   # 0..119
Tt, Vt = energy_arrays(tail)    # 0..73 (相对)
# 全片 1s 分段归一化数据（前段 0-119；尾段映射到 120-193）
F1S_T = Tf + [x + 120 for x in Tt]
F1S_V = Vf + Vt
assert len(F1S_T) == 194, len(F1S_T)

# ---------- 全片 5s 窗口 RMS（dB，跨段口径一致的原始实测值） ----------
# 前段 0..115（24点）
FRONT5_T = list(range(0, 120, 5))
FRONT5_V = [-19.1,-18.6,-19.6,-26.2,-23.2,-22.0,-26.7,-21.9,-18.8,-20.0,-18.4,-18.3,
            -21.5,-19.7,-20.3,-21.3,-19.2,-27.0,-19.2,-19.0,-19.0,-20.5,-32.8,-59.5]
# 尾段 0..70（相对）映射到 120..190（15点）
TAIL5_T = [120 + x for x in range(0, 75, 5)]
TAIL5_V = [-30.4,-20.9,-17.9,-20.2,-19.1,-35.4,-26.0,-22.6,-25.8,-23.0,-22.5,-28.7,-33.0,-34.8,-42.5]
# 118s 全静默谷底（117-118.8s 实测 -90.3dB）
CURVE_T = FRONT5_T + [118] + TAIL5_T
CURVE_V = FRONT5_V + [-90.3] + TAIL5_V
assert len(CURVE_T) == len(CURVE_V) == 40

# ---------- 镜头行：尾段重编号 40-72 ----------
rf, rt = A['rf'], A['rt']
new_tail = []
for i, row in enumerate(rt):
    new_no = i + 40
    row2 = re.sub(r'(<td class="no">)\d+(</td>)', r'\g<1>%d\g<2>' % new_no, row, count=1)
    new_tail.append(row2)

# ---------- 分组 ----------
def actrow(label, cool=False):
    cls = 'actrow cool' if cool else 'actrow'
    return '<tr class="%s"><td colspan="7">%s</td></tr>' % (cls, label)

shot_rows = []
shot_rows.append(actrow('第一幕 · 广场调查（00:00–00:36）· 冷', cool=True))
shot_rows += rf[0:12]
shot_rows.append(actrow('第二幕 · 家访父母（00:36–01:28）· 暖'))
shot_rows += rf[12:31]
shot_rows.append(actrow('第三幕 · 再访与揭示（01:28–02:00）· 冷', cool=True))
shot_rows += rf[31:39]
shot_rows.append(actrow('第四幕① 产品揭示·余韵（02:00–02:05）· 暖（承接01:52起12.8s产品长镜头）'))
shot_rows += new_tail[0:1]
shot_rows.append(actrow('第四幕② 归家·送枕（02:05–02:30）· 暖'))
shot_rows += new_tail[1:16]
shot_rows.append(actrow('第四幕③ 卧室·谈心（02:30–02:58）· 暖'))
shot_rows += new_tail[16:29]
shot_rows.append(actrow('第四幕④ 调查修正·落版（02:58–03:13）· 冷', cool=True))
shot_rows += new_tail[29:33]
SHOTS_HTML = '\n      '.join(shot_rows)

# ---------- CSS（复用前2分钟，无改动） ----------
CSS = re.search(r'<style>(.*?)</style>', front, re.S).group(1)

# ---------- 脚本数据序列化成 JS ----------
def js_arr(pairs):
    return '[' + ','.join('[%s,%s]' % (t, v) for t, v in pairs) + ']'
CURVE_JS = js_arr(zip(CURVE_T, CURVE_V))
F1S_JS = '[' + ','.join('[%s,%s]' % (t, v) for t, v in zip(F1S_T, F1S_V)) + ']'
print('curve points:', len(CURVE_T), '| 1s points:', len(F1S_T), '| shot rows:', len(shot_rows))

# ---------- 渲染 ----------
tpl = open(os.path.join(BASE, 'build', 'template.html'), encoding='utf-8').read()
html = (tpl
    .replace('__FAV__', A['fav'])
    .replace('__CSS__', CSS)
    .replace('__HERO__', A['hero_f'])
    .replace('__SHOTS__', SHOTS_HTML)
    .replace('__CURVE_DATA__', CURVE_JS)
    .replace('__F1S_DATA__', F1S_JS))

# 校验
assert html.count('data:image') == 1 + 72 + 1, html.count('data:image')  # favicon + 72镜头 + hero
assert '__' not in html.split('<script>')[0].replace('__INITIAL_STATE__',''), 'unreplaced placeholder in body'
assert html.count('class="no"') == 72

out = os.path.join(BASE, '拉片档案_挺好的_全片.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('written:', out, round(os.path.getsize(out)/1024/1024, 2), 'MB')
print('images embedded:', html.count('data:image'))
