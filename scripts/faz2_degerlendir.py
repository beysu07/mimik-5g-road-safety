"""results.json'i ground truth'a karsi puanlar (hakem degerlendirmesinin taklidi).

Hakemin tam metrigi bilinmiyor; makul ve savunulabilir bir olcum kullaniyoruz:
  - arac_bilgisi: tip/plaka/renk birebir esitlik
  - tespitler   : ayni etiket + zaman toleransi icinde birebir eslestirme (greedy),
                  eslesmeyen GT = kacirma (FN), eslesmeyen tahmin = yanlis alarm (FP)
GT "olaylar gorulebilir olduklari anda" isaretlendigi icin tolerans onemlidir;
birden fazla tolerans degeri raporlanir.

Kullanim:
  python scripts/faz2_degerlendir.py <results.json> [--gt veri/faz2/faz2_gt.json]
"""
import argparse
import collections
import json


def yukle(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def eslestir(gt_list, pred_list, tolerans):
    """Ayni etiketli olaylari zaman yakinligina gore greedy eslestirir."""
    kalan = list(pred_list)
    tp, fn = [], []
    for g in sorted(gt_list, key=lambda x: x['zaman_saniye']):
        adaylar = [(abs(p['zaman_saniye'] - g['zaman_saniye']), i, p)
                   for i, p in enumerate(kalan)
                   if p['etiket'] == g['etiket'] and p['kategori'] == g['kategori']
                   and abs(p['zaman_saniye'] - g['zaman_saniye']) <= tolerans]
        if adaylar:
            adaylar.sort(key=lambda x: x[0])
            _, i, p = adaylar[0]
            tp.append((g, p))
            kalan.pop(i)
        else:
            fn.append(g)
    return tp, fn, kalan          # kalan = FP


def rapor(gt, pred, toleranslar=(2.0, 5.0, 10.0)):
    print('=' * 78)
    print('ARAC BILGISI')
    print('=' * 78)
    ga, pa = gt.get('arac_bilgisi', {}), pred.get('arac_bilgisi', {})
    arac_puan = 0
    for alan in ('tip', 'plaka', 'renk'):
        g, p = ga.get(alan), pa.get(alan)
        ok = (g == p)
        arac_puan += ok
        print('  %-8s GT=%-12s TAHMIN=%-12s %s' % (alan, g, p, 'DOGRU' if ok else 'YANLIS'))
    print('  -> %d/3 dogru' % arac_puan)

    gts, prs = gt.get('tespitler', []), pred.get('tespitler', [])
    print()
    print('=' * 78)
    print('TESPITLER  (GT: %d olay, TAHMIN: %d olay)' % (len(gts), len(prs)))
    print('=' * 78)

    for tol in toleranslar:
        tp, fn, fp = eslestir(gts, prs, tol)
        P = len(tp) / len(prs) if prs else 0.0
        R = len(tp) / len(gts) if gts else 0.0
        F = 2 * P * R / (P + R) if (P + R) else 0.0
        print('  tolerans +-%4.1f sn : TP=%2d  FN=%2d  FP=%2d  |  P=%.2f  R=%.2f  F1=%.2f'
              % (tol, len(tp), len(fn), len(fp), P, R, F))

    # Etiket bazli kirilim (orta tolerans)
    tol = toleranslar[len(toleranslar) // 2]
    tp, fn, fp = eslestir(gts, prs, tol)
    gt_say = collections.Counter(e['etiket'] for e in gts)
    tp_say = collections.Counter(g['etiket'] for g, _ in tp)
    fp_say = collections.Counter(e['etiket'] for e in fp)

    print()
    print('  ETIKET BAZLI (tolerans +-%.0f sn)' % tol)
    print('  %-24s %4s %4s %4s  %s' % ('etiket', 'GT', 'TP', 'FP', 'durum'))
    print('  ' + '-' * 62)
    for et, n in gt_say.most_common():
        t = tp_say.get(et, 0)
        durum = 'TAM' if t == n else ('KISMI' if t else 'HIC YOK')
        print('  %-24s %4d %4d %4d  %s' % (et, n, t, fp_say.get(et, 0), durum))
    ekstra = set(fp_say) - set(gt_say)
    for et in sorted(ekstra):
        print('  %-24s %4d %4d %4d  %s' % (et, 0, 0, fp_say[et], 'FAZLADAN'))

    print()
    print('  Uretilen etiket cesidi : %d' % len(set(e['etiket'] for e in prs)))
    print('  GT etiket cesidi       : %d' % len(gt_say))
    return {'arac': arac_puan, 'tp': len(tp), 'fn': len(fn), 'fp': len(fp)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--gt', default='veri/faz2/faz2_gt.json')
    a = ap.parse_args()
    rapor(yukle(a.gt), yukle(a.results))


if __name__ == '__main__':
    main()
