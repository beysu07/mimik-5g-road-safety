# MIMIK FTR - cevrimdisi cikarim konteyneri (NVIDIA T4 / CUDA 12.1)
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics \
    MPLCONFIGDIR=/tmp/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/data/input /app/data/output /app/models /app/src

# CUDA 12.1 Torch ve tum runtime bagimliliklari build sirasinda kurulur.
# Triton yalniz derleme/egitim yolunda kullanilir; cikarim imajinda tutulmaz.
COPY requirements.docker.txt .
RUN pip3 install torch==2.1.2+cu121 torchvision==0.16.2+cu121 \
        --index-url https://download.pytorch.org/whl/cu121 \
    && pip3 install -r requirements.docker.txt \
    && pip3 install --no-deps ultralytics==8.4.14 \
    && pip3 uninstall -y triton \
    && python3 -c "import easyocr; easyocr.Reader(['en'])" \
    && python3 -c "import torch, torchvision, ultralytics, easyocr, cv2; print(torch.__version__, torchvision.__version__, ultralytics.__version__, easyocr.__version__, cv2.__version__)" \
    && rm -rf /usr/local/lib/python3.10/dist-packages/torch/include \
              /usr/local/lib/python3.10/dist-packages/torch/share/cmake \
    && find /usr/local/lib/python3.10/dist-packages -type d -name tests -prune -exec rm -rf '{}' + \
    && find /usr/local/lib/python3.10/dist-packages -type d -name __pycache__ -prune -exec rm -rf '{}' +

# Yalniz cikarimda kullanilan agirliklar; sartname yolu /app/models/.
COPY weights/yolo11s.pt /app/models/yolo11s.pt
COPY weights/type.pt /app/models/type.pt
COPY weights/color.pt /app/models/color.pt
COPY weights/plate.pt /app/models/plate.pt
COPY weights/seatbelt.pt /app/models/seatbelt.pt
COPY weights/phone_action.pt /app/models/phone_action.pt
COPY weights/self_actions_hd.pt /app/models/self_actions_hd.pt
COPY weights/kabin_v2.pt /app/models/kabin_v2.pt
COPY src/ /app/src/
COPY app.py /app/

# Agirlik yollari (predict.py bu env'leri okur)
ENV W_VEHICLE=/app/models/yolo11s.pt \
    W_TYPE=/app/models/type.pt \
    W_COLOR=/app/models/color.pt \
    W_PLATE=/app/models/plate.pt \
    W_BELT=/app/models/seatbelt.pt \
    W_ACTION=/app/models/phone_action.pt \
    W_CABIN=/app/models/self_actions_hd.pt \
    W_NESNE=/app/models/kabin_v2.pt

# /app/data/input/video.mp4 -> /app/data/output/results.json
CMD ["python3", "app.py"]
