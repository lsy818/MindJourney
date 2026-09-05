from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from utils.prepare_mmsi_bench import (  # noqa: E402
    OFFICIAL_DATASET_REVISION,
    OFFICIAL_EXPECTATIONS,
    DatasetExpectations,
    DatasetValidationError,
    parse_official_question,
    prepare_mmsi_bench,
)


def _question(index: int) -> str:
    if index == 1:
        return (
            "Where is the object?\n"
            "Options: A: Front; B: Rear; C: Left; D: Right"
        )
    return (
        "Where is the object?\n"
        "Options: A: Front, B: Rear, C: Left, D: Right"
    )


class PrepareMMSIBenchTest(unittest.TestCase):
    def test_official_expectations_pin_full_split(self) -> None:
        self.assertEqual(OFFICIAL_EXPECTATIONS.row_count, 1000)
        self.assertEqual(OFFICIAL_EXPECTATIONS.image_count, 2550)
        self.assertEqual(OFFICIAL_EXPECTATIONS.min_images_per_question, 2)
        self.assertEqual(OFFICIAL_EXPECTATIONS.max_images_per_question, 10)
        self.assertEqual(len(OFFICIAL_DATASET_REVISION), 40)

    def test_parse_official_question_supports_official_separators(self) -> None:
        stem, choices = parse_official_question(_question(0))
        self.assertEqual(stem, "Where is the object?")
        self.assertEqual(choices, [("A", "Front"), ("B", "Rear"), ("C", "Left"), ("D", "Right")])

        _, semicolon_choices = parse_official_question(_question(1))
        self.assertEqual(semicolon_choices, choices)

    def test_conversion_preserves_two_to_ten_image_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            image_root = root / "images"
            image_root.mkdir()
            source = root / "source.jsonl"
            output = root / "processed" / "test.json"
            provenance = root / "processed" / "provenance.json"

            rows = []
            image_counts = [2, 3, 10]
            answers = ["A", "C", "D"]
            for row_index, image_count in enumerate(image_counts):
                names = [f"{row_index:04d}_{image_index}.jpg" for image_index in range(image_count)]
                for image_index, name in enumerate(names):
                    (image_root / name).write_bytes(
                        f"row={row_index};image={image_index}".encode("ascii")
                    )
                rows.append(
                    {
                        "id": f"mmsif_{row_index:04d}",
                        "type": "Synthetic audit",
                        "question": _question(row_index),
                        "answer": answers[row_index],
                        "gt_answer": answers[row_index],
                        # Deliberately use a foreign source prefix. The converter
                        # must rebind basenames without changing list order.
                        "images": [f"/source-machine/data/{name}" for name in names],
                    }
                )
            with source.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")

            expectations = DatasetExpectations(
                row_count=3,
                image_count=15,
                min_images_per_question=2,
                max_images_per_question=10,
                image_count_distribution={2: 1, 3: 1, 10: 1},
                answer_counts={"A": 1, "C": 1, "D": 1},
                question_type_counts={"Synthetic audit": 3},
            )
            result = prepare_mmsi_bench(
                source,
                image_root,
                output,
                provenance,
                expectations=expectations,
            )

            converted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([len(row["img_paths"]) for row in converted], image_counts)
            for row_index, row in enumerate(converted):
                expected_names = [
                    f"{row_index:04d}_{image_index}.jpg"
                    for image_index in range(image_counts[row_index])
                ]
                self.assertEqual(row["official_image_order"], expected_names)
                self.assertEqual(
                    [Path(path).name for path in row["img_paths"]], expected_names
                )
                self.assertEqual(row["correct_answer_letter"], answers[row_index])
                self.assertTrue(row["correct_answer"].startswith(answers[row_index] + ": "))
                self.assertEqual([choice[:1] for choice in row["answer_choices"]], list("ABCD"))

            on_disk_provenance = json.loads(provenance.read_text(encoding="utf-8"))
            self.assertEqual(on_disk_provenance["images"]["missing"], 0)
            self.assertEqual(on_disk_provenance["images"]["extra"], 0)
            self.assertEqual(on_disk_provenance["images"]["count"], 15)
            self.assertEqual(on_disk_provenance["images"]["per_question_min"], 2)
            self.assertEqual(on_disk_provenance["images"]["per_question_max"], 10)
            self.assertEqual(result["validation"]["status"], "passed")

    def test_missing_image_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            image_root = root / "images"
            image_root.mkdir()
            (image_root / "0000_0.jpg").write_bytes(b"present")
            source = root / "source.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "id": "mmsif_0000",
                        "type": "Synthetic audit",
                        "question": _question(0),
                        "answer": "A",
                        "images": ["/old/0000_0.jpg", "/old/0000_1.jpg"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            expectations = DatasetExpectations(1, 2, 2, 10)
            with self.assertRaisesRegex(DatasetValidationError, "missing 1 referenced images"):
                prepare_mmsi_bench(
                    source,
                    image_root,
                    root / "test.json",
                    root / "provenance.json",
                    expectations=expectations,
                )

    def test_reversed_source_image_list_is_not_silently_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            image_root = root / "images"
            image_root.mkdir()
            for name in ("0000_0.jpg", "0000_1.jpg"):
                (image_root / name).write_bytes(name.encode("ascii"))
            source = root / "source.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "id": "mmsif_0000",
                        "type": "Synthetic audit",
                        "question": _question(0),
                        "answer": "B",
                        "images": ["/old/0000_1.jpg", "/old/0000_0.jpg"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            expectations = DatasetExpectations(1, 2, 2, 10)
            with self.assertRaisesRegex(DatasetValidationError, "image order mismatch"):
                prepare_mmsi_bench(
                    source,
                    image_root,
                    root / "test.json",
                    root / "provenance.json",
                    expectations=expectations,
                )


if __name__ == "__main__":
    unittest.main()
