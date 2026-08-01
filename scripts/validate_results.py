import json
import re
import sys
from pathlib import Path


VALID_TIP = {"sedan", "suv", "hatchback", "pickup", "minibus", "panelvan", "kamyon"}
VALID_RENK = {
    "beyaz", "siyah", "gri", "kirmizi", "mavi", "sari", "yesil", "turuncu", "kahverengi"
}
VALID_LABELS = {
    "sofor_eylemi": {
        "arkaya_bakma", "esneme", "sigara_icme", "su_icme", "telefonla_konusma",
        "slalom", "etrafa_bakinma", "emniyet_kemeri_ihlali",
    },
    "nesneler": {"teknocan", "bilgisayar"},
    "yolcular": {"arka_koltuk_1", "arka_koltuk_2", "on_koltuk"},
}
PLATE_RE = re.compile(
    r"^(0[1-9]|[1-7][0-9]|8[01])(([A-Z])(\d{4,5})|([A-Z]{2})(\d{3,4})|([A-Z]{3})(\d{2,3}))$"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def confidence(value, field):
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} sayi olmali")
    require(0.0 <= float(value) <= 1.0, f"{field} 0 ile 1 arasinda olmali")


def validate(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    require(set(data) == {"video_id", "arac_bilgisi", "tespitler"}, "kok JSON anahtarlari hatali")
    require(isinstance(data["video_id"], str) and data["video_id"], "video_id bos olmayan metin olmali")

    vehicle = data["arac_bilgisi"]
    require(isinstance(vehicle, dict), "arac_bilgisi nesne olmali")
    require(set(vehicle) == {"tip", "plaka", "renk", "confidence_score"}, "arac_bilgisi anahtarlari hatali")
    require(vehicle["tip"] in VALID_TIP, "gecersiz tip")
    require(vehicle["renk"] in VALID_RENK, "gecersiz renk")
    confidence(vehicle["confidence_score"], "arac_bilgisi.confidence_score")

    plate = vehicle["plaka"]
    require(isinstance(plate, str), "plaka metin olmali")
    plate_warning = plate == "tespit edilemedi"
    require(plate_warning or PLATE_RE.fullmatch(plate), "plaka regex'e uymuyor")

    detections = data["tespitler"]
    require(isinstance(detections, list), "tespitler dizi olmali")
    for index, event in enumerate(detections):
        prefix = f"tespitler[{index}]"
        require(isinstance(event, dict), f"{prefix} nesne olmali")
        require(
            set(event) == {"zaman_saniye", "kategori", "etiket", "confidence_score"},
            f"{prefix} anahtarlari hatali",
        )
        require(event["kategori"] in VALID_LABELS, f"{prefix}.kategori gecersiz")
        require(event["etiket"] in VALID_LABELS[event["kategori"]], f"{prefix}.etiket gecersiz")
        require(
            isinstance(event["zaman_saniye"], (int, float))
            and not isinstance(event["zaman_saniye"], bool)
            and event["zaman_saniye"] >= 0,
            f"{prefix}.zaman_saniye gecersiz",
        )
        confidence(event["confidence_score"], f"{prefix}.confidence_score")

    print("SCHEMA_OK")
    if plate_warning:
        print("UYARI: Plaka okunamadi; plaka puani beklenmemeli.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Kullanim: python scripts/validate_results.py <results.json>")
    try:
        validate(sys.argv[1])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"SCHEMA_ERROR: {exc}") from exc
