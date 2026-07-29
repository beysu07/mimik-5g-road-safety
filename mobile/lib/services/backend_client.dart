/// Analiz ucu (laptop/GPU) ile baglanti: canli sonuc + QoD durumu.
///
/// Mimari: telefon = NV girisi + gosterim, laptop = 7 modelli cikarim hatti.
/// Sunucu tarafi: scripts/live_server.py  (GET /durum)
library;

import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import '../models/detection.dart';

/// Canli analiz durumunun kaynagi. Gercek uygulamada [BackendClient], testlerde
/// sonlu bir akis veren sahte uygulama kullanilir (arayuz sayesinde ekran degismez).
abstract class AnalizKaynagi {
  Stream<AnalizDurumu> durumAkisi();

  /// Canli isaretli kare adresi; goruntu yoksa null.
  String? kareUrl() => null;
}

class BackendClient implements AnalizKaynagi {
  /// Ornek: http://192.168.1.20:8080  (laptop'un yarisma agindaki adresi).
  /// Bos birakilirsa istekler AYNI ORIGIN'e gider: uygulama web surumu olarak
  /// live_server.py uzerinden servis edildiginde adres girmeye gerek kalmaz.
  final String baseUrl;
  final bool mock;
  final Duration interval;
  final http.Client _http;

  BackendClient({
    this.baseUrl = '',
    this.mock = true,
    this.interval = const Duration(milliseconds: 800),
    http.Client? client,
  }) : _http = client ?? http.Client();

  /// Bos baseUrl -> ayni origin (web surumu); dolu ise mutlak adres (Android app).
  Uri _uri(String yol) => baseUrl.isEmpty
      ? Uri.base.resolve(yol)
      : Uri.parse('${baseUrl.replaceAll(RegExp(r"/+$"), "")}/$yol');

  /// Canli isaretli kare adresi. Tarayici onbellegini asmak icin zaman damgasi eklenir.
  /// Mock modda goruntu yoktur (null) -> ekran yalnizca metin gosterir.
  @override
  String? kareUrl() => mock
      ? null
      : _uri('kare').replace(queryParameters: {
          't': DateTime.now().millisecondsSinceEpoch.toString(),
        }).toString();

  /// Periyodik olarak analiz durumunu yayinlar.
  @override
  Stream<AnalizDurumu> durumAkisi() async* {
    if (mock) {
      yield* _mockAkis();
      return;
    }
    while (true) {
      try {
        final res = await _http.get(_uri('durum')).timeout(const Duration(seconds: 3));
        if (res.statusCode == 200) {
          yield AnalizDurumu.fromJson(
              jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>);
        }
      } catch (_) {
        // Baglanti kopmasi demoyu durdurmasin; bir sonraki turda yeniden denenir.
      }
      await Future<void>.delayed(interval);
    }
  }

  /// Sunucu olmadan da demo yapilabilsin diye senaryo benzetimi:
  /// IZLEME (best-effort) -> TALEP -> PENCERE (plaka okunur) -> IZLEME
  Stream<AnalizDurumu> _mockAkis() async* {
    final rnd = Random();
    var adim = 0;
    while (true) {
      adim = (adim + 1) % 24;
      late QodDurumu qod;
      late AracBilgisi arac;
      var tespitler = <Tespit>[];

      if (adim < 6) {
        qod = QodDurumu(durum: 'IZLEME', mbps: 0.8 + rnd.nextDouble() * 0.3);
        arac = AracBilgisi.bos;
      } else if (adim < 8) {
        qod = QodDurumu(
            durum: 'TALEP', sessionId: 'mock-oturum', qosProfile: 'QOS_L', mbps: 1.0);
        arac = const AracBilgisi(
            tip: 'suv', plaka: 'okunuyor...', renk: 'siyah', confidenceScore: 0.4);
      } else {
        qod = QodDurumu(
            durum: 'PENCERE',
            sessionId: 'mock-oturum',
            qosProfile: 'QOS_L',
            mbps: 24 + rnd.nextDouble() * 6);
        arac = const AracBilgisi(
            tip: 'suv', plaka: '34TC8532', renk: 'siyah', confidenceScore: 0.81);
        tespitler = const [
          Tespit(
              zamanSaniye: 1.2,
              kategori: 'sofor_eylemi',
              etiket: 'telefonla_konusma',
              confidenceScore: 0.71),
        ];
      }
      yield AnalizDurumu(arac: arac, tespitler: tespitler, qod: qod);
      await Future<void>.delayed(interval);
    }
  }
}
