/// CAMARA Number Verification — sebeke tabanli "sessiz" dogrulama.
///
/// Kritik kisit: operator, istegin geldigi IP adresini SIM karta esler. Bu yuzden
/// akis CIHAZDA ve MOBIL VERI uzerinde baslatilmalidir (Wi-Fi kapali). Backend'den
/// baslatilan akis calismaz -> operator sunucunun IP'sini gorur.
///
/// Jeton kisitlari (CAMARA): tek kullanimlik, refresh token yok, azami 300 sn.
library;

import 'dart:convert';
import 'package:http/http.dart' as http;

class NvConfig {
  /// Turkcell tarafindan verilecek degerler (bkz. docs/turkcell-erisim-talebi.md).
  final String authorizeUrl; // OIDC /authorize
  final String tokenUrl; // OIDC /token
  final String apiBaseUrl; // Number Verification base URL
  final String clientId;
  final String redirectUri;
  final bool mock;

  const NvConfig({
    this.authorizeUrl = '',
    this.tokenUrl = '',
    this.apiBaseUrl = '',
    this.clientId = '',
    this.redirectUri = 'tr.mimik.app://callback',
    this.mock = true,
  });
}

class NvResult {
  final bool verified;
  final String? devicePhoneNumber;
  final String detail;
  const NvResult(this.verified, {this.devicePhoneNumber, this.detail = ''});
}

class NvService {
  final NvConfig cfg;
  final http.Client _http;
  String? _accessToken;

  NvService(this.cfg, {http.Client? client}) : _http = client ?? http.Client();

  /// Sessiz dogrulama: OIDC Authorization Code Flow (prompt=none) -> token -> /verify.
  ///
  /// [phoneNumber] E.164 bicimindedir (+90...). Gizlilik icin sunucuya duz numara
  /// yerine SHA-256 ozeti gonderilebilir; CAMARA ikisinden yalnizca birini kabul eder.
  Future<NvResult> verify(String phoneNumber) async {
    if (cfg.mock) {
      await Future<void>.delayed(const Duration(milliseconds: 600));
      return NvResult(
        true,
        devicePhoneNumber: phoneNumber,
        detail: 'MOCK: sebeke dogrulamasi benzetildi (SMS/OTP yok)',
      );
    }

    _accessToken ??= await _authorize();
    final res = await _http.post(
      Uri.parse('${cfg.apiBaseUrl}/verify'),
      headers: {
        'Authorization': 'Bearer $_accessToken',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({'phoneNumber': phoneNumber}),
    );
    _accessToken = null; // CAMARA: jeton tek kullanimliktir

    if (res.statusCode != 200) {
      return NvResult(false, detail: 'HTTP ${res.statusCode}: ${res.body}');
    }
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    final ok = body['devicePhoneNumberVerified'] == true;
    return NvResult(ok, detail: ok ? 'Sebeke dogrulamasi basarili' : 'Numara eslesmedi');
  }

  /// Cihazin numarasini dogrudan sorar (scope: number-verification:device-phone-number:read).
  Future<String?> devicePhoneNumber() async {
    if (cfg.mock) return '+90XXXXXXXXXX';
    _accessToken ??= await _authorize();
    final res = await _http.get(
      Uri.parse('${cfg.apiBaseUrl}/device-phone-number'),
      headers: {'Authorization': 'Bearer $_accessToken'},
    );
    _accessToken = null;
    if (res.statusCode != 200) return null;
    return (jsonDecode(res.body) as Map<String, dynamic>)['devicePhoneNumber'] as String?;
  }

  /// OIDC yetkilendirme -> access token.
  ///
  /// TODO(turkcell): gercek akis, cihazi mobil veri uzerinden operatorun /authorize
  /// adresine yonlendirip donen "code"u /token ile takas eder. Turkcell'in
  /// Authorization Code Flow mu TS.43 mu destekledigi teyit edilince tamamlanacak
  /// (talep mailinde 9. soru). Yonlendirme icin flutter_web_auth_2 / app_links
  /// paketlerinden biri eklenecektir.
  Future<String> _authorize() async {
    throw UnimplementedError(
      'Turkcell OIDC uc noktalari ve akis tipi bekleniyor (mock=true ile calisin).',
    );
  }
}
