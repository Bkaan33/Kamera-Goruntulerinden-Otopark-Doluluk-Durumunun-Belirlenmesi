"""Otopark doluluk sisteminin değerlendirme scripti (İP 6).

Kullanım:
    # Etiketlerle tahminleri karşılaştır
    python tests/evaluate.py --labels data/labels --predictions data/predictions

    # Ön işleme süresini ölç
    python tests/evaluate.py --benchmark data/images
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJE_KOKU / "src"))


def json_oku(yol):
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    return {s["id"]: bool(s["occupied"]) for s in veri["spots"]}, veri.get("scenario", "-")


def degerlendir(etiket_klasoru, tahmin_klasoru):
    etiket_dosyalari = sorted(Path(etiket_klasoru).glob("*.json"))
    if not etiket_dosyalari:
        print(f"Hata: '{etiket_klasoru}' içinde etiket dosyası bulunamadı.")
        return 1

    # senaryo -> [görüntü sayısı, doğru, toplam alan, sayım hatası toplamı, yanlış boş]
    sonuc = defaultdict(lambda: [0, 0, 0, 0, 0])

    for etiket_yolu in etiket_dosyalari:
        tahmin_yolu = Path(tahmin_klasoru) / etiket_yolu.name
        if not tahmin_yolu.exists():
            print(f"Uyarı: {etiket_yolu.name} için tahmin dosyası yok, atlandı.")
            continue

        gercek, senaryo = json_oku(etiket_yolu)
        tahmin, _ = json_oku(tahmin_yolu)

        eksik = set(gercek) - set(tahmin)
        if eksik:
            print(f"Uyarı: {etiket_yolu.name} içinde tahmini olmayan alanlar: {sorted(eksik)}")

        dogru = sum(1 for i in gercek if tahmin.get(i) == gercek[i])
        yanlis_bos = sum(1 for i in gercek if gercek[i] and tahmin.get(i) is False)
        gercek_bos = sum(1 for v in gercek.values() if not v)
        tahmin_bos = sum(1 for i in gercek if tahmin.get(i) is False)

        for anahtar in (senaryo, "TOPLAM"):
            s = sonuc[anahtar]
            s[0] += 1
            s[1] += dogru
            s[2] += len(gercek)
            s[3] += abs(tahmin_bos - gercek_bos)
            s[4] += yanlis_bos

    if not sonuc:
        print("Hiçbir görüntü değerlendirilemedi.")
        return 1

    print(f"\n{'Senaryo':<8} {'Görüntü':>7} {'Doğruluk':>9} {'Ort. sayım hatası':>18} {'Yanlış boş':>11}")
    print("-" * 57)
    for anahtar in sorted(sonuc, key=lambda k: (k == "TOPLAM", k)):
        n, dogru, toplam, sayim, yb = sonuc[anahtar]
        print(f"{anahtar:<8} {n:>7} {dogru / toplam:>8.1%} {sayim / n:>18.2f} {yb:>11}")
    return 0


def benchmark(goruntu_klasoru, tekrar=20):
    import cv2
    from preprocessing import preprocess_image

    uzantilar = {".jpg", ".jpeg", ".png", ".bmp"}
    yollar = sorted(p for p in Path(goruntu_klasoru).iterdir() if p.suffix.lower() in uzantilar)
    if not yollar:
        print(f"Hata: '{goruntu_klasoru}' içinde görüntü bulunamadı.")
        return 1

    sureler = []
    for yol in yollar:
        goruntu = cv2.imread(str(yol))
        if goruntu is None:
            print(f"Uyarı: {yol.name} okunamadı, atlandı.")
            continue
        for _ in range(tekrar):
            baslangic = time.perf_counter()
            preprocess_image(goruntu)
            sureler.append((time.perf_counter() - baslangic) * 1000)

    if not sureler:
        return 1
    ort = sum(sureler) / len(sureler)
    print(f"Ön işleme: ortalama {ort:.2f} ms/kare (~{1000 / ort:.0f} FPS), {len(sureler)} ölçüm")
    print("Not: Doluluk kararı ve çizim eklenince bu ölçüm tüm işlem hattı için tekrarlanmalı.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Otopark doluluk sistemi değerlendirmesi")
    ap.add_argument("--labels", help="Gerçek etiket JSON klasörü")
    ap.add_argument("--predictions", help="Sistem çıktısı JSON klasörü")
    ap.add_argument("--benchmark", help="Süre ölçümü için görüntü klasörü")
    args = ap.parse_args()

    if args.benchmark:
        return benchmark(args.benchmark)
    if args.labels and args.predictions:
        return degerlendir(args.labels, args.predictions)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
