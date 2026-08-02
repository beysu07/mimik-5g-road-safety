# Ezberleme (Overfitting) Denetimi

> Soru: Elimizde etiketli **tek video** (faz2) var. Final günü farklı bir video gelecek.
> Yaptığımız iyileştirmeler o videoda da işe yarayacak mı, yoksa bu sahneye mi ezberledik?

## 1. Karar karar denetim

| Bileşen | Nasıl seçildi | Ezberleme riski |
|---|---|---|
| Epizodik olay üretimi | Şartname semantiği ("görülebilir olduğu an") | 🟢 Yok |
| Epizot sınırı = görünürlük kesintisi | Saf geometri | 🟢 Yok |
| Geçiş sınırı = araç genişliğinin yerel minimumu | Saf geometri | 🟢 Yok |
| **Yolcu tespiti = COCO `person`** | Hazır model (milyonlarca görüntü) | 🟢 Yok — bizim verimizle eğitilmedi |
| Koltuk ataması = konum + hareket yönü | Geometri; **ayna testini geçti** | 🟢 Yok |
| En öndeki kişi = sürücü | Fiziksel gerçek | 🟢 Yok |
| `PERSON_CONF = 0.25` | faz2'de en iyi **ve** Ultralytics varsayılanı | 🟢 Düşük |
| `EPIZOT_ARASI = 6.0` | **Ölçüldü: hiç bağlayıcı değil** (6 ↔ 1000 aynı sonuç) | 🟢 Yok |
| `CONF_CABIN = 0.20` | faz2 süpürmesi | 🟢 Düşük (model zaten ateşlemiyor) |
| `MIN_GOZLEM`, `GECIS_MIN_ARA`, slalom pencereleri | Sezgisel | 🟡 Orta (duyarlılığı ölçülmedi) |
| **`ARKA_KOLTUK_ETIKET = 'arka_koltuk_2'`** | **faz2 GT'sinde 12'ye 1** | 🔴 **YÜKSEK** |

## 2. Kanıt: farklı araç / farklı mekân

GT olmadan da "saçmalıyor mu" bakılabilir. Dört farklı videoda:

| Video | tip | plaka | renk | Tespit sayısı |
|---|---|---|---|---|
| deneme_1 (kırmızı SUV) | suv | 07BVB195 | kirmizi | 1 |
| deneme_3 (beyaz hatchback) | hatchback | 07AJL02 | beyaz | 2 |
| deneme_4 (kırmızı SUV) | suv | 07BVB195 | kirmizi | 2 |
| video_1 (siyah TOGG) | suv | 34TC8532 | siyah | 1 |

**Okuma:** Araç bilgisi dördünde de doğru/makul — ezberlemiş bir sistem hepsine
`34TC8532`/`siyah` derdi. Tespit sayıları da makul; halüsinasyon patlaması yok.

## 3. Kanıt: bozulma (perturbasyon) testi

Aynı video yapay olarak bozulup ölçüldü (`scripts/saglamlik_testi.py`).
Sahneye ezberlenmiş bir ayar küçük bozulmada çöker.

Kişi-tespiti mimarisine geçtikten sonraki ölçüm (1080p):

| Bozulma | F1 | Kayıp |
|---|---|---|
| temiz | 0,31 | — |
| bulanık / ayna | 0,31 | %0 |
| parlak | 0,30 | %4 |
| karanlık | 0,27 | %11 |
| uzak (×0,5) | 0,35 | **kazanç** |
| gürültü | 0,41 | **kazanç** |

Önceki mimaride en kötü kayıp %32'ydi; yeni mimaride **%11**. Özellikle **ayna testinde
hiç kayıp olmaması** kritik: sol/sağ sabit varsayımı yapmadığımızı, koltuk atamasının
hareket yönünden türetildiğini doğruluyor.

## 4. Kanıt: parametre duyarlılığı

`PERSON_CONF` süpürmesi (faz2 1080p, ±5 sn):

| 0,15 | 0,20 | **0,25** | 0,35 |
|---|---|---|---|
| 0,39 | 0,43 | **0,47** | 0,38 |

Eğri **yumuşak**, uçurum yok. Seçilen değer aynı zamanda kütüphane varsayılanı.

## 5. Kalan tek ciddi risk ve azaltma planı

**`arka_koltuk_1` / `arka_koltuk_2` konvansiyonu hiçbir belgede yazmıyor.**
Şu an sabit olarak `arka_koltuk_2` üretiyoruz (faz2'de 12'ye 1 olduğu için). Final
videosunda yolcu diğer arka koltuktaysa bu etiketten gelen **14 doğru tespit sıfırlanır**
(F1 ~0,47 → ~0,15).

**Azaltma:**
1. **3 Ağustos toplantısında sor** — kesin çözüm.
2. Cevap gelmezse: kişinin araç içindeki yanal konumundan türet; sabit varsayımı bırak.
   Ayna testi bu mantığın çalıştığını gösteriyor. Eşleme tek satırdır
   (`ARKA_KOLTUK_ETIKET` env değişkeni).

## 6. Değişmez kurallar

- Hiçbir eşik yalnız faz2-1080p'ye bakılarak seçilmeyecek; en az iki koşulda tutarlı olmalı.
- Zaman damgaları asla koda gömülmeyecek — yalnız görsel örüntü öğrenilecek.
- Model eğitimi yapılırsa augmentasyon (parlaklık/ölçek/bulanıklık) zorunlu.
- Her değişiklikten sonra: `faz2_degerlendir.py` **ve** `saglamlik_testi.py`.
