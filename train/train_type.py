import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from ultralytics import YOLO

if __name__ == '__main__':
    # 5 sinif (CompCars): sedan suv hatchback minibus pickup
    # panelvan + kamyon CompCars'ta yok -> sonra best-effort eklenecek
    YOLO('yolo11s-cls.pt').train(
        data='datasets/type_compcars_7',
        epochs=40, imgsz=224, batch=64, workers=4, device=0,
        name='type', exist_ok=True, patience=12)
