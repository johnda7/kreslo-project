#!/usr/bin/env python3
# Оверлей: сырые точки скана off-08 (сбоку) + мой контур из index.html. Проверка "сходится ли".
import trimesh, numpy as np, base64, io
from PIL import Image, ImageDraw, ImageFont

# --- мой контур из index.html (мм) ---
MZ =[ 12, 29, 52, 75, 93,116,133,156,174,197,220,237,261,278,301,319,342,365,382,405,428,451,463,486,510,527,550,567]
MR =[179,253,307,352,393,427,457,488,515,537,554,571,585,598,613,625,637,650,661,665,650,628,604,585,552,516,483,437]
MRi=[  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,130,175,230,270,315,360,395,430,455,475,488,498,495,475,435,380]
MZ=np.array(MZ,float); MR=np.array(MR,float); MRi=np.array(MRi,float)

# --- скан ---
m = trimesh.load('models/ufo-tripo-off08.glb', force='mesh')
V = np.asarray(m.vertices, float)
c = V.mean(0); X = V-c
cov = X.T@X
w,vec = np.linalg.eigh(cov)          # ось симметрии = наименьшее с.з. (тонкое направление линзы)
axis = vec[:,0]; e1=vec[:,1]; e2=vec[:,2]
t = X@axis; u = X@e1; v = X@e2
r = np.hypot(u,v)
f = 665.0/np.percentile(r,99.9)      # калибровка: макс.радиус -> 665мм (Ø133)
t=t*f; u=u*f; v=v*f; r=r*f
# ориентация: узкий конец (купол-полюс, малый r) — ВНИЗ, широкий рим — вверх
lo=t<np.percentile(t,8); hi=t>np.percentile(t,92)
if r[lo].mean() > r[hi].mean():      # низ шире верха -> перевернуть
    t=-t; print('(перевернул ось: узкий купол вниз)')
t = t - t.min()
Hs = t.max()

# --- ЧИСЛОВАЯ проверка: на каждой высоте max|u| скана vs мой MR ---
print("высота(см)  скан R(см)  мой R(см)  разн(см)")
for zc in range(5, int(Hs//10)*10+1, 5):
    zmm=zc*10
    sel=np.abs(t-zmm)<25
    if sel.sum()<50: continue
    scanR=np.percentile(np.abs(u[sel]),99.5)/10
    myR=np.interp(zmm,MZ,MR)/10
    print(f"  {zc:3d}       {scanR:6.1f}     {myR:6.1f}    {scanR-myR:+5.1f}")

# --- РЕНДЕР оверлея ---
W,Hh=1000,760; pad=70
img=Image.new('RGB',(W,Hh),'white'); d=ImageDraw.Draw(img)
try: fnt=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15); fb=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',18)
except: fnt=ImageFont.load_default(); fb=fnt
maxR_cm=70; maxH_cm=70
sc=min((W/2-pad)/maxR_cm,(Hh-2*pad)/maxH_cm)
cx=W//2; baseY=Hh-pad
def px(rcm,zcm): return (cx+rcm*sc, baseY-zcm*sc)
# сетка 10см
for g in range(-70,71,10):
    x=cx+g*sc; d.line([(x,pad),(x,baseY)],fill='#eee'); d.text((x-6,baseY+4),str(g),font=fnt,fill='#aaa')
for g in range(0,71,10):
    y=baseY-g*sc; d.line([(pad,y),(W-pad,y)],fill='#eee'); d.text((cx-maxR_cm*sc-24,y-8),str(g),font=fnt,fill='#aaa')
# точки скана (серые) — подвыборка
idx=np.random.default_rng(0).choice(len(u),size=min(40000,len(u)),replace=False)
for i in idx:
    x,y=px(u[i]/10,t[i]/10)
    if 0<=x<W and 0<=y<Hh: d.point((x,y),fill='#c9c9c9')
# мой контур (бирюза, ±MR)
for s in (1,-1):
    pts=[px(s*MR[i]/10,MZ[i]/10) for i in range(len(MZ))]
    d.line(pts,fill='#1f6f78',width=3)
# каверна (красный, ±MRi где >0)
for s in (1,-1):
    pts=[px(s*MRi[i]/10,MZ[i]/10) for i in range(len(MZ)) if MRi[i]>0]
    if len(pts)>1: d.line(pts,fill='#c0392b',width=2)
d.text((pad,20),'ОВЕРЛЕЙ: серые точки = реальный скан off-08 (сбоку) · бирюза = мой контур · красный = каверна сиденья',font=fb,fill='#2c3e6b')
d.text((pad,44),'если бирюза обнимает серое облако — контур сходится. масштаб — сантиметры.',font=fnt,fill='#555')
img.save('overlay-check.png')
b64=base64.b64encode(open('overlay-check.png','rb').read()).decode()
open('overlay-check.html','w').write(f'<!doctype html><meta charset=utf-8><title>Оверлей скан vs контур</title><body style="margin:0;background:#eceae4;font-family:Arial"><div style="max-width:1000px;margin:20px auto"><h2 style="color:#2c3e6b">Проверка: скан off-08 сбоку vs мой контур нарезки</h2><img src="data:image/png;base64,{b64}" style="width:100%;border:1px solid #ccc;border-radius:8px"></div>')
print('\nHs(cm)=%.1f  saved overlay-check.png + overlay-check.html'%(Hs/10))
