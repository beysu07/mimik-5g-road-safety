# Docker Kabul Testi

Test tarihi: 28 Haziran 2026

## Imaj

| Olcum | Sonuc |
|---|---:|
| Imaj etiketi | `mimik/ftr:final` |
| Imaj kimligi | `6a4ba1c16281` |
| Temel imaj | `nvidia/cuda:12.1.0-base-ubuntu22.04` |
| `docker image ls` boyutu | 7,55 GB |
| `docker image inspect .Size` | 2.698.657.499 bayt (2,513 GiB) |
| `imaj.tar` boyutu | 2.698.686.464 bayt (2,699 GB / 2,513 GiB) |
| `imaj.tar` SHA-256 | `BBDFBB9DD7590447D9E9F276F703A6B450113DABD57DDFABCFB40090EEDE47A7` |
| `docker load -i imaj.tar` | Basarili |

Hem Docker'in gosterdigi 7,55 GB imaj boyutu hem de teslim edilecek 2,699 GB tar
dosyasi 8 GB sinirinin altindadir.

## Runtime Testi

Konteyner su kisitlarla calistirildi:

```text
--rm --gpus all --network none --cpus=4 --memory=16g --shm-size=2g
girdi: /app/data/input/video.mp4
cikti: /app/data/output/results.json
```

Test videosu 3840x2160, 50 FPS, 457 kare ve 9,14 saniyedir. Konteyner cikis
kodu `0`, duvar saati 68,19 saniyedir. Bu deger 10 dakikalik sinirin altindadir.
`results.json`, `scripts/validate_results.py` ile `SCHEMA_OK` sonucunu vermistir.

Uretilen ozet:

```json
{
  "tip": "suv",
  "plaka": "34TC8532",
  "renk": "siyah",
  "confidence_score": 0.81,
  "olay": "telefonla_konusma",
  "olay_confidence_score": 0.68
}
```

## Ortam ve Modeller

- GPU gorunurlugu: `True`
- Yerel test GPU'su: NVIDIA GeForce RTX 4060 Laptop GPU
- PyTorch: 2.1.2+cu121
- Torchvision: 0.16.2+cu121
- Ultralytics: 8.4.14
- EasyOCR: 1.7.2
- OpenCV: 4.11.0
- `/app/models/` altindaki yedi modelin tamami basariyla acildi.

Yerel makinede Tesla T4 bulunmadigi icin fiziksel T4 testi yapilmamistir. Imaj CUDA
12.1 hedefiyle olusturulmus ve GPU cikarimi RTX 4060 uzerinde dogrulanmistir; T4
dogrulamasi yarismaci degerlendirme sunucusunda gerceklesecektir.

## Kontrol Sonucu

| Sartname maddesi | Sonuc |
|---|---|
| Kok dizinde Dockerfile | Gecti |
| Zorunlu temel imaj | Gecti |
| `/app/models/` agirlik yolu | Gecti |
| Otomatik `CMD` | Gecti |
| Sabit girdi/cikti yollari | Gecti |
| Runtime internet kapali | Gecti |
| GPU cikarimi | Gecti (RTX 4060) |
| 4 vCPU / 16 GB / 2 GB SHM | Gecti |
| 8 GB imaj siniri | Gecti |
| 10 dakika siniri | Gecti |
| JSON semasi | Gecti |
| Tar arsivinin yeniden yuklenmesi | Gecti |
