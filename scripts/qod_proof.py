"""QoD ISPAT DUZENEGI — sartname: "sebeke kalitesi arttiginda YZ basarim artisini
bu API kullanimi ile kanitlayacaklardir".

Ayni video, ayni modeller, TEK degisken = sebeke kalitesi. Uc kosu:

  1) qod_kapali : hep best-effort (dusuk bit hizi)          -> taban
  2) qod_adaptif: IZLEME -> kritik durum -> QoD penceresi    -> BIZIM SISTEM
                  -> DELETE (kaynak birakilir)
  3) surekli_yuksek: musluk hep acik                         -> ust sinir referansi

Beklenen sonuc: (2), (1)'e gore belirgin daha dogru; (3)'e yakin dogruluk ama
belirgin daha az bant genisligi -> "ihtiyaca gore acilip kapanan akilli kaynak".

Kullanim:
    python scripts/qod_proof.py [video] [--gt-plaka 34TC8532] [--gt-tip suv] [--gt-renk siyah]
"""
import argparse
import difflib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from net.boost_controller import BoostController          # noqa: E402
from net.netsim import BEST_EFFORT, QOS_L, NetworkSimulator  # noqa: E402
from net.qod import QoDClient                             # noqa: E402
from src.predict import TARGET_FPS, VEHICLE_COCO, Pipeline  # noqa: E402


def plate_score(pred, gt):
    """Plaka karakter dogrulugu: ayni uzunlukta konum-eslesmesi, degilse benzerlik."""
    if not pred or pred == 'tespit edilemedi':
        return 0.0, '0/%d' % len(gt)
    if len(pred) == len(gt):
        hit = sum(1 for a, b in zip(pred, gt) if a == b)
        return hit / float(len(gt)), '%d/%d' % (hit, len(gt))
    ratio = difflib.SequenceMatcher(None, pred, gt).ratio()
    return ratio, '~%d%%' % round(ratio * 100)


class AdaptiveHook:
    """Best-effort akista hafif izleme yapar, kritik durumda QoD penceresi actirir.

    Gercek mimariyle ayni: karar, ELDEKI (bozulmus) akis uzerinden verilir; kalite
    ancak QoD AVAILABLE olunca yukselir.
    """

    def __init__(self, pipeline, sim, controller):
        self.pipe, self.sim, self.ctrl = pipeline, sim, controller
        self.i = 0
        self.boosted_frames = 0

    def __call__(self, frame):
        out = self.sim(frame)                 # once mevcut kalite ile "agdan gecir"
        self.i += 1
        now = self.i / float(TARGET_FPS)      # video zamani (gercek zamanli beklemeden)
        vbox = None
        try:                                   # hafif izleme modeli (bozulmus akista)
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
        active = self.ctrl.update(vbox, out.shape, now=now)
        self.sim.switch(QOS_L if active else BEST_EFFORT)
        if active:
            self.boosted_frames += 1
        return out


def run_mode(pipe, video, mode):
    """Tek kosu: (sonuc_json, olcum_ozeti, olay_logu)."""
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    events = []
    t0 = time.time()
    if mode == 'qod_kapali':
        sim = NetworkSimulator(BEST_EFFORT)
        res = pipe.run(video, frame_hook=sim)
        hook = None
    elif mode == 'surekli_yuksek':
        sim = NetworkSimulator(QOS_L)
        res = pipe.run(video, frame_hook=sim)
        hook = None
    else:                                       # qod_adaptif
        sim = NetworkSimulator(BEST_EFFORT)
        qod = QoDClient(mock=True, mock_setup_seconds=0.0)   # gercekte: base_url+token
        ctrl = BoostController(qod, qos_profile='QOS_L', duration=30,
                               device={'phoneNumber': '+90XXXXXXXXXX'})
        hook = AdaptiveHook(pipe, sim, ctrl)
        res = pipe.run(video, frame_hook=hook)
        ctrl.release('kosu bitti')
        events = ctrl.events

    summary = sim.summary(TARGET_FPS)
    summary['sure_sn'] = round(time.time() - t0, 1)
    if hook is not None:
        summary['yuksek_kalite_kare'] = hook.boosted_frames
        summary['toplam_kare'] = hook.i
    return res, summary, events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', nargs='?', default='docker_test/input/video.mp4')
    ap.add_argument('--gt-plaka', default='34TC8532')
    ap.add_argument('--gt-tip', default='suv')
    ap.add_argument('--gt-renk', default='siyah')
    ap.add_argument('--out', default='reports/qod_ispat.json')
    a = ap.parse_args()

    pipe = Pipeline()                            # modeller bir kez yuklenir
    rows = []
    for mode in ('qod_kapali', 'qod_adaptif', 'surekli_yuksek'):
        res, summary, events = run_mode(pipe, a.video, mode)
        ab = res.get('arac_bilgisi', {})
        score, gosterim = plate_score(ab.get('plaka', ''), a.gt_plaka)
        rows.append({
            'mod': mode,
            'mbps': summary['tahmini_mbps'],
            'plaka': ab.get('plaka'),
            'plaka_dogruluk': gosterim,
            'plaka_skor': round(score, 3),
            'tip': ab.get('tip'),
            'tip_dogru': ab.get('tip') == a.gt_tip,
            'renk': ab.get('renk'),
            'renk_dogru': ab.get('renk') == a.gt_renk,
            'tespit_sayisi': len(res.get('tespitler', [])),
            'tespitler': [e['etiket'] for e in res.get('tespitler', [])],
            'olcum': summary,
            'qod_olaylari': [list(e) for e in events],
        })
        print('[%s] mbps=%.2f plaka=%s (%s) tip=%s renk=%s tespit=%d' % (
            mode, summary['tahmini_mbps'], ab.get('plaka'), gosterim,
            ab.get('tip'), ab.get('renk'), len(res.get('tespitler', []))))

    print('\n' + '=' * 92)
    print('QoD ISPAT TABLOSU  |  video: %s  |  gercek: %s / %s / %s' % (
        os.path.basename(a.video), a.gt_tip, a.gt_plaka, a.gt_renk))
    print('=' * 92)
    print('%-16s %10s %12s %10s %8s %8s %8s' % (
        'Mod', 'Mbps', 'Plaka', 'Dogruluk', 'Tip', 'Renk', 'Tespit'))
    print('-' * 92)
    for r in rows:
        print('%-16s %10.2f %12s %10s %8s %8s %8d' % (
            r['mod'], r['mbps'], (r['plaka'] or '-')[:12], r['plaka_dogruluk'],
            'OK' if r['tip_dogru'] else 'X', 'OK' if r['renk_dogru'] else 'X',
            r['tespit_sayisi']))
    print('-' * 92)

    kapali = next(r for r in rows if r['mod'] == 'qod_kapali')
    adaptif = next(r for r in rows if r['mod'] == 'qod_adaptif')
    yuksek = next(r for r in rows if r['mod'] == 'surekli_yuksek')
    print('KAZANIM  : plaka dogrulugu %s -> %s  (QoD ile)' % (
        kapali['plaka_dogruluk'], adaptif['plaka_dogruluk']))
    if yuksek['mbps'] > 0:
        print('VERIMLILIK: adaptif %.2f Mbps, surekli yuksek %.2f Mbps  (%%%d tasarruf)' % (
            adaptif['mbps'], yuksek['mbps'],
            round(100 * (1 - adaptif['mbps'] / yuksek['mbps']))))
    print('QoD OLAY LOGU (API cagrildiginin kaniti):')
    for e in adaptif['qod_olaylari']:
        print('   %s  [%s]  %s' % (e[0], e[1], e[2]))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({'video': a.video, 'gercek': {'tip': a.gt_tip, 'plaka': a.gt_plaka,
                                            'renk': a.gt_renk}, 'sonuclar': rows},
              open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('\nJSON -> %s' % a.out)


if __name__ == '__main__':
    main()
