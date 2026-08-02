"""MİMİK canli demo backend'i — VM'de (8.234.235.53) kosar.

Sartname akisi (Final Yarisma Senaryosu, Sekil 1):
  NV -> QoD -> streaming kaydi -> backend'e yukle -> YZ imajini tetikle
     -> results.json + SHA256 uygulamada gosterilir

Uc noktalar:
  GET  /saglik                 -> {"ok": true, "ogw_hazir": bool}
  POST /nv/basla   {telefon}   -> {"authorizeUrl": ..., "state": ...}
  GET  /api/auth/callback?code=&state=  -> jeton alir, numarayi dogrular
  GET  /nv/durum?state=        -> {"verified": bool, ...}
  POST /qod/oturum {sure}      -> {"ok": bool, "detay": {...}}   (201 = basarili)
  POST /yukle       (MP4 govde)-> {"id": ...}    kaydeder
  POST /cikarim    {id}        -> Docker imajini calistirir
  GET  /sonuc?id=              -> {"results": {...}, "sha256": "..."}

Kullanim (VM'de):
  OGW_API_URL=... OGW_CLIENT_ID=... OGW_CLIENT_SECRET=... \
  python3 backend/server.py --port 8080
Kimlik bilgisi verilmezse MOCK modda calisir (gelistirme kimlik beklemesin).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ogw import OgwClient, OgwHata            # noqa: E402

KOK = os.environ.get('DEMO_KOK', '/tmp/mimik_demo')
IMAJ = os.environ.get('YZ_IMAJ', 'teknofest-2026/mimik:latest')
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'mobile', 'build', 'web')

_kilit = threading.Lock()
_oturumlar = {}          # state -> {"verified":bool, "telefon":..., "detay":...}
_isler = {}              # id -> {"durum":..., "results":..., "sha256":...}
ogw = OgwClient()


def _kaydet(sozluk, anahtar, **kv):
    with _kilit:
        sozluk.setdefault(anahtar, {}).update(kv)


def cikarim_calistir(is_id):
    """Yuklenen videoyu YZ imajina verir (Web UI ile ayni mount duzeni)."""
    klasor = os.path.join(KOK, is_id)
    giris, cikis = os.path.join(klasor, 'input'), os.path.join(klasor, 'output')
    os.makedirs(cikis, exist_ok=True)
    komut = ['docker', 'run', '--rm', '--gpus', 'all',
             '-v', giris + ':/app/data/input:ro',
             '-v', cikis + ':/app/data/output', IMAJ]
    _kaydet(_isler, is_id, durum='calisiyor', komut=' '.join(komut))
    try:
        p = subprocess.run(komut, capture_output=True, text=True, timeout=900)
        yol = os.path.join(cikis, 'results.json')
        if p.returncode != 0 or not os.path.exists(yol):
            _kaydet(_isler, is_id, durum='hata',
                    hata=(p.stderr or '')[-800:] or 'results.json uretilmedi')
            return
        ham = open(yol, 'rb').read()
        _kaydet(_isler, is_id, durum='bitti',
                results=json.loads(ham.decode('utf-8')),
                sha256=hashlib.sha256(ham).hexdigest())
    except Exception as e:
        _kaydet(_isler, is_id, durum='hata', hata=str(e))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB_DIR if os.path.isdir(WEB_DIR) else None, **kw)

    # ------------------------------------------------------------ yardimcilar
    def _json(self, obj, kod=200):
        g = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(kod)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(g)))
        self.end_headers()
        self.wfile.write(g)

    def _govde(self):
        n = int(self.headers.get('Content-Length') or 0)
        return self.rfile.read(n) if n else b''

    def _sorgu(self):
        from urllib.parse import parse_qs, urlparse
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

    # ------------------------------------------------------------------- GET
    def do_GET(self):
        yol = self.path.split('?')[0]
        if yol == '/saglik':
            self._json({'ok': True, 'ogw_hazir': ogw.cfg.hazir, 'mock': ogw.mock,
                        'imaj': IMAJ})
        elif yol == '/api/auth/callback':
            q = self._sorgu()
            state, code = q.get('state', ''), q.get('code', '')
            try:
                jeton = ogw.token_al(code)
                tel = (_oturumlar.get(state) or {}).get('telefon', '')
                ok, detay = ogw.numara_dogrula(tel, jeton)
                _kaydet(_oturumlar, state, verified=ok, detay=detay, jeton=jeton)
                self._json({'verified': ok, 'detay': detay})
            except OgwHata as e:
                _kaydet(_oturumlar, state, verified=False, detay=str(e))
                self._json({'verified': False, 'hata': str(e)}, 502)
        elif yol == '/nv/durum':
            st = self._sorgu().get('state', '')
            self._json(_oturumlar.get(st) or {'verified': False, 'bilinmiyor': True})
        elif yol == '/sonuc':
            self._json(_isler.get(self._sorgu().get('id', '')) or {'durum': 'yok'}, 200)
        elif os.path.isdir(WEB_DIR):
            super().do_GET()                       # mobil uygulamanin web surumu
        else:
            self._json({'hata': 'bilinmeyen uc nokta'}, 404)

    # ------------------------------------------------------------------ POST
    def do_POST(self):
        yol = self.path.split('?')[0]
        try:
            if yol == '/nv/basla':
                istek = json.loads(self._govde() or b'{}')
                url, state = ogw.authorize_url()
                _kaydet(_oturumlar, state, telefon=istek.get('telefon', ''),
                        verified=False)
                if ogw.mock:                        # kimlik yokken akisi bloklama
                    ok, detay = ogw.numara_dogrula(istek.get('telefon', ''), 'mock')
                    _kaydet(_oturumlar, state, verified=ok, detay=detay)
                self._json({'authorizeUrl': url, 'state': state, 'mock': ogw.mock})

            elif yol == '/qod/oturum':
                istek = json.loads(self._govde() or b'{}')
                st = istek.get('state', '')
                jeton = (_oturumlar.get(st) or {}).get('jeton')
                ok, detay = ogw.qod_oturum(istek.get('sure', 60), jeton)
                self._json({'ok': ok, 'detay': detay})

            elif yol == '/yukle':
                is_id = uuid.uuid4().hex[:10]
                giris = os.path.join(KOK, is_id, 'input')
                os.makedirs(giris, exist_ok=True)
                ham = self._govde()
                with open(os.path.join(giris, 'video.mp4'), 'wb') as f:
                    f.write(ham)
                _kaydet(_isler, is_id, durum='yuklendi', bayt=len(ham))
                self._json({'id': is_id, 'bayt': len(ham)})

            elif yol == '/cikarim':
                is_id = json.loads(self._govde() or b'{}').get('id', '')
                if is_id not in _isler:
                    self._json({'hata': 'is yok'}, 404); return
                threading.Thread(target=cikarim_calistir, args=(is_id,),
                                 daemon=True).start()
                self._json({'id': is_id, 'durum': 'baslatildi'})
            else:
                self._json({'hata': 'bilinmeyen uc nokta'}, 404)
        except Exception as e:
            self._json({'hata': str(e)}, 500)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    a = ap.parse_args()
    os.makedirs(KOK, exist_ok=True)
    print('OGW:', ogw.cfg, '| mock:', ogw.mock)
    print('YZ imaji:', IMAJ, '| calisma klasoru:', KOK)
    print('Backend: http://0.0.0.0:%d/saglik' % a.port)
    ThreadingHTTPServer(('0.0.0.0', a.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
