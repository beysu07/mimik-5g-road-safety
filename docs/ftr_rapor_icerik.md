# MIMIK FTR - Juri Odakli Nihai Icerik

Bu metin `swfg_juri_final.docx` icin teknik gercek kaynaktir. Olculmus basarim,
ozgun cozum ve kabul kanitlari one cikarilmis; gelecek gelistirmeler tek bir bolumde
toplanmistir.

## 1. Proje Ozeti

MIMIK, yol kenari kamera videosunu tek geciste analiz ederek arac tipi, renk ve
plaka bilgisini; gorunebilen yolcu konumlarini; kabin ici nesneleri ve yol
guvenligini etkileyen surucu eylemlerini cikaran butunlesik bir bilgisayarli gorus
sistemidir. Cozum, yedi farkli derin ogrenme modelini goreve ozel ROI'ler ve Arac
Gecis Hafizasi ile birlestirir. Boylece tek karedeki goruntu bozukluklari yerine
gecis boyunca biriken coklu gozlemlerden karar verilir.

Plaka tespitinde 0,975 mAP@0.5 ve 0,968 F1; telefon tespitinde 0,941 mAP@0.5 ve
0,917 F1; arac tipinde %94,1, renkte %94,7 top-1 dogruluk elde edilmistir. Sistem,
CUDA 12.1 tabanli cevrimdisi Docker imajinda 4K test videosunu 68,19 saniyede
islemis, `SCHEMA_OK` sonucunu veren konsolide JSON uretmistir. Docker imaji 7,55
GB, teslim tar dosyasi 2,699 GB'dir.

## 2. Veri Stratejisi

Genel arac gorunumlerini ogrenmek icin acik kaynakli veri kumeleri, yarismadaki
sabit dis kamera gorusunu temsil etmek icin ise takim tarafindan toplanan yuksek
cozunurluklu kabin goruntuleri birlikte kullanilmistir. Bu hibrit strateji hem veri
cesitliligini hem de hedef alana uyumu guclendirmistir.

| Gorev | Veri kaynagi | Egitim | Dogrulama | Test |
|---|---|---:|---:|---:|
| Plaka tespiti | Roboflow License Plate Recognition | 7.057 | 2.048 | 1.020 |
| Arac rengi | VCoR, 9 hedef renk | 5.215 | 1.113 | 1.116 |
| Arac tipi | CompCars, 5 govde tipi | 13.714 | 2.420 | - |
| Kemer/on cam | Roboflow NoSeatbelt | 933 | 138 | 120 |
| Telefon/kabin | Birlesik Roboflow kumeleri | 4.763 | 1.203 | - |
| Yuksek coznurluklu kabin | Takim Self_v2 | 96 | 16 | - |

Sinif adlari tek sozlukte birlestirilmis, FTR'nin kucuk harfli ASCII etiketlerine
eslenmis ve bolme sayilari dosya manifestleriyle kayit altina alinmistir. Egitimde
mosaic=1,0, yatay cevirme=0,5, olcekleme=0,5, oteleme=0,1 ve goreve uygun HSV
degisimleri kullanilmistir. Renk siniflandirmasinda renk anlamini, plaka gorevinde
karakter geometrisini koruyan kontrollu artirma tercih edilmistir.

Kabin hedefleri ilk dusuk coznurluklu deneylerde yalniz birkac piksele kadar
kuculmustur. Veriler ozgun 2K coznurlukte yeniden disa aktarilip model girisi 1280
piksele cikarildiginda su sinifi icin mevcut dogrulamada mAP@0.5=0,995 elde
edilmistir. Bu deney, kucuk kabin hedeflerinde coznurluk seciminin etkisini somut
olarak gostermis ve final ROI tasarimini belirlemistir.

## 3. Cozum Mimarisi

Video OpenCV ile acilir, MOV yon bilgisi uygulanir ve degisken FPS degerlerinden
bagimsiz olarak yaklasik 8 analiz karesi/saniye secilir. COCO on-egitimli YOLO11s,
her karede ana araci bulur. Arac kirpimi, bir sonraki asamadaki tum uzman modellere
ortak ve arka plandan arindirilmis giris saglar.

### Arac ozellikleri

YOLO11s-cls tabanli iki siniflandirici arac tipi ve rengi ayri ayri belirler.
Gecis boyunca her sinif icin oylar ve guvenler biriktirilir; en cok desteklenen
sinif, o sinifa ait ortalama guvenle raporlanir. Bu yapi tek karedeki parlama,
golge veya kismi kapanmanin nihai karari bozmasini azaltir.

### Plaka tespiti ve OCR

Ozel YOLO11s modeli arac icindeki plakayi tespit eder. Plaka ROI'si dort kat
buyutulur, gri seviyeye cevrilir ve CLAHE ile yerel kontrasti artirilir. EasyOCR
yalniz buyuk harf ve rakam izin listesiyle calisir. Okumalar Turkiye plaka regex'i
ile denetlenir; farkli karelerdeki gecerli sonuclar OCR guveniyle agirlikli,
karakter konumlu oylamayla birlestirilir.

### Kabin ROI ve olaylar

Arac kutusunun ust yuzde 65'lik greenhouse bolgesi kabin ROI'si olarak secilir.
ROI uzun kenari kucuk hedefleri korumak icin gerekirse 1280 piksele buyutulur.
Telefon, emniyet kemeri, yolcu, su ve sigara bulgulari goreve ozel modellerle bu
daraltilmis bolgede aranir; bilgisayar COCO `laptop` sinifindan eslenir.

Telefon, su, sigara, kemer ve yolcu bulgulari 1,5 saniyelik pencerede en az uc
gozlemle dogrulanir. Surekli gorulen ayni durum tek olay olarak raporlanir. Bu
zamansal filtre anlik yansima ve tek karelik yanlis tespitlerin ciktiya dogrudan
aktarilmasini azaltir.

### Arac Gecis Hafizasi

VehiclePassMemory; tip ve renk oylarini, plaka okumalarini, kabin bulgularini,
zaman damgalarini ve arac kutusu merkezlerini ortak kayitta toplar. Slalom bulgusu,
yumusatilmis yanal merkez izindeki anlamli yon degisimlerinden uretilir. Nihai
karar katmani tum bulgulari FTR izin listesine gore suzerek tek `results.json`
dosyasinda birlestirir.

## 4. Cozumun Sinanmasi

Dagitilan `best.pt` agirliklarina karsilik gelen dogrulama satirlari kullanilmistir.
F1 degerleri precision ve recall'dan `2PR/(P+R)` ile hesaplanmistir.

| Model | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 / top-1 |
|---|---:|---:|---:|---:|---:|
| Plaka tespiti | 0,983 | 0,953 | **0,968** | **0,975** | 0,711 |
| Telefon/kabin tespiti | 0,920 | 0,914 | **0,917** | **0,941** | 0,563 |
| Kemer/on cam tespiti | 0,921 | 0,860 | **0,889** | **0,885** | 0,670 |
| Self_v2 kabin on deneyi | 0,781 | 0,661 | 0,716 | 0,714 | 0,320 |
| Arac tipi siniflandirma | - | - | - | - | **top-1 0,941** |
| Arac rengi siniflandirma | - | - | - | - | **top-1 0,947** |

Uctan uca Docker testinde 3840x2160, 50 FPS, 457 kare ve 9,14 saniyelik video
68,19 saniyede tamamlanmistir. Bu, kaynak video uzerinden **6,70 FPS** esdeger
uctan uca is hacmine karsilik gelir. Cikarim hatti 77 secilmis analiz karesini
islemis ve coklu model/OCR dahil **1,13 analiz FPS** elde etmistir. Sonuc 10
dakikalik kabul sinirinin yaklasik dokuzda biridir.

Test ciktisi araci `suv`, plakayi `34TC8532`, rengi `siyah` olarak belirlemis ve
`telefonla_konusma` olayini uretmistir. Anahtarlar, etiketler, guven araliklari ve
plaka regex'i bagimsiz dogrulayiciyla denetlenmis; sonuc `SCHEMA_OK` olmustur.

### Cozumumuze neden guveniyoruz?

- Plaka, telefon, kemer, tip ve renk gorevlerinde yuksek ve sayisal olarak
  izlenebilir dogrulama basarimi elde edilmistir.
- ROI tasarimi kucuk hedeflerin goruntu icindeki goreli boyutunu artirir ve arka
  plan kaynakli gurultuyu azaltir.
- Arac Gecis Hafizasi, kararlarini tek kare yerine zamansal olarak tutarli coklu
  gozlemlerden uretir.
- Plaka regex'i ve sabit JSON izin listesi otomatik degerlendirme uyumlulugunu
  kod seviyesinde korur.
- Final Docker imaji gercek video, GPU, kapali ag ve yarismadaki kaynak sinirlariyla
  uctan uca test edilmistir.

## 5. Docker ve Kabul Kaniti

Final `mimik/ftr:final` imaji zorunlu
`nvidia/cuda:12.1.0-base-ubuntu22.04` tabanindan uretilmistir. Yedi model
`/app/models/` altindan basariyla acilmistir. Konteyner `--network none`, 4 vCPU,
16 GB RAM ve 2 GB SHM ile GPU uzerinde calistirilmistir.

| Kabul maddesi | Dogrulanmis sonuc |
|---|---|
| Docker imaj boyutu | 7,55 GB |
| `imaj.tar` boyutu | 2,699 GB |
| Tar yeniden yukleme | Basarili |
| Uctan uca sure | 68,19 saniye |
| Konteyner cikis kodu | 0 |
| Runtime ag erisimi | Kapali |
| JSON dogrulamasi | `SCHEMA_OK` |

Tar SHA-256 degeri
`BBDFBB9DD7590447D9E9F276F703A6B450113DABD57DDFABCFB40090EEDE47A7`'dir.
Ayrintili komut ve kanitlar `reports/docker_acceptance.md` dosyasinda tutulmustur.

## 6. Gelecek Calismalar

Sonraki iterasyonda kabin verisi farkli arac, kisi, hava ve aydinlatma kosullariyla
genisletilecek; ek surucu davranislari ayni moduler mimariye dahil edilecektir.
Canli dagitim asamasinda mevcut cevrimdisi cikarim cekirdeginin Turkcell 5G Quality
on Demand ve Number Verification servisleriyle butunlestirilmesi hedeflenmektedir.

## 7. Kaynakca

[1] Ultralytics, "Ultralytics YOLO," GitHub.
https://github.com/ultralytics/ultralytics

[2] L. Yang, P. Luo, C. C. Loy ve X. Tang, "A Large-Scale Car Dataset for
Fine-Grained Categorization and Verification," CVPR, 2015.
https://mmlab.ie.cuhk.edu.hk/datasets/comp_cars/index.html

[3] L. Kezebou, "VCoR: Vehicle Color Recognition Dataset," Kaggle.
https://www.kaggle.com/datasets/landrykezebou/vcor-vehicle-color-recognition-dataset

[4] "License Plate Recognition," Roboflow Universe, surum 1.
https://universe.roboflow.com/dogukan-pvnlq/license-plate-recognition-rxg4e-skvyq/dataset/1

[5] "NoSeatbelt," Roboflow Universe, surum 1.
https://universe.roboflow.com/dogukan-pvnlq/noseatbelt-kqgo0/dataset/1

[6] "Seat Belt and Mobile," Roboflow Universe, surum 1.
https://universe.roboflow.com/dogukan-pvnlq/seat_belt-and-mobile-vjy3m/dataset/1

[7] "Seatbelt and Mobile," Roboflow Universe, surum 1.
https://universe.roboflow.com/dogukan-pvnlq/seatbelt-and-mobile-aayfs/dataset/1

[8] "Self_v2 / Sigara," Roboflow Universe, surum 2.
https://universe.roboflow.com/123s-workspace-tcilc/sigara-m4576/dataset/2

[9] JaidedAI, "EasyOCR," GitHub. https://github.com/JaidedAI/EasyOCR

[10] K. Zuiderveld, "Contrast Limited Adaptive Histogram Equalization,"
Graphics Gems IV, 1994, ss. 474-485.

[11] Y. Artan, O. Bulan, R. P. Loce ve P. Paul, "Driver Cell Phone Usage
Detection from HOV/HOT NIR Images," CVPRW, 2014, doi:10.1109/CVPRW.2014.36.
