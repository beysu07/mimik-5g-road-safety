# MİMİK – 5G Destekli Akıllı Yol Güvenliği Sistemi

MİMİK, yol kenarı kamera görüntülerinden araç, plaka, araç içi nesne ve sürücü
davranışı gibi güvenlik kritik bilgileri çıkarmayı hedefleyen; ileride 5G Quality on
Demand API ile ağ kalitesini dinamik artırmayı amaçlayan yapay zekâ destekli bir akıllı
yol güvenliği sistemidir.

> TEKNOFEST 2026 · 5G & Yapay Zekâ ile Akıllı Yol Güvenliği Yarışması · Takım MİMİK

## Amaç
Bu proje, yapay zekâ tabanlı görüntü işleme ile 5G ağ API yeteneklerini bir araya
getirerek yol güvenliği analitiği üretmeyi hedefler. **FTR aşaması** için çevrimdışı
çalışan, `video.mp4 → results.json` üreten çıkarım hattı bu repoda uygulanmıştır.

## Temel Bileşenler (vizyon)
- Araç tespiti · TOGG tespiti · Plaka okuma · Hız tahmini
- Araç içi nesne analizi · Sürücü davranışı analizi
- Quality on Demand API · Number Verification API · Mobil uygulama arayüzü

## Sistem Mimarisi (4 katman)
1. Görüntü Yakalama Katmanı
2. Mobil Uygulama ve 5G API Katmanı
3. Yapay Zekâ Çıkarım Katmanı
4. Kullanıcı Arayüzü Katmanı

---

## ✅ FTR Çıkarım Hattı (bu repoda uygulanan)
Çevrimdışı, tek konteyner: **`video.mp4 → results.json`** (şartnameye birebir şema).
```
video → kare örnekleme → araç tespiti+takip (YOLO11+ByteTrack)
      → araç crop → tip/renk sınıflandırma
      → plaka tespiti → EasyOCR → regex
      → kabin ROI → telefon / kemer / kişi(yolcu)
      → ARAÇ GEÇİŞ HAFIZASI (geçiş boyunca füzyon) → results.json
```
**Araç Geçiş Hafızası** (`src/predict.py → VehiclePassMemory`): kareleri tek tek değil,
aracın geçişi boyunca biriktirip karar verir — plaka **karakter bazlı zamansal oylama**,
yolcu **kalıcılık**, sürekli eylem **tek olay**.

### Klasör yapısı
| Yol | Açıklama |
|---|---|
| `app.py` | Giriş: `video → results.json` |
| `src/predict.py` | Çıkarım hattı + Araç Geçiş Hafızası |
| `src/utils.py` | CLAHE, plaka regex |
| `train/` | Eğitim scriptleri (tip, renk, plaka, kemer, telefon) |
| `viz.py` | Annotasyonlu video (kutuları görmek için) |
| `docs/`, `configs/`, `scripts/` | Tasarım dökümanları, config, kare çıkarma |
| `datasets/`, `runs/`, `veri/` | **git'te YOK** (büyük) — ayrı paylaşılır |

### Kurulum & Çalıştırma
```bash
pip install -r requirements.txt   # GPU icin CUDA uyumlu torch gerekir
python app.py veri/video_1 runs/_pred/video_1.json   # cikarim
python viz.py veri/video_1 runs/_viz/video_1.mp4      # gorsel dogrulama
```
> Ağırlıklar (`runs/.../weights/best.pt`) git'te yok — Drive'dan al **veya** `train/` ile eğit.

### Güncel yetenek / sınırlar (dürüst)
- ✅ Güvenilir: **tip, renk, plaka**, telefon varlığı, kemer ihlali (varsa)
- ⚠️ Sınırlı: telefon↔sigara↔su (dış açıdan el-yüz belirsizliği), `yolcular` ön=gürültülü
- 🔴 Yapılamıyor: arka koltuk (dış kameradan görünmez), esneme/teknocan

## Geliştirme Durumu
- [x] Ön Tasarım Raporu
- [x] GitHub deposu + tasarım dökümanları
- [x] Proje klasör yapısı
- [x] Veri işleme hattı (kare çıkarma + çıkarım)
- [x] Araç/plaka/renk tespit modelleri (eğitildi)
- [x] Sürücü davranışı (telefon/kemer) + Araç Geçiş Hafızası
- [ ] 5G API entegrasyonu (canlı dağıtım katmanı)
- [ ] Mobil arayüz prototipi

## Veri Politikası
Yarışma test videoları, gerçek plaka/API bilgileri ve özel veri setleri bu repoya
yüklenmez; yalnızca yerel ortamda tutulur.

## Veri toplama (yolcular için kritik)
Sabit kamera + araç kameraya doğru gelip geçsin; 2-3 kişi **farklı koltuk
konfigürasyonlarında** (ön/arka), **farklı ışıkta (özellikle karanlık)**. Klipleri
konfigürasyona göre adlandırın.

## Takım
MİMİK Takımı
