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

cap = cv2.VideoCapture(VID)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
ret, f0 = cap.read()
H, W = f0.shape[:2]
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
ow = 1280; oh = int(H * ow / W)
writer = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*'mp4v'), 25, (ow, oh))


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
        cv2.rectangle(fr, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(fr, 'arac', (x1, y1 - 12), 0, 1.4, (0, 255, 0), 3)
        crop = fr[y1:y2, x1:x2]
        for b in plate.predict(crop, conf=0.3, verbose=False)[0].boxes:
            box(fr, b.xyxy[0], (x1, y1), (0, 255, 255), 'plaka')
        ch = int((y2 - y1) * 0.65)
        rp = person.predict(fr[y1:y1 + ch, x1:x2], conf=0.45, verbose=False)[0]
        for b in rp.boxes:
            if person.names[int(b.cls)] == 'person':
                box(fr, b.xyxy[0], (x1, y1), (255, 255, 0), 'kisi')
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
