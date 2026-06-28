import os, sys, cv2, json
from ultralytics import YOLO

VID = sys.argv[1] if len(sys.argv) > 1 else 'veri/video_2.mp4'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'runs/_viz/out.mp4'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
JS = 'runs/_pred/' + os.path.splitext(os.path.basename(VID))[0] + '.json'
info = json.load(open(JS)).get('arac_bilgisi', {}) if os.path.exists(JS) else {}

veh = YOLO('yolo11s.pt')
plate = YOLO('runs/detect/plate/weights/best.pt')
person = YOLO('runs/detect/phone_merged/weights/best.pt')
action = YOLO('runs/detect/phone_action/weights/best.pt')
bottle_path = os.environ.get('W_BOTTLE', 'runs/detect/bottle_external/weights/best.pt')
external_bottle = YOLO(bottle_path) if os.path.exists(bottle_path) else None
if external_bottle is None:
    print('HARICI BOTTLE AGIRLIGI YOK:', bottle_path)
cigarette_path = os.environ.get('W_CIGARETTE', 'runs/detect/cigarette/weights/best.pt')
external_cigarette = YOLO(cigarette_path) if os.path.exists(cigarette_path) else None

cap = cv2.VideoCapture(VID)
if hasattr(cv2, 'CAP_PROP_ORIENTATION_AUTO'):
    # iPhone MOV dosyalari kareleri yatay saklayip yonu metadata ile belirtebilir.
    cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
if not cap.isOpened():
    raise RuntimeError(f'Video acilamadi: {VID}')
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS) or 25
ret, f0 = cap.read()
if not ret:
    raise RuntimeError(f'Videodan ilk kare okunamadi: {VID}')
H, W = f0.shape[:2]
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
scale = 1280 / max(H, W)
ow = max(2, int(round(W * scale)) // 2 * 2)
oh = max(2, int(round(H * scale)) // 2 * 2)
writer = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*'mp4v'), fps / 2, (ow, oh))


def box(img, b, off, color, label):
    x1, y1, x2, y2 = map(int, b)
    ox, oy = off
    cv2.rectangle(img, (ox + x1, oy + y1), (ox + x2, oy + y2), color, 3)
    cv2.putText(img, label, (ox + x1, oy + y1 - 8), 0, 1.0, color, 3)


written, saved = 0, []
idx = -1
while True:
    ret, fr = cap.read()
    if not ret:
        break
    idx += 1
    if idx % 2:
        continue
    r = veh.predict(fr, conf=0.3, verbose=False)[0]
    vb, ba = None, 0
    for b in r.boxes:
        cls = int(b.cls)
        if cls in (2, 5, 7):
            x1, y1, x2, y2 = map(int, b.xyxy[0]); a = (x2 - x1) * (y2 - y1)
            if a > ba: ba, vb = a, (max(0, x1), max(0, y1), x2, y2)
        elif cls == 63:
            box(fr, b.xyxy[0], (0, 0), (255, 0, 255), 'bilgisayar')
    if vb:
        x1, y1, x2, y2 = vb
        crop = fr[y1:y2, x1:x2].copy()
        ch = int((y2 - y1) * 0.65)
        cabin = crop[:ch, :].copy()
        cv2.rectangle(fr, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(fr, 'arac', (x1, y1 - 12), 0, 1.4, (0, 255, 0), 3)
        cv2.rectangle(fr, (x1, y1), (x2, y1 + ch), (255, 128, 0), 2)
        cv2.putText(fr, 'kabin ROI', (x1 + 8, y1 + 34), 0, 1.0, (255, 128, 0), 3)
        for b in plate.predict(crop, conf=0.3, verbose=False)[0].boxes:
            box(fr, b.xyxy[0], (x1, y1), (0, 255, 255), 'plaka')
        rp = person.predict(cabin, conf=0.45, verbose=False)[0]
        for b in rp.boxes:
            if person.names[int(b.cls)] == 'person':
                box(fr, b.xyxy[0], (x1, y1), (255, 255, 0), 'kisi')
        fw = cabin.shape[1]
        views = ((cabin[:, :int(fw * 0.62)], 0),
                 (cabin[:, int(fw * 0.38):], int(fw * 0.38)))
        if external_bottle is not None:
            target_ids = [i for i, name in external_bottle.names.items()
                          if str(name).lower() in ('bottle', 'water', 'water_bottle')]
            for bottle_view, view_x in views:
                rb = external_bottle.predict(
                    bottle_view, conf=0.25, classes=target_ids,
                    imgsz=1280, verbose=False
                )[0]
                for b in rb.boxes:
                    box(fr, b.xyxy[0], (x1 + view_x, y1), (255, 0, 255),
                        f'EXTERNAL bottle {float(b.conf):.2f}')
        if external_cigarette is not None:
            target_ids = [i for i, name in external_cigarette.names.items()
                          if str(name).lower() == 'cigarette']
            for cigarette_view, view_x in views:
                rc = external_cigarette.predict(
                    cigarette_view, conf=0.25, classes=target_ids,
                    imgsz=1280, verbose=False
                )[0]
                for b in rc.boxes:
                    box(fr, b.xyxy[0], (x1 + view_x, y1), (0, 128, 255),
                        f'EXTERNAL cigarette {float(b.conf):.2f}')
        ra = action.predict(crop, conf=0.35, verbose=False)[0]
        for b in ra.boxes:
            if action.names[int(b.cls)] == 'mobile':
                box(fr, b.xyxy[0], (x1, y1), (0, 0, 255), 'telefon')
    hdr = f"tip:{info.get('tip','-')}  renk:{info.get('renk','-')}  plaka:{info.get('plaka','-')}"
    cv2.rectangle(fr, (0, 0), (W, 72), (0, 0, 0), -1)
    cv2.putText(fr, hdr, (20, 50), 0, 1.6, (255, 255, 255), 3)
    small = cv2.resize(fr, (ow, oh))
    writer.write(small)
    if written % 30 == 0 and len(saved) < 4:
        p = OUT.replace('.mp4', f'_key{len(saved)}.png'); cv2.imwrite(p, small); saved.append(p)
    written += 1
cap.release(); writer.release()
print('VIZ ->', OUT, '| boyut:', os.path.getsize(OUT), 'bytes | keyframes:', len(saved))
