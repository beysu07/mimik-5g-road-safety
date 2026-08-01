# Arac Tipi Veri Seti ve Dogruluk Test Plani

Bu plan FTR cikti formatindaki `arac_bilgisi.tip` alani icindir.

## 1. Yarismada Gecerli Tip Siniflari

Final JSON icin kabul edilen tipler:

- `sedan`
- `suv`
- `hatchback`
- `pickup`
- `minibus`
- `panelvan`
- `kamyon`

Not: `togg` bir govde tipi degil, marka/model bilgisidir. Model icinde ek sinif olarak tutulabilir; ancak final `results.json` icinde `tip: "togg"` yazmak risklidir. Togg T10X icin final tip buyuk ihtimalle `suv` olmalidir.

## 2. Su An Lazim Olanlar

1. CompCars klasor yolu
   - Web-nature full car image klasoru.
   - Model/type attribute dosyalari.
   - Varsa train/test split dosyalari.

2. Sinif map dosyasi
   - CompCars'in `type of car` bilgisini yarismadaki 7 sinifa cevirecek tablo.

3. Togg gorselleri
   - Togg ayri takip edilecekse en az 200-500 gorsel iyi baslangic olur.
   - Farkli aci, isik, renk, mesafe ve kamera kalitesi olmali.
   - Cogu Togg T10X ise final mapping `togg -> suv` olmalidir.

4. ROI karari
   - Arac tipi on cam ROI'den degil, tum arac govde ROI'sinden tahmin edilmeli.
   - Final pipeline: frame -> ana arac ROI/crop -> arac tipi classifier -> video boyunca majority vote.

5. Train/valid/test ayrimi
   - Oneri: %70 train, %15 valid, %15 test.
   - Test set egitimde hic kullanilmamali.
   - Mumkunse ayni arac/model gorselleri train ve test'e karisik dusmemeli.

## 3. Onerilen Klasor Yapisi

```text
datasets/
  raw/
    compcars/
    togg/
  processed/
    vehicle_type/
      train/
        sedan/
        suv/
        hatchback/
        pickup/
        minibus/
        panelvan/
        kamyon/
      valid/
      test/
```

Eger `togg` ic sinif olarak tutulacaksa:

```text
datasets/processed/vehicle_type_internal/
  train/
    sedan/
    suv/
    hatchback/
    pickup/
    minibus/
    panelvan/
    kamyon/
    togg/
```

Final cikti asamasinda:

```text
togg -> suv
```

## 4. Dogruluk Nasil Test Edilecek?

### Goruntu Bazli Test

Test klasorundeki her gorsel icin:

1. Model tahmin yapar.
2. Tahmin edilen sinif, klasor adindaki gercek sinifla karsilastirilir.
3. Asagidaki metrikler hesaplanir:
   - accuracy
   - per-class precision
   - per-class recall
   - per-class F1
   - confusion matrix

Accuracy formulu:

```text
dogru_tahmin_sayisi / toplam_test_gorseli
```

FTR icin sadece accuracy yetmez; siniflar dengesiz olabilecegi icin `macro_f1` de rapora yazilmali.

### Video Bazli Test

Yarismadaki asil calisma sekli video oldugu icin ayrica video testi yap:

1. Videodan her 0.5 veya 1 saniyede bir frame al.
2. Ana arac ROI'sini crop et.
3. Her crop icin tip tahmini yap.
4. Video/track sonunda majority vote uygula.
5. Son `arac_bilgisi.tip` degerini gercek etiketle karsilastir.

Ornek:

```text
frame tahminleri: suv, suv, sedan, suv, suv
video sonucu: suv
```

## 5. Raporlanacak Sonuc Tablosu

```text
model,dataset,test_split,accuracy,macro_f1,sedan_recall,suv_recall,hatchback_recall,pickup_recall,minibus_recall,panelvan_recall,kamyon_recall,not
vehicle_type_v1,compcars+togg,test,0.00,0.00,,,,,,,,ilk test
```

## 6. Kritik Uyarilar

- Stanford Cars gibi marka/model veri setleri direkt tip sinifi degildir; mapping gerektirir.
- CompCars iyi kaynak ama yarisma videolari yol kenari/kamera acisi oldugu icin testte ROI crop kullanmak gerekir.
- `togg` sinifi final JSON'a direkt yazilmamalidir; cikti formatindaki resmi siniflardan birine map edilmelidir.
- En dusuk performans gosteren siniflar icin ekstra veri eklenmelidir. Genelde `panelvan`, `minibus`, `kamyon` ve `pickup` daha az ve daha karisik olur.
