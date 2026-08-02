"""Harici veri setleri + faz2 alan karelerini TEK egitim setinde birlestirir.

Gerekce (FTR dersi): yalniz harici setle egitmek TOGG dagiliminda yanlis-pozitif
patlamasi yapmisti; yalniz faz2 kareleriyle egitmek ezberleme olur. Dogru kurgu
ikisinin birlesimidir — cesitlilik harici setten, alan uyumu faz2'den gelir.

  Cigarette (5346) + Bottle (585)  ->  cesitlilik
  faz2 kareleri (etiketlenmis)     ->  alan uyumu (karanlik, cam ardi, bu aci)

Sinif adlari SEMA ile birebir olur: teknocan, bilgisayar, su_icme, sigara_icme

Kullanim:
  # once faz2 etiketleri Roboflow'dan YOLO formatinda indirilip su klasore konur:
  #   datasets/faz2_etiketli/{train,valid}/{images,labels}
  python scripts/veri_birlestir.py
  python scripts/veri_birlestir.py --harici-oran 0.5   # harici veriyi seyrelt
"""
import argparse
import os
import random
import shutil

# Harici setlerden hangi sinif hangi sema etiketine esleniyor
HARICI = [
    ('datasets/Cigarette', {'Cigarette': 'sigara_icme', 'smoking': 'sigara_icme'}),
    ('datasets/Bottle', {'bottle': 'su_icme'}),
    # Kendi dis-aci cekimlerimiz: az sayida ama ALAN UYUMLU (sigara 17, water 15 kutu)
    ('datasets/Self_v2', {'sigara': 'sigara_icme', 'water': 'su_icme'}),
]
FAZ2 = 'datasets/faz2_etiketli'          # Roboflow YOLO disa aktarimi
SEMA = ['teknocan', 'bilgisayar', 'su_icme', 'sigara_icme']


def sinif_adlari(kok):
    yol = os.path.join(kok, 'data.yaml')
    if not os.path.exists(yol):
        return []
    adlar, icinde = [], False
    for satir in open(yol, encoding='utf-8'):
        s = satir.rstrip()
        if s.startswith('names:'):
            icinde = True
            if '[' in s:
                return [p.strip().strip("'\"") for p in
                        s.split('[', 1)[1].rstrip(']').split(',')]
            continue
        if icinde:
            if s.startswith('- '):
                adlar.append(s[2:].strip())
            elif s and not s.startswith(' '):
                break
    return adlar


def aktar(kaynak_kok, esleme, hedef, split, oran, sayac, onek):
    """Bir setin etiketlerini sema indekslerine cevirip hedefe kopyalar."""
    adlar = sinif_adlari(kaynak_kok)
    if not adlar:
        print('  data.yaml yok:', kaynak_kok); return
    gd = os.path.join(kaynak_kok, split, 'images')
    ld = os.path.join(kaynak_kok, split, 'labels')
    if not os.path.isdir(gd):
        return
    dosyalar = sorted(os.listdir(gd))
    if oran < 1.0:
        random.seed(42)
        dosyalar = random.sample(dosyalar, max(1, int(len(dosyalar) * oran)))
    for f in dosyalar:
        e = os.path.join(ld, os.path.splitext(f)[0] + '.txt')
        if not os.path.exists(e):
            continue
        satirlar = []
        for satir in open(e):
            p = satir.split()
            if len(p) < 5:
                continue
            eski = adlar[int(p[0])] if int(p[0]) < len(adlar) else None
            yeni = esleme.get(eski) if esleme else (eski if eski in SEMA else None)
            if yeni is None:
                continue                       # ilgilenmedigimiz sinif
            satirlar.append(' '.join([str(SEMA.index(yeni))] + p[1:5]))
        if not satirlar:
            continue                           # bos etiket dosyasi uretme
        ad = '%s_%s' % (onek, f)
        shutil.copy2(os.path.join(gd, f), os.path.join(hedef, split, 'images', ad))
        with open(os.path.join(hedef, split, 'labels',
                               os.path.splitext(ad)[0] + '.txt'), 'w') as o:
            o.write('\n'.join(satirlar) + '\n')
        sayac[onek] = sayac.get(onek, 0) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='datasets/birlesik')
    ap.add_argument('--harici-oran', type=float, default=1.0,
                    help='harici setten alinacak oran (dengeleme icin)')
    a = ap.parse_args()

    if os.path.exists(a.out):
        shutil.rmtree(a.out)
    for s in ('train', 'valid'):
        for k in ('images', 'labels'):
            os.makedirs(os.path.join(a.out, s, k), exist_ok=True)

    sayac = {}
    for kok, esleme in HARICI:
        if not os.path.isdir(kok):
            print('YOK (atlandi):', kok); continue
        onek = os.path.basename(kok).lower()
        # Self_v2 kendi dis-aci cekimimiz = ALAN verisi; seyreltilmez.
        oran = 1.0 if onek.startswith('self') else a.harici_oran
        for s in ('train', 'valid'):
            aktar(kok, esleme, a.out, s, oran, sayac, onek)

    if os.path.isdir(FAZ2):
        for s in ('train', 'valid'):
            aktar(FAZ2, None, a.out, s, 1.0, sayac, 'faz2')
    else:
        print('\n!! %s YOK — faz2 etiketleri henuz hazir degil.' % FAZ2)
        print('   Roboflow YOLO disa aktarimini bu klasore koyun.')

    with open(os.path.join(a.out, 'data.yaml'), 'w', encoding='utf-8') as f:
        f.write('path: %s\ntrain: train/images\nval: valid/images\n' %
                os.path.abspath(a.out))
        f.write('nc: %d\nnames: %s\n' % (len(SEMA), SEMA))

    print('\n=== BIRLESIK SET: %s ===' % a.out)
    for k, v in sorted(sayac.items()):
        print('  %-12s %5d goruntu' % (k, v))
    for s in ('train', 'valid'):
        n = len(os.listdir(os.path.join(a.out, s, 'images')))
        print('  %-12s %5d' % (s, n))
    print('  siniflar   :', SEMA)
    print('\nEgitim: python scripts/model_egit.py')


if __name__ == '__main__':
    main()
