"""Birlesik veri setiyle kabin nesnesi modelini egitir (AGIR AUGMENTASYON).

Kucuk alan verisiyle (faz2 kareleri) ezberlemeyi onlemek icin augmentasyon
bilincli olarak agirdir: parlaklik/HSV, olcek, doner, mozaik. Amac modelin
"o otoparkin isigini" degil nesnenin kendisini ogrenmesi.

Egitim sonrasi KABUL KRITERI (docs/ezberleme-denetimi.md):
  - faz2'de F1 artmali
  - saglamlik testinde kayip %25'i asmamali
Asarsa model KULLANILMAZ.

Kullanim:
  python scripts/veri_birlestir.py && python scripts/model_egit.py
"""
import argparse
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--veri', default='datasets/birlesik/data.yaml')
    ap.add_argument('--epoch', type=int, default=80)
    ap.add_argument('--imgsz', type=int, default=960)
    ap.add_argument('--batch', type=int, default=8)
    ap.add_argument('--ad', default='kabin_nesneleri')
    a = ap.parse_args()

    if not os.path.exists(a.veri):
        print('Veri yok:', a.veri, '\nOnce: python scripts/veri_birlestir.py')
        return

    from ultralytics import YOLO
    model = YOLO('yolo11s.pt')          # COCO on-egitimli govde
    model.train(
        data=a.veri, epochs=a.epoch, imgsz=a.imgsz, batch=a.batch,
        name=a.ad, patience=20, seed=42,
        # --- ezberlemeye karsi agir augmentasyon ---
        hsv_h=0.02, hsv_s=0.7, hsv_v=0.6,   # renk/parlaklik: karanlik-aydinlik farki
        degrees=8.0, translate=0.15, scale=0.6, shear=2.0,
        perspective=0.0005, fliplr=0.5, mosaic=0.8,
        # mixup/erasing kapali: ultralytics 8.4'te augment hatasi veriyordu
    )
    print('\nAgirlik: runs/detect/%s/weights/best.pt' % a.ad)
    print('Sonraki adim:')
    print('  1) src/predict.py icinde W_KABIN olarak bagla')
    print('  2) python scripts/faz2_degerlendir.py <cikti.json>')
    print('  3) python scripts/saglamlik_testi.py     <-- kayip %25 ustuyse KULLANMA')


if __name__ == '__main__':
    main()
