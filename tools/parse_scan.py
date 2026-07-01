#!/usr/bin/env python3
"""
Разбор LiDAR-скана чаши/кресла (.usdz) → профиль вдоль оси симметрии через PCA.
Использование: python parse_scan.py <файл.usdz>

Метод (отработан на чашке и кресле):
- читаем меш из usdz через usd-core
- чаша сканируется под наклоном → истинная ось вращения через PCA
  (ось = собственный вектор ковариации с наименьшим собственным значением)
- профиль r(z) вдоль оси: 90-й перцентиль радиуса по уровням высоты = внешний контур
"""
import sys, numpy as np

def load_points(path):
    from pxr import Usd, UsdGeom, Gf
    stage = Usd.Stage.Open(path)
    pts = []
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            m = UsdGeom.Mesh(prim)
            p = m.GetPointsAttr().Get()
            if not p:
                continue
            xf = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
            for v in p:
                w = xf.Transform(Gf.Vec3d(v[0], v[1], v[2]))
                pts.append([w[0], w[1], w[2]])
    return np.array(pts)

def main(path):
    pts = load_points(path)
    print(f"Точек: {len(pts)}")
    print(f"Сырые габариты (см): " +
          " ".join(f"{ax}={np.ptp(pts[:,i])*100:.0f}" for i, ax in enumerate("XYZ")))

    c = pts.mean(0); P = pts - c
    ev, evec = np.linalg.eigh(np.cov(P.T))
    print(f"Собственные значения: {ev}")

    # для тела вращения ось = направление наименьшей дисперсии
    axis = evec[:, 0] / np.linalg.norm(evec[:, 0])
    t = P @ axis
    rad = P - np.outer(t, axis)
    r = np.linalg.norm(rad, axis=1)

    t0 = t - t.min()
    nb = 40
    bins = np.linspace(0, t0.max(), nb)
    pz, pr = [], []
    for i in range(nb - 1):
        m = (t0 >= bins[i]) & (t0 < bins[i+1])
        if m.sum() > 5:
            pz.append((bins[i] + bins[i+1]) / 2 * 100)
            pr.append(np.percentile(r[m], 90) * 100)
    pz, pr = np.array(pz), np.array(pr)
    if pr[0] > pr[-1]:
        pz = pz.max() - pz[::-1]; pr = pr[::-1]

    print(f"\nПрофиль: высота {pz.max():.0f} см, макс Ø {2*pr.max():.0f}, дно Ø {2*pr.min():.0f}")
    print("высота_см  диаметр_см")
    for z, rr in zip(pz, pr):
        print(f"{z:6.0f}  {2*rr:.0f}")

    # проекции на все 3 главные оси = реальные габариты (для яйцевидных)
    proj = P @ evec
    print("\nРеальные габариты по гл.осям (см): " +
          " ".join(f"{np.ptp(proj[:,i])*100:.0f}" for i in range(3)))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/scan-kreslo.usdz")
