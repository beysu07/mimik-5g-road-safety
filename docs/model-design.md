# Yapay Zekâ Model Tasarımı

Bu doküman, MİMİK projesinde kullanılacak yapay zekâ modellerinin genel tasarımını açıklar.

## Hedefler

Sistemin tespit etmesi hedeflenen ana unsurlar:

- Araç
- TOGG aracı
- Plaka
- Araç hızı
- Araç içi nesneler
- Sürücü davranışı
- Telefon kullanımı
- Sigara kullanımı
- Yorgunluk veya dikkat dağınıklığı göstergeleri

## Önerilen Yaklaşım

Model tasarımı modüler bir yapıda ele alınacaktır.

### 1. Araç Tespiti

Araç tespiti için YOLO tabanlı bir nesne tespit modeli kullanılacaktır. Bu modül, video karelerinde araç konumlarını belirlemekten sorumludur.

### 2. Plaka Tespiti ve OCR

Plaka bölgesi ayrı bir tespit modeli veya araç tespiti sonrası bölgesel analiz ile bulunacaktır. Plaka metni OCR yöntemiyle okunacaktır.

### 3. Hız Tahmini

Hız tahmini için ardışık karelerde araç konum değişimi analiz edilecektir. Kamera açısı, zaman farkı ve ölçekleme bilgileri kullanılarak yaklaşık hız hesaplanacaktır.

### 4. Araç İçi Nesne ve Sürücü Davranışı Analizi

Araç içi bölge için ayrı ROI analizi yapılacaktır. Telefon, sigara, emniyet kemeri, sürücü yüz durumu ve dikkat dağınıklığı gibi unsurlar incelenecektir.

## Değerlendirme Metrikleri

- Doğruluk
- Hassasiyet
- Geri çağırma
- F1 skoru
- Çıkarım süresi
- FPS
- Yanlış pozitif oranı
- Yanlış negatif oranı

## Geliştirme Notları

Model geliştirme sürecinde önce temel araç ve plaka tespiti tamamlanacak, ardından sürücü davranışı ve araç içi nesne analizi modülleri geliştirilecektir.
