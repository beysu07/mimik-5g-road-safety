/// Canli demo akisi — backend/server.py ile konusur.
///
/// Sartname akisi: NV -> QoD -> stream kaydi -> yukle -> cikarim
///                 -> results.json + SHA256 ekranda gosterilir
///
/// Kimlik bilgileri (client_id/secret) BACKEND'dedir; uygulama yalniz kendi
/// backend'imize konusur. NV dogrulamasi cihazin HUCRESEL agi uzerinden yapilir.
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

class NvSonuc {
  final bool dogrulandi;
  final String state;
  final String? authorizeUrl;
  final bool mock;
  final String detay;
  const NvSonuc({
    required this.dogrulandi,
    required this.state,
    this.authorizeUrl,
    this.mock = false,
    this.detay = '',
  });
}

class CikarimSonuc {
  final String durum; // yuklendi | calisiyor | bitti | hata
  final Map<String, dynamic>? results;
  final String? sha256;
  final String? hata;
  const CikarimSonuc({required this.durum, this.results, this.sha256, this.hata});

  bool get bitti => durum == 'bitti';
}

class DemoService {
  /// Bos ise ayni origin (uygulama backend'den servis ediliyorsa).
  final String baseUrl;
  final http.Client _http;

  DemoService({this.baseUrl = '', http.Client? client})
      : _http = client ?? http.Client();

  Uri _uri(String yol, [Map<String, String>? q]) {
    final temiz = baseUrl.replaceAll(RegExp(r'/+$'), '');
    final u = baseUrl.isEmpty ? Uri.base.resolve(yol) : Uri.parse('$temiz/$yol');
    return q == null ? u : u.replace(queryParameters: q);
  }

  Future<Map<String, dynamic>> _json(http.Response r) async =>
      jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;

  /// Backend ayakta mi, gercek Open Gateway kimlik bilgisi var mi?
  Future<Map<String, dynamic>> saglik() async =>
      _json(await _http.get(_uri('saglik')).timeout(const Duration(seconds: 5)));

  /// 1) NV baslat. mock=false ise donen authorizeUrl cihazda ACILMALIDIR
  /// (hucresel ag uzerinden), sonra [nvDurum] ile sonuc beklenir.
  Future<NvSonuc> nvBasla(String telefon) async {
    final r = await _http.post(_uri('nv/basla'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'telefon': telefon}));
    final j = await _json(r);
    final state = (j['state'] ?? '') as String;
    final mock = j['mock'] == true;
    if (mock) {
      final d = await nvDurum(state);
      return NvSonuc(
        dogrulandi: d.dogrulandi,
        state: state,
        mock: true,
        detay: 'MOCK: şebeke doğrulaması benzetildi (SMS/OTP yok)',
      );
    }
    return NvSonuc(
      dogrulandi: false,
      state: state,
      authorizeUrl: j['authorizeUrl'] as String?,
      detay: 'Şebeke doğrulaması bekleniyor',
    );
  }

  /// 2) NV sonucunu sorgular (callback backend'e dustukten sonra true olur).
  Future<NvSonuc> nvDurum(String state) async {
    final j = await _json(await _http.get(_uri('nv/durum', {'state': state})));
    return NvSonuc(
      dogrulandi: j['verified'] == true,
      state: state,
      detay: j['hata']?.toString() ?? '',
    );
  }

  /// 3) QoD oturumu ac. Turkcell dagitiminda 201 Created = basarili.
  Future<bool> qodOturum({required String state, int sure = 60}) async {
    final r = await _http.post(_uri('qod/oturum'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'state': state, 'sure': sure}));
    return (await _json(r))['ok'] == true;
  }

  /// 4) Kaydedilen MP4'u backend'e yukler -> is kimligi doner.
  Future<String> videoYukle(List<int> mp4) async {
    final r = await _http.post(_uri('yukle'),
        headers: {'Content-Type': 'application/octet-stream'}, body: mp4);
    return ((await _json(r))['id'] ?? '') as String;
  }

  /// 5) YZ imajini tetikler.
  Future<void> cikarimBaslat(String id) async {
    await _http.post(_uri('cikarim'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'id': id}));
  }

  /// 6) Sonucu (results.json + SHA256) sorgular.
  Future<CikarimSonuc> sonuc(String id) async {
    final j = await _json(await _http.get(_uri('sonuc', {'id': id})));
    return CikarimSonuc(
      durum: (j['durum'] ?? 'yok') as String,
      results: j['results'] as Map<String, dynamic>?,
      sha256: j['sha256'] as String?,
      hata: j['hata'] as String?,
    );
  }

  /// Cikarim bitene kadar bekler (hakem karsisinda ilerleme gostermek icin).
  Stream<CikarimSonuc> cikarimAkisi(String id,
      {Duration aralik = const Duration(seconds: 2)}) async* {
    while (true) {
      final s = await sonuc(id);
      yield s;
      if (s.bitti || s.durum == 'hata') return;
      await Future<void>.delayed(aralik);
    }
  }
}
