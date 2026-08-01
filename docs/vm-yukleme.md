# VM'e Yükleme ve Web UI'da Doğrulama

VM: `8.234.235.53` · kullanıcı `u4541474` · **hakem yalnız Web UI kullanacak.**

## Neden imajı değil kaynağı yüklüyoruz

`docker save` ile imaj tarball'ı **3–7 GB**; yüklemesi çok uzun sürer. Onun yerine
**kod + ağırlıkları (~150 MB)** gönderip **VM'de build ediyoruz**. VM'in interneti var,
torch'u oradan çeker. Sonuç aynı imaj, çok daha hızlı döngü.

## 1) Dosyaları gönder (yerelden, tek komut)

```bash
scp -r Dockerfile app.py requirements.docker.txt src weights u4541474@8.234.235.53:~/mimik/
```

> Şifre sorulacak (maildeki). `weights/` 149 MB — birkaç dakika sürer.
> Klasör yoksa önce: `ssh u4541474@8.234.235.53 "mkdir -p ~/mimik"`

## 2) VM'de imajı derle

```bash
ssh u4541474@8.234.235.53
```

```bash
cd ~/mimik && docker build -t teknofest-2026/mimik:latest .
```

> **İsim `teknofest-2026/` ile başlamalı** — aksi halde Web UI'ın sağ panelinde görünmez.

## 3) Web UI'da doğrula

1. `http://8.234.235.53` (⚠️ **https değil** — tarayıcı ekliyorsa sil)
2. Giriş: `u4541474` + şifre
3. Sağ panel **Docker – Images**'ta `teknofest-2026/mimik:latest` görünmeli
4. Bir proje aç → **Input video** seç (`TOGG_MOBESE_FULL.mp4`) → **Image to run** = yeni imaj → **Execute** → `OK`
5. **Live output**'ta beklenen: `EXECUTION COMPLETED – status: SUCCESS`
6. **Executions** → `results.json` indir

## 4) Puanla (yerelde)

```bash
python scripts/faz2_degerlendir.py <indirilen_results.json>
```

`TOGG_MOBESE_FULL.mp4` ile `faz2_gt.json` **aynı içeriği** kapsıyor (zaman damgaları
örtüşüyor, doğrulandı) — yani VM çıktısını doğrudan puanlayabiliriz.

## 5) Temizlik (final öncesi ZORUNLU)

Operasyon rehberi: VM'de **tek bir imaj** kalmalı, hakem hangisinin nihai olduğunu
anlayabilsin. Eski/denemelik imajlar sağ panelden silinmeli.

## 6) Parmak izi (7 Ağustos 21:00'dan önce)

```bash
docker images --no-trunc --format "{{.Repository}}:{{.Tag}} {{.ID}}" | grep teknofest-2026
```

Çıkan `sha256:...` değeri **hakeme ibraz edilecek parmak izidir**; saklayın. Bu saatten
sonra imaj değiştirilirse değerlendirmeye alınmaz.

---

## Sürüm karşılaştırma kaydı

| İmaj | Kaynak | Boyut | faz2 F1 | arac |
|---|---|---|---|---|
| `teknofest-2026/mimik_final:latest` | repoda olmayan kod | 7,55 GB | **0,06** | 3/3 |
| bu repo (epizodik + eşik 0,20) | `src/predict.py` | ~3,4 GB | **0,14** | 3/3 |

Ölçüm: `scripts/faz2_degerlendir.py`, tolerans ±5 sn.
