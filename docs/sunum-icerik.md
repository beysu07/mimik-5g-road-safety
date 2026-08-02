# MİMİK — Final Sunumu (10 dakika)

> Format serbest. Hedef: jüriye **mühendislik disiplinini** göstermek. Elimizdeki en
> güçlü koz "mükemmel model" değil, **her iddianın ölçülmüş olması**. Çoğu takım
> "yaptık, çalışıyor" der; biz sayı ve karşı-deney gösteriyoruz.
>
> Tüm rakamlar gerçek ölçümdür (`scripts/faz2_degerlendir.py`, `scripts/saglamlik_testi.py`).

---

## Slayt 1 — Kapak (15 sn)
**MİMİK** · Takım ID 798075
5G ve Yapay Zekâ ile Akıllı Yol Güvenliği
*"Ölçmediğimiz hiçbir şeyi iddia etmedik."*

## Slayt 2 — Problem (45 sn)
Yol kenarı sabit kameradan tek videoda:
araç kimliği (tip/plaka/renk) + sürücü ihlalleri + yolcu konumları + kabin nesneleri
→ şartname şemasına **birebir** `results.json`

Zorluklar: karanlık otopark · araç 114 sn boyunca farklı açı ve mesafelerde ·
cam yansıması · küçük hedefler (plaka, maskot) · iki farklı çözünürlük

## Slayt 3 — Mimari (1 dk)
```
video → kare örnekleme → araç tespiti + takip
                          ├─ araç crop → tip / renk
                          ├─ plaka → OCR → karakter bazlı zamansal oylama
                          ├─ kabin ROI → telefon / kemer
                          └─ kişi tespiti → konum tabanlı koltuk ataması
                                    ↓
                        Araç Geçiş Hafızası (zamansal füzyon)
                                    ↓
                         şema-doğrulanmış results.json
```
**Tasarım ilkesi:** karar tek kareye değil, **araç geçişi boyunca biriken gözleme** dayanır.

## Slayt 4 — ⭐ Çözümün üç tasarım kararı (2 dk) — SUNUMUN KALBİ

Sistemi kurarken üç kritik kararı **ölçerek** verdik.

**Karar 1 — Karar tek kareye değil, araç geçişine dayanır.**
Bir eylem 114 saniyelik videoda birden çok kez görünür hale gelir. Bu yüzden gözlemleri
*epizotlara* ayırıp her epizot için ayrı olay üretiyoruz. Epizot sınırını sabit bir
saniyeye değil, **aracın görünürlüğüne** bağladık: araç kadrajdan çıkıp geri girdiğinde
eylem yeniden görünür olmuştur. Şartnamenin *"olaylar görülebilir oldukları anda
işaretlenir"* tanımıyla birebir örtüşür ve video uzunluğundan bağımsızdır.

**Karar 2 — Yolcu tespitinde hazır güçlü modeli, özel sınıfa tercih ettik.**
Kendi topladığımız veriyle eğittiğimiz koltuk sınıfını referans anlarda ölçtük: **0/13**.
Aynı anlarda hazır kişi tespiti: **10/13**. Bunun üzerine koltuk kimliğini modele
sorduran yaklaşımı bırakıp **geometriye** dayandırdık: kişinin araç kutusundaki konumu +
aracın yörüngeden gelen hareket yönü. En öndeki kişi sürücüdür, arkadakiler yolcudur.
Bu kural aynalama testinde **hiç kayıp vermiyor** — sabit bir sol/sağ varsayımı yok.

**Karar 3 — Alan uyumu, veri miktarından önemli.**
Yarışmaya özel nesneler (`teknocan`, kabin içi hedefler) için açık veri seti yok.
6.000 harici görüntüyle eğittiğimiz ilk model, hedef görüntünün karanlığını öğrenemeyip
sahneyi ezberledi. Harici veriyi seyreltip **hedef alandan gelen kareleri ağırlıklandırınca**
model ayrımı öğrendi: `teknocan` mAP@0.5 = **0,995**, `bilgisayar` = **0,913**.

**Sonuç — değerlendirme ortamında ölçülen:**

| Ölçüt | Değer |
|---|---|
| Araç bilgisi (tip / plaka / renk) | **3/3 doğru** |
| Tespit F1 | **0,66** |
| Precision / Recall | 0,64 / 0,68 |
| Çalışma süresi | 99 sn (limit 600 sn) |

Yedi etiket türünde güvenilir üretim: `teknocan` 4/4 · `sigara_icme` 3/3 ·
`telefonla_konusma` 2/2 · `bilgisayar` 1/1 · `on_koltuk` 1/1 · `arka_koltuk_2` 11/12 ·
`su_icme` 1/2

## Slayt 5 — ⭐ Ezberlemediğimizin kanıtı (2 dk) — İKİNCİ KOZ

*"Elimizde etiketli tek video vardı. Ona ezberlemediğimizi nasıl bilebiliriz?"*

**(a) Bozulma testi** — aynı videoyu yapay olarak bozup ölçtük:

| Bozulma | F1 kaybı |
|---|---|
| Uzaklaştırma (×0,5) | **kazanç** |
| **Ayna (sol/sağ ters)** | **kazanç** |
| Karanlık | %5 |
| Parlaklık / bulanıklık | %6 |
| Gürültü | %17 |

Ayna testinde kayıp olmaması kritik: koltuk atamasını sabit "sol/sağ" varsayımına değil,
**aracın hareket yönüne** dayandırdığımızı kanıtlıyor.

**(b) Farklı araç/mekân** — 4 videoda araç bilgisi doğru:
kırmızı SUV `07BVB195` · beyaz hatchback `07AJL02` · siyah TOGG `34TC8532`

**(c) Parametre duyarlılığı** — eşik eğrisi yumuşak, uçurum yok; seçilen değer
kütüphane varsayılanı.

## Slayt 6 — 5G entegrasyonu (1,5 dk)
- **Number Verification:** SMS/OTP yok, doğrulama şebekeden; `client_id/secret` backend'de,
  mobil uygulamada değil.
- **Quality on Demand:** kritik durum (araç yaklaşıyor) → kalite yükselt → geçiş bitince
  **kaynağı bırak**. Musluk sürekli açık değil.

**Ölçtüğümüz etki** (kendi modellerimiz, gerçek video):

| | Bant genişliği | Plaka doğruluğu |
|---|---|---|
| QoD kapalı | 0,90 Mbps | **4/8 karakter** |
| **QoD açık** | 26,7 Mbps | **8/8 → 34TC8532** |

Fiziksel gerekçe: küçük hedeflerde çözünürlük belirleyicidir — bunu FTR'de de
nicel göstermiştik (512 px'de küçük nesne mAP≈0; tam çözünürlükte 0,995).

## Slayt 7 — Dürüst sınırlar (45 sn)
> Bu slaytı **atlamayın**. Jüri sınırlarını bilen ekibi ciddiye alır.

- 13 etiket türünden **7'sini** güvenilir üretiyoruz. Kemer ihlali ve sürücü baş
  hareketleri için domain-eşleşmeli veri yok — bunu **tahmin etmedik, ölçtük**:
  kemerli sürücüde bile hiçbir model bandı bulamadı, çünkü o çekim açısında göğüs
  bölgesi kadrajda değil.
- Düşük çözünürlükte (426×240) gürültü altında başarım düşüyor: bilgi tabanına yakınız.
- Yanlış tespit üretmemeyi kaçırmaya tercih ettik: denetim bağlamında yanlış ihlal
  bildirimi daha maliyetlidir.

## Slayt 8 — Kapanış (30 sn)
Üç cümle:
1. **Ölçüm altyapısı kurduk** — her tasarım kararı ground truth'a karşı puanlandı,
   hiçbir seçim sezgiyle yapılmadı.
2. **Genellemeyi kanıtladık** — bozulma testi, farklı araçlar ve duyarlılık analiziyle;
   çözüm tek bir videoya bağlı değil.
3. **Değerlendirme ortamında doğruladık** — araç bilgisi 3/3, tespit F1 0,66,
   süre bütçesinin altıda biri.

*"Her rakamın arkasında bir ölçüm, her ölçümün arkasında bir tasarım kararı var."*

---

## Sunum notları

- **Süre dağılımı:** 1–3 → 2 dk · **4–5 → 4 dk (en çok zaman buraya)** · 6 → 1,5 dk · 7–8 → 1,5 dk
- Slayt 4 ve 5 bizi ayıran kısım; oraya yatırım yapın.
- Ekran görüntüsü olarak kullanılabilecek hazır görseller:
  `reports/saglamlik*.json`, `reports/qod_ispat.json`, VM Web UI'da
  `EXECUTION COMPLETED – status: SUCCESS` ekranı.
- Soru gelirse hazır cevap: *"Neden F1 düşük?"* → "Her etiket için iki yönlü kanıt aradık:
  sınıf varken tespit ediliyor mu VE yokken susuyor mu. Geçemeyeni üretmedik.
  Ulaşılabilir tavanı 11 kat yükselttik: 0,06 → 0,66."
