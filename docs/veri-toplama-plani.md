# 📹 MİMİK — Veri Toplama Planı

Yol kenarı **sabit kamera** senaryosuna domain-eşleşmeli video toplama rehberi.

## Eksikler ve hangi çekim doldurur (öncelik sırasıyla)
| Öncelik | Eksik / hedef | Bunu dolduracak çekim |
|---|---|---|
| 🔴 P1 | **Güçlü etiketleri sağlamlaştır** (tip/renk/plaka/telefon, değişken koşul) | **A) Çeşitli koşullarda geçişler** |
| 🔴 P1 | **emniyet_kemeri_ihlali** (model var, tetiklenmiyor) | **B) Kemersiz sürücü** |
| 🟡 P2 | sigara / su (telefonla karışıyor) | C) Eylem ayrımı |
| 🟡 P2 | slalom (kodda var, test edilmedi) | D) Zikzak sürüş |
| 🟢 P3 | yolcular (ön=zor, arka=büyük ölçüde görünmez) | E) Yolcu konfigürasyonları |
| 🟢 P3 | teknocan / bilgisayar / kafa / esneme | F/G) Nesne, kafa, ağız |

> Not: yolcular **ikincil** — arka koltuk dış kameradan ticari sistemlerde bile zor görünür.
> Asıl kesin getiri **çeşitlilik (sağlamlık) + kemer.**

## ⚙️ Kamera kurulumu (EN KRİTİK — buna uyulmazsa veri İŞE YARAMAZ)
- **Sabit kamera** (tripod/sehpa), ~1.5–2 m yükseklik, yol/otopark kenarı. **Elde tutma yok.**
- Araç kameraya **doğru gelip yanından geçsin** (önce ön cam, sonra yan cam) — örnek TOGG videolarındaki gibi.
- **Yavaş hız** (~5–15 km/h), araç ~3–5 m yakından geçsin. **En yüksek çözünürlük** (4K), yatay. Plaka okunur olsun.

## 🎯 Senaryolar (öncelik sırasıyla — üstten yap)

### 🔴 P1 — Kesin getiri
**A) Çeşitli koşullarda normal geçişler** (güçlü etiketleri sağlamlaştırır):
Araç **normal sürüşle** kameradan geçsin — **gündüz + akşam + KARANLIK**, **farklı yer/arka plan**, mümkünse **farklı araç/renk**. → tip/renk/plaka/telefon’u eval’in değişken koşullarına hazırlar.

**B) Kemer ihlali:** Sürücü **kemersiz** (ön camdan görünür) birkaç geçiş + **kemerli** (negatif örnek). → Kemer modelini bizim domain’de çalıştırır.

### 🟡 P2 — Orta
**C) Eylem ayrımı:** Sürücü ayrı ayrı — `telefonla (kulağa)` · `sigara` · `su/içecek`. Net/abartılı.
**D) Slalom:** Araç **zikzak/yalpalayarak** geçsin.

### 🟢 P3 — İkincil (getiri belirsiz)
**E) Yolcu konfigürasyonları:** `+ön yolcu` · `+arka` · `dolu`. (Ön koltuğu netleştirir; arka koltuk büyük ölçüde görünmez.)
**F) Nesneler:** teknocan + laptop ön panele. **G)** kafa çevirme / esneme.

## 🌦️ Genel kurallar
- **Işık:** gündüz + akşam + **KARANLIK** (örnekler karanlıktı — en önemli).
- Farklı yer/arka plan; mümkünse yağmur/sis; farklı araç varsa.

## 📁 Dosya adlandırma (etiketlemeyi 10× hızlandırır)
`karanlik_normal_1.mp4` · `karanlik_kemersiz_1.mp4` · `gunduz_slalom_1.mp4` · `aksam_onyolcu_1.mp4`

## 📦 Ne kadar?
- **Minimum:** P1 (A+B), 3 ışık (gündüz/akşam/karanlık), ~4 geçiş ≈ **40–50 klip (~8 dk)**
- **İdeal:** + P2/P3 ≈ 70–90 klip
- **Kalite > miktar:** hedef net görünsün, kamera **SABİT**.

## 📤 Bize ulaştırma
Ham videoları **Google Drive**'a koyup link paylaş (adlandırma yeterli). Kareler çıkarılıp etiketlenip model eğitilecek.
