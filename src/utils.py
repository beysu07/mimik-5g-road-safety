import re
import cv2

_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))


def clahe_bgr(img):
    """Adaptif kontrast iyilestirme (sadece L kanali) - dusuk isik icin."""
    if img is None or img.size == 0:
        return img
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = _clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


# TR plaka regex (FTR sartnamesi) - bosluksuz, buyuk harf normalize edilmis hali
_TR = str.maketrans({'İ': 'I', 'I': 'I', 'Ö': 'O', 'Ü': 'U', 'Ş': 'S', 'Ç': 'C', 'Ğ': 'G'})
PLATE_RE = re.compile(
    r'^(0[1-9]|[1-7][0-9]|8[01])(([A-Z])(\d{4,5})|([A-Z]{2})(\d{3,4})|([A-Z]{3})(\d{2,3}))$'
)


def normalize_plate(text):
    """OCR metnini normalize edip TR plaka regex'ine uyuyorsa dondurur, yoksa None."""
    if not text:
        return None
    t = text.upper().translate(_TR)
    t = re.sub(r'[^A-Z0-9]', '', t)
    return t if PLATE_RE.match(t) else None
