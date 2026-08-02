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

## Slayt 4 — ⭐ Ölçülmüş iyileşme yolculuğu (2 dk) — SUNUMUN KALBİ

Faz2 videosu + ground truth ile her adım ölçüldü:

| Adım | Ne değişti | F1 |
|---|---|---|
| Taban | FTR'den gelen hat | **0,06** |
| 1 | Epizodik olay üretimi | 0,14 |
| 2 | Kişi tespiti + geometrik koltuk ataması | 0,31 |
| 3 | Epizotların araç geçişlerine hizalanması | 0,40 |
| 4 | "En öndeki kişi sürücüdür" düzeltmesi | **0,47** |

**~8 kat iyileşme — tek bir model eğitmeden.**

Anlatılacak üç teşhis (hepsi ölçümle bulundu):
1. **Tek-geçiş varsayımı:** hat 8 sn'lik video için tasarlanmıştı, etiket başına tek olay
   üretiyordu; 114 sn'de 34 olay bekleniyordu.
2. **Küresel oran eşiği çöküyordu:** `gözlem/toplam_kare ≥ oran` — video uzadıkça kısa
   olaylar matematiksel olarak eşiği geçemez hâle geliyordu.
3. **Kendi eğittiğimiz koltuk sınıfı kördü:** 13 referans anında **0/13**;
   hazır COCO kişi tespiti aynı anlarda **10/13**. → Özel sınıfı bırakıp
   kişi tespiti + geometri kullandık.

## Slayt 5 — ⭐ Ezberlemediğimizin kanıtı (2 dk) — İKİNCİ KOZ

*"Elimizde etiketli tek video vardı. Ona ezberlemediğimizi nasıl bilebiliriz?"*

**(a) Bozulma testi** — aynı videoyu yapay olarak bozup ölçtük:

| Bozulma | F1 kaybı |
|---|---|
| Uzaklaştırma (×0,5) | **kayıp yok** |
| **Ayna (sol/sağ ters)** | **kayıp yok** |
| Bulanıklık | %6 |
| Parlaklık / karanlık | %9–10 |
| Gürültü | %18 |

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

- Şu an 13 etiket türünden 3'ünü güvenilir üretiyoruz; `teknocan`, kemer ihlali ve
  sürücü baş hareketleri için **domain-eşleşmeli veri gerekiyor** — kaynağı biz belirledik,
  eğitim planı hazır.
- Düşük çözünürlükte (426×240) gürültü altında başarım düşüyor: bilgi tabanına yakınız.
- Yanlış tespit üretmemeyi kaçırmaya tercih ettik: denetim bağlamında yanlış ihlal
  bildirimi daha maliyetlidir.

## Slayt 8 — Kapanış (30 sn)
Üç cümle:
1. Ölçüm altyapısı kurduk: her değişiklik **ground truth'a karşı** puanlandı.
2. İyileşmeyi kanıtladık: **0,06 → 0,47**, model eğitmeden, mimari düzeltmelerle.
3. Genellemeyi kanıtladık: bozulma, farklı araç ve duyarlılık testleriyle.

*"Sonucumuz mükemmel değil; ama her rakamın arkasında bir ölçüm var."*

---

## Sunum notları

- **Süre dağılımı:** 1–3 → 2 dk · **4–5 → 4 dk (en çok zaman buraya)** · 6 → 1,5 dk · 7–8 → 1,5 dk
- Slayt 4 ve 5 bizi ayıran kısım; oraya yatırım yapın.
- Ekran görüntüsü olarak kullanılabilecek hazır görseller:
  `reports/saglamlik*.json`, `reports/qod_ispat.json`, VM Web UI'da
  `EXECUTION COMPLETED – status: SUCCESS` ekranı.
- Soru gelirse hazır cevap: *"Neden F1 düşük?"* → "13 etiketin 10'u için domain-eşleşmeli
  veri yok; hangi verinin gerektiğini ölçtük ve kaynaklarını belirledik. Elimizdekiyle
  ulaşılabilir tavanı 8 kat yükselttik."
