import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from ultralytics import YOLO

if __name__ == '__main__':
    # Disaridan/on camdan: mobile->telefonla_konusma, seatbelt, windshield(ROI)
    YOLO('yolo11s.pt').train(
        data='datasets/Phone/data.yaml',
        epochs=60, imgsz=640, batch=16, workers=4, device=0,
        name='phone_action', exist_ok=True, patience=15)
