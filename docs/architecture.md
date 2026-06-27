# Sistem Mimarisi

MİMİK sistemi dört ana katmandan oluşmaktadır.

## 1. Görüntü Yakalama Katmanı

Yol kenarına konumlandırılan kamera veya video kaynağından görüntü akışı alınır. Bu katman, video karelerinin sisteme aktarılmasından sorumludur.

## 2. Mobil Uygulama ve 5G API Katmanı

Mobil uygulama, kullanıcı doğrulama ve ağ kalitesi yönetimi görevlerini üstlenir. Number Verification API ile kullanıcı doğrulaması yapılması, Quality on Demand API ile kritik anlarda ağ kalitesinin artırılması hedeflenir.

## 3. Yapay Zekâ Çıkarım Katmanı

Bu katman; araç tespiti, TOGG tespiti, plaka okuma, hız tahmini, araç içi nesne analizi ve sürücü davranışı analizi görevlerini yürütür.

## 4. Kullanıcı Arayüzü Katmanı

Tespit edilen bilgiler, mobil uygulama veya kontrol paneli üzerinden kullanıcıya sunulur. Arayüzde araç, plaka, hız, risk durumu ve ağ kalitesi bilgileri gösterilir.

## Veri Akışı

1. Kamera veya video kaynağından görüntü alınır.
2. Görüntü karelere ayrılır.
3. Yapay zekâ modeli ile araç ve risk unsurları analiz edilir.
4. Kritik durum algılanırsa Quality on Demand API tetiklenir.
5. Ağ kalitesi arttığında daha yüksek kaliteli görüntü akışı analiz edilir.
6. Tespit sonuçları kullanıcı arayüzünde gösterilir.
