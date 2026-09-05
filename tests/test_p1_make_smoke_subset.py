import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "p1_make_smoke_subset.py"
SPEC = importlib.util.spec_from_file_location("p1_make_smoke_subset", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MakeSmokeSubsetTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.input_dir = self.root / "prepared"
        self.input_dir.mkdir()
        self.records = [
            {
                "database_idx": 0,
                "source_id": "mmsif_0000",
                "question": "first",
                "img_paths": ["/images/first-1.png", "/images/first-2.png"],
            },
            {
                "database_idx": 140,
                "eval_id": "official-string-id",
                "source_id": "mmsif_0140",
                "question": "selected",
                "img_paths": [f"/images/{number}.png" for number in range(10)],
            },
        ]
        self.input_file = self.input_dir / "test.json"
        self.input_file.write_text(
            json.dumps(self.records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.parent_provenance = self.input_dir / "provenance.json"
        self.parent_provenance.write_text(
            json.dumps({"dataset": "fixture"}) + "\n", encoding="utf-8"
        )
        self.output_dir = self.root / "smoke"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def create(self, **overrides):
        arguments = {
            "input_file": self.input_file,
            "output_dir": self.output_dir,
            "record_index": 1,
        }
        arguments.update(overrides)
        return MODULE.make_smoke_subset(**arguments)

    def test_writes_exactly_one_order_preserving_record_and_provenance(self):
        result = self.create()

        output_file = self.output_dir / "test.json"
        output_provenance = self.output_dir / "test_provenance.json"
        self.assertEqual(json.loads(output_file.read_text()), [self.records[1]])
        output_text = output_file.read_text(encoding="utf-8")
        self.assertLess(output_text.index('"database_idx"'), output_text.index('"eval_id"'))
        self.assertLess(output_text.index('/images/0.png'), output_text.index('/images/9.png'))

        provenance = json.loads(output_provenance.read_text(encoding="utf-8"))
        self.assertEqual(provenance, result)
        self.assertEqual(provenance["parent"]["test_json_path"], str(self.input_file.resolve()))
        self.assertEqual(
            provenance["parent"]["test_json_sha256"], sha256_file(self.input_file)
        )
        self.assertEqual(
            provenance["parent"]["provenance_path"],
            str(self.parent_provenance.resolve()),
        )
        self.assertEqual(
            provenance["parent"]["provenance_sha256"],
            sha256_file(self.parent_provenance),
        )
        self.assertEqual(provenance["selection"]["record_index"], 1)
        self.assertEqual(provenance["selection"]["effective_id"], "official-string-id")
        self.assertEqual(provenance["selection"]["source_id"], "mmsif_0140")
        self.assertEqual(provenance["selection"]["image_count"], 10)
        self.assertEqual(provenance["subset"]["records"], 1)
        self.assertEqual(provenance["subset"]["test_json_sha256"], sha256_file(output_file))

    def test_refuses_to_overwrite_by_default_without_changing_outputs(self):
        self.create()
        output_file = self.output_dir / "test.json"
        output_provenance = self.output_dir / "test_provenance.json"
        before = (output_file.read_bytes(), output_provenance.read_bytes())

        with self.assertRaisesRegex(MODULE.SmokeSubsetError, "refusing to overwrite"):
            self.create(record_index=0)

        self.assertEqual(before, (output_file.read_bytes(), output_provenance.read_bytes()))

    def test_force_replaces_both_outputs(self):
        self.create()
        result = self.create(record_index=0, force=True)

        self.assertEqual(
            json.loads((self.output_dir / "test.json").read_text()), [self.records[0]]
        )
        self.assertEqual(result["selection"]["effective_id"], 0)
        self.assertEqual(result["selection"]["source_id"], "mmsif_0000")
        self.assertEqual(result["selection"]["image_count"], 2)
        self.assertEqual(
            json.loads((self.output_dir / "test_provenance.json").read_text()), result
        )

    def test_rejects_invalid_index_before_creating_outputs(self):
        for invalid_index in (-1, 2):
            with self.subTest(record_index=invalid_index):
                with self.assertRaises(MODULE.SmokeSubsetError):
                    self.create(record_index=invalid_index)
                self.assertFalse((self.output_dir / "test.json").exists())
                self.assertFalse((self.output_dir / "test_provenance.json").exists())

    def test_requires_unambiguous_valid_parent_provenance(self):
        (self.input_dir / "test_provenance.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.SmokeSubsetError, "exactly one"):
            self.create()
        self.assertFalse((self.output_dir / "test.json").exists())

        result = self.create(parent_provenance=self.parent_provenance)
        self.assertEqual(
            result["parent"]["provenance_path"], str(self.parent_provenance.resolve())
        )

    def test_never_overwrites_parent_even_with_force(self):
        original = self.input_file.read_bytes()
        with self.assertRaisesRegex(MODULE.SmokeSubsetError, "parent input"):
            self.create(output_dir=self.input_dir, force=True)
        self.assertEqual(self.input_file.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
