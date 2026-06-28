# MİMİK FTR - cevrimdisi cikarim konteyneri (NVIDIA T4 / CUDA 12.1)
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Torch (CUDA 12.1) - build aninda; calisma aninda internet KAPALI olacak
RUN pip3 install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121
COPY requirements.docker.txt .
RUN pip3 install --no-cache-dir -r requirements.docker.txt

# EasyOCR modellerini build aninda indir (runtime offline calissin)
RUN python3 -c "import easyocr; easyocr.Reader(['en'])"

# Kod + agirliklar
COPY weights/ /app/weights/
COPY src/ /app/src/
COPY app.py /app/

# Agirlik yollari (predict.py bu env'leri okur)
ENV W_VEHICLE=/app/weights/yolo11s.pt \
    W_TYPE=/app/weights/type.pt \
    W_COLOR=/app/weights/color.pt \
    W_PLATE=/app/weights/plate.pt \
    W_BELT=/app/weights/seatbelt.pt \
    W_ACTION=/app/weights/phone_action.pt \
    W_CABIN=/app/weights/self_actions_hd.pt

# /app/data/input/video.mp4 -> /app/data/output/results.json
CMD ["python3", "app.py"]
