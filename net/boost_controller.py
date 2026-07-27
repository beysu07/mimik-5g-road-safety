"""Kritik durum -> QoD tetikleme durum makinesi.

IZLEME  : best-effort akis, yalnizca "arac var mi / yaklasiyor mu" izlenir
TALEP   : kritik durum dogrulandi, POST /sessions gonderildi, AVAILABLE bekleniyor
PENCERE : kalite yuksek; agir analizler (plaka OCR, kabin) burada yapilir
(BIRAKMA): arac cikti veya sure doldu -> DELETE /sessions, tekrar IZLEME

Sartname: kaynak "surekli acik musluk" degil, ihtiyaca gore acilip kapanan bir
kaynak olarak kullanilmalidir.
"""
import time

IZLEME = 'IZLEME'
TALEP = 'TALEP'
PENCERE = 'PENCERE'


class BoostController:
    """Arac yaklasmasini kalicilik sartiyla dogrular ve QoD penceresini yonetir.

    approach_frames: kritik durum icin gereken ardisik onayli kare sayisi
                     (anlik yanlis tespit pencereyi bosuna acmasin)
    min_area_ratio : arac kutusunun kareye orani - bu esigin ustu "yakin"
    grace_seconds  : arac kaybolunca pencereyi hemen kapatmadan onceki tolerans
    """

    def __init__(self, qod_client, qos_profile='QOS_L', duration=30,
                 device=None, application_server=None,
                 approach_frames=3, min_area_ratio=0.04, grace_seconds=1.5):
        self.qod = qod_client
        self.qos_profile, self.duration = qos_profile, duration
        self.device, self.application_server = device, application_server
        self.approach_frames = approach_frames
        self.min_area_ratio = min_area_ratio
        self.grace_seconds = grace_seconds

        self.state = IZLEME
        self.events = []            # (zaman, durum, aciklama) - ispat logu
        self._hits = 0
        self._prev_area = 0.0
        self._last_seen = None
        self._window_started = None

    # ------------------------------------------------------------- yardimcilar
    def _log(self, msg):
        self.events.append((round(time.time(), 3), self.state, msg))

    def _critical(self, vbox, frame_shape):
        """Kritik durum: arac kadrajda, yeterince buyuk ve BUYUYOR (yaklasiyor)."""
        if vbox is None:
            self._hits = 0
            self._prev_area = 0.0
            return False
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = vbox
        area = ((x2 - x1) * (y2 - y1)) / float(max(1, w * h))
        growing = area >= self._prev_area * 0.98      # kucuk titremeye tolerans
        self._prev_area = area
        if area >= self.min_area_ratio and growing:
            self._hits += 1
        else:
            self._hits = 0
        return self._hits >= self.approach_frames

    # ------------------------------------------------------------------ dongu
    def update(self, vbox, frame_shape, now=None):
        """Her karede cagrilir. Doner: True ise YUKSEK KALITE penceresi aktiftir."""
        now = now if now is not None else time.time()
        critical = self._critical(vbox, frame_shape)
        if vbox is not None:
            self._last_seen = now

        if self.state == IZLEME:
            if critical:
                self.state = TALEP
                self._log('kritik durum: arac yaklasiyor -> QoD talebi')
                try:
                    sid = self.qod.create_session(
                        qos_profile=self.qos_profile, duration=self.duration,
                        device=self.device, application_server=self.application_server)
                    self._log('POST /sessions -> %s' % sid)
                except Exception as e:                   # oturum acilamadi: akis surer
                    self.state = IZLEME
                    self._log('QoD talebi basarisiz: %s' % e)

        elif self.state == TALEP:
            info = None
            try:
                info = self.qod.get_session()
            except Exception as e:
                self._log('durum sorgusu hatasi: %s' % e)
            status = (info or {}).get('qosStatus')
            if status == 'AVAILABLE':
                self.state = PENCERE
                self._window_started = now
                self._log('qosStatus AVAILABLE -> yuksek kalite penceresi acildi')
            elif status == 'UNAVAILABLE':
                self.state = IZLEME
                self._log('qosStatus UNAVAILABLE -> best-effort ile devam')

        elif self.state == PENCERE:
            gone = self._last_seen is not None and (now - self._last_seen) > self.grace_seconds
            expired = self._window_started is not None and \
                (now - self._window_started) > self.duration
            if gone or expired:
                self.release('arac kadrajdan cikti' if gone else 'pencere suresi doldu')

        return self.state == PENCERE

    def release(self, reason='manuel'):
        """Pencereyi kapat ve sebeke kaynagini birak."""
        if self.qod.session_id:
            try:
                self.qod.delete_session()
                self._log('DELETE /sessions (%s) - kaynak birakildi' % reason)
            except Exception as e:
                self._log('DELETE hatasi: %s' % e)
        self.state = IZLEME
        self._window_started = None
        self._hits = 0
