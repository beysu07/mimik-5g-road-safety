# Veri Seti Araştırması — Sonuçlar ve Strateji

> Problem: Senaryomuz **dışarıdan, ön camdan** bakan sabit kamera. Açık veri setlerinin
> neredeyse tamamı **araç içi (kabin/dashcam)** kameradan. Bu alan farkı FTR'de bizi
> çarpmıştı ve şimdi `emniyet_kemeri_ihlali`, `sigara_icme`, `su_icme`, `esneme` gibi
> etiketlerde tekrar karşımıza çıkıyor.

## Ölçülmüş engel

| Model | Eğitim verisi | faz2'de sonuç |
|---|---|---|
| `seatbelt.pt` — `no seat-belt` | 82 örnek | ❌ Hiç ateşlemiyor |
| `phone_merged` — `seatbelt` | 2.123 örnek | ❌ **Kemerli sürücüde bile** ateşlemiyor (`deneme_2` ile test edildi) |
| `self_actions_hd` — `arka_koltuk` | 112 görüntü | ❌ 13 referans anında 0/13 |
| **COCO `person`** (hazır) | milyonlar | ✅ **10/13** |

**Çıkarılan ders:** Küçük ve alan-uyumsuz setlerle eğitilen özel sınıflar bu görüntüde
çalışmıyor; büyük ve genel modeller çalışıyor. Strateji buna göre kurulmalı.

## Aday veri setleri (durum)

| Set | Sınıflar / boyut | Durum |
|---|---|---|
| **ADMS (MDPI 2025)** | kemer 760 · sigara 570 · esneme 550 · telefon 1.900 (toplam 4.966) | ⚠️ **En umut verici** — bakış açısı ve indirilebilirliği **doğrulanmadı** |
| Zenodo 10.5281/zenodo.14908802 | 7.286 görüntü, safe driving / texting / turning | ❌ Araç içi cep telefonu çekimi, sınıflar uymuyor |
| traffic-violations/seatbelt-detection (Roboflow) | 7.365 görüntü, `person-noseatbelt`/`person-seatbelt`/`windshield` | ❌ **Link açılmıyor**, doğrulanamadı |
| SVIRO | Arka koltuk doluluk | ❌ Kabin içi + sentetik |
| YawDD / DMD / State Farm / AUC | Esneme, dikkat dağınıklığı | ❌ Hepsi kabin içi |
| HOV/HOT şerit denetimi veri setleri | Tam bizim açımız | ❌ Akademik/ticari, halka kapalı |

## Literatürden strateji (bizi doğruluyor)

Ön camdan sürücü davranışı tespiti üzerine güncel çalışmalar **iki aşamalı** yaklaşım
kullanıyor: önce ön cam bölgesi tespit edilir, sonra sürücü bölgesi kırpılıp davranış
sınıflandırılır. Bizim mimarimiz zaten bu (araç → kabin ROI → analiz), yani yön doğru.

Ayrıca gece/parlama literatüründe standart ön işlemeler: yüksek yoğunluk haritalama ile
parlama bastırma + düşük ışık iyileştirme. Bizde CLAHE var; **ROI'ye özel parlama
bastırma denenmedi** — 240p kırılganlığı için de aday bir önlem.

## Strateji önerisi (öncelik sırasıyla)

**1. Hazır güçlü modellerden azami fayda** — kanıtlanmış yol.
COCO `person` ile yolcu tespitinde 0/13 → 10/13 sıçraması bunu gösterdi. Aynı mantık
başka etiketlere de uygulanabilir mi, ölçülmeli (ör. `cell phone`, `bottle` COCO sınıfları
araç kutusu içinde aranabilir — hazır ve büyük veriyle eğitilmiş).

**2. Yarışmaya özel nesneler için kendi verimiz** — `teknocan` ve `bilgisayar`.
Açık set olması zaten mümkün değil; 114 kare hazır, etiketleme bekliyor. **En kesin kazanç.**

**3. ADMS setini doğrula** — bakış açısı dış/ön cam ise `emniyet_kemeri_ihlali`,
`sigara_icme` ve `esneme` için gerçek çözüm olur. MDPI makalesinden veri erişim
bilgisi çıkarılmalı.

**4. Vazgeçilecekler** — dengeli veri bulunamazsa `emniyet_kemeri_ihlali` ve
`sigara/su` zorlanmamalı. FTR'de zorlamanın zarar verdiğini ölçmüştük: sistem
kemerli sürücüye de ihlal basar, precision çöker.

## Değişmez kural

Bir etiketi üretmeden önce **iki yönlü kanıt** aranacak: sınıf varken tespit ediliyor mu
*ve* sınıf yokken tespit edilmiyor mu. Kemer testinde ikinci koşul sağlanıyordu ama
birincisi sağlanmadı (kemerli sürücüde de bulamadı) → bu yüzden kullanılmadı.
