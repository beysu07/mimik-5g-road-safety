# Veri Alanı Analizi — Hedef Görüntümüz ve Veri Seti Kriterleri

> Amaç: Veri seti seçimini "göz kararı" olmaktan çıkarıp **ölçülebilir kriterlere**
> bağlamak. Faz2 videosunun sayısal parmak izini çıkardık; artık her aday set
> objektif olarak yargılanabilir.

## 1. Hedef alanımızın ölçülmüş parmak izi

`yolo11s` ile tüm video taranarak (0,5 sn aralıkla) ölçüldü:

| Ölçüt | 1080p | 240p |
|---|---|---|
| Araç kutusu (medyan) | 764 × 594 px | 170 × 131 px |
| Araç kutusu (aralık) | 110×120 → 1217×739 | 24×28 → 270×165 |
| En/boy oranı | 0,67 – 1,70 (medyan **1,35**) | aynı |
| **Kişi kutusu (medyan)** | **91 × 90 px** | **24 × 26 px** |
| Kişi kutusu (aralık) | 23×38 → 350×413 | 7×13 → 81×89 |
| **Kabin parlaklığı (0–255)** | **medyan 20** | **medyan 20** |

## 2. Bu sayılar ne anlama geliyor

**(a) Kabin neredeyse karanlık.** Medyan parlaklık **20/255** — dinamik aralığın %8'i.
Tipik sürücü izleme veri setleri aydınlık kabinlerde çekilir (kabaca 100–180 bandı).
Aramızda **5–9 kat parlaklık farkı** var. Bir modelin aydınlık kabinde öğrendiği doku ve
kontrast ipuçları burada fiziksel olarak yok.

**(b) Sürücü çok küçük.** Medyan kişi kutusu 1080p'de **91×90 px**, 240p'de **24×26 px**.
Emniyet kemeri bandı gövde genişliğinin kabaca %8–10'u kadardır:
- 1080p'de yaklaşık **7–9 piksel** genişliğinde bir çizgi
- 240p'de yaklaşık **2 piksel** → pratikte alt-piksel

Karanlıkla birleşince kemer bandı **tespit edilebilir bir yapı olmaktan çıkıyor**.

**(c) Bakış açısı karışık.** En/boy oranı 0,67–1,70 arasında geziniyor: araç bazen
önden/arkadan (≈1), bazen yandan (>1,6) görünüyor. Tek bir sabit açı varsayımı yapılamaz.

## 3. Ölçümlerimizi bu tablo açıklıyor

| Gözlem | Açıklaması |
|---|---|
| Kemer modelleri hiç ateşlemiyor (2.123 örnekli olan dahil) | Band 7–9 px + parlaklık 20/255 |
| COCO `bottle` / `cell phone` **0 tespit** | Nesneler kişiden daha küçük, camın ardında |
| Kendi `arka_koltuk` sınıfımız 0/13 | 112 görüntülük set bu karanlığı hiç görmedi |
| **COCO `person` 10/13 çalışıyor** | 91×90 px bir kişi dedektörü için **yeterli** |
| 240p gürültüde %68 kayıp | Kişi 24×26 px — bilgi tabanına yakınız |

**Sonuç:** Başarısızlıklarımız model seçimi hatası değil; **hedefin fiziksel boyutu ve
aydınlatması** ile ilgili. Kişi ölçeğindeki hedefler çalışıyor, kişiden küçük hedefler
çalışmıyor.

## 4. Bir veri setinin işimize yaraması için kriterler

Aday set şu üç şartı **birlikte** sağlamalı:

| # | Kriter | Neden |
|---|---|---|
| 1 | **Dış/ön cam görüşü** (kabin içi kamera DEĞİL) | Cam yansıması + açı |
| 2 | **Düşük aydınlatma** (kabin parlaklığı ~20–60/255) | 5–9 kat fark kapanmalı |
| 3 | **Sürücü bölgesi ≤ ~150 px** | Büyük/yakın çekim öğrenilen ipuçları bize taşınmaz |

Ek olarak: sınıf başına en az birkaç yüz örnek, **iki yönlü** (hem ihlal hem ihlal-yok).

## 5. Aday setlerin bu kriterlere göre değerlendirmesi

| Set | (1) Dış görüş | (2) Karanlık | (3) Küçük hedef | Karar |
|---|---|---|---|---|
| ADMS (MDPI 2025) — kemer 760, sigara 570, esneme 550 | ⚠️ doğrulanmadı | ⚠️ | ⚠️ | **Tek ciddi aday** |
| Zenodo 14908802 (7.286) | ❌ araç içi telefon çekimi | ❌ | ❌ | Elendi |
| Roboflow seatbelt-detection (7.365) | ⚠️ | ❓ | ❓ | Erişilemiyor |
| SVIRO (arka koltuk) | ❌ kabin içi + sentetik | ❌ | ❌ | Elendi |
| YawDD / DMD / State Farm / AUC | ❌ kabin içi | ❌ | ❌ | Elendi |
| `seatbelt_windshield` (bizde) | ✅ | ❌ aydınlık | ❌ yakın çekim | Zayıf (82 örnek) |
| `phone_merged` (bizde, 2.123 kemer) | ✅ | ❌ aydınlık | ❌ yakın çekim | **Ölçüldü: çalışmıyor** |

**Kritik gözlem:** Elimizdeki `phone_merged` seti 1. kriteri sağlıyor ve 2.123 örneği var
— yine de çalışmadı. Demek ki **(1) tek başına yetmiyor**; (2) ve (3) belirleyici.

## 6. Stratejik sonuç

**A. Kişi ölçeğinde kal.** Ölçüm net: kişi boyutundaki hedefler çalışıyor, altındakiler
çalışmıyor. Yolcu/koltuk tespitini bu yüzden kazandık. Aynı ölçekte kalan başka etiket
varsa oraya yatırım yapılmalı.

**B. Kişiden küçük hedefler için tek yol: aynı koşullarda çekilmiş veri.**
`teknocan` (sarı maskot, yüksek kontrast) bu yüzden hâlâ mümkün — sarı, karanlıkta
belirgin ve ön panelde büyükçe duruyor. `bilgisayar` da benzer.
Kemer bandı ise ne büyük ne kontrastlı → en zoru.

**C. Aydınlık veri setiyle eğitmek işe yaramaz** — ölçtük. Kullanılacaksa **karanlık
artırma** (brightness/gamma augmentation) ile alan uyarlaması yapılmalı; ham hâliyle
transfer olmuyor.

**D. Yeni veri toplanacaksa** hedef: **kabin parlaklığı ~20/255, sürücü ≤150 px, dış açı.**
Bu üç sayı, çekim yaparken kontrol edilebilir somut kriterlerdir.

## 7. Sıradaki somut adımlar

1. **ADMS setini doğrula** — 3 kriteri sağlıyor mu? Sağlıyorsa kemer/sigara/esneme için
   gerçek çözüm; sağlamıyorsa liste tükendi demektir.
2. **`teknocan` + `bilgisayar`** — kriterlere uyan tek "kendi verimiz" işi, 114 kare hazır.
3. **Karanlık artırma denemesi** — `phone_merged`'i gamma/parlaklık augmentasyonuyla
   yeniden eğitip kemerin ateşleyip ateşlemediğini ölçmek. Ucuz ve C maddesini test eder.
