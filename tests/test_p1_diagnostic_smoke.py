from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from utils.p1_results import P1ResultsError
from utils.p1_smoke_results import (
    SVC_REVISION,
    SVC_WEIGHT_SHA256,
    _expected_arguments,
    validate_diagnostic_smoke,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


class DiagnosticSmokeResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input_dir = self.root / "input"
        self.input_dir.mkdir()
        self.input_file = self.input_dir / "test.json"
        self.provenance = self.input_dir / "test_provenance.json"
        self.experiment_manifest = self.root / "experiment.json"
        self.run_root = self.root / "run"
        self.result_dir = self.run_root / "results_spatial_beam_search"
        self.result_dir.mkdir(parents=True)
        self.row = {
            "eval_id": "mmsi/string-id-140",
            "database_idx": 140,
            "question_type": "spatial_relation",
            "question": "Where is A?",
            "answer_choices": ["A. left", "B. right"],
            "correct_answer": "A",
            "img_paths": ["/tmp/image-a.png", "/tmp/image-b.png"],
        }
        self.input_file.write_text(json.dumps([self.row]), encoding="utf-8")
        self.provenance.write_text('{"kind":"p1_smoke_subset"}\n', encoding="utf-8")
        self.experiment_manifest.write_text('{"experiment":"fixture"}\n', encoding="utf-8")
        self.source_sha = "a" * 64
        self.model = "Qwen/Qwen3.5-9B"
        self.revision = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
        self.hardware = "A100-1:A100-40GB:TP1+SVC1:diagnostic-smoke"
        self._write_manifest()
        self._write_result()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_manifest(self) -> None:
        values = {
            "run_id": "diag-fixture",
            "dataset": "mmsi",
            "method": "SVC",
            "model": self.model,
            "revision": self.revision,
            "thinking": "false",
            "dtype": "bfloat16",
            "max_model_len": "65536",
            "execution_scope": "diagnostic_smoke",
            "formal_eligible": "false",
            "formal_execution_cluster": "DAAI only",
            "diagnostic_host": "A100-1",
            "actual_hostname": "a100-one.example",
            "accelerator": "a10040",
            "tensor_parallel_size": "1",
            "svc_gpus": "1",
            "total_gpus": "2",
            "hardware": self.hardware,
            "input_file": str(self.input_file),
            "input_sha256": _sha(self.input_file),
            "dataset_provenance": str(self.provenance),
            "dataset_provenance_sha256": _sha(self.provenance),
            "experiment_manifest": str(self.experiment_manifest),
            "experiment_manifest_sha256": _sha(self.experiment_manifest),
            "source_sha256": self.source_sha,
            "split": "test",
            "num_questions": "1",
            "num_chunks": "1",
            "max_images": "10",
            "runtime_environment": "fixture-pinned-env",
        }
        (self.run_root / "launch_manifest.txt").write_text(
            "".join(f"{key}={value}\n" for key, value in values.items()),
            encoding="utf-8",
        )

    def _write_result(self) -> None:
        run_group = {
            "arguments": _expected_arguments(
                dataset="mmsi", model=self.model, input_dir=self.input_dir.resolve()
            ),
            "dataset_json_sha256": _sha(self.input_file),
            "dataset_provenance_sha256": _sha(self.provenance),
            "manifest_sha256": _sha(self.experiment_manifest),
            "source_sha256": self.source_sha,
            "submitted_source_sha256": self.source_sha,
            "model_revision": self.revision,
            "model_tree_sha256": None,
            "model_dtype": "bfloat16",
            "qwen_enable_thinking": False,
            "qwen_context_limit": "65536",
            "qwen_max_tokens": "1024",
            "vllm_version": "0.28.0",
            "svc_revision": SVC_REVISION,
            "svc_weight_sha256": SVC_WEIGHT_SHA256,
            "svc_strict_load": "1",
            "runtime_environment": "fixture-pinned-env",
            "hardware": self.hardware,
            "protocol": "paper-aligned SVC multi-image adaptation",
        }
        configuration = {
            "run_group": run_group,
            "output_dir": str(self.result_dir),
            "question_chunk_idx": 0,
        }
        result = {
            "experiment": {
                "fingerprint": _canonical_sha(configuration),
                "run_group_fingerprint": _canonical_sha(run_group),
                "configuration": configuration,
            },
            "evaluation": {
                "underlying_questions": 1,
                "evaluated_in_chunk": 1,
                "aggregation": "top1_accuracy_over_questions",
            },
            "current": "1 / 1",
            "accuracy": {
                "all": 1.0,
                "types": {self.row["question_type"]: 1.0},
            },
            "skip_indices": [],
            "progress": {
                self.row["question_type"]: {
                    "correct": [self.row["eval_id"]],
                    "wrong": [],
                }
            },
        }
        self.result_file = self.result_dir / "results.json"
        self.result_file.write_text(json.dumps(result), encoding="utf-8")
        self.complete_file = self.result_dir / "COMPLETE"
        self.complete_file.write_text(
            "".join(
                [
                    "run_id=diag-fixture\n",
                    "dataset=mmsi\n",
                    f"model={self.model}\n",
                    f"revision={self.revision}\n",
                    "execution_scope=diagnostic_smoke\n",
                    "diagnostic_host=A100-1\n",
                    "chunk_index=0\n",
                    f"results_sha256={_sha(self.result_file)}\n",
                ]
            ),
            encoding="utf-8",
        )

    def _validate(self) -> dict:
        return validate_diagnostic_smoke(
            run_root=self.run_root,
            input_file=self.input_file,
            dataset="mmsi",
            results_file=self.result_file,
            complete_file=self.complete_file,
        )

    def test_accepts_exact_string_id_and_complete_sha(self) -> None:
        summary = self._validate()
        self.assertEqual(summary["effective_id"], self.row["eval_id"])
        self.assertFalse(summary["formal_eligible"])
        self.assertEqual(summary["results_sha256"], _sha(self.result_file))

    def test_rejects_skip_wrong_id_and_fingerprint_tampering(self) -> None:
        result = json.loads(self.result_file.read_text(encoding="utf-8"))
        result["skip_indices"] = [self.row["eval_id"]]
        self.result_file.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(P1ResultsError, "zero skips"):
            self._validate()

        self._write_result()
        result = json.loads(self.result_file.read_text(encoding="utf-8"))
        result["progress"][self.row["question_type"]]["correct"] = [140]
        self.result_file.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(P1ResultsError, "unique selected ID"):
            self._validate()

        self._write_result()
        result = json.loads(self.result_file.read_text(encoding="utf-8"))
        result["experiment"]["fingerprint"] = "0" * 64
        self.result_file.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(P1ResultsError, "experiment fingerprint"):
            self._validate()

    def test_rejects_complete_checksum_or_formal_label(self) -> None:
        self.complete_file.write_text(
            self.complete_file.read_text(encoding="utf-8").replace(
                f"results_sha256={_sha(self.result_file)}", "results_sha256=" + "0" * 64
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(P1ResultsError, "checksum"):
            self._validate()

        self._write_result()
        manifest = self.run_root / "launch_manifest.txt"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "formal_eligible=false", "formal_eligible=true"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(P1ResultsError, "formal_eligible"):
            self._validate()


class DiagnosticLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.vllm = self.bin_dir / "vllm"
        self.vllm.write_text("#!/bin/sh\necho 'vllm 0.28.0'\n", encoding="utf-8")
        self.ninja = self.bin_dir / "ninja"
        self.ninja.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.nvidia_smi = self.bin_dir / "nvidia-smi"
        self._write_nvidia_smi(busy=False)
        for executable in (self.vllm, self.ninja, self.nvidia_smi):
            executable.chmod(0o755)

        self.model = self.root / "model"
        self.model.mkdir()
        (self.model / "config.json").write_text("{}\n", encoding="utf-8")
        (self.model / "model.safetensors.index.json").write_text(
            json.dumps({"weight_map": {"x": "model-00001.safetensors"}}),
            encoding="utf-8",
        )
        (self.model / "model-00001.safetensors").write_bytes(b"fixture")
        self.revision = self.root / "revision.txt"
        self.revision.write_text(
            "c202236235762e1c871ad0ccb60c8ee5ba337b9a\n", encoding="utf-8"
        )
        self.input_dir = self.root / "input"
        self.input_dir.mkdir()
        image = self.input_dir / "image.png"
        image.write_bytes(b"fixture")
        row = {
            "eval_id": "smoke-id",
            "database_idx": 140,
            "question_type": "spatial_relation",
            "question": "Where?",
            "answer_choices": ["A. left", "B. right"],
            "correct_answer": "A",
            "img_paths": [str(image)],
        }
        (self.input_dir / "test.json").write_text(json.dumps([row]), encoding="utf-8")
        (self.input_dir / "test_provenance.json").write_text(
            '{"kind":"p1_smoke_subset"}\n', encoding="utf-8"
        )
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_nvidia_smi(self, *, busy: bool) -> None:
        process_output = "echo 4321" if busy else ":"
        self.nvidia_smi.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            f"  *query-compute-apps*) {process_output} ;;\n"
            "  *) echo 'NVIDIA A100-SXM4-40GB, 40536, 0' ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        self.nvidia_smi.chmod(0o755)

    def _command(self, *, model: str = "qwen35-9b") -> list[str]:
        return [
            str(REPO_ROOT / "scripts/p1_run_local_diagnostic_smoke.sh"),
            "--host-label",
            "A100-2",
            "--model",
            model,
            "--dataset",
            "mmsi",
            "--gpus",
            "0,1",
            "--input-dir",
            str(self.input_dir),
            "--runtime-root",
            str(self.runtime),
            "--model-path",
            str(self.model),
            "--model-revision-file",
            str(self.revision),
            "--svc-python",
            sys.executable,
            "--vllm-bin",
            str(self.vllm),
            "--run-id",
            "dry-run-fixture",
            "--dry-run",
        ]

    def _run(self, *, model: str = "qwen35-9b") -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment.pop("CUDA_VISIBLE_DEVICES", None)
        environment["PATH"] = f"{self.bin_dir}:{environment['PATH']}"
        return subprocess.run(
            self._command(model=model),
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_idle_a10040_dry_run_preserves_tp_and_creates_nothing(self) -> None:
        completed = self._run()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("tensor_parallel_size=1", completed.stdout)
        self.assertIn("total_gpus=2", completed.stdout)
        self.assertIn("execution_scope=diagnostic_smoke", completed.stdout)
        self.assertIn("formal_eligible=false", completed.stdout)
        self.assertFalse((self.runtime / "dry-run-fixture").exists())

    def test_busy_gpu_is_rejected(self) -> None:
        self._write_nvidia_smi(busy=True)
        completed = self._run()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("active compute process", completed.stderr)
        self.assertFalse((self.runtime / "dry-run-fixture").exists())

    def test_a10040_72b_is_disabled(self) -> None:
        completed = self._run(model="qwen25vl-72b")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not enabled", completed.stderr)


class DiagnosticRegistryTests(unittest.TestCase):
    def _registry(self, model: str, accelerator: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "scripts/p1_model_registry.sh"),
                model,
                accelerator,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_a10040_profiles_and_formal_profiles(self) -> None:
        for model, tp, total in (
            ("qwen35-9b", 1, 2),
            ("qwen35-27b", 2, 3),
            ("qwen38-27b", 2, 3),
        ):
            completed = self._registry(model, "a10040")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(f"tensor_parallel_size={tp}", completed.stdout)
            self.assertIn(f"total_gpus={total}", completed.stdout)
            self.assertIn("diagnostic_only=true", completed.stdout)
        self.assertNotEqual(self._registry("qwen25vl-72b", "a10040").returncode, 0)

        formal = self._registry("qwen35-27b", "a100")
        self.assertEqual(formal.returncode, 0, formal.stderr)
        self.assertIn("tensor_parallel_size=1", formal.stdout)
        self.assertIn("total_gpus=2", formal.stdout)
        self.assertIn("diagnostic_only=false", formal.stdout)

        h20 = self._registry("qwen35-27b", "h20")
        self.assertEqual(h20.returncode, 0, h20.stderr)
        self.assertIn("tensor_parallel_size=1", h20.stdout)
        self.assertIn("total_gpus=2", h20.stdout)

    def test_manifest_separates_diagnostic_and_formal_hosts(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / "configs/p1_svc_multiimage.json").read_text(encoding="utf-8")
        )
        policy = manifest["hardware_policy"]
        self.assertEqual(policy["formal_execution_cluster"], "DAAI only")
        self.assertEqual(policy["diagnostic_smoke_hosts"], ["A100-1", "A100-2"])
        self.assertFalse(policy["diagnostic_smoke_results_are_formal"])
        self.assertEqual(
            manifest["models"]["Qwen/Qwen2.5-VL-72B-Instruct"]["diagnostic_a100_40gb"],
            "disabled",
        )


if __name__ == "__main__":
    unittest.main()
