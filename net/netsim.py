"""Sebeke kalitesi benzetimi (Turkcell uc noktalari gelmeden ispat duzenegi kurmak icin).

Gercek QoD'de kalite farki, akisin bit hizi/cozunurluk olarak degismesiyle olusur.
Burada ayni etki gonderici tarafta yeniden olceklendirme + JPEG sikistirma ile
uretilir; boylece "QoD kapali vs acik" karsilastirmasi bugun olculebilir.
Finalde bu katman devre disi birakilip gercek akis kullanilir.
"""
import cv2
import numpy as np


class NetworkProfile:
    """Bir sebeke kalitesi seviyesi: uzun kenar sinirlamasi + JPEG kalitesi."""

    def __init__(self, name, max_dim, jpeg_quality):
        self.name, self.max_dim, self.jpeg_quality = name, max_dim, jpeg_quality

    def __repr__(self):
        return 'NetworkProfile(%s, %dpx, q%d)' % (self.name, self.max_dim, self.jpeg_quality)


# Best-effort: sebeke yogunken tipik dusuk bit hizi -> kucuk hedefler bozulur
BEST_EFFORT = NetworkProfile('best_effort', max_dim=854, jpeg_quality=32)
# QoD ile yukseltilmis: yuksek bit hizi -> tam ayrinti korunur
QOS_L = NetworkProfile('QOS_L', max_dim=3840, jpeg_quality=92)


class NetworkSimulator:
    """Kareleri secili profile gore bozar ve tasinan bayt sayisini olcer.

    switch(profile) ile calisma aninda kalite degistirilebilir; BoostController
    PENCERE durumuna gecince cagrilir.
    """

    def __init__(self, profile=BEST_EFFORT):
        self.profile = profile
        self.total_bytes = 0
        self.frames = 0
        self.bytes_by_profile = {}

    def switch(self, profile):
        self.profile = profile

    def __call__(self, frame):
        """frame_hook arayuzu: kareyi 'agdan gecmis' haliyle dondurur."""
        p = self.profile
        h, w = frame.shape[:2]
        long_edge = max(h, w)
        if long_edge > p.max_dim:
            s = p.max_dim / float(long_edge)
            small = cv2.resize(frame, (max(1, int(w * s)), max(1, int(h * s))),
                               interpolation=cv2.INTER_AREA)
        else:
            small = frame

        ok, buf = cv2.imencode('.jpg', small, [int(cv2.IMWRITE_JPEG_QUALITY), p.jpeg_quality])
        if not ok:
            return frame
        nbytes = int(buf.nbytes)
        self.total_bytes += nbytes
        self.frames += 1
        self.bytes_by_profile[p.name] = self.bytes_by_profile.get(p.name, 0) + nbytes

        decoded = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if decoded is None:
            return frame
        # Modellerin girdi boyutu degismesin diye ozgun cerceveye geri olcekle:
        # bilgi kaybi (dusuk cozunurluk + sikistirma) kalicidir, sadece boyut geri gelir.
        if decoded.shape[:2] != (h, w):
            decoded = cv2.resize(decoded, (w, h), interpolation=cv2.INTER_CUBIC)
        return decoded

    def mbps(self, fps):
        """Olculen ortalama bit hizi (Mbit/s)."""
        if not self.frames:
            return 0.0
        return (self.total_bytes / float(self.frames)) * 8 * fps / 1e6

    def summary(self, fps):
        return {
            'profil': self.profile.name,
            'kare': self.frames,
            'ortalama_kare_bayt': int(self.total_bytes / self.frames) if self.frames else 0,
            'tahmini_mbps': round(self.mbps(fps), 2),
        }
