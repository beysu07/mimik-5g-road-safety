# MİMİK — 5G Ağ API Entegrasyon Planı (Final Etabı)

> Kaynak: yarışma şartnamesi §4.1 (Number Verification / Quality on Demand), §4.2 (aşamalar),
> §5 (puanlama), §6.7 (final etabı) + CAMARA/Open Gateway API standartları.
> Puan ağırlığı: **%40 YZ doğruluk · %40 5G API entegrasyonu · %20 rapor+sunum**.

---

## 1. Şartname tam olarak ne istiyor?

**Number Verification (NV).** Senaryonun ilk adımı: sisteme giriş yapan kullanıcının
(veya araç sisteminin) doğrulanması. Beklenen: *"SMS bekleme süresi veya manuel kod girişi
gibi adımları ortadan kaldırarak, şebeke tabanlı, güvenli ve **sessiz** bir doğrulama"*.
Cihaz/hat erişimi finalde Turkcell tarafından sağlanacak.

**Quality on Demand (QoD).** Yol kenarı kamera görüntüleri normalde standart kalitede
iletilecek; yapay zekâ bir **kritik durum** tespit ettiğinde (araç yaklaşması, plaka okuma
ihtiyacı, sürücü davranışı tespiti) QoD tetiklenip bağlantı kalitesi yükseltilecek.

**⚠️ Puanın asıl geldiği cümle:**
> *"Yarışmacılar, şebeke kalitesi arttığında yapay zekâ analiz sonuçlarındaki (araç tespiti,
> nesne tanıma, plaka okuma, risk unsuru algılama vb.) **başarım artışını bu API kullanımı ile
> kanıtlayacaklardır**."*

Yani QoD'yi çağırmak **yetmez**; "QoD kapalı → şu başarım, QoD açık → şu başarım" farkını
ölçüp göstermek zorundayız. Plan bunun üzerine kuruludur.

---

## 2. Kritik mimari karar (bunu yanlış kurarsak %40 gider)

FTR'deki sistemimiz **cihaz üstünde, yerel dosyadan** çalışıyordu. Bu mimaride ağ kalitesinin
YZ başarımına hiçbir etkisi olmaz → **ispat üretilemez**.

Bu yüzden final mimarisinde video, YZ'ye **ağ üzerinden** ulaşmalıdır:

```
[Yol kenarı kamera / kaynak cihaz]
        │  video akışı (5G veri bağlantısı)
        │  Normal: düşük bit hızı/çözünürlük  ── "best effort"
        ▼
   ((( 5G şebekesi )))  ←── QoD API ile kalite yükseltilir/bırakılır
        │  Kritik anda: yüksek bit hızı/çözünürlük
        ▼
[Analiz ucu: YOLO11 hattı + Araç Geçiş Hafızası]
        │
        ├─► results.json / tespitler
        └─► Mobil uygulama ekranı (sonuçların gösterimi)
```

Ağ kalitesi düştüğünde **küçük hedefler** (plaka karakterleri, telefon, kemer) önce bozulur —
bu bizim FTR'de zaten nicel olarak kanıtladığımız olgudur (512×512 → küçük nesne mAP≈0;
tam çözünürlük → su mAP 0,995). **QoD'nin neden gerekli olduğunun fiziksel gerekçesi budur** ve
sunumda bu sürekliliği vurgulamak güçlü bir hikâye olur.

---

## 3. Number Verification entegrasyonu

### 3.1. Akış (CAMARA standardı)

NV, **cihazın mobil veri bağlantısı üzerinden** yapılmak zorundadır: operatör, isteğin geldiği
IP adresini SIM karta eşler. Bu nedenle **backend'den başlatılan akış çalışmaz** (operatör
sunucunun IP'sini görür). İki yol vardır:

| Yöntem | Koşul | Not |
|---|---|---|
| **OIDC Authorization Code Flow** (varsayılan) | Cihaz **mobil şebekede** olmalı (Wi-Fi kapalı) | `prompt=none` ile sessiz çalışır |
| CIBA / JWT-Bearer + TS.43 token | Wi-Fi üzerinde de çalışır | `operatortoken:<token>` biçimi; operatör desteği gerekir |

Erişim jetonu kısıtları: **tek kullanımlık**, refresh token yok, **azami 300 sn** ömür.

### 3.2. Uç noktalar

| Uç nokta | Metot | Dönen | Scope |
|---|---|---|---|
| `/verify` | POST | `{ "devicePhoneNumberVerified": true/false }` | `number-verification:verify` |
| `/device-phone-number` | GET | `{ "devicePhoneNumber": "+90..." }` | `number-verification:device-phone-number:read` |

`/verify` gövdesi: `phoneNumber` (E.164) **veya** `hashedPhoneNumber` (SHA-256, 64 hex) —
**ikisinden yalnızca biri** gönderilir. Gizlilik açısından hash'li biçim tercih edilmelidir.

### 3.3. Bizim senaryodaki yeri

Uygulama açılışında operatör (yol güvenliği görevlisi / araç sistemi) **sessizce** doğrulanır;
doğrulanmayan oturum tespit gönderemez. Sunumda vurgulanacak: SMS OTP yok, kullanıcı
etkileşimi yok, doğrulama şebekeden.

---

## 4. Quality on Demand entegrasyonu

### 4.1. Uç noktalar (CAMARA QoD)

| Uç nokta | Metot | İşlev |
|---|---|---|
| `/sessions` | POST | QoS oturumu aç |
| `/sessions/{sessionId}` | GET | Oturum durumu |
| `/sessions/{sessionId}` | DELETE | Oturumu **sonlandır** (kaynağı bırak) |
| `/sessions/{sessionId}/extend` | POST | Süre uzat |
| `/retrieve-sessions` | POST | Cihaza ait oturumları listele |

### 4.2. Oturum açma gövdesi (alan adları birebir)

```json
{
  "duration": 30,
  "qosProfile": "QOS_L",
  "device": { "phoneNumber": "+90..." },
  "applicationServer": { "ipv4Address": "203.0.113.10/32" },
  "devicePorts":            { "ranges": [{ "from": 50000, "to": 50010 }] },
  "applicationServerPorts": { "ports": [8554] },
  "sink": "https://<bizim-webhook>/qod-events"
}
```

Yanıt (`SessionInfo`): `sessionId` (UUID), `qosStatus` ∈ **REQUESTED / AVAILABLE / UNAVAILABLE**,
`startedAt`, `expiresAt`, `statusInfo` ∈ DURATION_EXPIRED / NETWORK_TERMINATED / DELETE_REQUESTED.

> **Önemli:** `qosStatus` **AVAILABLE** olmadan kalite garantisi yoktur. Akış kalitesini
> yükseltme kararı, POST yanıtına değil **AVAILABLE durumuna** bağlanmalıdır (`sink` webhook'u
> veya kısa aralıklı GET ile).

Profil adları (`QOS_S/M/L/E`) sağlayıcıya göre değişir; kesin liste `qos-profiles` API'sinden
veya Turkcell onboarding'inden alınacaktır. Sık hatalar: `409 CONFLICT` (cihaz için zaten
oturum var), `422 QUALITY_ON_DEMAND.QOS_PROFILE_NOT_APPLICABLE`, `400 ...DURATION_OUT_OF_RANGE`.

### 4.3. Tetikleme mantığı (bizim YZ'ye bağlanışı)

```
DURUM: IZLEME  (best effort, düşük bit hızı)
  └─ Hafif model: yalnızca araç var mı? (YOLO11s, düşük çözünürlük yeterli)
     │
     │  KRİTİK DURUM: araç kadrajda + bbox alanı büyüyor (yaklaşıyor)
     │  ve son N karede tutarlı  → gürültüye karşı kalıcılık şartı
     ▼
DURUM: YÜKSELTME TALEBİ
  └─ POST /sessions (QOS_L, duration≈30 sn)  →  qosStatus AVAILABLE bekle
     ▼
DURUM: YÜKSEK KALİTE PENCERESİ
  └─ Encoder yükselt (1080p/4K, yüksek bit hızı)
  └─ Ağır analizler burada: plaka OCR, kabin (telefon/kemer/yolcu), araç tipi/renk
  └─ Araç Geçiş Hafızası bulguları biriktirir  ← FTR'den aynen taşınıyor
     ▼
DURUM: BIRAKMA  (araç kadrajdan çıktı veya süre doldu)
  └─ DELETE /sessions/{id}  → kaynak şebekeye iade  ("musluk sürekli açık değil")
```

Bu döngü, şartnamedeki *"ihtiyaca göre açılıp kapanabilen akıllı bir kaynak"* ifadesinin
birebir karşılığıdır ve gösterilmesi kolaydır.

### 4.4. Sağlayıcıdan bağımsız tasarım + mock

Turkcell'in gerçek uç noktaları/kimlik bilgileri eğitim seansında verilecek. Beklemeden
geliştirebilmek için **adaptör + mock** yaklaşımı:

```python
# net/qod.py  (iskelet)
class QoDClient:
    """CAMARA QoD adaptörü. mock=True iken şebeke yerine yerel şekillendirici kullanılır."""

    def __init__(self, base_url=None, token_provider=None, mock=False):
        self.base_url, self.token_provider, self.mock = base_url, token_provider, mock
        self.session_id = None

    def request_boost(self, profile='QOS_L', duration=30, device=None, app_server=None):
        """POST /sessions -> sessionId. mock modda anında AVAILABLE döner."""

    def wait_available(self, timeout=5.0):
        """qosStatus AVAILABLE olana kadar GET /sessions/{id} (veya sink webhook)."""

    def release(self):
        """DELETE /sessions/{id} — pencere bitince kaynağı bırak."""
```

**Mock modda ağ kalitesini gerçekten değiştiremeyiz; ama simüle edebiliriz:** gönderici tarafta
bit hızını/çözünürlüğü düşürüp yükselterek (ör. ffmpeg `-b:v 800k` ↔ `-b:v 10M`) tüm mantığı ve
**ölçüm düzeneğini** şimdiden kurar, finalde yalnızca `mock=False` yaparız. Bu, ispat tablosunu
gerçek şebeke gelmeden hazırlamamızı sağlar.

---

## 5. İspat (kanıt) düzeneği — puanın geldiği yer

Aynı araç geçişi, iki koşulda çalıştırılır ve **eş zamanlı ölçülür**:

| Ölçüt | QoD KAPALI (best effort) | QoD AÇIK (QOS_L) |
|---|---|---|
| Alınan bit hızı (Mbps) | ölçülecek | ölçülecek |
| Çözünürlük / kare hızı | ör. 720p @ 15 fps | ör. 1080p–4K @ 30 fps |
| Uçtan uca gecikme (ms) | ölçülecek | ölçülecek |
| **Plaka doğruluğu (karakter)** | ör. 4/8 veya "tespit edilemedi" | ör. **8/8 → 34TC8532** |
| Araç tipi/renk güveni | ölçülecek | ölçülecek |
| Kabin tespiti (telefon/kemer) | ölçülecek | ölçülecek |
| Doğru tespit sayısı | ölçülecek | ölçülecek |

Kurallar: aynı video/geçiş, aynı modeller, **tek değişken ağ kalitesi**; her koşu için
`qosStatus`, `sessionId`, zaman damgaları loglanır (API'nin gerçekten çağrıldığının kanıtı).
Çıktı: sunumda tek slaytlık **öncesi/sonrası** tablosu + ekran görüntüsü.

---

## 6. Turkcell eğitim seansında sorulacaklar (net liste)

1. QoD ve NV için **base URL**'ler, sandbox var mı, kimlik bilgileri (client_id/secret) nasıl verilecek?
2. Kullanılabilir **QoS profil adları** ve her birinin bant genişliği/gecikme garantisi; `maxDuration` sınırı?
3. QoD'de cihaz tanımlayıcı olarak ne kabul ediliyor: `phoneNumber` mi, `ipv4Address` mi? (2-legged/3-legged token farkı)
4. `applicationServer` olarak **hangi IP** beyan edilecek — analiz ucumuz yarışma ağında mı, dışarıda mı?
5. `sink` (webhook) desteği var mı; yoksa AVAILABLE durumu için polling aralığı önerisi?
6. NV'de **Authorization Code Flow** mu, **TS.43** mü destekleniyor? Wi-Fi kapalı olması şart mı?
7. Finalde verilecek hat/cihaz: kaç adet, hangi APN, sabit IP var mı?
8. Aynı anda kaç QoD oturumu açılabilir; art arda aç/kapa (churn) sınırı var mı? (409 riski)
9. Kamera akışı hangi protokolle bekleniyor (RTSP/WebRTC/SRT) ve yarışma alanında kaynak cihaz ne olacak?
10. Ölçüm/ispat için operatör tarafında log/rapor sağlanıyor mu?

---

## 7. Yol haritası

| # | İş | Bağımlılık | Kim |
|---|---|---|---|
| 1 | `net/qod.py` + `net/nv.py` adaptörleri (mock modlu) | yok — **hemen başlanabilir** | — |
| 2 | Akış hattı: kaynak → (bit hızı değiştirilebilir) → analiz ucu | yok | — |
| 3 | Durum makinesi: IZLEME → TALEP → PENCERE → BIRAKMA | 1, 2 | — |
| 4 | Ölçüm/log altyapısı (bit hızı, gecikme, YZ metrikleri, sessionId) | 2 | — |
| 5 | İspat tablosu: mock ile öncesi/sonrası koşusu | 3, 4 | — |
| 6 | Mobil uygulama: NV ile sessiz giriş + tespitlerin ekranda gösterimi | 1 | — |
| 7 | Gerçek Turkcell uç noktalarına geçiş (`mock=False`) | eğitim seansı | — |
| 8 | Kapsam artırma (eksik etiketler — ayrı iş kalemi) | — | — |

**Not:** 1–5 arası **Turkcell bilgileri gelmeden** tamamlanabilir; final günü riski böylece
yalnızca "uç nokta değiştirme"ye iner.

---

## 7b. TAKVİM — Final: 7–8–9 Ağustos 2026, İstanbul

Bugün 27 Temmuz → **11 gün**. 2 kişilik takım. Sıralama puana göre acımasız yapılmalıdır.

| Tarih | İş | Neden bu sırada |
|---|---|---|
| **27–29 Tem** | QoD adaptörü + mock + durum makinesi + **ölçüm/ispat düzeneği** | %40'lık kalemin çekirdeği; Turkcell bilgisi **gerekmez** |
| **30 Tem–1 Ağu** | Mobil uygulama iskeleti + **NV ile sessiz giriş** + tespit ekranı | NV cihazda çalışmak zorunda; uygulama olmadan olmaz |
| **2–3 Ağu** | Gerçek Turkcell uç noktalarına geçiş + uçtan uca entegrasyon testi | Kimlik bilgileri bu tarihe kadar gelmeli |
| **4–5 Ağu** | Prova + hata senaryoları (409 CONFLICT, UNAVAILABLE, ağ kesintisi, jeton süresi) | Sahada en çok bunlar patlar |
| **6 Ağu** | Sunum + **yedek plan** (mock fallback ile demo), toparlanma | Şartname §6.7: önce kısa sunum var |
| **7–9 Ağu** | **FİNAL — İstanbul** | |

**Kritik kural:** *"Gerçek şebeke gelmezse demo yapamayız"* durumuna asla düşme. 27–29 Temmuz'da
kurulacak **mock düzeneği**, kimlik bilgileri gecikse bile ispat tablosunu ve akışı çalışır
tutar; finalde yalnızca `mock=False` yapılır.

**Bugün yapılacak tek şey (bloke ediyor):** Turkcell/komiteden **QoD + NV kimlik bilgileri,
base URL, QoS profil adları ve test hattı** talebi. §6'daki 10 soruyu tek mailde sor — cevap
gelene kadar 1. adım paralel ilerler.

---

## 8. Açık konular
- Mobil uygulama platformu seçilmedi (Android native / Flutter). NV akışı cihazda çalışacağı
  için platform seçimi NV entegrasyonunu doğrudan etkiler.
- Analiz ucunun nerede koşacağı (telefon üstünde mi, sunucuda mı) kararı §6.7'deki
  *"mobil uygulamayı kendi telefonlarında çalıştırıp"* ifadesiyle birlikte netleştirilmeli.
