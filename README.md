# MIMIK - FTR Cikarim Sistemi

Bu depo, TEKNOFEST 2026 5G ve Yapay Zeka ile Akilli Yol Guvenligi Yarismasi
FTR formati icin bir videodan konsolide `results.json` ureten cevrimdisi cikarim
hattini icerir.

## Uretilen bilgiler

- Arac: `tip`, `plaka`, `renk` ve ortak `confidence_score`
- Surucu eylemi: `telefonla_konusma`, `su_icme`, `sigara_icme`,
  `emniyet_kemeri_ihlali`, `slalom`
- Nesne: `bilgisayar`
- Yolcu: `on_koltuk`, `arka_koltuk_1`

Telefon, su, sigara, kemer ve yolcu bulgulari tek kareden yazilmaz. Birbirine en
fazla 1,5 saniye uzak en az uc gozlem bulundugunda tek olay uretilir. Yuksek
cozunurluklu kabin ROI'si ile Arac Gecis Hafizasi, kucuk hedefleri ve zamansal
tutarliligi birlikte degerlendirir.

Final Docker testinde 4K/8 sn'lik video cevrimdisi (`--network none`) GPU uzerinde
~52 saniyede islenmis ve sema-gecerli `results.json` uretmistir. Imaj icerik boyutu
~3,41 GB olup sartnamedeki 8 GB sinirinin altindadir.

## Docker ile calistirma

Dockerfile'in temel imaji sartnamedeki
`nvidia/cuda:12.1.0-base-ubuntu22.04` imajidir. Modeller konteynerde
`/app/weights/` altindadir ve calisma aninda ag erisimi gerekmez.

```bash
docker build -t mimik/ftr:final .
docker run --rm --gpus all --network none --cpus=4 --memory=16g --shm-size=2g \
  -v <video-dosyasi>:/app/data/input/video.mp4:ro \
  -v <cikti-klasoru>:/app/data/output \
  mimik/ftr:final
```

Program otomatik baslar, girdiyi `/app/data/input/video.mp4` yolundan okur ve
sonucu `/app/data/output/results.json` yoluna yazar.

Teslim imajini disari aktarmak icin:

```bash
docker save -o imaj.tar mimik/ftr:final
```

## Yerel calistirma

```bash
pip install -r requirements.txt
python app.py <video-dosyasi> <results.json>
```

## Dosyalar

| Yol | Islev |
|---|---|
| `app.py` | Sabit Docker giris/cikis yollarini yoneten giris noktasi |
| `src/predict.py` | Model yukleme, ROI cikarimi, zamansal birlestirme ve JSON uretimi |
| `src/utils.py` | Turkiye plaka normalizasyonu ve sartname regex'i |
| `weights/` | Docker build baglamindaki model agirliklari |
| `requirements.docker.txt` | Kucultulmus konteyner runtime bagimliliklari |
| `docs/ftr_rapor_icerik.md` | Rapor icin dogrulanmis icerik ve kabul kontrolu |
| `reports/docker_acceptance.md` | Boyut, hash, offline GPU ve runtime kabul kaniti |
| `scripts/validate_results.py` | JSON anahtar, etiket, guven ve plaka regex denetimi |
| `swfg_juri_final.docx` | Olculmus basarimlari one cikaran, Docker kanitli juri surumu |

Tum cikti kategori ve etiketleri kucuk harfli ASCII olarak sabit izin listesine
gore suzulur. Plaka OCR sonucu sartnamedeki Turkiye plaka regex'ine uymuyorsa
`tespit edilemedi` olarak raporlanir.
