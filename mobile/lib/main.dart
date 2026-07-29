/// MİMİK — 5G ve Yapay Zekâ ile Akıllı Yol Güvenliği (final etabı mobil uygulaması).
///
/// Akis: Number Verification ile sessiz giris -> canli analiz ekrani (QoD durumu,
/// arac bilgisi, tespitler). Agir cikarim laptop/GPU tarafinda kosar.
library;

import 'package:flutter/material.dart';

import 'screens/login_screen.dart';
import 'services/backend_client.dart';
import 'services/nv_service.dart';

void main() => runApp(const MimikApp());

class MimikApp extends StatelessWidget {
  /// Testlerde sonlu bir akis enjekte edilebilir; uretimde null (BackendClient).
  final AnalizKaynagi? kaynak;

  const MimikApp({super.key, this.kaynak});

  @override
  Widget build(BuildContext context) {
    // Turkcell uc noktalari gelince: NvConfig(mock: false, authorizeUrl: ..., clientId: ...)
    final nv = NvService(const NvConfig(mock: true));

    return MaterialApp(
      title: 'MİMİK',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4CC38A),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0F151D),
        cardTheme: const CardThemeData(color: Color(0xFF17202B)),
      ),
      home: LoginScreen(nv: nv, kaynak: kaynak),
    );
  }
}
