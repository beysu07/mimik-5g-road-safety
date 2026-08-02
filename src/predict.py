import os
import sys
import cv2
import numpy as np
from collections import Counter, defaultdict
from ultralytics import YOLO
from src.utils import extract_plate, normalize_plate

# Egitim sonrasi Docker icin weights/ altina kopyalanacak; lokal testte runs/ yollari.
WEIGHTS = {
    'vehicle': os.environ.get('W_VEHICLE', 'yolo11s.pt'),               # pretrained COCO
    'type':    os.environ.get('W_TYPE',  'runs/classify/type/weights/best.pt'),
    'color':   os.environ.get('W_COLOR', 'runs/classify/color/weights/best.pt'),
    'plate':   os.environ.get('W_PLATE', 'runs/detect/plate/weights/best.pt'),
    'belt':    os.environ.get('W_BELT',  'runs/detect/seatbelt/weights/best.pt'),
    'action':  os.environ.get('W_ACTION', 'runs/detect/phone_action/weights/best.pt'),
    'cabin':   os.environ.get('W_CABIN', 'runs/detect/self_actions_hd/weights/best.pt'),
}
VEHICLE_COCO = {2, 5, 7}   # car, bus, truck
LAPTOP_COCO = 63           # laptop -> bilgisayar
PERSON_COCO = 0            # person -> yolcu (koltuk atamasi konumdan)
PERSON_CONF = 0.25         # arac+kisi ortak esigi (kisi icin olculdu: 10/13 bulundu)

# arka_koltuk_1 / _2 konvansiyonu belgelerde YAZMIYOR (3 Agu toplantisinda sorulacak).
# Ayrimi yapamadigimiz surece tek etiket uretiyoruz; cevap gelince burasi degisir.
ARKA_KOLTUK_ETIKET = os.environ.get('ARKA_KOLTUK_ETIKET', 'arka_koltuk_2')
# En ondeki kisi surucudur; yolcu sayilmamalidir (yanlis-pozitif kaynagi).
SURUCUYU_ATLA = os.environ.get('SURUCUYU_ATLA', '1') == '1'
TARGET_FPS = 8

# Olay uretimi (video uzunlugundan bagimsiz olmali; videoya ozel sabit YOK):
# Env ile ayarlanabilir: buyuk deger = yalniz GECIS SINIRI ve gorunurluk bolsun
EPIZOT_ARASI = float(os.environ.get('EPIZOT_ARASI', 6.0))
MIN_GOZLEM = 2        # bir epizodun olay sayilmasi icin gereken en az tespit
GECIS_MIN_ARA = 3.0        # sn - iki gecis siniri arasi asgari mesafe
GORUNURLUK_BOSLUGU = 1.0   # sn - arac bu sureden uzun kaybolduysa gecis kesildi demektir
SLALOM_PENCERE = 6.0  # sn - slalom aramasi icin kayan pencere
SLALOM_ADIM = 2.0     # sn - pencerenin kaydirma adimi

# Tespit esikleri - kalibrasyon icin env ile degistirilebilir (kod duzenlemeden olcum).
# 0.40 -> 0.20: faz2 uzerinde olculdu (F1 0.10 -> 0.14); 0.12 gurultuye boguluyor (0.08).
CONF_CABIN = float(os.environ.get('CONF_CABIN', 0.20))

# FTR sema guvencesi: cikti YALNIZ bu degerleri icerebilir (ASCII kucuk harf, birebir).
VALID_TIP = {'sedan', 'suv', 'hatchback', 'pickup', 'minibus', 'panelvan', 'kamyon'}
VALID_RENK = {'beyaz', 'siyah', 'gri', 'kirmizi', 'mavi', 'sari',
              'yesil', 'turuncu', 'kahverengi'}
VALID_LABELS = {
    'sofor_eylemi': {'arkaya_bakma', 'esneme', 'sigara_icme', 'su_icme',
                     'telefonla_konusma', 'slalom', 'etrafa_bakinma',
                     'emniyet_kemeri_ihlali'},
    'nesneler': {'teknocan', 'bilgisayar'},
    'yolcular': {'arka_koltuk_1', 'arka_koltuk_2', 'on_koltuk'},
}


def _load(path):
    try:
        if path.startswith('yolo') or os.path.exists(path):
            return YOLO(path)
        print('AGIRLIK YOK:', path)
    except Exception as e:
        print('model yuklenemedi', path, e)
    return None


class VehiclePassMemory:
    """ÖTR - Araç Geçiş Hafızası: aracin gecisi boyunca tum bulgulari (tip, renk,
    plaka okumalari, yorunge, eylemler) biriktirir; kare bazli yerine gecis bazli
    nihai karari uretir. Plaka karakter bazli zamansal oylamayla, slalom yorungeden."""

    def __init__(self):
        self.type_votes = Counter(); self.type_conf = defaultdict(list)
        self.color_votes = Counter(); self.color_conf = defaultdict(list)
        self.plate_reads = []          # (metin, ocr_guven)
        self.track = []                # (t, cx, genislik) - arac yorungesi
        self.action_obs = defaultdict(list)   # etiket -> [(t, conf)] - kalicilik icin
        self.events = []               # tespitler
        self._last = {}                # etiket -> son zaman (dedup)

    def vote_type(self, lab, conf):
        if lab:
            self.type_votes[lab] += 1; self.type_conf[lab].append(conf)

    def vote_color(self, lab, conf):
        if lab:
            self.color_votes[lab] += 1; self.color_conf[lab].append(conf)

    def add_plate(self, text, conf):
        if text:
            self.plate_reads.append((text, conf))

    def add_track(self, t, box):
        x1, y1, x2, y2 = box
        self.track.append((t, (x1 + x2) / 2.0, max(1.0, x2 - x1)))

    def add_action(self, etiket, t, conf):
        self.action_obs[etiket].append((t, conf))

    def yon(self):
        """Aracin yatay hareket yonu: +1 saga, -1 sola (aracin ONU bu yondedir).
        Yorunge kisayken 0 doner (koltuk atamasi yine de calisir, on/arka simetrik)."""
        if len(self.track) < 4:
            return 0
        son = self.track[-min(len(self.track), 12):]
        delta = son[-1][1] - son[0][1]
        return 1 if delta > 0 else (-1 if delta < 0 else 0)

    def add_event(self, t, kategori, etiket, conf, gap=2.5):
        # Surekli bir eylemi TEK olay say: yeni olay ancak onceki tespitten gap
        # saniyeden uzun sure sonra gelirse uretilir (epizot baslangici).
        last_det = self._last.get(etiket, -100.0)
        if t - last_det > gap:
            self.events.append({'zaman_saniye': t, 'kategori': kategori,
                                 'etiket': etiket, 'confidence_score': round(conf, 2)})
        self._last[etiket] = t

    def _pick(self, votes, conf):
        if not votes:
            return None, 0.0
        lab = votes.most_common(1)[0][0]
        return lab, float(np.mean(conf[lab]))

    def _fuse_plate(self):
        reads = self.plate_reads
        if not reads:
            return None, 0.0
        len_w = defaultdict(float)
        for t, c in reads:
            len_w[len(t)] += c
        L = max(len_w, key=len_w.get)               # guven-agirlikli en sik uzunluk
        same = [(t, c) for t, c in reads if len(t) == L]
        voted = ''
        for i in range(L):                          # her pozisyon icin en cok oylanan karakter
            ch = defaultdict(float)
            for t, c in same:
                ch[t[i]] += c
            voted += max(ch, key=ch.get)
        conf = round(float(np.mean([c for _, c in same])), 2)
        norm = normalize_plate(voted)
        if norm:
            return norm, conf
        bt, bc = max(reads, key=lambda x: x[1])      # oylama gecersizse en guvenli tekil
        return bt, round(bc, 2)

    @staticmethod
    def _zikzak_sayisi(dilim):
        """Bir yorunge diliminde yanal yon degisimi sayisi."""
        cx = np.array([p[1] for p in dilim], float)
        w = float(np.median([p[2] for p in dilim])) or 1.0
        k = min(5, len(cx))
        cs = np.convolve(cx, np.ones(k) / k, mode='valid')   # yumusat
        d = np.diff(cs)
        s = np.sign(d)
        s[np.abs(d) < 0.05 * w] = 0                          # kucuk titremeleri yok say
        nz = s[s != 0]
        return int(np.sum(nz[1:] * nz[:-1] < 0)) if len(nz) > 1 else 0

    def detect_slalom(self, pencere=SLALOM_PENCERE, adim=SLALOM_ADIM):
        """Kayan pencerede zikzak arar ve olayi PENCERENIN BASINDA uretir.

        Onceki surum tum yorungeyi TEK parca sayip olayi yorungenin ortasinda
        uretiyordu; 114 sn'lik videoda bu zamani sistematik olarak yanlis yapiyordu
        (54.7 sn uretildi, gercek 109.0 sn). Pencere yaklasimi video uzunlugundan
        bagimsizdir ve ayni videoda birden fazla slalom epizodunu yakalayabilir.
        """
        if len(self.track) < 8:
            return
        t = self.track[0][0]
        son = self.track[-1][0]
        while t <= son - pencere / 2:
            dilim = [p for p in self.track if t <= p[0] < t + pencere]
            if len(dilim) >= 8:
                rev = self._zikzak_sayisi(dilim)
                if rev >= 3:                                  # 3+ yon degisimi = zikzak
                    self.add_event(round(dilim[0][0], 1), 'sofor_eylemi', 'slalom',
                                   min(0.9, 0.5 + 0.1 * rev), gap=pencere)
            t += adim

    def _gecis_kesintileri(self):
        """Aracin kadrajdan kaybolup geri girdigi anlar: (kayboldu, geri_geldi)."""
        kesinti = []
        for onceki, simdi in zip(self.track, self.track[1:]):
            if simdi[0] - onceki[0] > GORUNURLUK_BOSLUGU:
                kesinti.append((onceki[0], simdi[0]))
        return kesinti

    def _gecis_sinirlari(self):
        """Arac gecislerinin sinir anlari: gorunen genisligin YEREL MINIMUMLARI.

        Arac yaklasirken kutusu buyur, uzaklasirken kuculur. Genisligin dip yaptigi
        an = arac en uzakta = bir gecis bitti, digeri basliyor. GT olaylari "gorunur
        oldugu anda" isaretledigi icin olay zamanlari bu sinirlarla hizalanmalidir.
        Tek gecislik videoda dip bulunmaz -> bos liste doner, davranis degismez.
        """
        if len(self.track) < 12:
            return []
        t = np.array([p[0] for p in self.track], float)
        w = np.array([p[2] for p in self.track], float)
        k = max(3, len(w) // 40) | 1                       # tek sayi pencere
        ws = np.convolve(w, np.ones(k) / k, mode='same')
        tepe = float(ws.max()) or 1.0
        sinirlar = []
        for i in range(1, len(ws) - 1):
            if ws[i] <= ws[i - 1] and ws[i] <= ws[i + 1] and ws[i] < 0.7 * tepe:
                if not sinirlar or t[i] - sinirlar[-1] > GECIS_MIN_ARA:
                    sinirlar.append(float(t[i]))
        return sinirlar

    def _epizotla(self, obs, ara=EPIZOT_ARASI):
        """(t, conf) gozlemlerini epizotlara ayirir.

        Iki olcut: (1) gozlemler arasi bosluk 'ara'yi asarsa, (2) ARADA ARAC
        KADRAJDAN CIKMISSA. Ikincisi sartnamenin "olaylar gorulebilir olduklari
        anda isaretlenmistir" tanimiyla birebir ortusur: arac gorunmez olup geri
        geldiginde ayni eylem YENIDEN gorunur hale gelmistir. Sabit bir saniye
        degerine bagli kalmadigi icin videodan bagimsizdir.
        """
        sirali = sorted(obs)
        kesinti = self._gecis_kesintileri()
        sinirlar = self._gecis_sinirlari()
        epizotlar, gecerli = [], [sirali[0]]
        for t, c in sirali[1:]:
            onceki_t = gecerli[-1][0]
            arada_kayip = any(onceki_t <= k0 and k1 <= t for k0, k1 in kesinti)
            # Iki gozlem arasinda bir GECIS SINIRI kaldiysa yeni gecis basladi demektir.
            arada_sinir = any(onceki_t < s0 <= t for s0 in sinirlar)
            if t - onceki_t > ara or arada_kayip or arada_sinir:
                epizotlar.append(gecerli)
                gecerli = [(t, c)]
            else:
                gecerli.append((t, c))
        epizotlar.append(gecerli)
        return epizotlar

    def _emit_actions(self):
        """Her EPIZOT icin ayri bir olay uretir (etiket basina tek olay DEGIL).

        Bir eylem video boyunca birden cok kez gorunebilir; onceki surum ilk
        dogrulanan pencereden sonra durdugu icin etiket basina yalnizca bir olay
        cikiyordu. Zaman, epizodun BASLANGICIDIR: sartname ground truth'u
        "olaylar gorulebilir olduklari anda isaretlenmistir" diye tanimlar.
        """
        yolcu = {'on_koltuk', 'arka_koltuk_1', 'arka_koltuk_2'}
        for etiket, obs in self.action_obs.items():
            if not obs:
                continue
            kat = 'yolcular' if etiket in yolcu else 'sofor_eylemi'
            for epizot in self._epizotla(obs):
                if len(epizot) < MIN_GOZLEM:
                    continue                      # tek-iki karelik parlama = gurultu
                self.events.append({
                    'zaman_saniye': round(epizot[0][0], 1),
                    'kategori': kat,
                    'etiket': etiket,
                    'confidence_score': round(max(c for _, c in epizot), 2),
                })

    def result(self, video_id):
        # result() canli modda tekrar tekrar cagrilir; detect_slalom/_emit_actions
        # self.events'e ekleme yaptigi icin cagri IDEMPOTENT olmalidir -> anlik goruntu
        # alinip sonunda geri yuklenir (aksi halde ayni tespit cogalir).
        _events_yedek = list(self.events)
        _last_yedek = dict(self._last)
        try:
            return self._result(video_id)
        finally:
            self.events = _events_yedek
            self._last = _last_yedek

    def _result(self, video_id):
        self.detect_slalom()
        self._emit_actions()   # yolcular artik Self_v2 koltuk modelinden (domain-eslesmeli)
        tip, tconf = self._pick(self.type_votes, self.type_conf)
        renk, rconf = self._pick(self.color_votes, self.color_conf)
        plaka, pconf = self._fuse_plate()
        comps = [x for x in (tconf, rconf, pconf) if x > 0]
        score = round(float(np.mean(comps)), 2) if comps else 0.0
        # Sema guvencesi: gecersiz tip/renk varsayilana duser, sema-disi tespit elenir.
        if tip not in VALID_TIP:
            tip = 'sedan'
        if renk not in VALID_RENK:
            renk = 'gri'
        tespitler = [e for e in self.events
                     if e['etiket'] in VALID_LABELS.get(e['kategori'], ())]
        return {
            'video_id': video_id,
            'arac_bilgisi': {
                'tip': tip,
                'plaka': plaka or 'tespit edilemedi',
                'renk': renk,
                'confidence_score': score,
            },
            'tespitler': sorted(tespitler, key=lambda e: e['zaman_saniye']),
        }


class Pipeline:
    """Cikarim hatti: kareleri Arac Gecis Hafizasi'na besler, gecis bazli karar uretir."""

    def __init__(self):
        self._clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.m_vehicle = _load(WEIGHTS['vehicle'])
        self.m_type = _load(WEIGHTS['type'])
        self.m_color = _load(WEIGHTS['color'])
        self.m_plate = _load(WEIGHTS['plate'])
        self.m_belt = _load(WEIGHTS['belt'])
        self.m_action = _load(WEIGHTS['action'])   # mobile -> telefonla_konusma (on cam)
        self.m_cabin = _load(WEIGHTS['cabin'])     # Self_v2 HD: yolcu koltuk siniflari
        try:
            import easyocr, torch
            self.ocr = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
        except Exception as e:
            print('easyocr yuklenemedi:', e)
            self.ocr = None

    def _cls(self, model, crop):
        if model is None or crop is None or crop.size == 0:
            return None, 0.0
        r = model.predict(crop, verbose=False)[0]
        i = int(r.probs.top1)
        return r.names[i], float(r.probs.top1conf)

    def _coco(self, frame):
        """Ayni cikarimdan arac + laptop + KISI kutularini birlikte doner.

        Kisi tespiti ek maliyet getirmez (zaten calisan model) ve kendi egittigimiz
        koltuk sinifindan cok daha saglamdir: faz2'nin 13 arka-koltuk aninda kendi
        sinifimiz 0/13 bulurken COCO 'person' 10/13 buldu.
        """
        if self.m_vehicle is None:
            return None, 0.0, []
        r = self.m_vehicle.predict(frame, verbose=False, conf=PERSON_CONF)[0]
        vbest, varea, lap, kisiler = None, 0, 0.0, []
        for b in r.boxes:
            cls = int(b.cls)
            if cls in VEHICLE_COCO:
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                area = (x2 - x1) * (y2 - y1)
                if area > varea:
                    varea, vbest = area, (max(0, x1), max(0, y1), x2, y2)
            elif cls == LAPTOP_COCO:
                lap = max(lap, float(b.conf))
            elif cls == PERSON_COCO:
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                kisiler.append((x1, y1, x2, y2, float(b.conf)))
        return vbest, lap, kisiler

    @staticmethod
    def _koltuk_ata(vbox, kisiler, yon):
        """Arac icindeki kisileri KONUMA gore koltuklara esler.

        Kural tamamen geometriktir (videoya ozel sabit yok):
          - Kisi arac kutusunun icinde olmali.
          - Aracin ONU, yorungeden gelen hareket yonundedir (yon = +1 saga, -1 sola).
          - Arac kutusunun on yarisindaki kisiler ON, arka yarisindakiler ARKA koltuk.
          - Onde surucu disindaki kisi -> on_koltuk.
        Doner: [(etiket, guven), ...]
        """
        x1, y1, x2, y2 = vbox
        gen = max(1, x2 - x1)
        ic = [k for k in kisiler
              if k[0] >= x1 - gen * 0.05 and k[2] <= x2 + gen * 0.05 and k[3] >= y1]
        if not ic:
            return []
        # Her kisinin arac kutusundaki yatay konumu (0 = sol kenar, 1 = sag kenar)
        konumlu = []
        for k in ic:
            oran = ((k[0] + k[2]) / 2.0 - x1) / gen
            # Yon +1 ise arac saga bakiyor: on taraf yuksek x. Yon -1 ise tersi.
            on_uzaklik = oran if yon >= 0 else (1.0 - oran)
            konumlu.append((on_uzaklik, k[4]))
        konumlu.sort(reverse=True)          # ona en yakindan uzaga

        cikti = []
        for i, (on_uzaklik, conf) in enumerate(konumlu):
            if i == 0 and SURUCUYU_ATLA:
                continue                    # en ondeki kisi SURUCUDUR, yolcu degil
            if on_uzaklik >= 0.5:           # arac kutusunun on yarisi -> on yolcu
                cikti.append(('on_koltuk', conf))
            else:                           # arka yari -> arka koltuk
                cikti.append((ARKA_KOLTUK_ETIKET, conf))
        return cikti

    def _prep_plate(self, img):
        h, w = img.shape[:2]
        img = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        g = self._clahe.apply(g)
        return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)

    def _plate(self, crop):
        if self.m_plate is None or self.ocr is None or crop.size == 0:
            return None, 0.0
        r = self.m_plate.predict(crop, verbose=False, conf=0.3)[0]
        best, bc = None, 0.0
        for b in r.boxes:
            c = float(b.conf)
            if c > bc:
                bc, best = c, tuple(map(int, b.xyxy[0]))
        if best is None:
            return None, 0.0
        x1, y1, x2, y2 = best
        pad = int((x2 - x1) * 0.12)
        x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
        x2, y2 = min(crop.shape[1], x2 + pad), min(crop.shape[0], y2 + pad)
        pc = crop[y1:y2, x1:x2]
        if pc.size == 0:
            return None, 0.0
        res = self.ocr.readtext(self._prep_plate(pc),
                                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', detail=1)
        text = ''.join(t for _, t, _ in res)
        oconf = float(np.mean([c for *_, c in res])) if res else 0.0
        norm = extract_plate(text)
        return (norm, oconf) if norm else (None, 0.0)

    def _phone(self, crop):
        if self.m_action is None or crop.size == 0:
            return None
        r = self.m_action.predict(crop, verbose=False, conf=0.45)[0]
        best = None
        for b in r.boxes:
            if r.names[int(b.cls)] == 'mobile':
                c = float(b.conf)
                if best is None or c > best:
                    best = c
        return best

    def _cabin_objects(self, roi):
        """Self_v2 (DOMAIN) modeliyle kabin ROI'sinde koltuk + su/sigara siniflari.
        su/sigara jenerik degil takim verisiyle egitilen domain modelinden alinir;
        ornek TOGG videolarinda bu siniflar icin yanlis-pozitif gozlenmemistir."""
        if self.m_cabin is None or roi is None or roi.size == 0:
            return {}
        h, w = roi.shape[:2]
        if max(h, w) < 1280:
            s = 1280.0 / max(h, w)
            roi = cv2.resize(roi, (int(w * s), int(h * s)))
        r = self.m_cabin.predict(roi, verbose=False, conf=CONF_CABIN, imgsz=1280)[0]
        out = {}
        for b in r.boxes:
            name = r.names[int(b.cls)]; c = float(b.conf)
            if name in ('on_koltuk_2', 'arka_koltuk', 'water', 'sigara') and c > out.get(name, 0):
                out[name] = c
        return out

    def _belt(self, crop):
        if self.m_belt is None or crop.size == 0:
            return None
        r = self.m_belt.predict(crop, verbose=False, conf=0.5)[0]
        best = None
        for b in r.boxes:
            if r.names[int(b.cls)] == 'no seat-belt':
                c = float(b.conf)
                if best is None or c > best:
                    best = c
        return best

    def run(self, video_path, frame_hook=None, on_update=None, update_every=4):
        """frame_hook: kareyi isleme almadan once donusturen istege bagli fonksiyon
        (5G ag benzetimi icin; None ise kare oldugu gibi kullanilir).
        on_update: canli mod icin her update_every karede bir kismi sonucu alan geri cagri."""
        cap = cv2.VideoCapture(video_path)
        if hasattr(cv2, 'CAP_PROP_ORIENTATION_AUTO'):
            # MOV rotation metadata'sini karelere uygula; aksi halde modeller yan goruntu alir.
            cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
        if not cap.isOpened():
            raise RuntimeError(f'Video acilamadi: {video_path}')
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        step = max(1, round(fps / TARGET_FPS))
        mem = VehiclePassMemory()
        idx = -1
        frame_errors = 0
        while True:
            if not cap.grab():
                break
            idx += 1
            if idx % step:
                continue
            ok, frame = cap.retrieve()
            if not ok:
                break
            try:
                if frame_hook is not None:
                    frame = frame_hook(frame)
                t = round(idx / fps, 1)
                vbox, laptop, kisiler = self._coco(frame)
                if laptop > 0.4:
                    mem.add_event(t, 'nesneler', 'bilgisayar', laptop, gap=2.0)
                if vbox is None:
                    continue
                mem.add_track(t, vbox)
                # Yolcular: kendi koltuk sinifimiz bu kosullarda kor (faz2'de 0/13),
                # COCO kisi tespiti calisiyor (10/13) -> koltugu KONUMDAN atiyoruz.
                for etiket, guven in self._koltuk_ata(vbox, kisiler, mem.yon()):
                    mem.add_action(etiket, t, guven)
                x1, y1, x2, y2 = vbox
                crop = frame[y1:y2, x1:x2]
                cabin = crop[0:int(crop.shape[0] * 0.65), :]   # arabanin ust kabin (greenhouse)
                cab = self._cabin_objects(cabin)
                if 'water' in cab:             # Self_v2 domain su -> su_icme
                    mem.add_action('su_icme', t, cab['water'])
                if 'sigara' in cab:            # Self_v2 domain sigara -> sigara_icme
                    mem.add_action('sigara_icme', t, cab['sigara'])
                lab, c = self._cls(self.m_type, crop); mem.vote_type(lab, c)
                lab, c = self._cls(self.m_color, crop); mem.vote_color(lab, c)
                ptext, poconf = self._plate(crop); mem.add_plate(ptext, poconf)
                ph = self._phone(crop)
                if ph is not None:
                    mem.add_action('telefonla_konusma', t, ph)
                bc = self._belt(crop)
                if bc is not None:
                    mem.add_action('emniyet_kemeri_ihlali', t, bc)
                if on_update is not None and (idx // step) % update_every == 0:
                    on_update(mem.result(os.path.basename(video_path)))
            except Exception as exc:
                frame_errors += 1
                if frame_errors <= 3:
                    print(f'Kare {idx} atlandi: {type(exc).__name__}: {exc}', file=sys.stderr)
                continue
        cap.release()
        if frame_errors:
            print(f'Toplam {frame_errors} kare hata nedeniyle atlandi.', file=sys.stderr)
        return mem.result(os.path.basename(video_path))
