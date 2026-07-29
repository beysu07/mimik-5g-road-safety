import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mimik_app/main.dart';
import 'package:mimik_app/models/detection.dart';
import 'package:mimik_app/screens/live_screen.dart';
import 'package:mimik_app/services/backend_client.dart';
import 'package:mimik_app/services/nv_service.dart';

/// Testlerde sonlu akis: gercek istemcinin sonsuz dongusu bekleyen timer birakir.
class SahteKaynak implements AnalizKaynagi {
  final AnalizDurumu durum;
  const SahteKaynak(this.durum);

  @override
  Stream<AnalizDurumu> durumAkisi() => Stream<AnalizDurumu>.value(durum);

  @override
  String? kareUrl() => null; // testlerde ag goruntusu cekilmez
}

const _pencereDurumu = AnalizDurumu(
  arac: AracBilgisi(tip: 'suv', plaka: '34TC8532', renk: 'siyah', confidenceScore: 0.81),
  tespitler: [
    Tespit(
        zamanSaniye: 1.2,
        kategori: 'sofor_eylemi',
        etiket: 'telefonla_konusma',
        confidenceScore: 0.71),
  ],
  qod: QodDurumu(durum: 'PENCERE', sessionId: 'test', qosProfile: 'QOS_L', mbps: 26.6),
);

void main() {
  testWidgets('Giris ekrani sessiz dogrulama sunar', (tester) async {
    await tester.pumpWidget(const MimikApp(kaynak: SahteKaynak(_pencereDurumu)));
    expect(find.text('MİMİK'), findsOneWidget);
    expect(find.text('Şebeke ile doğrula'), findsOneWidget);
  });

  testWidgets('Dogrulama sonrasi canli analiz ekranina gecilir', (tester) async {
    await tester.pumpWidget(const MimikApp(kaynak: SahteKaynak(_pencereDurumu)));
    await tester.tap(find.text('Şebeke ile doğrula'));
    await tester.pump(const Duration(seconds: 1)); // mock NV gecikmesi
    await tester.pumpAndSettle();
    expect(find.text('MİMİK — Canlı Analiz'), findsOneWidget);
    expect(find.text('34TC8532'), findsOneWidget);
  });

  testWidgets('Canli ekran QoD durumunu ve tespitleri gosterir', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: LiveScreen(telefon: '+900000000000', kaynak: const SahteKaynak(_pencereDurumu)),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Araç Bilgisi'), findsOneWidget);
    expect(find.textContaining('QoD AKTİF'), findsOneWidget);
    expect(find.text('telefonla_konusma'), findsOneWidget);
  });

  test('Sema ayristirma: results.json alanlari birebir okunur', () {
    final durum = AnalizDurumu.fromJson({
      'qod': {'durum': 'PENCERE', 'sessionId': 'x', 'qosProfile': 'QOS_L', 'mbps': 26.6},
      'sonuc': {
        'video_id': 'video.mp4',
        'arac_bilgisi': {
          'tip': 'suv',
          'plaka': '34TC8532',
          'renk': 'siyah',
          'confidence_score': 0.81,
        },
        'tespitler': [
          {
            'zaman_saniye': 1.2,
            'kategori': 'sofor_eylemi',
            'etiket': 'telefonla_konusma',
            'confidence_score': 0.71,
          }
        ],
      },
    });
    expect(durum.arac.plaka, '34TC8532');
    expect(durum.arac.tip, 'suv');
    expect(durum.qod.yuksekKalite, isTrue);
    expect(durum.tespitler.single.etiket, 'telefonla_konusma');
  });

  test('NV mock modda sessiz dogrulama yapar (SMS/OTP yok)', () async {
    final sonuc = await NvService(const NvConfig(mock: true)).verify('+905551112233');
    expect(sonuc.verified, isTrue);
    expect(sonuc.devicePhoneNumber, '+905551112233');
  });
}
