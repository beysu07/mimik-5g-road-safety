import cv2


def clamp(val, low, high):
    return max(low, min(val, high))


def points_to_bbox(points, frame_shape, pad_x=0, pad_y=0):
    """
    points: [(x,y), ...]
    return: (x1, y1, x2, y2)
    """
    h, w = frame_shape[:2]

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    x1 = clamp(min(xs) - pad_x, 0, w - 1)
    y1 = clamp(min(ys) - pad_y, 0, h - 1)
    x2 = clamp(max(xs) + pad_x, 0, w - 1)
    y2 = clamp(max(ys) + pad_y, 0, h - 1)

    return x1, y1, x2, y2


def crop_roi(frame, bbox):
    x1, y1, x2, y2 = bbox

    if x2 <= x1 or y2 <= y1:
        return None

    roi = frame[y1:y2, x1:x2].copy()
    if roi.size == 0:
        return None

    return roi


def draw_bbox(frame, bbox, color=(0, 255, 0), thickness=2):
    x1, y1, x2, y2 = bbox
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)


def draw_points(frame, points, color=(0, 0, 255), radius=2):
    for x, y in points:
        cv2.circle(frame, (x, y), radius, color, -1)