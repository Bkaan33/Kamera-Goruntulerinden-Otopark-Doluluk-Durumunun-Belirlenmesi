"""Fareyle park alanı seçimi ve elle doluluk etiketleme.

python dataset/roi_selector.py --image dataset/images/otopark.jpg
Sol sürükle: alan ekle; sol tık: seç; sağ tık: sil; o: dolu; b: boş.
s: kaydet; q/ESC: çık. Koordinatlar orijinal görüntü boyutundadır.
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent


def read_image(path):
    """Windows'ta Türkçe karakter içeren dosya yollarını da okuyabilir."""
    image = cv2.imdecode(np.frombuffer(Path(path).read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Görüntü okunamadı: {path}")
    return image


def validate_rois(data, width, height):
    if not isinstance(data, dict) or not isinstance(data.get("spots"), list) or not data["spots"]:
        raise ValueError("JSON içinde boş olmayan bir spots listesi gerekli.")
    if (data.get("image_width", width), data.get("image_height", height)) != (width, height):
        raise ValueError("ROI dosyasının görüntü boyutu seçilen fotoğrafla eşleşmiyor.")
    seen = set()
    for spot in data["spots"]:
        if not isinstance(spot, dict):
            raise ValueError("Her ROI bir JSON nesnesi olmalı.")
        if any(type(spot.get(k)) is not int for k in ("id", "x", "y", "width", "height")):
            raise ValueError("id, x, y, width ve height tam sayı olmalı.")
        x, y, w, h = (spot[k] for k in ("x", "y", "width", "height"))
        if spot["id"] in seen or spot["id"] < 0:
            raise ValueError("Park yeri id değerleri benzersiz ve negatif olmayan sayılar olmalı.")
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            raise ValueError(f"Görüntü dışına taşan veya geçersiz alan: {spot['id']}")
        seen.add(spot["id"])
    return data["spots"]


def write_json(path, data):
    """Dosyayı geçici dosya üzerinden değiştirerek yarım yazımı önler."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class ROIEditor:
    def __init__(self, image, spots=None):
        self.image = image
        self.height, self.width = image.shape[:2]
        # Görüntü boyutu değişmez; sadece ekranda gösterilen kopya küçültülür.
        self.display_width = min(self.width, 1200)
        self.display_height = max(1, round(self.height * self.display_width / self.width))
        self.spots = [dict(s) for s in (spots or [])]
        self.labels = {}
        self.selected = None
        self.start = self.end = None
        self.dirty = False

    def point(self, x, y):
        return (min(max(round(x * self.width / self.display_width), 0), self.width - 1),
                min(max(round(y * self.height / self.display_height), 0), self.height - 1))

    def at(self, point):
        x, y = point
        return next((s for s in reversed(self.spots)
                     if s["x"] <= x < s["x"] + s["width"]
                     and s["y"] <= y < s["y"] + s["height"]), None)

    def mouse(self, event, x, y, flags, parameter):
        point = self.point(x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start = self.end = point
        elif event == cv2.EVENT_MOUSEMOVE and self.start is not None:
            self.end = point
        elif event == cv2.EVENT_LBUTTONUP and self.start is not None:
            x1, x2 = sorted((self.start[0], point[0]))
            y1, y2 = sorted((self.start[1], point[1]))
            if x2 - x1 >= 4 and y2 - y1 >= 4:
                identity = max((s["id"] for s in self.spots), default=-1) + 1
                self.spots.append(dict(id=identity, x=x1, y=y1, width=x2-x1, height=y2-y1))
                self.selected = identity
                self.dirty = True
            else:
                hit = self.at(point)
                self.selected = hit["id"] if hit else None
            self.start = self.end = None
        elif event == cv2.EVENT_RBUTTONDOWN:
            hit = self.at(point)
            if hit:
                self.spots.remove(hit)
                self.labels.pop(hit["id"], None)
                self.selected = None
                self.dirty = True

    def render(self):
        canvas = self.image.copy()
        for s in self.spots:
            value = self.labels.get(s["id"])
            color = (0, 0, 230) if value is True else (0, 200, 0) if value is False else (0, 220, 255)
            x, y, w, h = (s[k] for k in ("x", "y", "width", "height"))
            cv2.rectangle(canvas, (x, y), (x+w-1, y+h-1), color, 3 if s["id"] == self.selected else 1)
            cv2.putText(canvas, str(s["id"]), (x+2, y+14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        if self.start is not None:
            cv2.rectangle(canvas, self.start, self.end, (255, 255, 0), 2)
        return canvas

    def save(self, image_path, output, label_path, scenario):
        data = dict(image=Path(image_path).name, image_width=self.width,
                    image_height=self.height, spots=self.spots)
        validate_rois(data, self.width, self.height)
        # Eksik etiket varsa ROI dahil hiçbir dosyayı yazma.
        if label_path and any(s["id"] not in self.labels for s in self.spots):
            raise ValueError("Etiket kaydı için her alanı seçip o (dolu) veya b (boş) tuşuna bas.")
        write_json(output, data)
        if label_path:
            write_json(label_path, dict(image=Path(image_path).name, scenario=scenario,
                       spots=[dict(id=s["id"], occupied=self.labels[s["id"]]) for s in self.spots]))
        self.dirty = False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "rois.json")
    parser.add_argument("--labels", type=Path, help="İsteğe bağlı gerçek dolu/boş etiket dosyası")
    parser.add_argument("--scenario", default="S1")
    parser.add_argument("--preview", type=Path, help="ROI önizlemesini kaydet ve pencere açmadan çık")
    args = parser.parse_args(argv)
    try:
        if args.labels and args.labels.resolve() == args.output.resolve():
            raise ValueError("ROI ve etiket dosyalarının yolları farklı olmalı.")
        image = read_image(args.image)
        height, width = image.shape[:2]
        spots = []
        if args.output.exists():
            spots = validate_rois(json.loads(args.output.read_text(encoding="utf-8")), width, height)
        editor = ROIEditor(image, spots)
        if args.labels and args.labels.exists():
            labels = json.loads(args.labels.read_text(encoding="utf-8"))
            if labels.get("image") != Path(args.image).name:
                raise ValueError("Etiket dosyası başka bir görüntüye ait.")
            rows = labels.get("spots", [])
            if any(type(s.get("occupied")) is not bool for s in rows):
                raise ValueError("occupied alanları true/false olmalı.")
            editor.labels = {s["id"]: s["occupied"] for s in rows}
            if len(editor.labels) != len(rows) or set(editor.labels) != {s["id"] for s in spots}:
                raise ValueError("Etiket ve ROI id değerleri eşleşmiyor.")
        if args.preview:
            if not spots:
                raise ValueError("Önizleme için önce ROI alanlarını kaydet.")
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            ok, encoded = cv2.imencode(args.preview.suffix or ".png", editor.render())
            if not ok:
                raise ValueError("Önizleme oluşturulamadı.")
            encoded.tofile(str(args.preview))
            print(f"Önizleme kaydedildi: {args.preview}")
            return 0
        name = "ROI secimi | surukle: ekle, tikla: sec, sag: sil, o/b: dolu/bos, s: kaydet, q: cik"
        print(name)
        print("Sarı: etiketsiz; kırmızı: dolu; yeşil: boş. S ile kaydetmeden çıkarsan değişiklikler silinir.")
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(name, editor.mouse)
        try:
            while True:
                cv2.imshow(name, cv2.resize(editor.render(), (editor.display_width, editor.display_height)))
                key = cv2.waitKey(20) & 0xFF
                if key in (ord("q"), 27) or cv2.getWindowProperty(name, cv2.WND_PROP_VISIBLE) < 1:
                    if editor.dirty:
                        print("Kaydedilmemiş değişiklikler bırakıldı.")
                    break
                if key in (ord("o"), ord("b")) and editor.selected is not None:
                    editor.labels[editor.selected] = key == ord("o")
                    editor.dirty = True
                if key == ord("s"):
                    try:
                        editor.save(args.image, args.output, args.labels, args.scenario)
                        print(f"{len(editor.spots)} alan kaydedildi: {args.output}")
                    except ValueError as error:
                        print(f"Hata: {error}")
        finally:
            cv2.destroyAllWindows()
        return 0
    except (OSError, ValueError, KeyError, TypeError, cv2.error) as error:
        print(f"Hata: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
