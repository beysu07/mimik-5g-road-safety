"""
Video dosyasından belirli aralıklarla kare çıkarma scripti.

Kullanım:
    python scripts/extract_frames.py --video data/raw/video.mp4 --output data/processed/frames --step 10
"""

import argparse
from pathlib import Path

import cv2


def extract_frames(video_path: str, output_dir: str, step: int) -> None:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video bulunamadı: {video_path}")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Video açılamadı: {video_path}")

    frame_index = 0
    saved_index = 0

    while True:
        success, frame = cap.read()

        if not success:
            break

        if frame_index % step == 0:
            output_path = output_dir / f"frame_{saved_index:06d}.jpg"
            cv2.imwrite(str(output_path), frame)
            saved_index += 1

        frame_index += 1

    cap.release()
    print(f"Tamamlandı. Kaydedilen kare sayısı: {saved_index}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Video dosyasından kare çıkarır.")
    parser.add_argument("--video", required=True, help="Giriş video dosyası")
    parser.add_argument("--output", required=True, help="Çıkış klasörü")
    parser.add_argument("--step", type=int, default=10, help="Kaç karede bir kayıt yapılacağı")

    args = parser.parse_args()
    extract_frames(args.video, args.output, args.step)


if __name__ == "__main__":
    main()
