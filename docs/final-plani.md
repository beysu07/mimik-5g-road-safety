# MİMİK — Final Planı (8–9 Ağustos 2026, İstanbul)

> Kaynak: "Final Yarışma Senaryosu", "Yarışmacı Platformu Operasyon Rehberi",
> "Open Gateway Demo UX Akış Kılavuzu", `OGW_Teknofest.pdf`, Postman koleksiyonu,
> `faz2_gt.json`. Tümü 29 Tem 2026'da okundu ve doğrulandı.

---

## 0. Sabit gerçekler (doğrulandı)

| Konu | Değer |
|---|---|
| Yarışma günü | **8 Ağustos** (sunum + canlı demo), 9 Ağustos devam/ödül |
| **İmaj donması** | **7 Ağustos 21:00** — sonrasında değişen imaj değerlendirilmez |
| İmaj kimliği | SHA256 parmak izi alınacak, hakem eşleşmeyi kontrol edecek |
| Sunum | Takım başına **en fazla 10 dk**, format serbest |
| VM | `8.234.235.53` · `u4541474` · Ubuntu, Google Cloud |
| Çalıştırma | **Yalnızca Web UI** (`http://<VM_IP>`); komut satırı değerlendirilmez |
| İmaj adı | **`teknofest-2026/` ile başlamalı**, VM'de sonunda **tek imaj** kalmalı |
| Yollar | `/app/data/input/video.mp4` → `/app/data/output/results.json` (mevcut hâlimizle aynı) |
| Faz2 HLS | `https://teknofest-arge-turkcell.ercdn.net/hls/4/pZ/faz2/faz2.smil/playlist.m3u8` |
| Rendition'lar | **1080p** (9,16 Mbps) · **240p** (289 kbps) — doğrulandı |
| Test numarası | `+905390000020` |
| QoD profili | `teknofest2026` · `applicationServer.ipv4Address = "0.0.0.0/0"` |

**Puanlama:** Düşük Kaliteli Video **%25** · Yüksek Kaliteli Video **%25** · Canlı Demo **%25** · Sunum **%25**

**Canlı demo kırılımı:** NV başarısız → **0 puan** (akış biter). NV ✓ → +5. QoD ✓ → +5.
Streaming ✓ → kaydedilen videonun YZ puanı kullanılır. Streaming ✗ → o ana dek toplanan 5 veya 10.

---

## 1. Mimari (şartname Şekil 2–3 ile birebir)

```
[Telefon + 5G SIM]                    [Google Cloud Ubuntu VM  8.234.235.53]
  Mobil Uygulama  ──1) video────────►  Backend (bizim)
        ▲                                  │  2) video.mp4
        │                                  ▼
        └──4) results.json──────────  Yapay Zeka İmajı (bizim, teknofest-2026/…)
                                           3) results.json
  Mobil Uygulama ◄──stream kaydı──  [Streaming Server (Turkcell)]
  Mobil Uygulama ──►  Backend  ──►  [Open Gateway: NV + QoD (Turkcell)]
```

**Kritik:** Backend ve YZ imajı **VM'de** koşar (laptop'ta değil). NV/QoD çağrıları
**backend'den** gider — `client_id/secret` backend'de saklanır, mobil uygulamada değil.

---

## 2. Open Gateway entegrasyonu (kesin şekil)

**NV akışı (backend merkezli):**
1. App → Backend `POST /nv/verify {phoneNumber}`
2. Backend → App: 302, Open Gateway `/oauth2/authorize` linki
3. App (hücresel ağ) → `GET {api-gateway-url}/oauth2/authorize?response_type=code&client_id=…&redirect_uri=http://<VM_IP>:8080/api/auth/callback&state=…&scope=…`
   - **scope:** `openid dpv:RequestedServiceProvision#quality-on-demand:sessions:create dpv:FraudPreventionAndDetection#number-verification:verify`
4. OGW → 302 → `…/api/auth/callback?code=…`
5. Backend → `POST /oauth2/token` (form: `grant_type=authorization_code`, `code`, `redirect_uri`) + **HTTP Basic Auth** (`base64(client_id:client_secret)`)
6. Backend → `POST {api}/number-verification/v1/verify` (`Bearer access_token`, body `{"phoneNumber": "+90…"}`)
7. Yanıt: `{"devicePhoneNumberVerified": true}` → App'e iletilir

**QoD akışı:** App → Backend `{duration}` → Backend `POST {api}/quality-on-demand/v1/sessions`
```json
{"duration": 60, "applicationServer": {"ipv4Address": "0.0.0.0/0"}, "qosProfile": "teknofest2026"}
```
→ **201 Created = BAŞARILI.**

> ⚠️ **Mevcut kodumuzda düzeltilecek:** Turkcell dağıtımında QoD'de yalnızca `POST /sessions`
> vardır; `GET /sessions/{id}`, `DELETE`, `extend` **yoktur**. `net/qod.py` içindeki
> `wait_available()` / `delete_session()` / `extend_session()` bu ortamda kullanılamaz.
> Başarı yalnızca **201**'e bakılarak belirlenir. Token ömrü **300 sn** → süresi dolarsa
> 3–8. adımlar tekrarlanır.

---

## 3. En büyük kaldıraç: %50'lik YZ puanı

`faz2_gt.json` = değerlendirme videosunun cevap anahtarı (111,5 sn, 34 tespit).
**Mevcut kapsamımız: 15/34 (%44).**

| Etiket | GT adedi | Durum |
|---|---|---|
| **arka_koltuk_2** | **12** | ❌ yok — tek başına GT'nin %35'i |
| **teknocan** | **4** | ❌ yok |
| emniyet_kemeri_ihlali | 4 | ✅ |
| sigara_icme | 3 | ✅ |
| telefonla_konusma | 2 | ✅ |
| su_icme | 2 | ✅ |
| esneme / arkaya_bakma / etrafa_bakinma | 1+1+1 | ❌ yok |
| bilgisayar / arka_koltuk_1 / on_koltuk / slalom | 1×4 | ✅ |

**Altın fırsat:** GT **zaman damgalı**. Yani eksik sınıfların videoda tam olarak *nerede*
olduğunu biliyoruz → o saniyelerden kare çıkarıp hızlı etiketleyebiliriz. Kör arama yok.

**Uyarı — ezberleme riski:** Final günü videosu faz2 ile aynı olmayabilir ("final günü
videosu" ifadesi ayrı geçiyor). Zaman damgalarına değil, **görsel örüntüye** göre
öğrenmeliyiz; GT'yi doğrulama/ölçüm için kullanmalı, sabit zamanları çıktıya gömmemeliyiz.

**İkinci uyarı — 240p:** Düşük kaliteli video 426×240. Plaka/küçük nesneler orada büyük
ihtimalle okunamayacak. Düşük çözünürlükte **ne üretebildiğimizi ölçmek** ve ona göre
davranmak gerekiyor (%25'lik ayrı kalem).

---

## 4. Yol haritası (29 Tem → 7 Ağu 21:00)

| Tarih | İş | Çıktı |
|---|---|---|
| **29–30 Tem** | ffmpeg kur · faz2 videosunu **iki çözünürlükte** indir · **değerlendirme scripti** yaz (GT'ye karşı puanla) · mevcut hattı iki videoda koştur | **Taban skor** — nerede olduğumuzu bilelim |
| **30 Tem–2 Ağu** | **Kapsam çalışması:** GT zamanlarından kare çıkar → `arka_koltuk_2`, `teknocan`, `esneme`, `arkaya_bakma`, `etrafa_bakinma` etiketle → eğit → yeniden ölç | Kapsam %44 → hedef %80+ |
| **31 Tem–3 Ağu** | **Backend (VM'de):** `/nv/verify`, `/api/auth/callback`, `/qod/session`, `/upload`, `/results` + Docker tetikleme | Canlı demo iskeleti |
| **3 Ağu 11:00** | **Soru-Cevap toplantısı** — `client_id/secret`, `api-gateway-url`, Lifebox detayı | Kimlik bilgileri |
| **3–5 Ağu** | **Mobil:** NV akışı (backend üzerinden), QoD butonu (süre seçimli), **HLS kaydı → MP4**, upload, results.json + **SHA256 gösterimi** | Uçtan uca demo |
| **5–6 Ağu** | VM'de Web UI testi · imaj adı `teknofest-2026/…` · tek imaj bırak · uçtan uca prova · hata senaryoları | Sahaya hazır |
| **6–7 Ağu** | **Sunum (10 dk)** hazırlığı + prova | Sunum |
| **7 Ağu 21:00** | **İMAJ DONDU** — SHA256 al ve sakla | Parmak izi |
| **8 Ağu** | Final | |

---

## 5. Mevcut varlıklarımız (yeniden kullanılacak)

| Var olan | Finalde rolü |
|---|---|
| 7 modelli çıkarım hattı, şema-geçerli `results.json` | %50'lik kalemin çekirdeği — kapsam artırılacak |
| Docker (offline, 3,41 GB, ~46 sn) | VM'ye taşınacak, adı `teknofest-2026/…` olacak |
| `net/qod.py`, `net/boost_controller.py` | **Sadeleştirilecek**: POST-only, 201 kontrolü |
| `scripts/live_server.py` | Backend'e evrilecek (VM'de) |
| Flutter app (NV mock, canlı ekran, sunucu adresi ayarı) | Gerçek akışa bağlanacak + HLS kaydı + SHA256 eklenecek |
| `scripts/qod_proof.py`, ağ benzetimi | Sunumda "QoD etkisi" kanıtı olarak kullanılacak |

---

## 6. Riskler

1. **Kapsam (%50)** — en büyük risk; 5 sınıf eksik, `arka_koltuk_2` tek başına GT'nin %35'i.
2. **NV başarısızlığı = demodan 0.** Tek nokta arıza. Yedek plan ve saha provası şart.
3. **Kimlik bilgileri 3 Ağustos'ta geliyor** → NV/QoD'yi gerçek ortamda denemek için **5 gün** kalıyor.
4. **240p'de küçük nesne** — düşük kaliteli video kalemi (%25) doğal olarak zayıf olabilir.
5. **Web UI zorunluluğu** — imaj VM'de Web UI'dan çalışmazsa çıkarım puanı alınamaz; erken test edilmeli.
6. **iPhone/Mac** — Android cihaz yoksa web sürümü ile gidilecek; finalde NV'nin **hücresel ağ** üzerinden çalışması gerektiği unutulmamalı (Wi-Fi kapalı).
