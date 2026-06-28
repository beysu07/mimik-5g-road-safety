import os
import cv2
import numpy as np
from collections import Counter, defaultdict
from ultralytics import YOLO
from src.utils import clahe_bgr, extract_plate, normalize_plate

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
TARGET_FPS = 8

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

    def detect_slalom(self):
        """Yorungedeki yanal salinimdan slalom (zikzak) tespiti."""
        if len(self.track) < 8:
            return
        cx = np.array([p[1] for p in self.track], float)
        w = float(np.median([p[2] for p in self.track])) or 1.0
        k = min(5, len(cx))
        cs = np.convolve(cx, np.ones(k) / k, mode='valid')   # yumusat
        d = np.diff(cs)
        s = np.sign(d)
        s[np.abs(d) < 0.05 * w] = 0                          # kucuk titremeleri yok say
        nz = s[s != 0]
        rev = int(np.sum(nz[1:] * nz[:-1] < 0)) if len(nz) > 1 else 0
        if rev >= 3:                                          # 3+ yon degisimi = zikzak
            t = round(self.track[len(self.track) // 2][0], 1)
            self.add_event(t, 'sofor_eylemi', 'slalom', min(0.9, 0.5 + 0.1 * rev), gap=0)

    def _emit_actions(self):
        """Kisa eylemleri yakin zamanli 3 nesne tespitiyle, digerlerini oranla uret."""
        total = max(1, len(self.track))
        yolcu = {'on_koltuk', 'arka_koltuk_1', 'arka_koltuk_2'}
        # telefonla_konusma sik gorunur -> dusuk oran; su/sigara icin kalicilik iste
        # (anlik domain yanlis-pozitifi elesin); yolcular varsayilan 0.25.
        ratios = {'telefonla_konusma': 0.15, 'su_icme': 0.25, 'sigara_icme': 0.25}
        for etiket, obs in self.action_obs.items():
            min_ratio = ratios.get(etiket, 0.25)
            confirmed = len(obs) >= 3 and len(obs) / total >= min_ratio
            if confirmed:
                t_m, c_m = max(obs, key=lambda x: x[1])
                kat = 'yolcular' if etiket in yolcu else 'sofor_eylemi'
                self.events.append({'zaman_saniye': round(t_m, 1), 'kategori': kat,
                                    'etiket': etiket, 'confidence_score': round(c_m, 2)})

    def result(self, video_id):
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
        if self.m_vehicle is None:
            return None, 0.0
        r = self.m_vehicle.predict(frame, verbose=False, conf=0.3)[0]
        vbest, varea, lap = None, 0, 0.0
        for b in r.boxes:
            cls = int(b.cls)
            if cls in VEHICLE_COCO:
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                area = (x2 - x1) * (y2 - y1)
                if area > varea:
                    varea, vbest = area, (max(0, x1), max(0, y1), x2, y2)
            elif cls == LAPTOP_COCO:
                lap = max(lap, float(b.conf))
        return vbest, lap

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
        r = self.m_cabin.predict(roi, verbose=False, conf=0.4, imgsz=1280)[0]
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

    def run(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if hasattr(cv2, 'CAP_PROP_ORIENTATION_AUTO'):
            # MOV rotation metadata'sini karelere uygula; aksi halde modeller yan goruntu alir.
            cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
        if not cap.isOpened():
            return {'video_id': os.path.basename(video_path), 'arac_bilgisi': {}, 'tespitler': []}
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        step = max(1, round(fps / TARGET_FPS))
        mem = VehiclePassMemory()
        idx = -1
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
                t = round(idx / fps, 1)
                vbox, laptop = self._coco(frame)
                if laptop > 0.4:
                    mem.add_event(t, 'nesneler', 'bilgisayar', laptop, gap=2.0)
                if vbox is None:
                    continue
                mem.add_track(t, vbox)
                x1, y1, x2, y2 = vbox
                crop = frame[y1:y2, x1:x2]
                cabin = crop[0:int(crop.shape[0] * 0.65), :]   # arabanin ust kabin (greenhouse)
                cab = self._cabin_objects(cabin)
                if 'on_koltuk_2' in cab:       # Self_v2 on yolcu -> sema 'on_koltuk'
                    mem.add_action('on_koltuk', t, cab['on_koltuk_2'])
                if 'arka_koltuk' in cab:       # Self_v2 arka yolcu -> sema 'arka_koltuk_1'
                    mem.add_action('arka_koltuk_1', t, cab['arka_koltuk'])
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
            except Exception:
                continue   # gecici hata ( or. OOM) bu kareyi atla, gecisi surdur
        cap.release()
        return mem.result(os.path.basename(video_path))
