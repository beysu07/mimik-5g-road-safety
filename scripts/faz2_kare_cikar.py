"""Faz2 videosundan etiketleme seti hazirlar (GT zaman damgalari yol gosterici).

Mantik: GT bir olayi "gorulebilir oldugu anda" isaretler. O anin CEVRESINDEN kare
alarak nesneyi/kisiyi farkli poz ve mesafelerde yakalariz. Ayrica olaydan uzak
"negatif" kareler de cikarilir (yanlis-pozitifi azaltmak icin).

ONEMLI: Kareler HEM 1080p HEM 240p'den cikarilir. Dusuk cozunurluk ayri bir puan
kalemi; yalniz 1080p ile egitilirse 240p zayif kalir.

Arac kutusu bulunup kirpma yapilir (kabin hedefleri kucuk; tam karede etiketlemek zor).

Kullanim:
  python scripts/faz2_kare_cikar.py --etiket teknocan
  python scripts/faz2_kare_cikar.py --etiket arka_koltuk_2 --pencere 2.0
  python scripts/faz2_kare_cikar.py --hepsi
"""
import argparse
import json
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VIDEOLAR = [('1080p', 'veri/faz2/faz2_1080p.ts'), ('240p', 'veri/faz2/faz2_240p.ts')]
VEHICLE_COCO = {2, 5, 7}


def arac_kutusu(model, frame):
    r = model.predict(frame, verbose=False, conf=0.3)[0]
    best, alan = None, 0
    for b in r.boxes:
        if int(b.cls) in VEHICLE_COCO:
            x1, y1, x2, y2 = map(int, b.xyxy[0])
            a = (x2 - x1) * (y2 - y1)
            if a > alan:
                alan, best = a, (max(0, x1), max(0, y1), x2, y2)
    return best


def kirp(frame, kutu, pay=0.08):
    """Arac kutusunu biraz genisleterek kirpar (baglam kalsin)."""
    if kutu is None:
        return frame
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = kutu
    dw, dh = int((x2 - x1) * pay), int((y2 - y1) * pay)
    return frame[max(0, y1 - dh):min(h, y2 + dh), max(0, x1 - dw):min(w, x2 + dw)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gt', default='veri/faz2/faz2_gt.json')
    ap.add_argument('--etiket', help='yalniz bu etiketin anlari (ornek: teknocan)')
    ap.add_argument('--hepsi', action='store_true', help='tum etiketler')
    ap.add_argument('--pencere', type=float, default=1.5,
                    help='olay anindan +- kac saniye')
    ap.add_argument('--adim', type=float, default=0.5, help='pencere icinde kare araligi (sn)')
    ap.add_argument('--negatif', type=int, default=12, help='olaylardan uzak kare sayisi')
    ap.add_argument('--out', default='datasets/faz2_etiketlenecek')
    ap.add_argument('--tam-kare', action='store_true', help='arac kirpma yapma')
    a = ap.parse_args()

    gt = json.load(open(a.gt, encoding='utf-8'))
    olaylar = gt['tespitler']
    if a.etiket:
        olaylar = [e for e in olaylar if e['etiket'] == a.etiket]
    elif not a.hepsi:
        print('--etiket veya --hepsi verin'); return
    if not olaylar:
        print('Bu etikette olay yok:', a.etiket); return

    from ultralytics import YOLO
    veh = YOLO(os.environ.get('W_VEHICLE', 'weights/yolo11s.pt'))

    # Cikarilacak zamanlar: her olayin cevresi + olaylardan uzak negatifler
    zamanlar = {}
    for e in olaylar:
        t0 = e['zaman_saniye']
        n = int(a.pencere / a.adim)
        for k in range(-n, n + 1):
            t = round(t0 + k * a.adim, 2)
            if t >= 0:
                zamanlar.setdefault(t, e['etiket'])

    olay_anlari = [e['zaman_saniye'] for e in gt['tespitler']]
    sure = max(olay_anlari) + 3
    adim_neg = sure / max(1, a.negatif + 1)
    for i in range(1, a.negatif + 1):
        t = round(i * adim_neg, 2)
        if all(abs(t - o) > 3.0 for o in olay_anlari):
            zamanlar.setdefault(t, 'negatif')

    os.makedirs(a.out, exist_ok=True)
    toplam = 0
    for cozunurluk, yol in VIDEOLAR:
        if not os.path.exists(yol):
            print('YOK:', yol); continue
        cap = cv2.VideoCapture(yol)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        for t in sorted(zamanlar):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
            ok, fr = cap.read()
            if not ok:
                continue
            etiket = zamanlar[t]
            kutu = arac_kutusu(veh, fr)
            if kutu is None:
                # Arac kadrajda degil: olay penceresinin disina tasmisiz. Kare
                # degerli (negatif ornek) ama olay adiyla kaydedilirse etiketlemede
                # yanlis yonlendirir -> negatif olarak isaretle.
                etiket = 'negatif'
            elif not a.tam_kare:
                fr = kirp(fr, kutu)
            if fr is None or fr.size == 0 or min(fr.shape[:2]) < 32:
                continue
            ad = '%s_%s_t%07.2f.jpg' % (etiket, cozunurluk, t)
            cv2.imwrite(os.path.join(a.out, ad), fr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            toplam += 1
        cap.release()
        print('%s bitti' % cozunurluk)

    print()
    print('%d kare -> %s' % (toplam, a.out))
    print('Dosya adlari "<etiket>_<cozunurluk>_t<saniye>.jpg" bicimindedir;')
    print('Roboflow\'a yukleyip kutu cizmek yeterli (sinif adlari sema ile ayni olmali).')


if __name__ == '__main__':
    main()
