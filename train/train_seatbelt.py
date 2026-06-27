import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from ultralytics import YOLO

if __name__ == '__main__':
    # Siniflar: 0ar(arac), 'no seat-belt'->emniyet_kemeri_ihlali, windshield(ROI)
    YOLO('yolo11s.pt').train(
        data='datasets/seatbelt_windshield/data.yaml',
        epochs=80, imgsz=640, batch=16, workers=4, device=0,
        name='seatbelt', exist_ok=True, patience=20)
