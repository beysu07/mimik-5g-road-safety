# Eksik Sınıflar için Veri Kaynağı Planı

> İlke: **tek videoya (faz2) dayanmak ezberlemedir.** Her sınıf için mümkün olduğunca
> açık kaynak + kendi verimiz karıştırılacak; faz2 yalnız *doğrulama* ve *alan uyumu*
> için kullanılacak.
>
> ⚠️ **Kritik filtre:** Açık veri setlerinin çoğu **araç içi (dashcam/kabin) kamera**
> içerir. Bizim senaryomuz **dışarıdan, ön camdan** bakan sabit kameradır. FTR'de tam
> bu yüzden çakılmıştık (jenerik modeller TOGG dağılımında yanlış-pozitif verdi).
> Bu yüzden **yalnız dış açı / ön camdan görüş** içeren setler alınacaktır.

## Sınıf bazlı durum

| Sınıf | GT payı | Açık veri | Karar |
|---|---|---|---|
| `emniyet_kemeri_ihlali` | %12 (4) | ✅ **Tam uyumlu set var** | Açık set + faz2 |
| `arka_koltuk_2` | **%35 (12)** | ❌ **Dış açıdan açık set YOK** | Kendi verimiz + faz2 |
| `teknocan` | %12 (4) | ❌ yarışmaya özel nesne | Yalnız faz2 (88 kare hazır) |
| `esneme` | %3 (1) | ⚠️ var ama **kabin içi** | Düşük öncelik |
| `arkaya_bakma` / `etrafa_bakinma` | %6 (2) | ⚠️ var ama **kabin içi** | Düşük öncelik |

---

## 1. `emniyet_kemeri_ihlali` — açık set BULUNDU ✅

**Seatbelt Detection (traffic-violations, Roboflow Universe)**
- **7.365 görüntü**, sınıflar: `seatbelt`, `person-noseatbelt`, `person-seatbelt`, `windshield`
- Yayınlanan başarım: mAP@50 %87,3 · P %86,1 · R %83,6
- **Ön cam/dış görüş için tasarlanmış** → bizim senaryoyla uyumlu
- https://universe.roboflow.com/traffic-violations/seatbelt-detection-esut6

Neden önemli: mevcut `seatbelt.pt` modelimiz faz2'de `no seat-belt` sınıfını **hiç**
üretmiyor (`conf>=0.10`'da bile). `person-noseatbelt` / `person-seatbelt` ikilisi
doğrudan aradığımız ayrım.

Elimizdeki tamamlayıcılar: `datasets/seatbelt_windshield`, `datasets/Phone`+`Phone_2`
(`seatbelt`/`windshield` sınıfları içeriyor), `Self_v2/seatbelt`.

## 2. `arka_koltuk_2` — açık set YOK ❌ (en büyük kalem)

Aramada çıkanlar bizim açımıza **uymuyor**:
- **SVIRO** — arka koltuk doluluk seti ama **kabin içi + sentetik** (araç içine monte kamera)
- HOV/HOT şerit denetim çalışmaları — tam bizim açımız (yol kenarı, ön camdan) fakat
  veri setleri **akademik/ticari, halka açık değil**; yalnız makale/patent düzeyinde

Sonuç: bu sınıf için **kendi verimizi kullanmak zorundayız**. İyi haber: elimizde var —
- `datasets/Yeni/IMG_*.MOV` → **36 kendi çekimimiz**, dış açı, arka koltukta yolcu içerenler
- `datasets/Self_v2` → `arka_koltuk` etiketli kareler (sol/sağ ayrımı yok)
- faz2 → 12 GT anı

**Yapılacak:** Self_v2 + Yeni videolarından kare çıkar, arka koltuğu **sol/sağ ayırarak**
etiketle. Böylece `arka_koltuk_1` / `arka_koltuk_2` ayrımı öğrenilir.
⚠️ Hangi tarafın `_1` hangisinin `_2` olduğu belgelerde yazmıyor → **3 Ağustos toplantısında sorulacak.**

## 3. `teknocan` — yarışmaya özel

Açık set olamaz (TEKNOFEST maskotu). Faz2'den **80 kare + 8 negatif** çıkarıldı
(`datasets/faz2_etiketlenecek/`, hem 1080p hem 240p). Fiziksel nesne olduğu için
görünümünü öğrenmek **genelleşir**; sadece görünme anlarını ezberlememek gerekir.

## 4. Sürücü davranışları (esneme / arkaya_bakma / etrafa_bakinma)

Açık setler mevcut (YawDD, DMD, State Farm/AUC Distracted Driver) **ancak hepsi kabin
içi kameradan**. Bizim dış açımızda sürücünün yüzü karanlık camın ardında ve küçük.
Alan farkı çok büyük — FTR'deki sigara/su hatasını tekrarlama riski yüksek.

**Karar: düşük öncelik.** Toplam GT payı %9 (3 olay). Diğer üçü bitmeden başlanmayacak.

---

## Uygulama sırası

1. **Kemer:** açık seti indir → mevcut kemer verimizle birleştir → faz2 kareleriyle
   alan uyumu ekle → eğit → ölç (**hem 1080p hem 240p**)
2. **arka_koltuk_2:** Self_v2 + Yeni videolarından kare çıkar → sol/sağ etiketle → eğit
3. **teknocan:** hazır 88 kareyi etiketle → eğit (küçük set, hızlı)
4. Her adımdan sonra: `scripts/faz2_degerlendir.py` + `scripts/saglamlik_testi.py`

## Değişmez kural

Hiçbir model **yalnız faz2** ile eğitilmeyecek (teknocan zorunlu istisna). Eğitimde
augmentasyon (parlaklık/ölçek/bulanıklık/gürültü) uygulanacak — modelin o otoparkın
ışığını ezberlememesi için.
