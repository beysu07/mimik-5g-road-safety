# MİMİK Mobil Uygulama — Kurulum ve Çalıştırma

Üç hedef aynı kod tabanından üretilir: **iOS**, **Android**, **Web**.
Hangisinin ne zaman kullanılacağı aşağıdadır.

| Hedef | Gereksinim | Süre | Durum |
|---|---|---|---|
| **Web** | Yok (Windows yeterli) | 0 dk | ✅ çalışıyor — garanti yedek |
| **iOS** | MacBook + Xcode | ~1 sa (ilk sefer) | ⬜ dosyalar hazır, Mac bekliyor |
| **Android** | JDK + SDK lisansları + Android telefon | ~30 dk | ⬜ lisanslar kabul edilmedi |

---

## A) Web — Mac/Android gerekmez (şu an çalışan yol)

```bash
cd mobile && flutter build web --release
cd .. && python scripts/live_server.py --dongu --port 8080
```
Telefonda (aynı Wi-Fi): `http://<laptop-ip>:8080/` · IP: `ipconfig`

Sunucu hem uygulamayı hem API'yi aynı adresten verir → CORS/adres ayarı gerekmez.

---

## B) iOS — MacBook ile (ücretli hesap GEREKMEZ)

iOS derlemesi yalnızca macOS'ta yapılabilir (Xcode zorunlu). `ios/` klasörü ve
gerekli izinler **hazır durumdadır**; Mac'te yapılacaklar:

1. **Xcode kur** (App Store, ~10 GB — önceden indir, uzun sürer) ve bir kez aç,
   lisansı kabul et.
2. **Flutter SDK kur** (macOS sürümü) ve depoyu klonla.
3. Bağımlılıklar:
   ```bash
   cd mobile && flutter pub get
   ```
4. **Xcode'da aç:** `mobile/ios/Runner.xcworkspace` *(.xcodeproj değil, .xcworkspace)*
5. **İmzalama:** Runner → *Signing & Capabilities*
   - *Automatically manage signing* işaretli
   - *Team*: Apple ID'nle **Personal Team** seç (ücretsiz)
   - *Bundle Identifier*: benzersiz yap, ör. `tr.mimik.app.dogukan`
6. iPhone'u USB ile bağla, telefonda "Bu bilgisayara güven" de.
7. Çalıştır:
   ```bash
   flutter run --release -d <cihaz-id>     # flutter devices ile id'yi gör
   ```
8. İlk açılışta iPhone'da: **Ayarlar → Genel → VPN ve Cihaz Yönetimi →**
   geliştirici sertifikanı **güven**.
9. Uygulama açılınca iOS **yerel ağ izni** soracak → **İzin Ver**
   (laptop'a bağlanmak için şart; `NSLocalNetworkUsageDescription` eklenmiştir).

### ⚠️ Ücretsiz imzalamanın 7 gün sınırı
Personal Team ile imzalanan uygulama **7 gün sonra açılmaz**. Final 7–9 Ağustos
olduğundan uygulamayı **6 Ağustos'ta yeniden kurmak** gerekir (Mac o gün elinizde
olmalı). Ücretli Apple Developer hesabı ($99/yıl) bu süreyi 1 yıla çıkarır.

---

## C) Android

```bash
flutter doctor --android-licenses      # tüm lisansları kabul et
flutter run --release                  # telefon USB + geliştirici modu açık
```
`flutter doctor` "Could not determine java version" diyorsa JDK 17 kurulmalıdır
(Android Studio kurulumu bunu da getirir).

> Şartname §4.1: *"final yarışma ortamında ilgili cihaz/hat erişimi Turkcell
> tarafından sağlanacak"* → finalde verilecek cihaz büyük olasılıkla Android'dir;
> Turkcell'e sorulan 10. soru bunu netleştirecektir.

---

## Uygulamada bağlantı ayarı

Giriş ekranında **"Bağlantı ayarları"** bölümü analiz ucunun adresini alır:

- **Web** sürümünde boş bırakılır → aynı sunucu kullanılır.
- **iOS/Android** sürümünde laptop adresi yazılır: `http://192.168.1.20:8080`
- Adres boş ve uygulama native ise **mock** moda düşer (sunucusuz demo yedeği).

## Sorun giderme

| Belirti | Sebep / çözüm |
|---|---|
| iOS'ta "Görüntü bekleniyor..." kalıyor | Yerel ağ izni verilmemiş veya adres yanlış; Ayarlar → MİMİK → Yerel Ağ |
| Telefon laptop'a hiç ulaşamıyor | Aynı Wi-Fi'da değil, ya da Windows Güvenlik Duvarı 8080'i engelliyor |
| Uygulama 7 gün sonra açılmıyor | Ücretsiz iOS imzası doldu → yeniden kur (bkz. B/⚠️) |
| Android'de ağ hatası | `usesCleartextTraffic` ayarlıdır; adresin `http://` ile başladığından emin ol |
