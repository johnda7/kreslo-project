#!/usr/bin/env python3
# ОВЕРЛЕЙ СБОКУ: реальное облако off-08 (u,t) + АСИММЕТРИЧНЫЙ контур из index.html
# (левый край MRL, правый MRR, каверна MRi со смещением seatOff). Должен лежать 1:1 на flatM.
import trimesh, numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- массивы 1:1 из index.html (мм) ---
MZ  = [0,6,14,24,36,50,66,84,104,126,150,176,204,234,266,300,334,368,402,436,470,500,528,552,564]
MRL = [69,106,143,191,231,270,306,339,373,407,443,476,507,536,563,581,592,595,591,579,567,555,544,538,533]
MRR = [72,111,150,196,235,274,310,343,377,412,445,476,505,531,555,578,595,594,575,544,506,466,434,422,413]
MRi = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,205,229,270,310,344,373,392,400,397,391]
seatOff = 39  # мм к переду
MZ=np.array(MZ,float); MRL=np.array(MRL,float); MRR=np.array(MRR,float); MRi=np.array(MRi,float)

# --- скан off-08 (та же калибровка что в overlay_check/overlay_top) ---
m = trimesh.load('models/ufo-tripo-off08.glb', force='mesh')
V = np.asarray(m.vertices, float); c=V.mean(0); X=V-c
w,vec=np.linalg.eigh(X.T@X); axis=vec[:,0]; e1=vec[:,1]; e2=vec[:,2]
t=X@axis; u=X@e1; v=X@e2; r=np.hypot(u,v)
f=665.0/np.percentile(r,99.9); t=t*f; u=u*f; v=v*f; r=r*f
lo=t<np.percentile(t,8); hi=t>np.percentile(t,92)
if r[lo].mean()>r[hi].mean(): t=-t
t=t-t.min()

# --- РЕНДЕР ---
W,H=1000,760; pad=70
img=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(img)
try:
    fnt=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    fb=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',18)
except Exception:
    fnt=ImageFont.load_default(); fb=fnt
maxR_cm=70; maxH_cm=70
sc=min((W/2-pad)/maxR_cm,(H-2*pad)/maxH_cm); cx=W//2; baseY=H-pad
def px(rcm,zcm): return (cx+rcm*sc, baseY-zcm*sc)
for g in range(-70,71,10):
    x=cx+g*sc; d.line([(x,pad),(x,baseY)],fill='#eee'); d.text((x-6,baseY+4),str(g),font=fnt,fill='#aaa')
for g in range(0,71,10):
    y=baseY-g*sc; d.line([(pad,y),(W-pad,y)],fill='#eee'); d.text((cx-maxR_cm*sc-24,y-8),str(g),font=fnt,fill='#aaa')
idx=np.random.default_rng(0).choice(len(u),size=min(40000,len(u)),replace=False)
for i in idx:
    x,y=px(u[i]/10,t[i]/10)
    if 0<=x<W and 0<=y<H: d.point((x,y),fill='#c9c9c9')
# контур: левый край (−MRL) и правый (+MRR)
ptsL=[px(-MRL[i]/10,MZ[i]/10) for i in range(len(MZ))]
ptsR=[px( MRR[i]/10,MZ[i]/10) for i in range(len(MZ))]
d.line(ptsL,fill='#1f6f78',width=3); d.line(ptsR,fill='#1f6f78',width=3)
d.line([ptsL[0],ptsR[0]],fill='#1f6f78',width=3)  # замкнуть низ
# каверна (красный) смещена влево на seatOff
for s in (1,-1):
    pts=[px((-seatOff+s*MRi[i])/10,MZ[i]/10) for i in range(len(MZ)) if MRi[i]>0]
    if len(pts)>1: d.line(pts,fill='#c0392b',width=2)
d.text((pad,20),'ОВЕРЛЕЙ СБОКУ: серое = реальный скан off-08 · бирюза = контур реза (лев/прав край облака) · красный = каверна',font=fb,fill='#2c3e6b')
d.text((pad,44),'контур обведён по краю облака, устье (кончается пенопласт, без кожи) Ø80 смещено ~4 см к переду (замер). см.',font=fnt,fill='#555')
img.save('overlay-fit.png')
print('saved overlay-fit.png  Hs(cm)=%.1f'%(t.max()/10))
