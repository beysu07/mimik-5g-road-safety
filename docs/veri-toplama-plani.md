# 📹 MİMİK — Veri Toplama Planı

Yol kenarı **sabit kamera** senaryosuna domain-eşleşmeli video toplama rehberi.
Amaç: aşağıdaki eksikleri kapatacak gerçek görüntüleri toplamak.

## Neden? Eksikler ve hangi çekim doldurur
| Eksik / zayıf nokta | Şu an | Bunu dolduracak çekim |
|---|---|---|
| **yolcular** (ön/arka koltuk) | gürültülü / arka görünmez | **A) Yolcu konfigürasyonları** |
| **emniyet_kemeri_ihlali** | modelde var, tetiklenmiyor | **B) Kemersiz sürücü** |
| **sigara / su içme** | telefonla karışıyor | **C) Eylem ayrımı** |
| **slalom** | kodda var, test edilmedi | **D) Zikzak sürüş** |
| **teknocan / bilgisayar** | veri yok | **E) Panele nesne** |
| arkaya/etrafa bakma, esneme | yapılamıyor | F/G) Kafa/ağız |

## ⚙️ Kamera kurulumu (EN KRİTİK — buna uyulmazsa veri İŞE YARAMAZ)
- **Sabit kamera** (tripod/sehpa), ~1.5–2 m yükseklik, yol/otopark kenarı. **Elde tutma yok.**
- Araç kameraya **doğru gelip yanından geçsin** (önce ön cam, sonra yan cam görünsün) — örnek TOGG videolarındaki gibi.
- **Yavaş hız** (~5–15 km/h), araç ~3–5 m yakından geçsin (yolcular camdan net görünsün).
- **En yüksek çözünürlük** (4K varsa), yatay çekim. Plaka okunur olsun.

## 🎯 Senaryolar (öncelik sırasıyla — üstten yap)

### 🔴 P1 — EN KRİTİK
**A) Yolcu konfigürasyonları** (yolcular için tek çözüm):
`sürücü tek` · `+ön yolcu` · `+1 arka (sol)` · `+1 arka (sağ)` · `+2 arka` · `dolu (4 kişi)`
→ Her biri **3–5 geçiş**, **2 ışıkta** (gündüz + karanlık).

**B) Kemer ihlali:** Sürücü **kemersiz** (ön camdan görünür) birkaç geçiş + **kemerli** (negatif örnek).

### 🟡 P2 — Orta
**C) Eylem ayrımı:** Sürücü ayrı ayrı — `telefonla (kulağa)` · `sigara` · `su/içecek`. Net/abartılı, her biri birkaç geçiş.
**D) Slalom:** Araç **zikzak/yalpalayarak** geçsin, birkaç geçiş.

### 🟢 P3 — Bonus
**E) Nesneler:** `teknocan` + laptop **ön panele** konsun (camdan görünür).
**F) Kafa:** sürücü arkaya bakma / etrafa bakınma. **G) Esneme:** ağız açık.

## 🌦️ Genel kurallar
- **Işık:** gündüz + akşam + **KARANLIK** (örnekler karanlıktı — en önemli).
- Farklı yer/arka plan; mümkünse yağmur/sis; farklı araç varsa (tip çeşitliliği).

## 📁 Dosya adlandırma (etiketlemeyi 10× hızlandırır)
`karanlik_surucu+onyolcu_kemersiz_1.mp4` · `gunduz_slalom_1.mp4` · `karanlik_sigara_1.mp4`

## 📦 Ne kadar?
- **Minimum:** P1 (A+B), 2 ışık, ~4 geçiş ≈ **50 klip (~10 dk)**
- **İdeal:** P1+P2+P3, 3 ışık ≈ 80–100 klip
- **Kalite > miktar:** yolcular/eylem net görünsün, kamera **SABİT**.

## 📤 Bize ulaştırma
Ham videoları **Google Drive**'a koyup link paylaş (adlandırma yeterli). Kareler çıkarılıp
koltuk/eylem konumları etiketlenip model eğitilecek.
