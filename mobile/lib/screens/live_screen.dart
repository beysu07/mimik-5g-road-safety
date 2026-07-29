/// Canli analiz ekrani — QoD durumu + arac bilgisi + tespitler.
///
/// Sartname 6.7-b: "Tespit edilen veriler, takimlarca gelistirilen mobil uygulama
/// ekraninda gosterilecektir."
library;

import 'package:flutter/material.dart';

import '../models/detection.dart';
import '../services/backend_client.dart';

class LiveScreen extends StatelessWidget {
  final String telefon;
  final AnalizKaynagi kaynak;

  LiveScreen({super.key, required this.telefon, AnalizKaynagi? kaynak})
      : kaynak = kaynak ?? BackendClient(mock: true);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MİMİK — Canlı Analiz'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Row(children: [
              const Icon(Icons.verified_user, size: 16, color: Color(0xFF4CC38A)),
              const SizedBox(width: 6),
              Text(telefon, style: const TextStyle(fontSize: 12)),
            ]),
          ),
        ],
      ),
      body: StreamBuilder<AnalizDurumu>(
        stream: kaynak.durumAkisi(),
        initialData: AnalizDurumu.bos,
        builder: (context, snap) {
          final d = snap.data ?? AnalizDurumu.bos;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _CanliGoruntu(url: kaynak.kareUrl()),
              _QodBanner(qod: d.qod),
              const SizedBox(height: 16),
              _AracKarti(arac: d.arac),
              const SizedBox(height: 16),
              Text('Tespitler (${d.tespitler.length})',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              if (d.tespitler.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(
                      child: Text('Henüz tespit yok', style: TextStyle(color: Colors.white38))),
                )
              else
                ...d.tespitler.map((t) => _TespitSatiri(tespit: t)),
            ],
          );
        },
      ),
    );
  }
}

/// Analiz ucundan gelen isaretli canli kare (arac kutusu + QoD serit).
class _CanliGoruntu extends StatelessWidget {
  final String? url;
  const _CanliGoruntu({required this.url});

  @override
  Widget build(BuildContext context) {
    if (url == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: AspectRatio(
          aspectRatio: 16 / 9,
          child: Image.network(
            url!,
            fit: BoxFit.cover,
            gaplessPlayback: true, // kare degisiminde titreme olmasin
            errorBuilder: (_, __, ___) => Container(
              color: const Color(0xFF17202B),
              alignment: Alignment.center,
              child: const Text('Görüntü bekleniyor...',
                  style: TextStyle(color: Colors.white38)),
            ),
          ),
        ),
      ),
    );
  }
}

/// QoD durumu: sebeke kaynaginin ne zaman acilip kapandigini gorunur kilar.
class _QodBanner extends StatelessWidget {
  final QodDurumu qod;
  const _QodBanner({required this.qod});

  @override
  Widget build(BuildContext context) {
    final (renk, ikon, baslik) = switch (qod.durum) {
      'PENCERE' => (const Color(0xFF4CC38A), Icons.speed, 'QoD AKTİF — yüksek kalite'),
      'TALEP' => (const Color(0xFFD9A441), Icons.hourglass_top, 'QoD talep edildi...'),
      _ => (const Color(0xFF6B7A8C), Icons.wifi_tethering, 'İzleme — standart kalite'),
    };
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: renk.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: renk.withValues(alpha: 0.6), width: 1.5),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(ikon, color: renk),
          const SizedBox(width: 10),
          Expanded(
              child: Text(baslik,
                  style: TextStyle(color: renk, fontWeight: FontWeight.bold, fontSize: 16))),
          Text('${qod.mbps.toStringAsFixed(1)} Mbps',
              style: TextStyle(color: renk, fontWeight: FontWeight.bold)),
        ]),
        if (qod.sessionId != null) ...[
          const SizedBox(height: 8),
          Text('oturum: ${qod.sessionId}   profil: ${qod.qosProfile ?? "-"}',
              style: const TextStyle(fontSize: 11, color: Colors.white54)),
        ],
      ]),
    );
  }
}

class _AracKarti extends StatelessWidget {
  final AracBilgisi arac;
  const _AracKarti({required this.arac});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Araç Bilgisi',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 14),
          Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 10),
              decoration: BoxDecoration(
                color: arac.plakaKararli ? Colors.white : const Color(0xFFE8E8E8),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.black26, width: 2),
              ),
              // Gecis basinda oylama henuz oturmamisken ara okumayi plaka gibi
              // gostermek yaniltici olur -> dusuk guvende "okunuyor..." yazilir.
              child: Text(
                arac.plakaKararli ? arac.plaka : 'okunuyor...',
                style: TextStyle(
                    color: arac.plakaKararli ? Colors.black : Colors.black45,
                    fontSize: arac.plakaKararli ? 26 : 20,
                    fontWeight: FontWeight.bold,
                    letterSpacing: arac.plakaKararli ? 3 : 1),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: _Alan(etiket: 'Tip', deger: arac.tip)),
            Expanded(child: _Alan(etiket: 'Renk', deger: arac.renk)),
            Expanded(
                child: _Alan(
                    etiket: 'Güven', deger: arac.confidenceScore.toStringAsFixed(2))),
          ]),
        ]),
      ),
    );
  }
}

class _Alan extends StatelessWidget {
  final String etiket;
  final String deger;
  const _Alan({required this.etiket, required this.deger});

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text(etiket, style: const TextStyle(fontSize: 12, color: Colors.white54)),
      const SizedBox(height: 4),
      Text(deger, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
    ]);
  }
}

class _TespitSatiri extends StatelessWidget {
  final Tespit tespit;
  const _TespitSatiri({required this.tespit});

  @override
  Widget build(BuildContext context) {
    final renk = switch (tespit.kategori) {
      'sofor_eylemi' => const Color(0xFFE5904B),
      'yolcular' => const Color(0xFF5B9BD5),
      _ => const Color(0xFF9C7BD5),
    };
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: renk.withValues(alpha: 0.2),
          child: Icon(Icons.warning_amber_rounded, color: renk, size: 20),
        ),
        title: Text(tespit.etiket, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text('${tespit.kategori}  ·  ${tespit.zamanSaniye.toStringAsFixed(1)} sn'),
        trailing: Text(tespit.confidenceScore.toStringAsFixed(2),
            style: TextStyle(color: renk, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
