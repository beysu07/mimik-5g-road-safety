import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from ultralytics import YOLO

if __name__ == '__main__':
    # Tek sinif License_Plate -> cikti uretirken 'plaka' olarak kullanilacak
    YOLO('yolo11s.pt').train(
        data='datasets/plate/data.yaml',
        epochs=40, imgsz=640, batch=16, workers=4, device=0,
        name='plate', exist_ok=True, patience=15)
