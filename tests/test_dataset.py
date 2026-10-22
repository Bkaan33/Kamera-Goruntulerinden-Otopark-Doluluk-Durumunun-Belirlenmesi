"""ROI aracı ve veri setinin detector/evaluate uyumluluk kontrolleri."""

import importlib.util
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("roi_selector", ROOT / "dataset/roi_selector.py")
roi_selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roi_selector)


class EditorTests(unittest.TestCase):
    def test_reverse_drag_keeps_original_coordinates_after_display_scaling(self):
        editor = roi_selector.ROIEditor(np.zeros((1000, 2000, 3), np.uint8))
        editor.mouse(cv2.EVENT_LBUTTONDOWN, 300, 240, 0, None)
        editor.mouse(cv2.EVENT_LBUTTONUP, 60, 60, 0, None)
        self.assertEqual(editor.spots, [dict(id=0, x=100, y=100, width=400, height=300)])

    def test_delete_does_not_renumber_other_spots(self):
        spots = [dict(id=4, x=10, y=10, width=20, height=30),
                 dict(id=9, x=70, y=10, width=20, height=30)]
        editor = roi_selector.ROIEditor(np.zeros((100, 100, 3), np.uint8), spots)
        editor.labels = {4: True, 9: False}
        editor.mouse(cv2.EVENT_RBUTTONDOWN, 15, 15, 0, None)
        self.assertEqual([s['id'] for s in editor.spots], [9])
        self.assertEqual(editor.labels, {9: False})

    def test_invalid_geometry_is_rejected(self):
        valid = dict(id=0, x=10, y=10, width=20, height=30)
        for change in [dict(x=-1), dict(width=0), dict(height=101), dict(x=1.5), dict(id=True)]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                roi_selector.validate_rois(dict(spots=[dict(valid, **change)]), 100, 100)
        with self.assertRaises(ValueError):
            roi_selector.validate_rois(dict(spots=[valid, valid]), 100, 100)
        with self.assertRaises(ValueError):
            roi_selector.validate_rois(dict(image_width=200, spots=[valid]), 100, 100)

    def test_incomplete_labels_do_not_overwrite_files(self):
        editor = roi_selector.ROIEditor(np.zeros((100, 100, 3), np.uint8),
                                        [dict(id=0, x=10, y=10, width=20, height=30)])
        with tempfile.TemporaryDirectory() as directory:
            rois, labels = Path(directory)/'rois.json', Path(directory)/'labels.json'
            rois.write_text('unchanged')
            with self.assertRaises(ValueError):
                editor.save('photo.jpg', rois, labels, 'S1')
            self.assertEqual(rois.read_text(), 'unchanged')
            self.assertFalse(labels.exists())
            editor.labels[0] = False
            editor.save('photo.jpg', rois, labels, 'S1')
            self.assertEqual(json.loads(labels.read_text())['spots'], [dict(id=0, occupied=False)])


class DatasetTests(unittest.TestCase):
    def test_samples_match_manifest_rois_and_detector(self):
        from detector.parking_detector import load_rois, ParkingDetector, save_predictions
        manifest = json.loads((ROOT/'dataset/manifest.json').read_text())
        data = json.loads((ROOT/'dataset/rois.json').read_text())
        rois = load_rois(ROOT/'dataset/rois.json')
        self.assertEqual(len(manifest['images']), 12)
        self.assertEqual(len(rois), 37)
        states = set()
        for sample in manifest['images']:
            with self.subTest(image=sample['image']):
                path = ROOT/'dataset/images'/sample['image']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sample['sha256'])
                image = roi_selector.read_image(path)
                h, w = image.shape[:2]
                roi_selector.validate_rois(data, w, h)
                self.assertEqual((w,h), (sample['width'], sample['height']))
                labels = json.loads((ROOT/'dataset/labels'/path.with_suffix('.json').name).read_text())
                self.assertEqual(labels['image'], path.name)
                self.assertEqual([s['id'] for s in labels['spots']], [r['id'] for r in rois])
                self.assertTrue(all(type(s['occupied']) is bool for s in labels['spots']))
                states.update(s['occupied'] for s in labels['spots'])
                predictions = ParkingDetector(rois).detect(image)
                self.assertEqual(len(predictions), len(rois))
                with tempfile.TemporaryDirectory() as directory:
                    output = Path(directory)/'predictions.json'
                    save_predictions(predictions, path.name, output, sample['scenario'])
                    saved = json.loads(output.read_text())
                    self.assertEqual([s['id'] for s in saved['spots']], [s['id'] for s in labels['spots']])
        self.assertEqual(states, {True, False})


if __name__ == '__main__':
    unittest.main()
