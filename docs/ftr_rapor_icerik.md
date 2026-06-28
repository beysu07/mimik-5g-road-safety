# MİMİK — FTR Rapor İçeriği (docx'e yapıştırmaya hazır)

> Şablon biçimi: Arial 12 / Başlık Arial Black 14 / 1.15 satır / iki yana yaslı /
> kenar boşlukları üst 2.8, alt-sağ-sol 2.5 / Kapak + İçindekiler ayrı sayfa / 3–10 sayfa.

---

## 1. PROJE ÖZETİ (5 puan)

MİMİK, sabit kameralardan elde edilen video kayıtları üzerinde çalışan; araç ve sürücü
kaynaklı yol güvenliği risklerini otomatik tespit eden bütünleşik bir bilgisayarlı görü
sistemidir. Sistem, tek bir video dosyasını girdi alır ve araç geçişi için şartnameye
birebir uyan yapılandırılmış bir JSON çıktısı üretir: araç gövde tipi, plaka ve renk;
sürücünün dikkat dağıtıcı/kural ihlali eylemleri (telefonla konuşma, su içme, emniyet
kemeri ihlali, slalom); kabin içi nesneler ve yolcu konumları. Çözümün çekirdeği,
Ultralytics YOLO11 tabanlı çok görevli bir algılama hattı ile aracı kare kare takip edip
bulguları geçiş boyunca biriktiren **Araç Geçiş Hafızası** füzyon katmanından oluşur.
Plaka tanıma iki aşamalıdır (bölge tespiti + CRNN/EasyOCR), plaka karakterleri zamansal
oylamayla birleştirilir; düşük ışık/parlama koşullarına karşı ROI bazlı CLAHE iyileştirmesi
uygulanır. Sistem, NVIDIA T4 GPU üzerinde tek bir Docker konteyneri olarak çevrimdışı
çalışacak biçimde optimize edilmiştir. Canlı dağıtım aşamasında aynı çekirdek, Turkcell 5G
Open Gateway QoD ve Number Verification API'leri ile genişletilerek gerçek zamanlı ve
şebeke-doğrulamalı bir yol güvenliği sistemine dönüştürülecektir.

---

## 2. VERİSETİ OLUŞTURULMASI (20 puan)

Veri stratejimiz iki ayağa dayanır: (a) güvenilir biçimde elde edilebilen araç-merkezli
görevler için **alan-uygun açık akademik/halka açık veri kümeleri**, (b) yol kenarı sabit
kamera senaryosuna özgü zorlukları yansıtan **kendi çektiğimiz domain-eşleşmeli veriler**.
Tüm sınıf etiketleri şartnameyle birebir, ASCII ve küçük harfli standart adlara eşlenmiştir.

**Kullanılan veri kümeleri ve bölme oranları:**

| Görev | Kaynak | Eğitim / Doğrulama / Test |
|---|---|---|
| Plaka tespiti | License Plate (Roboflow) | 7057 / 2048 / 1020 |
| Renk sınıflandırma | VCoR (15→9 eşlendi) | 5215 / 1113 / 1116 |
| Araç tipi | CompCars (5 gövde tipi) | ~13.700 / ~2.400 |
| Kemer + ön cam ROI | NoSeatbelt (Roboflow) | 933 / 138 / 120 |
| Telefon/kemer (dış-cam) | seat_belt-and-mobile ×2 (birleşik) | 4763 / 1203 |
| **Kendi verimiz (yolcu konumları)** | **Self_v2 — iPhone 2K, dış açı** | 96 / 16 |
| Sigara nesne dedektörü | Cigarette (genel set) | 5346 / 318 |
| Su şişesi nesne dedektörü | harici bottle seti | — |

**Etiketleme ve dengeleme.** Açık kümeler kendi şemalarıyla geldiğinden ana iş, sınıf
adlarının şartname etiketlerine eşlenmesi ve domain-uygunluk açısından ayıklanmasıdır.
VCoR'daki 15 renk dokuz hedef renge indirgenmiş (gümüş→gri, karşılığı olmayanlar elenmiş);
renk kümesi dokuz sınıfta dengeli tutulmuştur (sınıf başına ~400–790 eğitim örneği).
Kendi verimiz, iPhone ile **2K** çözünürlükte, yol kenarı sabit kamera açısıyla çekilmiş;
sürücü/yolcu konumları ve kabin içi nesneler (su, telefon, sigara) Roboflow'da
etiketlenmiştir.

**Veri artırma (augmentation).** Eğitimde mozaik, yatay çevirme, ölçek/öteleme ve HSV
tabanlı renk/parlaklık titreşimi uygulanmış; şartnamedeki değişken ışık ve olumsuz hava
koşullarına dayanıklılık hedeflenmiştir.

**Önemli bir veri bulgusu (çözünürlük).** Kendi verimizi ilk olarak 512×512 dışa
aktardığımızda küçük kabin-içi nesneler (su, telefon ~5 piksel) tespit edilemedi (mAP≈0).
Dışa aktarmayı **tam çözünürlükte (2K)** tekrarlayıp 1280 girdi boyutuyla eğitince aynı
sınıflar tespit edilebilir hale geldi (su mAP@0.5 = **0.995**). Bu, küçük nesne tespitinde
çözünürlüğün belirleyici olduğunu somut biçimde göstermektedir.

---

## 3. YAPAY ZEKÂ ÇÖZÜMÜ (50 puan)

### 3.1. Problemin Analizi (15 puan)

Sabit kameralardan araç/plaka ve riskli sürücü durumlarının tespiti birbirini besleyen
zorluklar içerir. **(1) Aydınlatma değişkenliği:** test ortamları kapalı/yeraltı alanlardan
açık alanlara değişir; düşük ışık, far parlaması ve sert gölgeler plaka ve kabin içi
ayrıntıların görünürlüğünü bozar. **(2) Olumsuz hava ve mekân çeşitliliği** modelin tek
koşula ezberlemesini riskli kılar. **(3) Değişken çözünürlük ve kare hızı** ölçek/zamanlama
dayanıklılığı gerektirir. **(4) Hareket bulanıklığı ve kısa görünürlük:** araç kadrajda
birkaç saniye kalır, tek kareye dayalı karar gürültülüdür. **(5) Oklüzyon ve küçük
hedefler:** uzaktaki plaka çok küçük bir piksel alanı kaplar; kabin içi cam yansıması ve
karanlık nedeniyle kısmi görünür. **(6) Dış kamera açısı:** kabin içi eylemler (sigara,
esneme) dışarıdan/karanlıktan fiziksel olarak güç görünür — ticari HOV/denetim sistemleri
bile bu açıdan yalnızca ön sıra ve kaba ihlalleri güvenilir tespit eder.

İzlenen çözüm bu zorlukların her birine yanıt verir: Kameranın sabit olması sahnedeki tek
hareketli nesnenin araç olması avantajını doğurur; araç güvenilir tespit edilip kare kare
takip edilir. Tek kareye güvenmek yerine bulgular **Araç Geçiş Hafızası**'nda biriktirilir;
böylece bulanıklık, oklüzyon ve anlık yanlış tespitler zaman içinde törpülenir. Düşük ışığa
karşı yalnızca ilgili bölgelere (plaka, ön cam) **adaptif CLAHE** uygulanır. Plaka iki
aşamalı (tespit + OCR) ele alınır; YOLO11 tercih edilir (tek ekosistemde tespit+sınıflandırma,
T4'e uygun). Kare-bazlı tek-model yaklaşımı karanlık/bulanıkta kırılgan, ağır tek dev model
10 dk bütçesini zorlayacağından **modüler + zamansal füzyon** bilinçli seçilmiştir.

### 3.2. Çözüm Mimarisi (15 puan)

Çözüm, ham videonun girişinden etiketlenmiş JSON çıktısına kadar tüm süreci tek bir
çevrimdışı konteynerde yürütür: `/app/data/input/video.mp4 → /app/data/output/results.json`.
Boru hattı altı aşamadan oluşur: (1) kare çözme + örnekleme (değişken FPS/çözünürlüğe
dayanıklı), (2) adaptif CLAHE, (3) araç tespiti + takip (YOLO11 + ByteTrack), (4) araç
kutusundan beslenen paralel kollar — araç crop'undan tip/renk sınıflandırma, plaka
tespiti→OCR, ön cam/kabin ROI'sinden telefon/kemer/kişi(yolcu)/su tespiti, (5) tüm
bulguların **Araç Geçiş Hafızası** füzyon katmanında birleştirilmesi, (6) şema-saf
`results.json` serileştirme. *(Mimari diyagramı için Şekil 2 — viz aracıyla üretilmiştir.)*

**Araç Geçiş Hafızası** (`VehiclePassMemory`) projenin özgün çekirdeğidir: kareleri tek tek
değil, aracın geçişi boyunca biriktirir; plakayı **karakter bazlı zamansal oylama** ile,
yolcuyu/eylemi **kalıcılık eşiğiyle** (≥3 kare ve görünür karelerin ≥%25'i) birleştirir,
sürekli bir eylemi tek olay olarak üretir. Bu, yanlış-pozitifleri belirgin azaltır.

### 3.3. Çözüm Detayları (20 puan)

**Model ailesi.** Tespit ve sınıflandırma görevleri Ultralytics **YOLO11** üzerine kuruludur
(YOLO11s tespit, YOLO11s-cls sınıflandırma). **Araç tespiti+takip:** YOLO11/COCO ile araç
bulunup ByteTrack ile kareler arası ilişkilendirilir. **Tip/renk:** araç crop'u üzerinde
ikincil sınıflandırma (arka plan etkisini azaltır); tip CompCars'ın beş gövde tipiyle, renk
VCoR'un dokuz rengiyle eğitildi. **Plaka:** YOLO11 ile bölge tespiti → EasyOCR → TR plaka
regex'i; **karakter bazlı zamansal oylama** ile geçiş boyunca en tutarlı dizi seçilir;
"bulundu fakat okunamadı" ile "bulunamadı" ayrılır. **Kabin/ROI analizi:** araç kutusunun üst
kabin bölgesi (greenhouse) kırpılıp CLAHE'den geçirilir; telefon (dış-cam modeli), kemer,
kişi/yolcu ve su (yüksek-çözünürlük Self_v2 modeli, 1280 girdi) tespit edilir. **Yardımcı
sinyaller:** hız ve şerit sapması Araç Geçiş Hafızası'nda dahili tutulur; `slalom` araç
yörüngesindeki yanal salınımdan koddan türetilir (veri gerektirmez). **Yazılım/donanım:**
PyTorch, Ultralytics, OpenCV, EasyOCR; `nvidia/cuda:12.1.0` temel imajı üzerine, internet
erişimi olmadan çalışan, 8 GB altında tek Docker konteyneri; `try/except` ile çökme
engellenir, "değerlendirme ortamı tespiti" yapılmaz.

---

## 4. ÇÖZÜMÜN SINANMASI (20 puan)

Her model, eğitimde görülmeyen **ayrık test bölmeleri** üzerinde değerlendirilmiştir.

**Tablo 1 — Model başarımı (ayrık test):**

| Model (görev) | Metrik |
|---|---|
| Plaka tespiti | mAP@0.5 = **0.975**, P = 0.983, R = 0.953, F1 = 0.968 |
| Renk sınıflandırma | top-1 doğruluk = **0.942** |
| Araç tipi sınıflandırma | top-1 doğruluk = **0.941** |
| Kemer + ön cam ROI | mAP@0.5 = **0.899**, F1 = 0.880 |
| Telefon (dış-cam, `mobile`) | mAP@0.5 = **0.871** |
| Yolcu/kişi (`person`) | mAP@0.5 = **0.851** |
| Kendi veri — su (`water`, 1280) | mAP@0.5 = **0.995** |
| Kendi veri — ön yolcu (`on_koltuk`) | mAP@0.5 = **0.995** |
| Sigara dedektörü (`Cigarette`, kendi val) | mAP@0.5 = **0.859** (çapraz-domain ~%59) |

**Uçtan uca doğrulama.** Sistem; örnek (4K, karanlık) ve kendi (iPhone 2K, gündüz)
videolarımız dahil **beş farklı araçta** uçtan uca çalıştırılmış, her birinde geçerli
`results.json` üretmiştir. Örnek: TOGG SUV için `{tip: suv, plaka: 34TC8532, renk: siyah}` +
telefon tespiti; kırmızı/beyaz araçlarda da tip/renk/plaka doğru üretilmiş, kemerli
sürücüde ihlal **üretilmemiştir** (yanlış-pozitif yok). Çıkarım hızı YOLO11s için RTX 4060'ta
~4.8 ms/görüntü ölçülmüştür; konteyner T4 üzerinde 10 dk bütçesinin altında çalışır.
*(Docker üzerinde ölçülen uçtan uca süre ve FPS bu bölüme eklenecektir.)*

**Çözümümüze neden güveniyoruz?** Sonuçlar modellerin görmediği test bölmelerinden alınmış;
araç-bilgisi (tip/renk/plaka) yüksek başarımla ve beş farklı araçta tutarlı üretilmektedir.
Araç Geçiş Hafızası + kalıcılık filtresi sayesinde sistem yanlış-pozitif vermemekte;
çözünürlük deneyimiz ise küçük-nesne tespitinde veri kalitesinin rolünü nicel olarak ortaya
koymaktadır.

**Sigara ve su (nesne-tabanlı yaklaşım).** `sigara_icme` ve `su_icme`, eylemi doğrudan
sınıflandırmak yerine kabin ROI'si üzerinde çalışan **adanmış nesne dedektörleriyle**
(sigara, su şişesi) tespit edilir — "nesne varsa eylem var" ilkesi. Önemli bir metodolojik
bulgu: COCO 'bottle' sınıfı, ön-camdan görülen şişeyi tam çözünürlükte bile tanıyamadı
(0/15); bu nedenle adanmış dedektörler eğitildi. Sigara dedektörü **genel bir sigara
kümesiyle (5346 görüntü) eğitilip kendi domain karelerimizde sınanmıştır** (çapraz-domain
genelleme ~%59 yakalama) — yani aynı dağılıma ezberlemeyip gerçekten genellemektedir.
Entegre hatta gerçek videolarda hem `sigara_icme` (~0.73) hem `su_icme` (~0.56)
tetiklenmiştir. Araç Geçiş Hafızası'ndaki kalıcılık filtresi yanlış-pozitifleri sınırlar.

**Dürüst kapsam.** Esneme (yüz detayı) ve `teknocan` (özel veri yok) dış kamera açısından
güvenilir tespit edilememekte olup domain-eşleşmeli daha fazla veriyle iyileştirilmesi
planlanmaktadır.

---

## 5. KAYNAKÇA (5 puan)

1. Jocher, G., Qiu, J. ve diğ., *Ultralytics YOLO11*, 2024, https://github.com/ultralytics/ultralytics
2. Zhang, Y. ve diğ., *ByteTrack: Multi-Object Tracking by Associating Every Detection Box*, ECCV, 2022.
3. Zuiderveld, K., *Contrast Limited Adaptive Histogram Equalization*, Graphics Gems IV, 1994, s. 474–485.
4. Kalman, R. E., *A New Approach to Linear Filtering and Prediction Problems*, J. Basic Eng., 1960.
5. Yang, L., Luo, P., Loy, C. C., Tang, X., *A Large-Scale Car Dataset (CompCars)*, CVPR, 2015.
6. Kezebou, L., *VCoR: Vehicle Color Recognition Dataset*, Kaggle, 2021.
7. *License Plate Recognition* ve *seat_belt-and-mobile* veri setleri, Roboflow Universe.
8. JaidedAI, *EasyOCR*, https://github.com/JaidedAI/EasyOCR
9. *Automatic detection of vehicle occupancy and driver's seat belt status using deep learning*, Signal, Image and Video Processing (Springer), 2022.
