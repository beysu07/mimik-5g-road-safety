# Faz2 Taban Ölçümü ve Teşhis (29 Tem 2026)

## Taban skor (mevcut hat, hiç değişiklik yapılmadan)

| | 1080p | 240p |
|---|---|---|
| Süre | **99 sn** (limit 600) ✓ | 63 sn ✓ |
| arac_bilgisi | **3/3 doğru** (suv/34TC8532/siyah) | 2/3 (plaka `41C8522` yanlış) |
| Tespit | 2 üretildi (GT: 34) | 2 üretildi |
| **F1** | **0.06** (TP=1, FN=33, FP=1) | **0.06** |

## Kök nedenler (ölçülerek doğrulandı)

**1. Tek-geçiş varsayımı.** Hat 8 sn'lik tek araç geçişi için tasarlandı; etiket başına
**tek olay** üretiyor. GT ise 114 sn'de **34 olay** bekliyor (arka_koltuk_2 12 kez,
teknocan 4, emniyet_kemeri_ihlali 4, sigara 3...). Desteklediğimiz etiketlerde bile
1/4, 1/3 üretiyoruz.

**2. Küresel oran eşiği 114 sn'de çöküyor.** `_emit_actions` şartı
`gözlem/toplam_kare >= oran`. Toplam kare 779 → `telefonla_konusma` 70 gözlem =
oran 0.090 < eşik 0.15. Kısa süreli olaylar matematiksel olarak elenemez hâle geliyor.
Üstelik koşudan koşuya sınırda gidip geliyor (**kararsız**).

**3. Modeller bu videoda çok düşük güven veriyor (alan farkı).**
Düşük ışık + yan açı + uzak mesafe. `conf>=0.10` ile ölçüm:

| Model | Bu videoda ne görüyor |
|---|---|
| Kemer (`seatbelt.pt`) | Yalnız `0ar` (0.15–0.86). Aradığımız `no seat-belt` **hiç çıkmıyor** → `emniyet_kemeri_ihlali` hep 0 |
| Kabin (`self_actions_hd.pt`) | Ağırlıkla `on_koltuk_1` (0.1–0.43) — bunu hiçbir şeye **eşlemiyoruz**. `arka_koltuk` 0.15, `on_koltuk_2` 0.12 → eşiğimiz **0.40**, hepsi altında |

**4. Sınıf eşleme boşluğu.** `on_koltuk_1` (sürücü koltuğu) modelde var ama çıktıya
bağlanmamış. GT'de `arka_koltuk_2` 12 kez var; modelde `arka_koltuk_2` sınıfı **yok**.

## Sonuç

Sorun "5 sınıf eksik" değil; **üç katmanlı**: (a) olay üretim mantığı (tek olay →
epizodik), (b) eşikler (küresel oran → yerel pencere), (c) alan farkı (bu videonun
kareleriyle fine-tune). Şartname zaten bunu söylüyor: *"İki çözünürlükteki video ve
ground truth'u kullanarak çözümünüzü fine-tune etmeniz beklenmektedir."*

## İyi haber

- `arac_bilgisi` 1080p'de **3/3** — %50'lik kalemin bir kısmı zaten sağlam
- Süre limiti rahat (99 sn / 600 sn)
- GT **zaman damgalı** → eksik sınıfların nerede olduğunu biliyoruz, kör arama yok
