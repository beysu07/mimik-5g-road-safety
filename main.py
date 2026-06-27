import cv2
import time
import csv
import matplotlib.pyplot as plt
from detection import BlinkCounter

from config import (
    CAMERA_INDEX,
    WINDOW_MAIN,
    WINDOW_LEFT_EYE,
    WINDOW_RIGHT_EYE,
    WINDOW_MOUTH,
    EYE_PADDING_X,
    EYE_PADDING_Y,
    MOUTH_PADDING_X,
    MOUTH_PADDING_Y,
    EMA_ALPHA_EAR,
    EMA_ALPHA_MAR,
    # EAR_BLINK_THRESHOLD,
    # MIN_CLOSED_FRAMES_FOR_BLINK,
)
from landmarks import FaceLandmarkDetector
from roi import points_to_bbox, crop_roi, draw_bbox, draw_points
from metrics import eye_aspect_ratio, mouth_aspect_ratio
from smoothing import EMAFilter


def show_if_valid(window_name, image):
    if image is not None and image.size > 0:
        cv2.imshow(window_name, image)


def put_metric(frame, label, value, x, y, color=(0, 255, 0)):
    text = f"{label}: {value:.3f}" if value is not None else f"{label}: N/A"
    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,   
        0.65,
        color,
        2,
    )


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("Kamera açılamadı.")
        return

    detector = FaceLandmarkDetector()

    ear_filter = EMAFilter(alpha=EMA_ALPHA_EAR)
    mar_filter = EMAFilter(alpha=EMA_ALPHA_MAR)

    raw_ear_history = []
    ema_ear_history = []
    raw_mar_history = []
    ema_mar_history = []
    time_history = []

    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame okunamadı.")
            break

        frame = cv2.flip(frame, 1)

        landmarks = detector.get_landmarks(frame)

        if landmarks is not None:
            left_eye_pts = detector.get_left_eye_points(landmarks)
            right_eye_pts = detector.get_right_eye_points(landmarks)
            mouth_pts = detector.get_mouth_points(landmarks)

            # Landmark noktaları
            draw_points(frame, left_eye_pts, color=(255, 0, 0), radius=2)
            draw_points(frame, right_eye_pts, color=(0, 255, 255), radius=2)
            draw_points(frame, mouth_pts, color=(0, 0, 255), radius=2)

            # ROI kutuları
            left_eye_box = points_to_bbox(
                left_eye_pts, frame.shape, pad_x=EYE_PADDING_X, pad_y=EYE_PADDING_Y
            )
            right_eye_box = points_to_bbox(
                right_eye_pts, frame.shape, pad_x=EYE_PADDING_X, pad_y=EYE_PADDING_Y
            )
            mouth_box = points_to_bbox(
                mouth_pts, frame.shape, pad_x=MOUTH_PADDING_X, pad_y=MOUTH_PADDING_Y
            )

            draw_bbox(frame, left_eye_box, color=(255, 0, 0), thickness=2)
            draw_bbox(frame, right_eye_box, color=(0, 255, 255), thickness=2)
            draw_bbox(frame, mouth_box, color=(0, 0, 255), thickness=2)

            # ROI crop
            left_eye_roi = crop_roi(frame, left_eye_box)
            right_eye_roi = crop_roi(frame, right_eye_box)
            mouth_roi = crop_roi(frame, mouth_box)

            show_if_valid(WINDOW_LEFT_EYE, left_eye_roi)
            show_if_valid(WINDOW_RIGHT_EYE, right_eye_roi)
            show_if_valid(WINDOW_MOUTH, mouth_roi)

            # Ham EAR
            left_ear = eye_aspect_ratio(left_eye_pts)
            right_ear = eye_aspect_ratio(right_eye_pts)

            raw_avg_ear = None
            if left_ear is not None and right_ear is not None:
                raw_avg_ear = (left_ear + right_ear) / 2.0

            # Ham MAR
            raw_mar = mouth_aspect_ratio(mouth_pts)

            # EMA uygulanmış değerler
            smooth_ear = ear_filter.update(raw_avg_ear)
            smooth_mar = mar_filter.update(raw_mar)
            

            t = time.time() - start_time

            time_history.append(t)
            raw_ear_history.append(raw_avg_ear if raw_avg_ear is not None else float("nan"))
            ema_ear_history.append(smooth_ear if smooth_ear is not None else float("nan"))
            raw_mar_history.append(raw_mar if raw_mar is not None else float("nan"))
            ema_mar_history.append(smooth_mar if smooth_mar is not None else float("nan"))

            cv2.putText(
                frame,
                "Face detected",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            # Ham değerler
            put_metric(frame, "Raw Left EAR", left_ear, 20, 70, color=(255, 0, 0))
            put_metric(frame, "Raw Right EAR", right_ear, 20, 100, color=(0, 255, 255))
            put_metric(frame, "Raw Avg EAR", raw_avg_ear, 20, 130, color=(0, 200, 0))
            put_metric(frame, "Raw MAR", raw_mar, 20, 160, color=(0, 0, 255))

            # Smooth değerler
            put_metric(frame, "EMA EAR", smooth_ear, 20, 210, color=(255, 255, 255))
            put_metric(frame, "EMA MAR", smooth_mar, 20, 240, color=(255, 255, 255))

        else:
            cv2.putText(
                frame,
                "No face detected",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

            # Yüz kaybolursa filtreyi koruyabilirsin ya da resetleyebilirsin.
            # Uzun süre yüz kaybında reset mantıklı olabilir.
            # ear_filter.reset()
            # mar_filter.reset()

        cv2.imshow(WINDOW_MAIN, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    plt.figure(figsize=(12, 6))
    plt.plot(time_history, raw_ear_history, label="Raw EAR")
    plt.plot(time_history, ema_ear_history, label="EMA EAR")
    plt.xlabel("Time (s)")
    plt.ylabel("EAR")
    plt.title("EAR over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("ear_plot.png", dpi=200)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(time_history, raw_mar_history, label="Raw MAR")
    plt.plot(time_history, ema_mar_history, label="EMA MAR")
    plt.xlabel("Time (s)")
    plt.ylabel("MAR")
    plt.title("MAR over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("mar_plot.png", dpi=200)
    plt.show()
    detector.close()
    cap.release()
    cv2.destroyAllWindows()

    # METRİCLERİ KAYDETME
    with open("metrics_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "raw_ear", "ema_ear", "raw_mar", "ema_mar"])

        for t, re, ee, rm, em in zip(
            time_history,
            raw_ear_history,
            ema_ear_history,
            raw_mar_history,
            ema_mar_history,
    ):
            writer.writerow([t, re, ee, rm, em])


if __name__ == "__main__":
    main()