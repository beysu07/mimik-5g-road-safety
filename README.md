# MİMİK — 5G & Yapay Zekâ ile Akıllı Yol Güvenliği (FTR)

Yol kenarı **sabit kameradan** alınan videoyu çevrimdışı işleyip araç ve sürücü/yolcu
durumlarını tespit eden bilgisayarlı görü sistemi. Çıktı: şartnameye birebir uyan
`results.json`.

> Takım: MİMİK · TEKNOFEST 5G & Yapay Zekâ ile Akıllı Yol Güvenliği Yarışması

## Ne yapıyor?
Girdi `video.mp4` → Çıktı `results.json`:
- **arac_bilgisi:** `tip` (sedan/suv/hatchback/pickup/minibus…), `renk` (9 sınıf), `plaka` (TR, OCR), `confidence_score`
- **tespitler:** `telefonla_konusma`, `emniyet_kemeri_ihlali`, `slalom`, `bilgisayar`, (`yolcular` — deneysel)

## Mimari (özet)
```
video → kare örnekleme → araç tespiti+takip (YOLO11+ByteTrack)
      → araç crop → tip/renk sınıflandırma
      → plaka tespiti → CRNN/EasyOCR → regex
      → kabin ROI → telefon / kemer / kişi(yolcu)
      → ARAÇ GEÇİŞ HAFIZASI (geçiş boyunca füzyon) → results.json
```
**Araç Geçiş Hafızası** (`src/predict.py` → `VehiclePassMemory`): kareleri tek tek
değil, aracın geçişi boyunca biriktirip karar verir. Plakayı **karakter bazlı zamansal
oylama** ile, yolcuyu **kalıcılık** ile, sürekli eylemi **tek olay** olarak üretir.

## Klasör yapısı
| Yol | Açıklama |
|---|---|
| `app.py` | Giriş noktası: `video → results.json` |
| `src/predict.py` | Çıkarım hattı + Araç Geçiş Hafızası |
| `src/utils.py` | CLAHE, plaka regex |
| `train/` | Eğitim scriptleri (tip, renk, plaka, kemer, telefon) |
| `viz.py` | Annotasyonlu video (kutuları görmek için) |
| `datasets/`, `runs/`, `veri/` | **git'te YOK** (büyük) — ayrı paylaşılır |

## Kurulum
```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
# GPU için CUDA uyumlu torch gerekir (ultralytics çeker). easyocr ilk çalışmada model indirir.
```

## Çalıştırma
```bash
python app.py veri/video_1 runs/_pred/video_1.json     # cikarim
python viz.py veri/video_1 runs/_viz/video_1.mp4        # gorsel dogrulama
```
> **Ağırlıklar** (`runs/.../weights/best.pt`) git'te yok. Çalıştırmak için ağırlıkları
> Drive'dan al **veya** `train/` scriptleriyle yeniden eğit (veri setleri gerekir).

## Güncel yetenek / sınırlar (dürüst)
- ✅ Güvenilir: **tip, renk, plaka** (mAP/doğruluk yüksek), **telefon varlığı**, **kemer ihlali** (varsa).
- ⚠️ Sınırlı: telefon↔sigara↔su (dış açıdan el-yüz belirsizliği), `yolcular` ön=gürültülü.
- 🔴 Yapılamıyor: arka koltuk (dış kameradan görünmez), esneme/teknocan.

## Veri toplama (yolcular için kritik)
Sabit kamera + araç kameraya doğru gelip geçsin; 2-3 kişi **farklı koltuk
konfigürasyonlarında** (ön/arka), **farklı ışıkta (özellikle karanlık)**. Klipleri
konfigürasyona göre adlandırın.
