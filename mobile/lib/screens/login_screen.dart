/// Sessiz giris ekrani — Number Verification ile SMS/OTP olmadan dogrulama.
library;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

import '../services/backend_client.dart';
import '../services/demo_service.dart';
import '../services/nv_service.dart';
import 'live_screen.dart';

class LoginScreen extends StatefulWidget {
  final NvService nv;

  /// Canli analiz kaynagi; verilmezse [BackendClient] varsayilani kullanilir.
  final AnalizKaynagi? kaynak;

  const LoginScreen({super.key, required this.nv, this.kaynak});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _controller = TextEditingController(text: '+90');

  /// Analiz ucunun adresi. Bos = ayni origin (uygulama sunucudan servis ediliyorsa).
  final _sunucu = TextEditingController(text: kIsWeb ? '' : 'http://192.168.1.20:8080');
  bool _calisiyor = false;
  bool _ayarlarAcik = false;
  String? _hata;

  /// Testlerde enjekte edilen kaynak varsa o, yoksa girilen adrese gore istemci.
  /// Web'de adres bos birakilabilir; Android'de laptop IP'si girilir.
  AnalizKaynagi _kaynakOlustur() {
    if (widget.kaynak != null) return widget.kaynak!;
    final adres = _sunucu.text.trim();
    if (adres.isEmpty && !kIsWeb) return BackendClient(mock: true); // demo yedegi
    return BackendClient(baseUrl: adres, mock: false);
  }

  Future<void> _dogrula() async {
    setState(() {
      _calisiyor = true;
      _hata = null;
    });
    try {
      // NV artik BACKEND uzerinden yapilir: client_id/secret orada durur ve
      // dogrulama cihazin HUCRESEL agi uzerinden gerceklesir (sartname geregi).
      final telefon = _controller.text.trim();
      bool dogrulandi;
      String detay;
      try {
        final nv = await DemoService(baseUrl: _sunucu.text.trim()).nvBasla(telefon);
        if (!nv.dogrulandi && nv.authorizeUrl != null) {
          // Gercek akis: cihaz mobil veride iken bu adres acilmali, sonra
          // backend callback'i alinca /nv/durum true doner.
          setState(() => _hata = 'Şebeke doğrulaması bekleniyor. Cihaz mobil '
              'veride olmalı (Wi-Fi kapalı).\nAdres: ${nv.authorizeUrl}');
          return;
        }
        dogrulandi = nv.dogrulandi;
        detay = nv.detay;
      } on Object {
        // Backend erisilemiyorsa (gelistirme) yerel mock ile devam et.
        final yerel = await widget.nv.verify(telefon);
        dogrulandi = yerel.verified;
        detay = yerel.detail;
      }
      if (!mounted) return;
      if (dogrulandi) {
        Navigator.of(context).pushReplacement(MaterialPageRoute(
          builder: (_) => LiveScreen(telefon: telefon, kaynak: _kaynakOlustur()),
        ));
      } else {
        setState(() => _hata = detay);
      }
    } catch (e) {
      if (mounted) setState(() => _hata = '$e');
    } finally {
      if (mounted) setState(() => _calisiyor = false);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _sunucu.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.shield_outlined, size: 72, color: Color(0xFF4CC38A)),
              const SizedBox(height: 16),
              const Text('MİMİK',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 34, fontWeight: FontWeight.bold, letterSpacing: 2)),
              const SizedBox(height: 6),
              const Text('5G ve Yapay Zekâ ile Akıllı Yol Güvenliği',
                  textAlign: TextAlign.center, style: TextStyle(color: Colors.white70)),
              const SizedBox(height: 40),
              TextField(
                controller: _controller,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Telefon numarası (E.164)',
                  hintText: '+905XXXXXXXXX',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.sim_card_outlined),
                ),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _calisiyor ? null : _dogrula,
                icon: _calisiyor
                    ? const SizedBox(
                        width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.verified_user_outlined),
                label: Text(_calisiyor ? 'Şebeke doğruluyor...' : 'Şebeke ile doğrula'),
                style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16)),
              ),
              if (_hata != null) ...[
                const SizedBox(height: 12),
                Text(_hata!, style: const TextStyle(color: Color(0xFFE5534B))),
              ],
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  onPressed: () => setState(() => _ayarlarAcik = !_ayarlarAcik),
                  icon: Icon(_ayarlarAcik ? Icons.expand_less : Icons.expand_more, size: 20),
                  label: const Text('Bağlantı ayarları'),
                ),
              ),
              if (_ayarlarAcik)
                TextField(
                  controller: _sunucu,
                  keyboardType: TextInputType.url,
                  decoration: const InputDecoration(
                    labelText: 'Analiz ucu adresi',
                    hintText: 'http://192.168.1.20:8080  (boş = aynı sunucu)',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.dns_outlined),
                    helperText: 'Laptop üzerinde: python scripts/live_server.py',
                  ),
                ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF17202B),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF2B3948)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline, size: 20, color: Colors.white54),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Doğrulama Number Verification API ile şebeke üzerinden yapılır: '
                        'SMS beklemesi ve manuel kod girişi yoktur.',
                        style: TextStyle(fontSize: 12, color: Colors.white60),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
