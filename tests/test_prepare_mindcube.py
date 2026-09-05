from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from utils.prepare_mindcube import (
    DatasetExpectations,
    MindCubePreparationError,
    build_prepared_rows,
    prepare_mindcube,
    validate_prepared_rows,
)


class PrepareMindCubeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.image_root = self.root / "data"
        self.raw_path = self.root / "MindCube_tinybench.jsonl"
        self.output_dir = self.root / "prepared"

        # The lexical order deliberately differs from semantic Image 1..N order.
        self.rows = [
            {
                "id": "among_case_1",
                "question": "Where is the object? A. Left B. Right C. Behind",
                "images": [
                    "other_all_image/z_front.jpg",
                    "other_all_image/a_left.jpg",
                    "other_all_image/m_back.jpg",
                    "other_all_image/b_right.jpg",
                ],
                "gt_answer": "C",
                "category": ["fixture"],
                "type": "fixture",
                "meta_info": ["object"],
            },
            {
                "id": "around_case_2",
                "question": "How did the view change? A. Forward B. Backward",
                "images": [
                    "other_all_image/y_second.png",
                    "other_all_image/c_first.png",
                ],
                "gt_answer": "A",
                "category": ["fixture"],
                "type": "fixture",
                "meta_info": ["object"],
            },
            {
                "id": "rotation_case_3",
                "question": "What is visible? A. Chair B. Desk C. Door D. Lamp",
                "images": [
                    "other_all_image/x_view1.png",
                    "other_all_image/d_view2.png",
                    "other_all_image/w_view3.png",
                ],
                "gt_answer": "D",
                "category": ["fixture"],
                "type": "fixture",
                "meta_info": ["object"],
            },
        ]
        for relative_path in {
            image for row in self.rows for image in row["images"]
        }:
            path = self.image_root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("fixture:" + relative_path).encode("utf-8"))

        with self.raw_path.open("w", encoding="utf-8") as handle:
            for row in self.rows:
                handle.write(json.dumps(row) + "\n")

        self.expectations = DatasetExpectations(
            records=3,
            image_references=9,
            unique_images=9,
            image_count_distribution=((2, 1), (3, 1), (4, 1)),
            setting_distribution=(("among", 1), ("around", 1), ("rotation", 1)),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def raw_sha256(self) -> str:
        return hashlib.sha256(self.raw_path.read_bytes()).hexdigest()

    def test_prepare_preserves_semantic_order_and_answers(self) -> None:
        summary = prepare_mindcube(
            raw_path=self.raw_path,
            image_root=self.image_root,
            output_dir=self.output_dir,
            expectations=self.expectations,
            expected_raw_sha256=self.raw_sha256(),
            official_code_revision="fixture-code-revision",
            dataset_revision="fixture-data-revision",
            data_archive_sha256="f" * 64,
        )

        prepared = json.loads((self.output_dir / "test.json").read_text())
        first = prepared[0]
        self.assertEqual(first["source_images"], self.rows[0]["images"])
        self.assertNotEqual(first["source_images"], sorted(self.rows[0]["images"]))
        self.assertEqual(
            first["img_paths"],
            [str((self.image_root / path).resolve()) for path in self.rows[0]["images"]],
        )
        self.assertEqual(first["correct_answer_letter"], "C")
        self.assertEqual(first["gt_answer"], "C")
        self.assertEqual(first["correct_answer"], "C. Behind")
        self.assertEqual(first["answer_choices"], ["A. Left", "B. Right", "C. Behind"])

        provenance = json.loads(
            (self.output_dir / "test_provenance.json").read_text()
        )
        self.assertEqual(provenance["dataset"]["revision"], "fixture-data-revision")
        self.assertEqual(
            provenance["official_code"]["revision"], "fixture-code-revision"
        )
        self.assertEqual(provenance["validation"]["records"], 3)
        self.assertEqual(provenance["validation"]["image_references"], 9)
        self.assertEqual(provenance["validation"]["unique_images"], 9)
        self.assertEqual(provenance["validation"]["missing_images"], 0)
        self.assertEqual(
            [entry["relative_path"] for entry in provenance["unique_image_manifest_first_seen"][:4]],
            self.rows[0]["images"],
        )
        self.assertEqual(summary["output"], str((self.output_dir / "test.json").resolve()))

    def test_validator_rejects_reordered_images_even_if_paths_exist(self) -> None:
        prepared = build_prepared_rows(self.rows, self.image_root)
        prepared[0]["source_images"] = list(reversed(prepared[0]["source_images"]))
        prepared[0]["img_paths"] = list(reversed(prepared[0]["img_paths"]))

        with self.assertRaisesRegex(
            MindCubePreparationError, "Official image order changed"
        ):
            validate_prepared_rows(
                self.rows, prepared, self.image_root, self.expectations
            )

    def test_validator_rejects_missing_image(self) -> None:
        prepared = build_prepared_rows(self.rows, self.image_root)
        (self.image_root / self.rows[-1]["images"][-1]).unlink()

        with self.assertRaisesRegex(MindCubePreparationError, "missing MindCube images"):
            validate_prepared_rows(
                self.rows, prepared, self.image_root, self.expectations
            )

    def test_converter_rejects_absolute_source_image(self) -> None:
        bad_rows = [dict(self.rows[0])]
        bad_rows[0]["images"] = ["/tmp/not-official.jpg", "other_all_image/a_left.jpg"]
        with self.assertRaisesRegex(
            MindCubePreparationError, "safe relative POSIX paths"
        ):
            build_prepared_rows(bad_rows, self.image_root)


if __name__ == "__main__":
    unittest.main()
