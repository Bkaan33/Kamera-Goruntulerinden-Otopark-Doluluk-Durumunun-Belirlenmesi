"""Park alanı doluluk tespiti (Kutay KAYA).

ROI koordinatlarını okur, her park alanındaki beyaz piksel oranını hesaplar
ve dolu/boş kararı verir. Ön işleme için src/preprocessing.py kullanılır.

ROI dosyası (dataset/rois.json) formatı:
    {
      "spots": [
        {"id": 0, "x": 40, "y": 60, "width": 107, "height": 48},
        {"id": 1, "x": 160, "y": 60, "width": 107, "height": 48}
      ]
    }
Koordinatlar piksel cinsindendir; (x, y) park yerinin sol üst köşesidir.
Aynı kamera açısı ve görüntü boyutu için geçerlidir.
"""

import json
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np

# Ön işleme src/preprocessing.py içinde (Furkan TAŞKIRAN)
PREPROCESSING_KLASORU = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(PREPROCESSING_KLASORU))
from preprocessing import preprocess_image  # noqa: E402

VARSAYILAN_ROI_DOSYASI = Path(__file__).resolve().parent.parent / "dataset" / "rois.json"

# Beyaz piksel oranı bu değerin üzerindeyse alan DOLU sayılır.
# Başlangıç değeridir; park çizgisi kenarları boş alanda bile ~0.15-0.20 oran verir.
# Gerçek değer eşik setiyle belirlenecek (bkz. docs/test_plani.md).
VARSAYILAN_ESIK = 0.25


class ROIHatasi(Exception):
    """ROI dosyası okunamadığında veya geçersiz olduğunda fırlatılır."""


def load_rois(yol=VARSAYILAN_ROI_DOSYASI):
    """dataset/rois.json dosyasını okur, her alan için {"id", "x", "y", "width", "height"} döndürür."""
    yol = Path(yol)
    if not yol.exists():
        raise ROIHatasi(f"ROI dosyası bulunamadı: {yol}")

    try:
        with open(yol, encoding="utf-8") as f:
            ham = json.load(f)
    except (OSError, ValueError) as e:
        raise ROIHatasi(f"ROI dosyası okunamadı ({yol.name}): {e}") from e

    alanlar = ham.get("spots") if isinstance(ham, dict) else ham
    if not isinstance(alanlar, list) or not alanlar:
        raise ROIHatasi(f"ROI dosyasında 'spots' listesi yok veya boş: {yol}")

    rois, gorulen_idler = [], set()
    for i, a in enumerate(alanlar):
        try:
            roi = {"id": a.get("id", i), "x": int(a["x"]), "y": int(a["y"]),
                   "width": int(a["width"]), "height": int(a["height"])}
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ROIHatasi(f"{i}. alanda id/x/y/width/height eksik veya hatalı: {a}") from None
        if roi["width"] <= 0 or roi["height"] <= 0:
            raise ROIHatasi(f"{i}. alanın genişlik/yüksekliği pozitif olmalı: {a}")
        if roi["id"] in gorulen_idler:
            raise ROIHatasi(f"Aynı id birden fazla kez kullanılmış: {roi['id']}")
        gorulen_idler.add(roi["id"])
        rois.append(roi)
    return rois


def kose_noktalari(roi):
    """Çizim için dikdörtgenin dört köşesi."""
    x, y, w, h = roi["x"], roi["y"], roi["width"], roi["height"]
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.int32)


class ParkingDetector:
    """Her karede park alanlarının doluluğunu belirler.

    gecmis > 1 verilirse (video/kamera), her alanın kararı son N karedeki
    kararların çoğunluğuna göre verilir; anlık titremeler engellenir.
    """

    def __init__(self, rois, esik=VARSAYILAN_ESIK, gecmis=1):
        self.rois = rois
        self.esik = esik
        self._gecmis = {r["id"]: deque(maxlen=gecmis) for r in rois}
        self._kontrol_edilen_boyut = None

    def _sinirlari_kontrol_et(self, yukseklik, genislik):
        """ROI'ler görüntünün dışına taşıyorsa bir kez uyarır."""
        if self._kontrol_edilen_boyut == (yukseklik, genislik):
            return
        self._kontrol_edilen_boyut = (yukseklik, genislik)
        tasanlar = [r["id"] for r in self.rois
                    if r["x"] < 0 or r["y"] < 0
                    or r["x"] + r["width"] > genislik or r["y"] + r["height"] > yukseklik]
        if tasanlar:
            print(f"Uyarı: {len(tasanlar)} park alanı görüntünün ({genislik}x{yukseklik}) "
                  f"dışına taşıyor: {tasanlar[:10]}. ROI dosyası bu görüntü boyutu "
                  f"için hazırlanmamış olabilir.")

    def detect(self, frame):
        """Bir kareyi işler. Her alan için {"id", "occupied", "ratio", "points"} döndürür."""
        if frame is None or frame.size == 0:
            raise ValueError("Boş kare alındı.")

        islenmis = preprocess_image(frame)
        h_img, w_img = islenmis.shape[:2]
        self._sinirlari_kontrol_et(h_img, w_img)

        sonuclar = []
        for roi in self.rois:
            x1, y1 = max(roi["x"], 0), max(roi["y"], 0)
            x2 = min(roi["x"] + roi["width"], w_img)
            y2 = min(roi["y"] + roi["height"], h_img)
            alan = max(x2 - x1, 0) * max(y2 - y1, 0)
            oran = cv2.countNonZero(islenmis[y1:y2, x1:x2]) / alan if alan else 0.0

            gecmis = self._gecmis[roi["id"]]
            gecmis.append(oran > self.esik)
            dolu = sum(gecmis) > len(gecmis) / 2

            sonuclar.append({"id": roi["id"], "occupied": dolu,
                             "ratio": round(oran, 4), "points": kose_noktalari(roi)})
        return sonuclar


def bos_sayisi(sonuclar):
    return sum(1 for s in sonuclar if not s["occupied"])


def save_predictions(sonuclar, goruntu_adi, yol, senaryo=None):
    """Sonuçları tests/evaluate.py'nin okuduğu JSON formatında kaydeder:
    {"image": ..., "scenario": ..., "spots": [{"id": 0, "occupied": true, "ratio": 0.42}, ...]}
    """
    veri = {"image": goruntu_adi}
    if senaryo:
        veri["scenario"] = senaryo
    veri["spots"] = [{"id": s["id"], "occupied": s["occupied"], "ratio": s["ratio"]}
                     for s in sonuclar]
    Path(yol).parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
