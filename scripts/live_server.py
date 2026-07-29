"""Canli analiz sunucusu — mobil uygulamanin bagli oldugu laptop/GPU ucu.

Mimari: telefon (NV girisi + gosterim)  <--HTTP-->  laptop (7 modelli cikarim + QoD)

Uc noktalar:
    GET /durum   -> {"qod": {...}, "sonuc": {results.json semasi}, "guncelleme": ts}
    GET /saglik  -> {"ok": true}
    GET /*       -> mobile/build/web (varsa) - uygulamanin web surumu ayni adresten servis
                    edilir; boylece telefon (iPhone dahil) tarayicidan acip kullanabilir
                    ve istekler ayni origin'e gider (CORS sorunu olusmaz).

Kullanim:
    python scripts/live_server.py [video] [--port 8080] [--dongu]
Telefon: http://<laptop-ip>:8080/  ·  Android app: BackendClient(baseUrl: ..., mock: false)
"""
import argparse
import json
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from net.boost_controller import BoostController          # noqa: E402
from net.netsim import BEST_EFFORT, QOS_L, NetworkSimulator  # noqa: E402
from net.qod import QoDClient                             # noqa: E402
from src.predict import TARGET_FPS, VEHICLE_COCO, Pipeline  # noqa: E402

_kilit = threading.Lock()
_durum = {
    'qod': {'durum': 'IZLEME', 'sessionId': None, 'qosProfile': None, 'mbps': 0.0},
    'sonuc': {'arac_bilgisi': {}, 'tespitler': []},
    'guncelleme': 0.0,
}
_son_kare = {'jpeg': None}          # telefonda gosterilecek son isaretli kare


def _yaz(**kwargs):
    with _kilit:
        _durum.update(kwargs)
        _durum['guncelleme'] = round(time.time(), 3)


def _kare_yayinla(frame, vbox, qod_durum, mbps):
    """Kareyi kucultup arac kutusu + QoD serit ile isaretleyip JPEG olarak saklar."""
    h, w = frame.shape[:2]
    olcek = 720.0 / max(1, w)
    kare = cv2.resize(frame, (int(w * olcek), int(h * olcek))) if olcek < 1 else frame.copy()
    if vbox is not None:
        x1, y1, x2, y2 = [int(v * olcek) if olcek < 1 else int(v) for v in vbox]
        cv2.rectangle(kare, (x1, y1), (x2, y2), (80, 220, 80), 3)
    renk = (76, 195, 138) if qod_durum == 'PENCERE' else (140, 140, 140)
    cv2.rectangle(kare, (0, 0), (kare.shape[1], 34), (20, 24, 32), -1)
    etiket = 'QoD AKTIF' if qod_durum == 'PENCERE' else qod_durum
    cv2.putText(kare, '%s  %.1f Mbps' % (etiket, mbps), (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, renk, 2)
    ok, buf = cv2.imencode('.jpg', kare, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if ok:
        with _kilit:
            _son_kare['jpeg'] = buf.tobytes()


class CanliHook:
    """Her karede: agdan gecir -> hafif izleme -> QoD karari -> kalite anahtarla."""

    def __init__(self, pipe, sim, ctrl):
        self.pipe, self.sim, self.ctrl = pipe, sim, ctrl
        self.i = 0

    def __call__(self, frame):
        out = self.sim(frame)
        self.i += 1
        vbox = None
        try:
            r = self.pipe.m_vehicle.predict(out, verbose=False, conf=0.3)[0]
            best, area = None, 0
            for b in r.boxes:
                if int(b.cls) in VEHICLE_COCO:
                    x1, y1, x2, y2 = map(int, b.xyxy[0])
                    a = (x2 - x1) * (y2 - y1)
                    if a > area:
                        area, best = a, (max(0, x1), max(0, y1), x2, y2)
            vbox = best
        except Exception:
            pass
        aktif = self.ctrl.update(vbox, out.shape, now=self.i / float(TARGET_FPS))
        self.sim.switch(QOS_L if aktif else BEST_EFFORT)
        mbps = round(self.sim.mbps(TARGET_FPS), 2)
        _yaz(qod={
            'durum': self.ctrl.state,
            'sessionId': self.ctrl.qod.session_id,
            'qosProfile': self.ctrl.qos_profile if aktif else None,
            'mbps': mbps,
        })
        try:
            _kare_yayinla(out, vbox, self.ctrl.state, mbps)
        except Exception:
            pass                                  # gorsel yayin demoyu durdurmasin
        return out


def analiz_dongusu(video, dongu, qod_base_url=None, qod_token=None, telefon=None):
    pipe = Pipeline()
    qod = QoDClient(base_url=qod_base_url, token=qod_token,
                    mock=not qod_base_url)      # Turkcell bilgisi gelince mock kapanir
    ctrl = BoostController(qod, qos_profile='QOS_L', duration=30,
                           device={'phoneNumber': telefon} if telefon else None)
    print('Analiz basladi: %s (mock QoD: %s)' % (video, qod.mock))
    while True:
        sim = NetworkSimulator(BEST_EFFORT)
        hook = CanliHook(pipe, sim, ctrl)
        try:
            sonuc = pipe.run(video, frame_hook=hook,
                             on_update=lambda s: _yaz(sonuc=s), update_every=2)
            _yaz(sonuc=sonuc)
        except Exception as e:
            print('analiz hatasi:', e, file=sys.stderr)
        ctrl.release('gecis bitti')
        _yaz(qod={'durum': 'IZLEME', 'sessionId': None, 'qosProfile': None, 'mbps': 0.0})
        if not dongu:
            break
        time.sleep(2)                            # araclar arasi bosluk (izleme fazi)


WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'mobile', 'build', 'web')


class Handler(SimpleHTTPRequestHandler):
    """API uc noktalari + (varsa) uygulamanin web surumu ayni sunucudan."""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB_DIR if os.path.isdir(WEB_DIR) else None, **kw)

    def _json(self, obj, code=200):
        govde = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def do_GET(self):
        if self.path.startswith('/durum'):
            with _kilit:
                self._json(dict(_durum))
        elif self.path.startswith('/kare'):
            with _kilit:
                jpeg = _son_kare['jpeg']
            if not jpeg:
                self._json({'hata': 'kare yok'}, 404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(jpeg)))
            self.end_headers()
            self.wfile.write(jpeg)
        elif self.path.startswith('/saglik'):
            self._json({'ok': True})
        elif os.path.isdir(WEB_DIR):
            super().do_GET()                      # Flutter web surumu
        else:
            self._json({'hata': 'bilinmeyen uc nokta'}, 404)

    def log_message(self, *a):
        pass                                      # istek loglarini bastir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', nargs='?', default='docker_test/input/video.mp4')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--dongu', action='store_true', help='videoyu surekli tekrarla (demo)')
    ap.add_argument('--qod-url', default=None, help='Turkcell QoD base URL (yoksa mock)')
    ap.add_argument('--qod-token', default=None)
    ap.add_argument('--telefon', default=None, help='QoD device.phoneNumber (+90...)')
    a = ap.parse_args()

    threading.Thread(target=analiz_dongusu,
                     args=(a.video, a.dongu, a.qod_url, a.qod_token, a.telefon),
                     daemon=True).start()

    srv = ThreadingHTTPServer(('0.0.0.0', a.port), Handler)
    print('Canli sunucu: http://0.0.0.0:%d/durum  (mobil app buraya baglanir)' % a.port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nkapatiliyor...')


if __name__ == '__main__':
    main()
