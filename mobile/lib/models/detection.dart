/// Analiz ucunun (laptop) urettigi sonuc semasi — FTR results.json ile birebir.
library;

class AracBilgisi {
  final String tip;
  final String plaka;
  final String renk;
  final double confidenceScore;

  const AracBilgisi({
    required this.tip,
    required this.plaka,
    required this.renk,
    required this.confidenceScore,
  });

  /// Gecis boyunca karakter oylamasi oturmadan ara okumalar cikabilir; bunlari
  /// kesin plaka gibi gostermemek icin esik. (0.5 = uc modelin ortak guveni)
  bool get plakaKararli =>
      confidenceScore >= 0.5 && plaka.length >= 7 && plaka != 'tespit edilemedi';

  factory AracBilgisi.fromJson(Map<String, dynamic> j) => AracBilgisi(
        tip: (j['tip'] ?? '-') as String,
        plaka: (j['plaka'] ?? '-') as String,
        renk: (j['renk'] ?? '-') as String,
        confidenceScore: ((j['confidence_score'] ?? 0) as num).toDouble(),
      );

  static const bos = AracBilgisi(tip: '-', plaka: '-', renk: '-', confidenceScore: 0);
}

class Tespit {
  final double zamanSaniye;
  final String kategori; // sofor_eylemi | nesneler | yolcular
  final String etiket;
  final double confidenceScore;

  const Tespit({
    required this.zamanSaniye,
    required this.kategori,
    required this.etiket,
    required this.confidenceScore,
  });

  factory Tespit.fromJson(Map<String, dynamic> j) => Tespit(
        zamanSaniye: ((j['zaman_saniye'] ?? 0) as num).toDouble(),
        kategori: (j['kategori'] ?? '') as String,
        etiket: (j['etiket'] ?? '') as String,
        confidenceScore: ((j['confidence_score'] ?? 0) as num).toDouble(),
      );
}

/// QoD oturum durumu — sartname geregi ekranda gorunur olmali.
class QodDurumu {
  final String durum; // IZLEME | TALEP | PENCERE
  final String? sessionId;
  final String? qosProfile;
  final double mbps;

  const QodDurumu({
    this.durum = 'IZLEME',
    this.sessionId,
    this.qosProfile,
    this.mbps = 0,
  });

  bool get yuksekKalite => durum == 'PENCERE';

  factory QodDurumu.fromJson(Map<String, dynamic> j) => QodDurumu(
        durum: (j['durum'] ?? 'IZLEME') as String,
        sessionId: j['sessionId'] as String?,
        qosProfile: j['qosProfile'] as String?,
        mbps: ((j['mbps'] ?? 0) as num).toDouble(),
      );
}

class AnalizDurumu {
  final AracBilgisi arac;
  final List<Tespit> tespitler;
  final QodDurumu qod;

  const AnalizDurumu({
    required this.arac,
    required this.tespitler,
    required this.qod,
  });

  factory AnalizDurumu.fromJson(Map<String, dynamic> j) {
    final sonuc = (j['sonuc'] ?? const {}) as Map<String, dynamic>;
    final liste = (sonuc['tespitler'] ?? const []) as List<dynamic>;
    return AnalizDurumu(
      arac: sonuc['arac_bilgisi'] == null
          ? AracBilgisi.bos
          : AracBilgisi.fromJson(sonuc['arac_bilgisi'] as Map<String, dynamic>),
      tespitler:
          liste.map((e) => Tespit.fromJson(e as Map<String, dynamic>)).toList(),
      qod: j['qod'] == null
          ? const QodDurumu()
          : QodDurumu.fromJson(j['qod'] as Map<String, dynamic>),
    );
  }

  static const bos = AnalizDurumu(
    arac: AracBilgisi.bos,
    tespitler: <Tespit>[],
    qod: QodDurumu(),
  );
}
