import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from ultralytics import YOLO

if __name__ == '__main__':
    # 9 sinif: beyaz siyah gri kirmizi mavi sari yesil turuncu kahverengi
    YOLO('yolo11s-cls.pt').train(
        data='datasets/color_vcor_9',
        epochs=40, imgsz=224, batch=64, workers=4, device=0,
        name='color', exist_ok=True, patience=15)
