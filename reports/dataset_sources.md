# FTR Veri Seti Kaynak Listesi

Bu liste plate/plaka seti bulundu varsayilarak hazirlandi. Oncelik, hizli demo ve FTR icin kullanilabilir veri bulmak.

## 1. Kemer Tespiti

Oncelik: Roboflow Universe

Roboflow'da sirayla ara:

- `seatbelt detection`
- `seat belt detection`
- `driver seatbelt`
- `no seatbelt`
- `seatbelt violation`

Secerken bak:

- Siniflar `seatbelt`, `no-seatbelt` veya benzeri olmali.
- YOLOv8/YOLOv11 export olmali.
- Train/valid/test ayrimi hazir olmali.
- Goruntuler mumkunse arac ici veya trafik kamerasi acisina benzemeli.

Not: Kemer icin Kaggle tarafinda dogrudan temiz bbox seti bulmak zor. Bu modulde Roboflow en mantikli yol.

## 2. Telefon Kullanimi

Oncelik 1: Roboflow Universe

Roboflow'da sirayla ara:

- `driver phone detection`
- `phone usage driver`
- `mobile phone driver`
- `distracted driver phone`
- `cell phone driver`

Oncelik 2: AUC Distracted Driver Dataset

Link:

- https://heshameraqi.github.io/distraction_detection

Bu veri seti detection degil, davranis siniflandirma icin daha uygun. Siniflarda `Phone Right`, `Phone Left`, `Text Right`, `Text Left` gibi telefonla ilgili davranislar var.

Oncelik 3: State Farm Distracted Driver Detection

Link:

- https://www.kaggle.com/c/state-farm-distracted-driver-detection

Bu da detection degil, siniflandirma veri seti. FTR'de destek/veri cesitliligi olarak yazilabilir.

## 3. Sigara / Smoking

Oncelik: Roboflow Universe

Roboflow'da sirayla ara:

- `driver smoking`
- `smoking detection`
- `cigarette detection`
- `smoker detection`
- `smoking driver`

Secerken dikkat:

- Genel sigara seti yerine surucu/insan uzerinde sigara olan set daha iyi.
- Siniflar `cigarette`, `smoking`, `person-smoking` gibi olmali.
- Eger sadece `smoking` / `not smoking` klasorleri varsa bu object detection degil classification olur.

Yedek:

- Roboflow'da uygun set bulunamazsa sigara modulu FTR'de "veri toplama ve etiketleme ihtiyaci olan alt modul" olarak yazilabilir.
- Kisa vadede 100-200 ornek gorsel Roboflow'da manuel etiketlenip kucuk YOLO denemesi yapilabilir.

## 4. Arac Rengi

Oncelik: VCoR Vehicle Color Recognition

Link:

- https://www.kaggle.com/datasets/landrykezebou/vcor-vehicle-color-recognition-dataset

Gorev:

- Classification
- Ornek siniflar: beyaz, siyah, gri, kirmizi, mavi vb.

Kullanim:

- Once arac/plaka bolgesi tespit edilir.
- Arac crop'i uzerinden renk siniflandirma modeli calistirilir.

Roboflow alternatifi:

- `vehicle color`
- `car color classification`
- `vehicle color recognition`

## 5. Arac Tipi

Oncelik: Roboflow Universe

Roboflow'da sirayla ara:

- `vehicle type`
- `car body type`
- `vehicle classification`
- `car truck bus detection`
- `sedan suv hatchback`

Secilecek siniflar:

- `car`
- `bus`
- `truck`
- `motorcycle`
- `van`
- mumkunse `sedan`, `suv`, `hatchback`

Not:

- Stanford Cars, marka/model icin iyi ama bu proje icin fazla detayli kalir.
- FTR'de "arac tipi" deniyorsa Roboflow'daki govde tipi veya genel arac tipi seti daha mantikli.

## 6. Esneme / Yorgunluk

Oncelik: YawDD

Link:

- https://www.site.uottawa.ca/~shervin/yawning/

Bu video tabanli veri seti. Esneme icin uygun, ancak hazir YOLO klasoru gibi gelmeyebilir. Frame cikarma ve etiketleme/ayirma gerekebilir.

Alternatif:

- Roboflow'da `yawning detection`, `drowsiness detection`, `eye closed`, `driver drowsiness` ara.

## En Hizi Ne?

Bugun yetisecek en mantikli paket:

1. Plaka: zaten bulunan set.
2. Kemer: Roboflow `seatbelt detection`.
3. Telefon: Roboflow `driver phone detection`; olmazsa AUC veya State Farm classification.
4. Sigara: Roboflow `driver smoking` veya `cigarette detection`.
5. Renk: Kaggle VCoR.
6. Esneme: YawDD.

## FTR'ye Yazilacak Temiz Ifade

Proje kapsaminda veri setleri gorev bazli ayrilmistir. Plaka, kemer, telefon ve sigara gibi nesne tespiti gerektiren moduller icin YOLO formatinda etiketlenmis Roboflow Universe veri setleri tercih edilmistir. Arac rengi icin VCoR, surucu davranisi icin AUC/State Farm, esneme ve yorgunluk analizi icin YawDD veri setleri destekleyici kaynaklar olarak belirlenmistir. Veri setleri egitim, dogrulama ve test alt kumelerine ayrilarak model performansi mAP, precision, recall ve accuracy metrikleriyle degerlendirilecektir.
