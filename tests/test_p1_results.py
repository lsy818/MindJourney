from __future__ import annotations

import hashlib
import io
import json
import random
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from utils.p1_results import (
    P1ResultsError,
    main,
    reconstruct_effective_chunks,
    validate_single_chunk,
    validate_and_merge,
)


class P1ResultsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input_file = self.root / "prepared" / "test.json"
        self.input_file.parent.mkdir()
        self.run_root = self.root / "run"
        self.num_questions = 1000
        self.num_chunks = 7
        self.max_images = 10
        self.model = "Qwen/Qwen3.5-9B"
        self.rows = [
            {
                "eval_id": f"mmsif_{index:04d}",
                "database_idx": index,
                "question_type": f"type_{index % 3}",
                "img_paths": [f"image_{index}_0.jpg", f"image_{index}_1.jpg"]
                + ([f"image_{index}_{extra}.jpg" for extra in range(2, 10)] if index == 0 else []),
            }
            for index in range(self.num_questions)
        ]
        self.input_file.write_text(json.dumps(self.rows), encoding="utf-8")
        self._write_valid_run()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_valid_run(self, *, argument_max_images: int | None = None) -> None:
        self.run_root.mkdir(parents=True, exist_ok=True)
        manifest = "\n".join(
            [
                "run_id=fixture-run",
                "dataset=mmsi",
                f"model={self.model}",
                f"num_questions={self.num_questions}",
                f"num_chunks={self.num_chunks}",
                f"max_images={self.max_images}",
                "",
            ]
        )
        (self.run_root / "launch_manifest.txt").write_text(manifest, encoding="utf-8")
        dataset_sha256 = hashlib.sha256(self.input_file.read_bytes()).hexdigest()
        run_group = {
            "arguments": {
                "num_questions": self.num_questions,
                "num_question_chunks": self.num_chunks,
                "max_images": argument_max_images or self.max_images,
                "vlm_model_name": self.model,
            },
            "dataset_json_sha256": dataset_sha256,
            "protocol": "paper-aligned SVC multi-image adaptation",
        }
        encoded = json.dumps(run_group, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        chunk_root = self.run_root / f"results_spatial_beam_search_qc{self.num_chunks}"
        chunks = reconstruct_effective_chunks(
            self.rows,
            num_questions=self.num_questions,
            num_chunks=self.num_chunks,
        )
        for chunk_index, expected in enumerate(chunks):
            progress: dict[str, dict[str, list[str]]] = {}
            for row in expected:
                buckets = progress.setdefault(
                    row["question_type"], {"correct": [], "wrong": []}
                )
                original_index = int(row["eval_id"].rsplit("_", 1)[1])
                outcome = "correct" if original_index % 2 == 0 else "wrong"
                buckets[outcome].append(row["eval_id"])
            chunk_dir = chunk_root / f"question_chunk_{chunk_index}"
            chunk_dir.mkdir(parents=True, exist_ok=True)
            result = {
                "experiment": {
                    "run_group_fingerprint": fingerprint,
                    "configuration": {
                        "run_group": run_group,
                        "question_chunk_idx": chunk_index,
                    },
                },
                "evaluation": {
                    "underlying_questions": self.num_questions,
                    "evaluated_in_chunk": len(expected),
                },
                "skip_indices": [],
                "progress": progress,
                "parsing_err_stats": {
                    "scores": chunk_index,
                    "answer": 0,
                    "scores_qid": [],
                    "answer_qid": [],
                },
            }
            results_path = chunk_dir / "results.json"
            results_path.write_text(json.dumps(result), encoding="utf-8")
            checksum = hashlib.sha256(results_path.read_bytes()).hexdigest()
            (chunk_dir / "COMPLETE").write_text(
                "\n".join(
                    [
                        "run_id=fixture-run",
                        "dataset=mmsi",
                        f"chunk_index={chunk_index}",
                        f"results_sha256={checksum}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

    def _result_path(self, chunk_index: int) -> Path:
        return (
            self.run_root
            / f"results_spatial_beam_search_qc{self.num_chunks}"
            / f"question_chunk_{chunk_index}"
            / "results.json"
        )

    def _rewrite_result_and_checksum(self, chunk_index: int, value: dict) -> None:
        path = self._result_path(chunk_index)
        path.write_text(json.dumps(value), encoding="utf-8")
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        complete = path.parent / "COMPLETE"
        lines = complete.read_text(encoding="utf-8").splitlines()
        complete.write_text(
            "\n".join(
                checksum.join(line.split(line.split("=", 1)[1]))
                if line.startswith("results_sha256=")
                else line
                for line in lines
            )
            + "\n",
            encoding="utf-8",
        )

    def test_reconstructs_pipeline_selection_and_last_chunk_remainder(self) -> None:
        rows = [{"database_idx": index} for index in range(10)]
        expected_sample = random.Random(10).sample(rows, k=10)
        chunks = reconstruct_effective_chunks(
            rows, num_questions=10, num_chunks=3, seed=10
        )
        self.assertEqual([len(chunk) for chunk in chunks], [3, 3, 4])
        self.assertEqual([row for chunk in chunks for row in chunk], expected_sample)

    def test_validates_single_chunk_without_complete_and_prints_sha(self) -> None:
        results_path = self._result_path(2)
        (results_path.parent / "COMPLETE").unlink()
        summary = validate_single_chunk(
            run_root=self.run_root,
            input_file=self.input_file,
            dataset="mmsi",
            chunk_index=2,
            results_file=results_path,
        )
        self.assertEqual(summary["expected"], 142)
        self.assertEqual(summary["correct"] + summary["wrong"], 142)
        self.assertEqual(
            summary["results_sha256"],
            hashlib.sha256(results_path.read_bytes()).hexdigest(),
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main(
                [
                    "--run-root",
                    str(self.run_root),
                    "--input-file",
                    str(self.input_file),
                    "--dataset",
                    "mmsi",
                    "--chunk-index",
                    "2",
                    "--results-file",
                    str(results_path),
                ]
            )
        self.assertEqual(status, 0)
        self.assertIn(f"results_sha256={summary['results_sha256']}", stdout.getvalue())

    def test_single_chunk_rejects_non_effective_id_and_skip(self) -> None:
        result = json.loads(self._result_path(0).read_text(encoding="utf-8"))
        result["skip_indices"] = ["mmsif_0000"]
        self._result_path(0).write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(P1ResultsError, "zero skips"):
            validate_single_chunk(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
                chunk_index=0,
            )

        result["skip_indices"] = []
        first_buckets = next(iter(result["progress"].values()))
        outcome = "correct" if first_buckets["correct"] else "wrong"
        first_buckets[outcome][0] = "not-in-effective-chunk"
        self._result_path(0).write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(P1ResultsError, "unexpected question ID"):
            validate_single_chunk(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
                chunk_index=0,
            )

    def test_merges_complete_string_eval_ids_and_refuses_default_overwrite(self) -> None:
        merged = validate_and_merge(
            run_root=self.run_root,
            input_file=self.input_file,
            dataset="mmsi",
        )
        self.assertEqual(merged["counts"], {"correct": 500, "wrong": 500, "total": 1000})
        self.assertEqual(merged["accuracy"]["all"], 0.5)
        self.assertEqual(merged["validation"]["status"], "passed")
        self.assertEqual(merged["validation"]["expected_total"], 1000)
        merged_ids = {
            qid
            for buckets in merged["progress"].values()
            for outcome in ("correct", "wrong")
            for qid in buckets[outcome]
        }
        self.assertEqual(merged_ids, {row["eval_id"] for row in self.rows})
        output_path = self.run_root / "results_merged.json"
        original_bytes = output_path.read_bytes()
        with self.assertRaisesRegex(P1ResultsError, "Refusing to overwrite"):
            validate_and_merge(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
            )
        self.assertEqual(output_path.read_bytes(), original_bytes)
        validate_and_merge(
            run_root=self.run_root,
            input_file=self.input_file,
            dataset="mmsi",
            overwrite=True,
        )

    def test_rejects_skips_duplicate_or_missing_effective_ids(self) -> None:
        result = json.loads(self._result_path(0).read_text(encoding="utf-8"))
        result["skip_indices"] = ["mmsif_0000"]
        self._rewrite_result_and_checksum(0, result)
        with self.assertRaisesRegex(P1ResultsError, "zero skips"):
            validate_and_merge(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
            )

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input_file = self.root / "prepared" / "test.json"
        self.input_file.parent.mkdir()
        self.run_root = self.root / "run"
        self.input_file.write_text(json.dumps(self.rows), encoding="utf-8")
        self._write_valid_run()
        result = json.loads(self._result_path(0).read_text(encoding="utf-8"))
        buckets = next(iter(result["progress"].values()))
        duplicate = buckets["correct"][0] if buckets["correct"] else buckets["wrong"][0]
        buckets["wrong"].append(duplicate)
        self._rewrite_result_and_checksum(0, result)
        with self.assertRaisesRegex(P1ResultsError, "repeats question ID"):
            validate_and_merge(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
            )

    def test_rejects_run_group_and_formal_parameter_mismatches(self) -> None:
        result = json.loads(self._result_path(1).read_text(encoding="utf-8"))
        result["experiment"]["run_group_fingerprint"] = "0" * 64
        self._rewrite_result_and_checksum(1, result)
        with self.assertRaisesRegex(P1ResultsError, "does not match its run_group"):
            validate_and_merge(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
            )

        self.temporary.cleanup()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input_file = self.root / "prepared" / "test.json"
        self.input_file.parent.mkdir()
        self.run_root = self.root / "run"
        self.input_file.write_text(json.dumps(self.rows), encoding="utf-8")
        self._write_valid_run(argument_max_images=9)
        with self.assertRaisesRegex(P1ResultsError, "max_images=9"):
            validate_and_merge(
                run_root=self.run_root,
                input_file=self.input_file,
                dataset="mmsi",
            )

    def test_rejects_wrong_official_total(self) -> None:
        short_input = self.root / "short-mindcube.json"
        short_rows = [
            {
                "eval_id": f"mindcube-{index}",
                "question_type": "rotation",
                "img_paths": ["a.jpg", "b.jpg"],
            }
            for index in range(1049)
        ]
        short_input.write_text(json.dumps(short_rows), encoding="utf-8")
        manifest = (self.run_root / "launch_manifest.txt").read_text(encoding="utf-8")
        manifest = manifest.replace("dataset=mmsi", "dataset=mindcube").replace(
            "num_questions=1000", "num_questions=1050"
        )
        (self.run_root / "launch_manifest.txt").write_text(manifest, encoding="utf-8")
        with self.assertRaisesRegex(P1ResultsError, "must contain 1050 rows"):
            validate_and_merge(
                run_root=self.run_root,
                input_file=short_input,
                dataset="mindcube",
            )


if __name__ == "__main__":
    unittest.main()
