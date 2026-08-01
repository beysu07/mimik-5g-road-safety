"""SAGLAMLIK (genelleme) TESTI — ayarlarimiz tek videoya mi ezberlendi?

Elimizde tek etiketli video (faz2) var. Final gunu videosu farkli isik/aci/mesafe
olacak. Yeni etiketli veri olmadan genellemeyi olcmenin yolu: ayni videoyu YAPAY
olarak bozup skorun ne kadar dustugune bakmak. Sahneye ezberlenmis bir ayar kucuk
bozulmada coker; saglam bir ayar kademeli duser.

Kullanim:
  python scripts/saglamlik_testi.py [--video veri/faz2/faz2_1080p.ts] [--hizli]
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.faz2_degerlendir import eslestir, yukle          # noqa: E402


# ----------------------------------------------------------------- bozulmalar
def _parlaklik(kat, ofset):
    return lambda f: cv2.convertScaleAbs(f, alpha=kat, beta=ofset)


def _bulanik(k):
    return lambda f: cv2.GaussianBlur(f, (k, k), 0)


def _gurultu(sigma):
    def uygula(f):
        g = np.random.normal(0, sigma, f.shape).astype(np.int16)
        return np.clip(f.astype(np.int16) + g, 0, 255).astype(np.uint8)
    return uygula


def _olcek(oran):
    """Araci uzaklastirir: kucult, sonra ayni cerceveye geri koy (detay kaybi kalir)."""
    def uygula(f):
        h, w = f.shape[:2]
        k = cv2.resize(f, (max(2, int(w * oran)), max(2, int(h * oran))))
        return cv2.resize(k, (w, h), interpolation=cv2.INTER_CUBIC)
    return uygula


def _ayna(f):
    return cv2.flip(f, 1)


BOZULMALAR = [
    ('temiz (referans)', None),
    ('karanlik  (x0.6)', _parlaklik(0.6, -10)),
    ('parlak    (x1.5)', _parlaklik(1.5, 20)),
    ('bulanik   (k=7)', _bulanik(7)),
    ('gurultu   (s=12)', _gurultu(12)),
    ('uzak      (x0.5)', _olcek(0.5)),
    ('ayna (sol-sag)', _ayna),
]


def puanla(gt, pred, tol=5.0):
    tp, fn, fp = eslestir(gt.get('tespitler', []), pred.get('tespitler', []), tol)
    P = len(tp) / len(pred['tespitler']) if pred.get('tespitler') else 0.0
    R = len(tp) / len(gt['tespitler']) if gt.get('tespitler') else 0.0
    F = 2 * P * R / (P + R) if (P + R) else 0.0
    ga, pa = gt.get('arac_bilgisi', {}), pred.get('arac_bilgisi', {})
    arac = sum(ga.get(k) == pa.get(k) for k in ('tip', 'plaka', 'renk'))
    return {'tp': len(tp), 'fp': len(fp), 'P': P, 'R': R, 'F1': F, 'arac': arac,
            'tespit': len(pred.get('tespitler', []))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', default='veri/faz2/faz2_1080p.ts')
    ap.add_argument('--gt', default='veri/faz2/faz2_gt.json')
    ap.add_argument('--out', default='reports/saglamlik.json')
    ap.add_argument('--hizli', action='store_true', help='yalniz 4 bozulma calistir')
    a = ap.parse_args()

    from src.predict import Pipeline
    gt = yukle(a.gt)
    pipe = Pipeline()                       # modeller bir kez yuklenir
    testler = BOZULMALAR[:4] if a.hizli else BOZULMALAR

    sonuclar = []
    for ad, fn in testler:
        r = pipe.run(a.video, frame_hook=fn)
        s = puanla(gt, r)
        s['bozulma'] = ad
        sonuclar.append(s)
        print('%-18s tespit=%2d  TP=%2d FP=%2d  P=%.2f R=%.2f F1=%.2f  arac=%d/3'
              % (ad, s['tespit'], s['tp'], s['fp'], s['P'], s['R'], s['F1'], s['arac']))

    print()
    print('=' * 74)
    print('%-18s %8s %8s %8s %8s' % ('BOZULMA', 'F1', 'F1 kayip', 'arac', 'tespit'))
    print('=' * 74)
    ref = sonuclar[0]['F1'] or 1e-9
    for s in sonuclar:
        kayip = 100 * (1 - s['F1'] / ref) if ref else 0
        print('%-18s %8.2f %7.0f%% %8d %8d' % (s['bozulma'], s['F1'], kayip,
                                               s['arac'], s['tespit']))
    print('=' * 74)
    print('Okuma: F1 kaybi kucukse ayar SAGLAM; kucuk bozulmada cokuyorsa sahneye')
    print('ezberlenmis demektir. arac (tip/plaka/renk) 3/3 kalmali.')

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({'video': a.video, 'sonuclar': sonuclar},
              open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('JSON ->', a.out)


if __name__ == '__main__':
    main()
