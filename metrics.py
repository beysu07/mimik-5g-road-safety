import math


def euclidean_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.hypot(x2 - x1, y2 - y1)


def eye_aspect_ratio(eye_points):
    """
    6 noktalı göz için EAR hesaplar.
    Nokta sırası:
    [p1, p2, p3, p4, p5, p6]

    Formül:
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    if eye_points is None or len(eye_points) != 6:
        return None

    p1, p2, p3, p4, p5, p6 = eye_points

    vertical_1 = euclidean_distance(p2, p6)
    vertical_2 = euclidean_distance(p3, p5)
    horizontal = euclidean_distance(p1, p4)

    if horizontal == 0:
        return None

    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return ear


def mouth_aspect_ratio(mouth_points):
    """
    12 noktalı dış ağız konturu için basit MAR hesaplar.

    Index sırası:
    [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308]

    Yaklaşık eşleşme:
    sol köşe  -> mouth_points[0]
    sağ köşe  -> mouth_points[10]
    üst orta  -> mouth_points[5]
    alt orta  -> mouth_points[11]   # bu seçim veri akışına göre değişebilir

    Not:
    MediaPipe ağız noktalarında farklı MAR tanımları kullanılabilir.
    Bu sürüm başlangıç için yeterli.
    """
    if mouth_points is None or len(mouth_points) < 12:
        return None

    left_corner = mouth_points[0]
    right_corner = mouth_points[10]

    upper_lip = mouth_points[5]
    lower_lip = mouth_points[11]

    vertical = euclidean_distance(upper_lip, lower_lip)
    horizontal = euclidean_distance(left_corner, right_corner)

    if horizontal == 0:
        return None

    mar = vertical / horizontal
    return mar