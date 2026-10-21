"""Park alanı doluluk tespiti (Kutay KAYA).

ROI koordinatlarını okur, her park alanındaki beyaz piksel oranını hesaplar
ve dolu/boş kararı verir. Ön işleme için src/preprocessing.py kullanılır.

Desteklenen ROI dosya formatları:
  1. CarParkPos (pickle): [(x, y), (x, y), ...]  sol üst köşeler,
     tüm alanlar sabit genişlik/yükseklikte kabul edilir.
  2. JSON, dikdörtgen: {"spots": [{"id": 0, "x": 10, "y": 20, "w": 107, "h": 48}, ...]}
  3. JSON, çokgen:     {"spots": [{"id": 0, "points": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]}, ...]}
"""

import json
import pickle
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np

# preprocessing.py taşınırsa sadece bu satırı güncellemek yeterli
PREPROCESSING_KLASORU = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(PREPROCESSING_KLASORU))
from preprocessing import preprocess_image  # noqa: E402

# CarParkPos formatında park alanı boyutu (piksel)
VARSAYILAN_GENISLIK = 107
VARSAYILAN_YUKSEKLIK = 48

# Beyaz piksel oranı bu değerin üzerindeyse alan DOLU sayılır.
# Başlangıç değeridir; park çizgisi kenarları boş alanda bile ~0.15-0.20 oran verir.
# Gerçek değer eşik setiyle belirlenecek (bkz. docs/test_plani.md).
VARSAYILAN_ESIK = 0.25


class ROIHatasi(Exception):
    """ROI dosyası okunamadığında veya geçersiz olduğunda fırlatılır."""


def _dikdortgen(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def load_rois(yol, genislik=VARSAYILAN_GENISLIK, yukseklik=VARSAYILAN_YUKSEKLIK):
    """ROI dosyasını okur, her alan için {"id", "points"} listesi döndürür."""
    yol = Path(yol)
    if not yol.exists():
        raise ROIHatasi(f"ROI dosyası bulunamadı: {yol}")

    try:
        if yol.suffix.lower() == ".json":
            with open(yol, encoding="utf-8") as f:
                ham = json.load(f)
            alanlar = ham["spots"] if isinstance(ham, dict) else ham
        else:  # CarParkPos / .pickle / .pkl
            with open(yol, "rb") as f:
                ham = pickle.load(f)
            alanlar = [{"id": i, "x": p[0], "y": p[1], "w": genislik, "h": yukseklik}
                       for i, p in enumerate(ham)]
    except (OSError, ValueError, KeyError, TypeError, pickle.UnpicklingError) as e:
        raise ROIHatasi(f"ROI dosyası okunamadı ({yol.name}): {e}") from e

    rois = []
    for i, a in enumerate(alanlar):
        if "points" in a:
            noktalar = a["points"]
        elif all(k in a for k in ("x", "y", "w", "h")):
            noktalar = _dikdortgen(a["x"], a["y"], a["w"], a["h"])
        else:
            raise ROIHatasi(f"{i}. alanın koordinatları eksik: {a}")
        rois.append({"id": a.get("id", i), "points": np.array(noktalar, dtype=np.int32)})

    if not rois:
        raise ROIHatasi(f"ROI dosyasında hiç park alanı yok: {yol}")
    return rois


class ParkingDetector:
    """Her karede park alanlarının doluluğunu belirler.

    gecmis > 1 verilirse (video/kamera), her alanın kararı son N karedeki
    kararların çoğunluğuna göre verilir; anlık titremeler engellenir.
    """

    def __init__(self, rois, esik=VARSAYILAN_ESIK, gecmis=1):
        self.rois = rois
        self.esik = esik
        self._maskeler = {}
        self._gecmis = {r["id"]: deque(maxlen=gecmis) for r in rois}

    def _maske(self, roi, sekil):
        """Çokgen ROI için maske ve sınır kutusu (önbellekli)."""
        anahtar = (roi["id"], sekil)
        if anahtar not in self._maskeler:
            x, y, w, h = cv2.boundingRect(roi["points"])
            x, y = max(x, 0), max(y, 0)
            w, h = min(w, sekil[1] - x), min(h, sekil[0] - y)
            maske = np.zeros((max(h, 0), max(w, 0)), np.uint8)
            if w > 0 and h > 0:
                cv2.fillPoly(maske, [roi["points"] - [x, y]], 255)
            self._maskeler[anahtar] = (x, y, w, h, maske, cv2.countNonZero(maske))
        return self._maskeler[anahtar]

    def detect(self, frame):
        """Bir kareyi işler. Her alan için {"id", "occupied", "ratio", "points"} döndürür."""
        if frame is None or frame.size == 0:
            raise ValueError("Boş kare alındı.")

        islenmis = preprocess_image(frame)
        sonuclar = []
        for roi in self.rois:
            x, y, w, h, maske, alan = self._maske(roi, islenmis.shape[:2])
            if alan == 0:  # ROI görüntünün dışında
                oran = 0.0
            else:
                parca = islenmis[y:y + h, x:x + w]
                oran = cv2.countNonZero(cv2.bitwise_and(parca, maske)) / alan

            gecmis = self._gecmis[roi["id"]]
            gecmis.append(oran > self.esik)
            dolu = sum(gecmis) > len(gecmis) / 2

            sonuclar.append({"id": roi["id"], "occupied": dolu,
                             "ratio": round(oran, 4), "points": roi["points"]})
        return sonuclar


def bos_sayisi(sonuclar):
    return sum(1 for s in sonuclar if not s["occupied"])


def save_predictions(sonuclar, goruntu_adi, yol, senaryo=None):
    """Sonuçları tests/evaluate.py'nin okuduğu JSON formatında kaydeder."""
    veri = {"image": goruntu_adi,
            "spots": [{"id": s["id"], "occupied": s["occupied"], "ratio": s["ratio"]}
                      for s in sonuclar]}
    if senaryo:
        veri["scenario"] = senaryo
    Path(yol).parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
