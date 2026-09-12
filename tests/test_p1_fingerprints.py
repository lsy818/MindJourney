from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from utils.p1_fingerprints import (
    SOURCE_FILES,
    FingerprintError,
    sha256_file,
    source_sha256,
    verify_runtime_fingerprints,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SUBMIT = REPO_ROOT / "scripts" / "p1_submit.sh"


class SourceFingerprintTests(unittest.TestCase):
    def test_reviewed_file_set_is_sorted_unique_and_complete(self) -> None:
        self.assertEqual(SOURCE_FILES, tuple(sorted(set(SOURCE_FILES))))
        for required in (
            "configs/p1_svc_multiimage.json",
            "scripts/p1_array.sbatch",
            "scripts/p1_run_chunk.sh",
            "scripts/p1_run_pipeline.sh",
            "scripts/p1_serve_vllm.sh",
            "scripts/p1_submit.sh",
            "scripts/p1_svc_assets.py",
            "utils/p1_fingerprints.py",
        ):
            self.assertIn(required, SOURCE_FILES)

        discovered_python = {
            path.relative_to(REPO_ROOT).as_posix()
            for source_root in ("pipelines", "utils", "stable_virtual_camera")
            for path in (REPO_ROOT / source_root).rglob("*.py")
        }
        self.assertTrue(discovered_python.issubset(SOURCE_FILES))
        self.assertTrue(all((REPO_ROOT / path).is_file() for path in SOURCE_FILES))

    def test_hash_is_deterministic_and_changes_with_a_listed_file(self) -> None:
        first = source_sha256(REPO_ROOT)
        self.assertEqual(first, source_sha256(REPO_ROOT))
        self.assertRegex(first, r"^[0-9a-f]{64}$")

        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary)
            for relative in SOURCE_FILES:
                destination = copied_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO_ROOT / relative, destination)
            before = source_sha256(copied_root)
            changed = copied_root / "scripts/p1_run_chunk.sh"
            changed.write_bytes(changed.read_bytes() + b"\n# fingerprint fixture\n")
            self.assertNotEqual(before, source_sha256(copied_root))


class RuntimeFingerprintTests(unittest.TestCase):
    def test_runtime_verifier_accepts_exact_files_and_rejects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_file = root / "test.json"
            provenance = root / "test_provenance.json"
            experiment = root / "experiment.json"
            tree = root / "revision-tree.json"
            for path, payload in (
                (input_file, b"[]\n"),
                (provenance, b"{}\n"),
                (experiment, b'{"experiment":"fixture"}\n'),
                (tree, b'{"revision":"fixture"}\n'),
            ):
                path.write_bytes(payload)

            expected_source = source_sha256(REPO_ROOT)
            files = [
                ("input", input_file, sha256_file(input_file)),
                ("provenance", provenance, sha256_file(provenance)),
                ("experiment_manifest", experiment, sha256_file(experiment)),
                ("model_tree_manifest", tree, sha256_file(tree)),
            ]
            verified = verify_runtime_fingerprints(
                repo_root=REPO_ROOT,
                expected_source_sha256=expected_source,
                files=files,
            )
            self.assertEqual(verified["model_tree_manifest_sha256"], sha256_file(tree))

            input_file.write_bytes(b"[{}]\n")
            with self.assertRaisesRegex(FingerprintError, "input SHA256 mismatch"):
                verify_runtime_fingerprints(
                    repo_root=REPO_ROOT,
                    expected_source_sha256=expected_source,
                    files=files,
                )

    def test_worker_verifies_before_starting_vllm_and_exports_to_svc(self) -> None:
        worker_source = (REPO_ROOT / "scripts/p1_run_chunk.sh").read_text(
            encoding="utf-8"
        )
        self.assertLess(
            worker_source.index("utils/p1_fingerprints.py"),
            worker_source.index('"$script_dir/p1_serve_vllm.sh"'),
        )
        for name in (
            "P1_EXPECTED_INPUT_SHA256",
            "P1_EXPECTED_PROVENANCE_SHA256",
            "P1_EXPECTED_MANIFEST_SHA256",
            "P1_EXPECTED_SOURCE_SHA256",
        ):
            self.assertIn(name, worker_source)

        pipeline_source = (REPO_ROOT / "scripts/p1_run_pipeline.sh").read_text(
            encoding="utf-8"
        )
        for name in (
            "MINDJOURNEY_EXPECTED_INPUT_SHA256",
            "MINDJOURNEY_EXPECTED_PROVENANCE_SHA256",
            "MINDJOURNEY_EXPECTED_MANIFEST_SHA256",
            "MINDJOURNEY_EXPECTED_SOURCE_SHA256",
            "MINDJOURNEY_MODEL_TREE_SHA256",
        ):
            self.assertIn(name, pipeline_source)


class SubmitResumeFingerprintTests(unittest.TestCase):
    def test_resume_rejects_changed_input_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake_svc_python = bin_dir / "svc-python"
            fake_svc_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_sbatch = bin_dir / "sbatch"
            fake_sbatch.write_text("#!/bin/sh\necho 12345\n", encoding="utf-8")
            for executable in (fake_svc_python, fake_sbatch):
                executable.chmod(0o755)

            input_dir = root / "input"
            input_dir.mkdir()
            image = input_dir / "image.png"
            image.write_bytes(b"fixture")
            input_file = input_dir / "test.json"
            row = {
                "eval_id": "fixture-1",
                "database_idx": 1,
                "question_type": "spatial_relation",
                "question": "Where?",
                "answer_choices": ["A. left", "B. right"],
                "correct_answer": "A",
                "img_paths": [str(image)],
            }
            input_file.write_text(json.dumps([row]), encoding="utf-8")
            (input_dir / "test_provenance.json").write_text(
                '{"kind":"fixture"}\n', encoding="utf-8"
            )

            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}\n", encoding="utf-8")
            (model / "revision.txt").write_text(
                "c202236235762e1c871ad0ccb60c8ee5ba337b9a\n", encoding="utf-8"
            )
            tree_manifest = (
                model
                / ".cache/huggingface/trees"
                / "c202236235762e1c871ad0ccb60c8ee5ba337b9a.json"
            )
            tree_manifest.parent.mkdir(parents=True)
            tree_manifest.write_text('{"revision":"fixture"}\n', encoding="utf-8")
            runtime = root / "runtime"
            runtime.mkdir()
            command = [
                "bash",
                str(SUBMIT),
                "--mode",
                "smoke",
                "--model",
                "qwen35-9b",
                "--dataset",
                "mindcube",
                "--input-dir",
                str(input_dir),
                "--runtime-root",
                str(runtime),
                "--model-path",
                str(model),
                "--svc-python",
                str(fake_svc_python),
                "--run-id",
                "resume-input-fixture",
                "--submit",
            ]
            environment = dict(os.environ)
            environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
            first = subprocess.run(
                command,
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            launch_manifest = runtime / "resume-input-fixture" / "launch_manifest.txt"
            original_hash = hashlib.sha256(input_file.read_bytes()).hexdigest()
            self.assertIn(
                f"input_sha256={original_hash}",
                launch_manifest.read_text(encoding="utf-8"),
            )
            tree_hash = hashlib.sha256(tree_manifest.read_bytes()).hexdigest()
            self.assertIn(
                f"model_tree_manifest={tree_manifest}",
                launch_manifest.read_text(encoding="utf-8"),
            )
            self.assertIn(
                f"model_tree_sha256={tree_hash}",
                launch_manifest.read_text(encoding="utf-8"),
            )
            self.assertIn(
                f"P1_MODEL_TREE_SHA256={tree_hash}",
                first.stdout,
            )

            row["question"] = "Where exactly?"
            input_file.write_text(json.dumps([row]), encoding="utf-8")
            resumed = subprocess.run(
                [*command[:-1], "--resume", "--submit"],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(resumed.returncode, 0)
            self.assertIn("Resume manifest mismatch: expected line input_sha256=", resumed.stderr)


class SvcSeedManifestTests(unittest.TestCase):
    def test_manifest_records_verified_internal_seed(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / "configs/p1_svc_multiimage.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["svc_weights"]["internal_seed"], 23)
        source = (REPO_ROOT / "stable_virtual_camera/demo.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('options["seed"] = 23', source)
        self.assertIn("seed=seed", source)


if __name__ == "__main__":
    unittest.main()
