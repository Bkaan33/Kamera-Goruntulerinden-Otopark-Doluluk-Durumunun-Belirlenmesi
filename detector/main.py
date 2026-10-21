"""Otopark doluluk sistemi - çalıştırma dosyası (Kutay KAYA).

Örnekler:
    # Fotoğraf
    python detector/main.py --source dataset/otopark.jpg --rois dataset/CarParkPos

    # Video (tekrar etmek için --loop)
    python detector/main.py --source dataset/otopark.mp4 --rois dataset/rois.json

    # Webcam (0 = varsayılan kamera)
    python detector/main.py --source 0 --rois dataset/rois.json

Pencerede: q veya ESC = çıkış, + / - = eşiği değiştir, boşluk = duraklat.
"""

import argparse
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parking_detector import (VARSAYILAN_ESIK, VARSAYILAN_GENISLIK,  # noqa: E402
                              VARSAYILAN_YUKSEKLIK, ParkingDetector, ROIHatasi,
                              bos_sayisi, load_rois, save_predictions)

YESIL = (0, 200, 0)
KIRMIZI = (0, 0, 220)
GORUNTU_UZANTILARI = {".jpg", ".jpeg", ".png", ".bmp"}


def ciz(frame, sonuclar, esik, fps=None):
    """Alanları yeşil/kırmızı çizer, sayacı ve bilgileri ekrana yazar."""
    cikti = frame.copy()
    for s in sonuclar:
        renk = KIRMIZI if s["occupied"] else YESIL
        cv2.polylines(cikti, [s["points"]], True, renk, 2)
        x, y = s["points"].min(axis=0)
        cv2.putText(cikti, f"{s['ratio']:.2f}", (int(x) + 3, int(y) + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, renk, 1, cv2.LINE_AA)

    bos, toplam = bos_sayisi(sonuclar), len(sonuclar)
    # OpenCV Türkçe karakter (ş, ı) çizemediği için "Bos" yazılıyor
    metin = f"Bos: {bos} / {toplam}"
    (tw, th), _ = cv2.getTextSize(metin, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
    cv2.rectangle(cikti, (10, 10), (30 + tw, 30 + th), (40, 40, 40), -1)
    cv2.putText(cikti, metin, (20, 20 + th), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                YESIL if bos else KIRMIZI, 2, cv2.LINE_AA)

    bilgi = f"esik={esik:.2f}" + (f"  fps={fps:.0f}" if fps else "")
    cv2.putText(cikti, bilgi, (20, 50 + th), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA)
    return cikti


def tus_isle(tus, detector):
    """Klavye kısayolları. Çıkılacaksa False döndürür."""
    if tus in (ord("q"), 27):
        return False
    if tus in (ord("+"), ord("=")):
        detector.esik = min(detector.esik + 0.01, 1.0)
    elif tus == ord("-"):
        detector.esik = max(detector.esik - 0.01, 0.0)
    return True


def fotograf_isle(args, detector):
    frame = cv2.imread(args.source)
    if frame is None:
        print(f"Hata: '{args.source}' okunamadı. Dosya yolu ve formatı doğru mu?")
        return 1

    while True:
        baslangic = time.perf_counter()
        sonuclar = detector.detect(frame)
        sure = (time.perf_counter() - baslangic) * 1000
        cikti = ciz(frame, sonuclar, detector.esik)

        if args.show:
            cv2.imshow("Otopark Doluluk", cikti)
            if tus_isle(cv2.waitKey(0) & 0xFF, detector):
                continue  # eşik değişti, tekrar hesapla
        break

    print(f"Boş: {bos_sayisi(sonuclar)} / {len(sonuclar)}  ({sure:.1f} ms)")
    if args.output:
        cv2.imwrite(args.output, cikti)
        print(f"Çıktı görüntüsü kaydedildi: {args.output}")
    if args.save_json:
        save_predictions(sonuclar, Path(args.source).name, args.save_json, args.scenario)
        print(f"Tahminler kaydedildi: {args.save_json}")
    return 0


def video_isle(args, detector):
    kaynak = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(kaynak)
    if not cap.isOpened():
        print(f"Hata: '{args.source}' açılamadı. "
              + ("Kamera bağlı mı?" if isinstance(kaynak, int) else "Dosya yolu doğru mu?"))
        return 1

    yazici, duraklat, fps, sonuclar, frame = None, False, 0.0, [], None
    try:
        while True:
            if not duraklat or frame is None:
                ok, frame = cap.read()
                if not ok or frame is None:
                    if args.loop and not isinstance(kaynak, int):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    break

            baslangic = time.perf_counter()
            sonuclar = detector.detect(frame)
            gecen = time.perf_counter() - baslangic
            fps = 0.9 * fps + 0.1 * (1 / gecen) if fps else 1 / gecen
            cikti = ciz(frame, sonuclar, detector.esik, fps)

            if args.output:
                if yazici is None:
                    h, w = cikti.shape[:2]
                    yazici = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"),
                                             cap.get(cv2.CAP_PROP_FPS) or 25, (w, h))
                yazici.write(cikti)

            if args.show:
                cv2.imshow("Otopark Doluluk", cikti)
                tus = cv2.waitKey(1) & 0xFF
                if tus == ord(" "):
                    duraklat = not duraklat
                elif not tus_isle(tus, detector):
                    break
    finally:
        cap.release()
        if yazici:
            yazici.release()

    if sonuclar:
        print(f"Son kare - Boş: {bos_sayisi(sonuclar)} / {len(sonuclar)}, ~{fps:.0f} FPS")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Kamera görüntülerinden otopark doluluk tespiti")
    ap.add_argument("--source", required=True, help="Fotoğraf, video yolu veya kamera numarası (0)")
    ap.add_argument("--rois", required=True, help="ROI dosyası (CarParkPos/pickle veya .json)")
    ap.add_argument("--threshold", type=float, default=VARSAYILAN_ESIK, help="Doluluk eşiği (0-1)")
    ap.add_argument("--width", type=int, default=VARSAYILAN_GENISLIK, help="CarParkPos alan genişliği")
    ap.add_argument("--height", type=int, default=VARSAYILAN_YUKSEKLIK, help="CarParkPos alan yüksekliği")
    ap.add_argument("--history", type=int, default=5, help="Video için çoğunluk oyu kare sayısı")
    ap.add_argument("--output", help="Çıktıyı kaydet (fotoğraf veya .mp4)")
    ap.add_argument("--save-json", help="Tahminleri evaluate.py formatında kaydet (sadece fotoğraf)")
    ap.add_argument("--scenario", help="Test senaryosu etiketi (S1, S2...)")
    ap.add_argument("--loop", action="store_true", help="Video bitince başa sar")
    ap.add_argument("--no-show", dest="show", action="store_false", help="Pencere açma")
    args = ap.parse_args()

    try:
        rois = load_rois(args.rois, args.width, args.height)
    except ROIHatasi as e:
        print(f"Hata: {e}")
        return 1
    print(f"{len(rois)} park alanı yüklendi.")

    fotograf = Path(args.source).suffix.lower() in GORUNTU_UZANTILARI
    detector = ParkingDetector(rois, esik=args.threshold,
                               gecmis=1 if fotograf else max(args.history, 1))
    try:
        return fotograf_isle(args, detector) if fotograf else video_isle(args, detector)
    finally:
        if args.show:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    sys.exit(main())
