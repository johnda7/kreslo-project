#!/usr/bin/env python3
# ВИД СВЕРХУ обведён по РЕАЛЬНОМУ облаку скана off-08 (взгляд вдоль оси симметрии).
# Как overlay_check.py, но проекция на плоскость u-v (сверху). Обводим наружный обод
# И устье-отверстие сиденья по точкам. Смещение и нахлёст — ЗАМЕР, не выдумка.
import trimesh, numpy as np, base64
from PIL import Image, ImageDraw, ImageFont

m = trimesh.load('models/ufo-tripo-off08.glb', force='mesh')
V = np.asarray(m.vertices, float)
c = V.mean(0); X = V - c
cov = X.T @ X
w, vec = np.linalg.eigh(cov)
axis = vec[:, 0]; e1 = vec[:, 1]; e2 = vec[:, 2]
t = X @ axis; u = X @ e1; v = X @ e2
r = np.hypot(u, v)
f = 665.0 / np.percentile(r, 99.9)          # калибровка обод -> 665мм (как в overlay_check)
t = t * f; u = u * f; v = v * f; r = r * f
# ориентация оси: узкий купол вниз
lo = t < np.percentile(t, 8); hi = t > np.percentile(t, 92)
if r[lo].mean() > r[hi].mean():
    t = -t
t = t - t.min()
H = t.max()

# --- НАРУЖНЫЙ ОБОД: угловой макс.радиус по секторам (силуэт сверху) ---
ang = np.arctan2(v, u)
NS = 180
edges = np.linspace(-np.pi, np.pi, NS + 1)
outer = np.zeros(NS)
for i in range(NS):
    sel = (ang >= edges[i]) & (ang < edges[i + 1])
    outer[i] = np.percentile(r[sel], 99.0) if sel.sum() > 30 else np.nan
# заполнить пропуски
good = ~np.isnan(outer)
outer = np.interp(np.arange(NS), np.where(good)[0], outer[good], period=NS)
# сгладить по кругу
k = 5; ext = np.concatenate([outer[-k:], outer, outer[:k]])
outer = np.convolve(ext, np.ones(2*k+1)/(2*k+1), 'same')[k:-k]

# --- УСТЬЕ = внутренний край ОБОДА на уровне рима (там пенопласт кончается, начинается кожа) ---
# ПРОФИЛЬ ЧАШИ: внутр. радиус (min-край облака) по высоте — чтобы видеть где устье широкое (верх) и дно (низ).
print("\nПРОФИЛЬ КАВЕРНЫ (внутр. край) по высоте:")
for zc in range(int(H)-20, 200, -40):
    sel = np.abs(t - zc) < 20
    if sel.sum() > 200:
        ir = np.percentile(r[sel], 12.0)
        print("  z=%3d мм  внутр.радиус≈%3.0f мм (Ø%3.0f)" % (zc, ir, 2*ir/10*10/10*10))
# устье берём в самой ВЕРХНЕЙ полосе (рим) — там отверстие самое широкое
rim = t > (H - 45)                       # верхние ~4.5 см = кромка обода
au = np.arctan2(v[rim], u[rim]); ru = r[rim]
inner = np.zeros(NS)
for i in range(NS):
    sel = (au >= edges[i]) & (au < edges[i + 1])
    inner[i] = np.percentile(ru[sel], 15.0) if sel.sum() > 12 else np.nan   # внутр. кромка обода
good = ~np.isnan(inner)
inner = np.interp(np.arange(NS), np.where(good)[0], inner[good], period=NS)
ext = np.concatenate([inner[-k:], inner, inner[:k]])
inner = np.convolve(ext, np.ones(2*k+1)/(2*k+1), 'same')[k:-k]

# центр устья и его смещение от оси
mid = (edges[:-1] + edges[1:]) / 2
ix = inner * np.cos(mid); iy = inner * np.sin(mid)
ox, oy = ix.mean(), iy.mean()
off = np.hypot(ox, oy)
print("экватор Ø(ср) = %.0f см,  устье Ø(ср) = %.0f см" % (2*outer.mean()/10, 2*inner.mean()/10))
print("смещение устья от оси = %.1f см,  направление (u,v)=(%.1f, %.1f)" % (off/10, ox/10, oy/10))
# нахлёст = обод - устье по направлению смещения и против
# найдём индекс угла смещения
adir = np.arctan2(oy, ox); i_dir = np.argmin(np.abs(((mid - adir + np.pi) % (2*np.pi)) - np.pi))
i_opp = (i_dir + NS//2) % NS
nah_far = (outer[i_dir] - inner[i_dir]) / 10   # со стороны куда смещено... проверим
nah_near = (outer[i_opp] - inner[i_opp]) / 10
print("нахлёст по стороне смещения = %.0f см, против = %.0f см" % (nah_far, nah_near))

# --- РЕНДЕР ---
W, Hh = 900, 900; pad = 70
img = Image.new('RGB', (W, Hh), 'white'); d = ImageDraw.Draw(img)
try:
    fnt = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    fb = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17)
except Exception:
    fnt = ImageFont.load_default(); fb = fnt
maxcm = 70
sc = (min(W, Hh) - 2*pad) / (2*maxcm)
cx, cy = W//2, Hh//2
def px(xcm, ycm): return (cx + xcm*sc, cy - ycm*sc)
# сетка 10см
for g in range(-70, 71, 10):
    x = cx + g*sc; d.line([(x, pad), (x, Hh-pad)], fill='#eee')
    y = cy - g*sc; d.line([(pad, y), (W-pad, y)], fill='#eee')
    if g: d.text((x-6, cy+3), str(g), font=fnt, fill='#bbb'); d.text((cx+3, y-8), str(g), font=fnt, fill='#bbb')
# облако (серое) — подвыборка
idx = np.random.default_rng(0).choice(len(u), size=min(45000, len(u)), replace=False)
for i in idx:
    x, y = px(u[i]/10, v[i]/10)
    if 0 <= x < W and 0 <= y < Hh: d.point((x, y), fill='#cccccc')
# наружный обод (бирюза)
pts = [px(outer[i]/10*np.cos(mid[i]), outer[i]/10*np.sin(mid[i])) for i in range(NS)]
d.line(pts + [pts[0]], fill='#1f6f78', width=3)
# устье (красный)
pin = [px(inner[i]/10*np.cos(mid[i]), inner[i]/10*np.sin(mid[i])) for i in range(NS)]
d.line(pin + [pin[0]], fill='#c0392b', width=3)
# центр устья
xo, yo = px(ox/10, oy/10)
d.ellipse([xo-4, yo-4, xo+4, yo+4], fill='#c0392b')
d.line([px(0, 0), (xo, yo)], fill='#c0392b', width=1)
d.text((20, 20), 'ВИД СВЕРХУ обведён по облаку off-08. бирюза=обод, красный=устье сиденья. см.', font=fb, fill='#2c3e6b')
d.text((20, 44), 'устье смещено %.0f см от оси — нахлёст-обод НЕровный (шире с одной стороны)' % (off/10), font=fnt, fill='#555')
img.save('overlay-top.png')
print('saved overlay-top.png')

# --- ЭКСПОРТ массивов для схемы drawTop (72 угла, мм, ЗАМЕР по облаку) ---
N2 = 72
ang2 = np.linspace(-np.pi, np.pi, N2, endpoint=False)
def resample(arr):
    return np.interp(ang2, mid, arr, period=2*np.pi)
o72 = resample(outer); i72 = resample(inner)
print('\n// ВИД СВЕРХУ обведён по облаку off-08, %d углов, радиус в мм (ЗАМЕР)' % N2)
print('const TOP_ANG=%d;' % N2)
print('const TOP_OUTER=[' + ','.join('%d' % round(x) for x in o72) + '];')
print('const TOP_INNER=[' + ','.join('%d' % round(x) for x in i72) + '];')
print('const TOP_OFF=[%d,%d]; // смещение центра устья от оси (мм)' % (round(ox), round(oy)))

# --- MRi для БОКА: внутр. радиус каверны на сетке высот MZ (ЗАМЕР по облаку, сглажено) ---
MZ = [0,6,14,24,36,50,66,84,104,126,150,176,204,234,266,300,334,368,402,436,470,500,528,552,564]
mri = []
for zmm in MZ:
    sel = np.abs(t - zmm) < 28
    if sel.sum() > 150:
        mri.append(np.percentile(r[sel], 12.0))
    else:
        mri.append(np.nan)
mri = np.array(mri)
# сгладить + сделать монотонно-разумным: каверна открывается ~z300, ниже = 0 (сплошной купол)
sm = mri.copy()
for _ in range(3):
    sm[1:-1] = (sm[:-2] + 2*sm[1:-1] + sm[2:]) / 4
z0 = 300
out = []
for zmm, val in zip(MZ, sm):
    if zmm < z0 or np.isnan(val):
        out.append(0)
    else:
        out.append(int(round(val)))
print('// MRi для БОКА (внутр. радиус каверны, мм, ЗАМЕР по облаку, 0=сплошной низ):')
print('const MRi=[' + ','.join('%3d' % x for x in out) + '];')
