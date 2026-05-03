# 5G API Entegrasyonu

Bu doküman, MİMİK projesinde kullanılacak 5G ağ API entegrasyonlarının genel tasarımını açıklar.

## Number Verification API

Number Verification API, mobil uygulama kullanıcısının telefon numarasını doğrulamak için kullanılacaktır.

Amaç:

- Kullanıcı girişini güvenli hâle getirmek
- SMS tabanlı doğrulama ihtiyacını azaltmak
- Mobil şebeke üzerinden sessiz doğrulama sağlamak

## Quality on Demand API

Quality on Demand API, kritik analiz anlarında ağ kalitesini geçici olarak artırmak için kullanılacaktır.

Kritik durum örnekleri:

- TOGG aracının yaklaşması
- Plaka okuma ihtiyacının oluşması
- Sürücü davranışı analizi için daha kaliteli görüntü gerekmesi
- Risk teşkil eden durum algılanması

## QoD Tetikleme Mantığı

1. Sistem standart kaliteyle görüntü analizi yapar.
2. Araç veya kritik durum algılanır.
3. Sistem daha yüksek çözünürlüklü analiz ihtiyacı belirler.
4. Quality on Demand API çağrısı yapılır.
5. Ağ kalitesi artırılır.
6. Daha yüksek başarımlı model veya daha yüksek kaliteli görüntü analizi devreye girer.
7. Kritik durum sona erdiğinde ağ kalitesi standart seviyeye döndürülür.

## Güvenlik

API anahtarları, tokenlar, uç nokta bilgileri ve özel bağlantı detayları GitHub deposuna yüklenmeyecektir. Bu bilgiler yerel `.env` dosyalarında tutulacaktır.
