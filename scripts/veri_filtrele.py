"""Veri setlerini HEDEF ALAN kriterlerine gore suzer.

Faz2 olcumleri (docs/veri-alan-analizi.md):
  - kabin parlakligi  : medyan 20/255  (cok karanlik)
  - surucu/kisi kutusu: medyan 91x90 px (1080p), 24x26 px (240p)

Aydinlik ve yakin-cekim goruntulerle egitmenin ise yaramadigini olctuk
(phone_merged'de 2123 kemer ornegi var, faz2'de hic atesleimiyor). Bu script,
elimizdeki setlerin NE KADARININ bizim alana uydugunu sayisal olarak gosterir.

Kullanim:
  python scripts/veri_filtrele.py datasets/phone_merged
  python scripts/veri_filtrele.py datasets/phone_merged --kopyala datasets/suzulmus
"""
import argparse
import os
import shutil
import sys

import cv2
import numpy as np

# Hedef alan kriterleri
PARLAKLIK_UST = 60      # 0-255; ustu "aydinlik" sayilir (faz2 medyani 20)
KUTU_UST = 150          # px; uzeri "yakin cekim" sayilir (faz2 medyani 91)


def yaml_sinif_adlari(kok):
    yol = os.path.join(kok, 'data.yaml')
    if not os.path.exists(yol):
        return []
    adlar, icinde = [], False
    for satir in open(yol, encoding='utf-8'):
        s = satir.rstrip()
        if s.startswith('names:'):
            icinde = True
            if '[' in s:                       # tek satir: names: ['a','b']
                return [p.strip().strip("'\"") for p in
                        s.split('[', 1)[1].rstrip(']').split(',')]
            continue
        if icinde:
            if s.startswith('- '):
                adlar.append(s[2:].strip())
            elif s and not s.startswith(' '):
                break
    return adlar


def olc(goruntu, kutular):
    """Her kutu icin (uzun_kenar_px, ortalama_parlaklik) doner."""
    h, w = goruntu.shape[:2]
    gri = cv2.cvtColor(goruntu, cv2.COLOR_BGR2GRAY)
    out = []
    for cx, cy, bw, bh in kutular:
        x1 = max(0, int((cx - bw / 2) * w)); x2 = min(w, int((cx + bw / 2) * w))
        y1 = max(0, int((cy - bh / 2) * h)); y2 = min(h, int((cy + bh / 2) * h))
        if x2 <= x1 or y2 <= y1:
            continue
        out.append((max(x2 - x1, y2 - y1), float(gri[y1:y2, x1:x2].mean())))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kok', help='veri seti klasoru (data.yaml iceren)')
    ap.add_argument('--sinif', help='yalniz bu sinifi olc (ornek: seatbelt)')
    ap.add_argument('--kopyala', help='kriterlere uyan goruntuleri buraya kopyala')
    ap.add_argument('--limit', type=int, default=4000)
    a = ap.parse_args()

    adlar = yaml_sinif_adlari(a.kok)
    hedef_id = None
    if a.sinif:
        if a.sinif not in adlar:
            print('Sinif yok. Mevcut:', adlar); return
        hedef_id = adlar.index(a.sinif)

    goruntuler = []
    for split in ('train', 'valid', 'test'):
        d = os.path.join(a.kok, split, 'images')
        if os.path.isdir(d):
            goruntuler += [os.path.join(d, f) for f in os.listdir(d)
                           if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    goruntuler = goruntuler[:a.limit]
    if not goruntuler:
        print('Goruntu bulunamadi:', a.kok); return

    boyutlar, parlakliklar, uyan = [], [], []
    for g in goruntuler:
        etiket = g.replace(os.sep + 'images' + os.sep, os.sep + 'labels' + os.sep)
        etiket = os.path.splitext(etiket)[0] + '.txt'
        if not os.path.exists(etiket):
            continue
        kutular = []
        for satir in open(etiket):
            p = satir.split()
            if len(p) < 5:
                continue
            if hedef_id is not None and int(p[0]) != hedef_id:
                continue
            kutular.append(tuple(float(x) for x in p[1:5]))
        if not kutular:
            continue
        im = cv2.imread(g)
        if im is None:
            continue
        for kenar, parlaklik in olc(im, kutular):
            boyutlar.append(kenar); parlakliklar.append(parlaklik)
            if parlaklik <= PARLAKLIK_UST and kenar <= KUTU_UST:
                uyan.append(g)

    if not boyutlar:
        print('Olculebilir kutu yok.'); return

    b, p = np.array(boyutlar), np.array(parlakliklar)
    print('=' * 68)
    print('SET: %s   sinif: %s   olculen kutu: %d' % (a.kok, a.sinif or 'hepsi', len(b)))
    print('=' * 68)
    print('  kutu uzun kenari (px): medyan %5.0f   [%.0f - %.0f]' % (np.median(b), b.min(), b.max()))
    print('  parlaklik (0-255)    : medyan %5.0f   [%.0f - %.0f]' % (np.median(p), p.min(), p.max()))
    print()
    print('  HEDEF ALAN (faz2)    : kutu ~91 px, parlaklik ~20')
    print('  KRITER               : kutu <= %d px  VE  parlaklik <= %d' % (KUTU_UST, PARLAKLIK_UST))
    print()
    print('  yeterince karanlik   : %5d / %d  (%%%.0f)' % (
        (p <= PARLAKLIK_UST).sum(), len(p), 100 * (p <= PARLAKLIK_UST).mean()))
    print('  yeterince kucuk      : %5d / %d  (%%%.0f)' % (
        (b <= KUTU_UST).sum(), len(b), 100 * (b <= KUTU_UST).mean()))
    print('  IKISI BIRDEN (uygun) : %5d / %d  (%%%.0f)' % (
        len(uyan), len(b), 100 * len(uyan) / len(b)))

    if a.kopyala and uyan:
        os.makedirs(a.kopyala, exist_ok=True)
        for g in set(uyan):
            shutil.copy2(g, os.path.join(a.kopyala, os.path.basename(g)))
        print('\n  %d benzersiz goruntu -> %s' % (len(set(uyan)), a.kopyala))


if __name__ == '__main__':
    main()
