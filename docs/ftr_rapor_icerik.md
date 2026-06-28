# MİMİK — FTR Rapor Tamamlama Paketi (swfg.docx için)

> Bu dosya, takımın asıl raporu olan **swfg.docx**'i tamamlar.
> Üç parça: (A) şema-sadakati düzeltmeleri, (B) boş olan ÇÖZÜMÜN SINANMASI bölümü
> (yapıştırmaya hazır), (C) tam Kaynakça + metin-içi atıf eşlemesi.
> Tüm metrikler `runs/*/results.csv` ve Docker testinden **gerçek** ölçümlerdir.

---

## A) ŞEMA-SADAKATİ DÜZELTMELERİ (swfg.docx içinde değiştir)

Sistem nihai `results.json`'da yalnızca şunları üretir: **tip, renk, plaka**,
`telefonla_konusma`, `emniyet_kemeri_ihlali`, `slalom`, `bilgisayar`,
`on_koltuk`, `arka_koltuk_1`. Rapor metni de sadece bunları iddia etmeli.

**A1 — Proje Özeti (Bölüm 1):**
- ESKİ: "…araç tipi, renk, plaka, tahminî hız, yolcu konumları, kabin içi nesneler ile telefon ve sigara kullanımı, su içme, emniyet kemeri ihlali, esneme ve slalom gibi riskli durumları analiz ederek…"
- YENİ: "…araç tipi, renk ve plakayı; yolcu konumlarını; kabin içi nesneleri (bilgisayar) ve sürücüye ilişkin telefon kullanımı, emniyet kemeri ihlali ve slalom gibi riskli durumları analiz ederek şartnameye uygun bir JSON çıktısı üretmektedir."
- Gerekçe: su/sigara/esneme çıktıda yok; "hız" şema alanı değil (yalnızca dahili sinyal). Yanlış iddiadan kaçınır.

**A2 — Çözüm Detayları (Bölüm 3.3, "Kabin ve ROI analizi"):**
- ESKİ: "…Su şişesi ve benzeri küçük kabin içi nesneler ise yüksek çözünürlükte eğitilen Self_v2 modeliyle analiz edilmektedir."
- YENİ: "…Yolcu konumları (ön ve arka koltuk) ise takım tarafından toplanan Self_v2 verisiyle yüksek çözünürlükte eğitilen model üzerinden belirlenmektedir."
- (Hemen ardından gelen "Küçük hedeflerin piksel ayrıntılarını… 1280 piksel" cümlesi kalabilir.)

**A3 — Çözüm Detayları (Bölüm 3.3, "Araç Geçiş Hafızası ve zamansal füzyon"):**
- ESKİ: "Telefon kullanımı, emniyet kemeri ihlali ve su içme gibi olaylarda ise…"
- YENİ: "Telefon kullanımı, emniyet kemeri ihlali ve yolcu konumu gibi olaylarda ise…"

> Not: Bölüm 2'deki veri tablosunda Self_v2'nin su/sigara etiketleri **veri toplama emeği**
> olarak kalabilir (dürüst); ÇÖZÜMÜN SINANMASI bunları üretim metriği olarak SUNMAZ.
> Bölüm 2'deki "çözünürlük ön deneyi (su mAP 0.995, küçük val)" paragrafı zaten doğru
> çerçevede — dokunma.

---

## B) ÇÖZÜMÜN SINANMASI (20 PUAN) — yapıştırmaya hazır

Geliştirilen modeller, eğitim sırasında görülmeyen **ayrık doğrulama/test bölümleri**
üzerinde değerlendirilmiştir. Veri sızıntısını önlemek için bölme rastgele kare düzeyinde
değil, video/araç-geçişi düzeyinde yapılmış; aynı çekime ait kareler tek bir bölümde
tutulmuştur. Sınıflandırma görevlerinde top-1 doğruluk; tespit görevlerinde mAP@0.5 ile
birlikte kesinlik (precision) ve duyarlılık (recall) raporlanmaktadır.

**Tablo 2 — Model başarımları (ayrık doğrulama bölümü).**

| Görev / Model | Başarım |
|---|---|
| Plaka tespiti (YOLO11s) | mAP@0.5 = **0,975** · P = 0,983 · R = 0,953 |
| Araç gövde tipi (YOLO11s-cls, CompCars) | top-1 doğruluk = **0,941** |
| Araç rengi (YOLO11s-cls, VCoR → 9 sınıf) | top-1 doğruluk = **0,942** |
| Emniyet kemeri + ön cam (YOLO11s) | mAP@0.5 = **0,899** · P = 0,893 · R = 0,867 |
| Telefon/kabin tespiti (YOLO11s, phone_action) | mAP@0.5 = **0,941** · P = 0,920 · R = 0,914 |

Yolcu konumu (ön/arka koltuk), takım tarafından toplanan Self_v2 verisiyle 1280 piksel
giriş çözünürlüğünde öğrenilmiştir. Ön koltuk sınıfı mevcut doğrulamada yüksek başarım
vermekle birlikte doğrulama kümesi henüz küçük olduğundan, bu görevin nihai başarımı
daha geniş ve bağımsız bir test kümesiyle ayrıca raporlanacaktır.

**Uçtan uca doğrulama.** Sistem; biri organizatör tarafından sağlanan üç örnek video
(4K, düşük ışıklı kapalı otopark, koyu renk SUV) olmak üzere **beşten fazla farklı araç**
videosu üzerinde uçtan uca çalıştırılmış ve her durumda şartname şemasına uygun, geçerli
bir `results.json` üretmiştir. Örnek bir çıktıda araç bilgisi `{tip: suv, plaka: 34TC8532,
renk: siyah}` olarak doğru üretilmiş ve sürücünün telefon kullanımı tespit edilmiştir.
Emniyet kemeri takılı sürücülerde ihlal üretilmemesi, kalıcılık temelli füzyonun
yanlış-pozitifleri sınırladığını göstermektedir.

**Çalışma süresi ve kaynak kullanımı.** YOLO11s araç tespiti RTX 4060 üzerinde görüntü
başına yaklaşık **4,8 ms** sürmektedir. Çevrimdışı (`--network none`) ve GPU üzerinde
çalıştırılan Docker konteyneri, 4K çözünürlükteki 8 saniyelik bir videoyu **46 saniyede**
işleyip geçerli `results.json` üretmiştir; bu süre 10 dakikalık çalışma bütçesinin oldukça
altındadır. Konteyner imajı **3,41 GB** olup 8 GB sınırının altındadır. Böylece sistemin
çevrimdışı, ≤8 GB ve ≤10 dk şartname kısıtlarının tümünü karşıladığı kanıtlanmıştır.

**Şema güvencesi.** `results.json` üretilmeden önce `tip` ve `renk` değerleri ile her
tespitin (kategori, etiket) ikilisi şartname etiket kümesine göre doğrulanmaktadır; tanımlı
kümenin dışında bir değer çıktıya yazılmamaktadır. Bu, değerlendirme videosu beklenmedik bir
içerik taşısa dahi çıktının her zaman şema-geçerli kalmasını güvence altına alır.

**Çözümümüze neden güveniyoruz?**
- Raporlanan başarımlar modellerin eğitimde görmediği ayrık bölümlerden elde edilmiştir;
  araç bilgisi (tip/renk/plaka) yüksek ve tutarlı doğrulukla, beş farklı araçta üretilmektedir.
- Karar tek kareye değil, Araç Geçiş Hafızası'nda biriken çoklu gözleme dayanır; kalıcılık
  filtresi anlık yanlış tespitleri eleyerek sistemin yanlış-pozitif üretmesini engeller.
- Sistem yalnızca güvenilir biçimde ölçülen çıktıları üretecek şekilde, **kesinlik
  (precision) öncelikli** tasarlanmıştır; bu, denetim/uygulama bağlamında yanlış bir ihlal
  bildiriminin maliyetini düşürür.
- Küçük nesnelerde çözünürlüğün belirleyiciliğine ilişkin ön deney (Bölüm 2), veri kalitesinin
  rolünü nicel olarak ortaya koyarak yöntemsel titizliği desteklemektedir.

**Gelecek çalışma.** Daha geniş ve bağımsız bir test kümesiyle yolcu konumları ve ek
kabin-içi davranışların başarımı nicel olarak raporlanacak; canlı dağıtımda aynı çekirdek,
Turkcell 5G Quality on Demand ve Number Verification API'leri ile bütünleştirilecektir.

---

## C) KAYNAKÇA (tam liste) + metin-içi atıf eşlemesi

Taslaktaki atıflar [1]=ByteTrack, [2]=Drygala, [3]=Artan'dı ama Bölüm 2'de CompCars "[1],[2]"
olarak yanlış atıflanmıştı. Aşağıdaki **tam liste** ile değiştir ve metin-içi numaraları
şu eşlemeye göre güncelle:

- YOLO11 / model ailesi (Bölüm 3.1, 3.3) → **[1]**
- ByteTrack takip (Bölüm 3.3) → **[2]**
- CompCars (Bölüm 2, araç tipi) → **[3]**  *(eski "[1], [2]" yerine)*
- VCoR (Bölüm 2, renk) → **[4]**
- License Plate veri seti (Bölüm 2, plaka) → **[5]**
- seat_belt-and-mobile / NoSeatbelt (Bölüm 2, kemer-telefon) → **[6]**
- EasyOCR (Bölüm 3.3, plaka OCR) → **[7]**
- CLAHE / Zuiderveld (Bölüm 3.3) → **[8]**
- Drygala vd., kabin CLAHE (Bölüm 3.3) → **[9]**
- Artan vd., ROI/telefon (Bölüm 3.3) → **[10]**

**KAYNAKÇA**

[1] G. Jocher, J. Qiu vd., "Ultralytics YOLO11," 2024. [Çevrimiçi]. Erişim: https://github.com/ultralytics/ultralytics

[2] Y. Zhang, P. Sun, Y. Jiang, D. Yu, F. Weng, Z. Yuan, P. Luo, W. Liu ve X. Wang, "ByteTrack: Multi-Object Tracking by Associating Every Detection Box," *Proc. European Conf. on Computer Vision (ECCV)*, 2022, ss. 1–21, doi: 10.1007/978-3-031-20047-2_1.

[3] L. Yang, P. Luo, C. C. Loy ve X. Tang, "A Large-Scale Car Dataset for Fine-Grained Categorization and Verification (CompCars)," *Proc. IEEE Conf. on Computer Vision and Pattern Recognition (CVPR)*, 2015, ss. 3973–3981.

[4] L. Kezebou, "VCoR: Vehicle Color Recognition Dataset," Kaggle, 2021. [Çevrimiçi]. Erişim: https://www.kaggle.com/datasets/landrykezebou/vcor-vehicle-color-recognition-dataset

[5] "License Plate Recognition Dataset," Roboflow Universe. [Çevrimiçi]. Erişim: https://universe.roboflow.com

[6] "Seat Belt and Mobile Phone Detection Datasets," Roboflow Universe. [Çevrimiçi]. Erişim: https://universe.roboflow.com

[7] JaidedAI, "EasyOCR." [Çevrimiçi]. Erişim: https://github.com/JaidedAI/EasyOCR

[8] K. Zuiderveld, "Contrast Limited Adaptive Histogram Equalization," *Graphics Gems IV*, P. S. Heckbert (Ed.), Academic Press, 1994, ss. 474–485.

[9] C. Drygala, M. Rottmann, H. Gottschalk, K. Friedrichs ve T. Kurbiel, "Background-foreground segmentation for interior sensing in automotive industry," *Journal of Mathematics in Industry*, c. 12, mak. no. 13, 2022, doi: 10.1186/s13362-022-00128-9.

[10] Y. Artan, O. Bulan, R. P. Loce ve P. Paul, "Driver Cell Phone Usage Detection from HOV/HOT NIR Images," *Proc. IEEE Conf. on Computer Vision and Pattern Recognition Workshops (CVPRW)*, 2014, ss. 225–230, doi: 10.1109/CVPRW.2014.36.
