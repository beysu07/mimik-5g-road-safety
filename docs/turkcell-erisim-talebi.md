# Turkcell / Yarışma Komitesi — 5G Ağ API Erişim Talebi (gönderilecek mail)

> Gönderim: yarışma komitesi + Turkcell teknik iletişim kanalı (varsa eğitim seansı e-postası).
> Konu satırı ve gövde aşağıda hazırdır; köşeli parantezli yerleri doldurup gönderin.

---

**Konu:** 5G Ağ API (QoD + Number Verification) Erişim Bilgileri Talebi — Takım MİMİK (Takım ID: 798075)

Sayın Yarışma Komitesi ve Turkcell Teknik Ekibi,

2026 5G ve Yapay Zekâ ile Akıllı Yol Güvenliği Yarışması'nda finale kalan **MİMİK** takımıyız
(Takım ID: 798075, Başvuru ID: 4541474).

7–9 Ağustos'taki final etabına hazırlanırken, şartnamenin 4.1 maddesinde tanımlanan **Quality on
Demand** ve **Number Verification** API'lerinin entegrasyonunu tamamlamak istiyoruz. Uygulama
tarafındaki geliştirmemiz (kritik durum tespiti → QoD tetikleme → kaynak bırakma döngüsü ve
ölçüm altyapısı) hazır durumdadır; gerçek şebeke entegrasyonuna geçebilmek için aşağıdaki
bilgilere ihtiyacımız bulunmaktadır.

**A. Erişim ve kimlik doğrulama**
1. QoD ve Number Verification API'leri için **base URL**'ler ve varsa sandbox/test ortamı bilgisi.
2. Kimlik bilgileri (client_id / client_secret) nasıl ve ne zaman tarafımıza iletilecek?
3. Yetkilendirme akışı: 2-legged (client credentials) mi, 3-legged (kullanıcı onaylı) mı bekleniyor?

**B. Quality on Demand**
4. Kullanılabilir **QoS profil adları** (ör. QOS_S/M/L/E) ve her birinin bant genişliği/gecikme
   değerleri ile `maxDuration` sınırı.
5. `device` alanında hangi tanımlayıcı kabul ediliyor: `phoneNumber` mi, `ipv4Address` mi?
6. `applicationServer` olarak hangi adresi beyan etmeliyiz — analiz ucumuz yarışma alanındaki
   yerel ağda mı olacak, yoksa dış IP üzerinden mi erişilecek?
7. Bildirim için `sink` (webhook) destekleniyor mu? Desteklenmiyorsa `qosStatus` **AVAILABLE**
   durumu için önerilen polling aralığı nedir ve tipik kaynak tahsis süresi (kurulum gecikmesi)
   ne kadardır?
8. Eş zamanlı oturum sınırı ve art arda aç/kapa (churn) kısıtı var mıdır? (409 CONFLICT riski)

**C. Number Verification**
9. **Authorization Code Flow** mu yoksa **TS.43 / CIBA** mı destekleniyor? Authorization Code
   Flow kullanılacaksa cihazın Wi-Fi kapalı ve mobil veride olması gerektiğini varsayıyoruz;
   teyit edebilir misiniz?

**D. Final alanı ve cihaz/akış**
10. Finalde tarafımıza sağlanacak hat/cihaz sayısı, APN bilgisi ve sabit IP tahsisi olup
    olmayacağı; ayrıca canlı kamera görüntüsünün hangi protokolle (RTSP / WebRTC / SRT vb.)
    sunulacağı ve kaynak cihazın ne olacağı.

Ek olarak, şartnamedeki *"şebeke kalitesi arttığında yapay zekâ başarım artışının API kullanımı
ile kanıtlanması"* gerekliliği için ölçüm düzeneğimizi kurduk; operatör tarafında oturum/kalite
loglarına erişim sağlanabiliyorsa bunu da ispat kayıtlarımıza eklemek isteriz.

Bilgilerin en geç **2 Ağustos**'a kadar tarafımıza ulaşması, final öncesi uçtan uca testi
tamamlayabilmemiz açısından bizim için kritik önemdedir. Yardımlarınız için şimdiden teşekkür
eder, iyi çalışmalar dileriz.

Saygılarımızla,
**Muhammet Doğukan Bingöl** — Takım MİMİK, Takım Kaptanı
Takım ID: 798075 / Başvuru ID: 4541474
Tel: [telefon] · E-posta: [e-posta]
