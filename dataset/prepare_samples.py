"""Sabitlenmiş PKLot örneklerini ve kaynak etiketlerini yeniden hazırlar.

python dataset/prepare_samples.py
Yalnızca Python standart kütüphanesini kullanır. Ağ erişimi gerektirir.
"""

import hashlib
import io
import json
import math
import tarfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def download(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def rectangle(annotation, width, height):
    x, y, w, h = annotation["bbox"]
    left, top = max(0, math.floor(x)), max(0, math.floor(y))
    right, bottom = min(width, math.ceil(x+w)), min(height, math.ceil(y+h))
    if right <= left or bottom <= top:
        raise ValueError("Kaynakta geçersiz park alanı var.")
    return left, top, right-left, bottom-top


def prepare():
    config = json.loads((ROOT / "sample_sources.json").read_text(encoding="utf-8"))
    base = f"https://raw.githubusercontent.com/{config['repository']}/{config['commit']}/"
    archive = download(base + config["annotation_archive"])
    # Arşivi diske açmadan yalnızca JSON içeriğini oku.
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as handle:
        member = next(m for m in handle.getmembers() if m.isfile() and m.name.endswith(".json"))
        annotations = json.load(handle.extractfile(member))
    category_names = {c["id"]: c["name"] for c in annotations["categories"]}
    if category_names != {0: "empty", 1: "occupied"}:
        raise ValueError("Kaynağın kategori eşlemesi değişmiş.")
    wanted = {config["subset"] + "/" + path for path in config["images"]}
    images = {im["file_name"]: im for im in annotations["images"] if im["file_name"] in wanted}
    if set(images) != wanted:
        raise ValueError("Bazı örneklerin kaynak etiketleri eksik.")
    selected_ids = {im["id"] for im in images.values()}
    per_image = {identity: [] for identity in selected_ids}
    for annotation in annotations["annotations"]:
        if annotation["image_id"] in selected_ids:
            per_image[annotation["image_id"]].append(annotation)

    def get_image(relative):
        name = Path(relative).name
        image_bytes = download(base + config["subset"] + "/" + relative)
        (ROOT / "images").mkdir(parents=True, exist_ok=True)
        (ROOT / "images" / name).write_bytes(image_bytes)
        return name, hashlib.sha256(image_bytes).hexdigest()

    with ThreadPoolExecutor(max_workers=4) as executor:
        hashes = dict(executor.map(get_image, config["images"]))
    reference_geometry = None
    manifest = []
    for index, relative in enumerate(config["images"]):
        name = Path(relative).name
        image = images[config["subset"] + "/" + relative]
        width, height = image["width"], image["height"]
        areas = sorted(per_image[image["id"]], key=lambda a: rectangle(a, width, height))
        geometry = [rectangle(a, width, height) for a in areas]
        if not geometry or len(set(geometry)) != len(geometry):
            raise ValueError("Park alanı koordinatları eksik veya yinelenmiş.")
        if reference_geometry is None:
            reference_geometry = geometry
            spots = [dict(id=i, x=x, y=y, width=w, height=h)
                     for i, (x, y, w, h) in enumerate(geometry)]
            dump(ROOT / "rois.json", dict(image=name, image_width=width, image_height=height,
                 camera="UFPR04", source=config["repository"], spots=spots))
        if geometry != reference_geometry:
            raise ValueError("Kamera geometrisi değişmiş; ayrı ROI dosyası gerekli.")
        weather = relative.split("/")[0]
        scenario = "S1" if weather == "Sunny" else "S4"
        dump(ROOT / "labels" / (Path(name).stem + ".json"),
             dict(image=name, scenario=scenario,
                  spots=[dict(id=i, occupied=a["category_id"] == 1) for i, a in enumerate(areas)]))
        manifest.append(dict(image=name, width=width, height=height, weather=weather,
                        scenario=scenario, split="calibration" if index % 4 == 0 else "test",
                        source_url=base + config["subset"] + "/" + relative,
                        source_image_id=image["id"], sha256=hashes[name],
                        annotation_ids=[a["id"] for a in areas]))
    dump(ROOT / "manifest.json", dict(camera="UFPR04", license="CC BY 4.0",
         annotation_archive_url=base + config["annotation_archive"],
         annotation_archive_sha256=hashlib.sha256(archive).hexdigest(), images=manifest))
    print(f"{len(manifest)} görüntü, {len(reference_geometry)} park alanı ve etiketleri hazır.")


if __name__ == "__main__":
    prepare()
