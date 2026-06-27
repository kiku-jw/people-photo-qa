from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from photoqa.workflow import analyze_photos, export_report, ingest_directory, init_database


class BasicMvpTest(unittest.TestCase):
    def test_ingest_analyze_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            photos = root / "photos"
            photos.mkdir()
            image_path = photos / "person_001.jpg"
            image = Image.new("RGB", (900, 1200), color=(180, 160, 145))
            image.save(image_path)

            db_path = root / "photoqa.sqlite"
            report_path = root / "report.csv"

            init_database(db_path)
            ingest_result = ingest_directory(
                db_path,
                photos,
                "signed_consent_v1",
                "stem",
                False,
            )
            analyze_result = analyze_photos(db_path, None, False)
            exported = export_report(db_path, report_path, None)

            self.assertEqual(ingest_result["inserted"], 1)
            self.assertEqual(ingest_result["errors"], 0)
            self.assertEqual(analyze_result["analyzed"], 1)
            self.assertEqual(exported, 1)

            with report_path.open("r", newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["subject_id"], "person_001")
            self.assertEqual(rows[0]["width"], "900")
            self.assertEqual(rows[0]["height"], "1200")
            self.assertTrue(rows[0]["quality_score"])


if __name__ == "__main__":
    unittest.main()
