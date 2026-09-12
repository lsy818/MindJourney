from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER = REPO_ROOT / "scripts" / "p1_build_persistent_envs.sbatch"
PROLOG = REPO_ROOT / "scripts" / "p1_persistent_env_prolog.sh"
SUBMIT = REPO_ROOT / "scripts" / "p1_submit.sh"
RUN_PIPELINE = REPO_ROOT / "scripts" / "p1_run_pipeline.sh"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PersistentEnvironmentBuilderTests(unittest.TestCase):
    @staticmethod
    def _slurm_environment(root: Path) -> dict[str, str]:
        bin_dir = root / "test-bin"
        bin_dir.mkdir()
        flock = bin_dir / "flock"
        flock.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        flock.chmod(0o755)
        environment = dict(os.environ)
        environment.update(
            {
                "SLURM_JOB_ID": "123",
                "SLURM_JOB_NODELIST": "node1",
                "PATH": f"{bin_dir}:{environment['PATH']}",
            }
        )
        return environment

    def test_scripts_have_valid_bash_syntax(self) -> None:
        for script in (BUILDER, PROLOG):
            with self.subTest(script=script.name):
                subprocess.run(["bash", "-n", str(script)], check=True)

    def test_builder_rejects_login_node_before_creating_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "persistent"
            environment = dict(os.environ)
            environment.pop("SLURM_JOB_ID", None)
            environment.pop("SLURM_JOB_NODELIST", None)
            completed = subprocess.run(
                ["bash", str(BUILDER), str(target)],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("Slurm compute job", completed.stderr)
            self.assertFalse(target.exists())

    def test_builder_refuses_nonempty_target_without_calling_installer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "persistent"
            target.mkdir()
            marker = target / "owned-by-user.txt"
            marker.write_text("preserve\n", encoding="utf-8")
            environment = self._slurm_environment(Path(temporary))
            completed = subprocess.run(
                ["bash", str(BUILDER), str(target)],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("Refusing to overwrite", completed.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve\n")

    def test_resume_rejects_unknown_partial_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "persistent"
            (target / ".BUILDING").mkdir(parents=True)
            marker = target / "not-builder-owned.txt"
            marker.write_text("preserve\n", encoding="utf-8")
            environment = self._slurm_environment(Path(temporary))
            completed = subprocess.run(
                ["bash", str(BUILDER), "--resume", str(target)],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("Refusing unknown entry", completed.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve\n")

    def test_resume_accepts_strict_legacy_layout_before_repo_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "persistent"
            for directory in (".BUILDING", "qwen", "svc", "uv-cache"):
                (target / directory).mkdir(parents=True, exist_ok=True)
            environment = self._slurm_environment(Path(temporary))
            environment.pop("P1_REPO_DIR", None)
            environment.pop("SLURM_SUBMIT_DIR", None)
            completed = subprocess.run(
                ["bash", str(BUILDER), "--resume", str(target)],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("P1_REPO_DIR", completed.stderr)
            self.assertNotIn("Refusing unknown entry", completed.stderr)

    def test_builder_is_bound_to_daai_account_uv_and_module(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('/home/comp/24482277/.local/bin/uv', source)
        self.assertIn('miniconda/py312_24.7.1-0', source)
        self.assertIn('SLURM_SUBMIT_DIR', source)
        self.assertNotIn('dirname -- "${BASH_SOURCE[0]}"', source)
        self.assertNotIn('/home/comp/tyjiang', source)
        self.assertIn('P1_BUILD_SCRATCH_PARENT', source)
        self.assertIn('mktemp -d', source)
        self.assertIn('export XDG_CACHE_HOME="$build_cache_root/xdg-cache"', source)
        self.assertIn('export CARGO_HOME="$XDG_CACHE_HOME/puccinialin/cargo"', source)
        self.assertIn('export CARGO_TARGET_DIR="$build_cache_root/cargo-target"', source)
        self.assertIn('persistent_puccinialin_root=', source)
        self.assertIn('export PATH="$persistent_cargo_bin:$PATH"', source)
        self.assertIn('export TMPDIR="$build_cache_root/tmp"', source)
        self.assertNotIn('build_cache_root="$target_root/.build-cache"', source)
        self.assertIn('ensure_venv "$qwen_env"', source)
        self.assertIn('format=mindjourney-p1-persistent-build-v2', source)


class PersistentEnvironmentPrologTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.env_root = self.root / "persistent"
        (self.env_root / "qwen" / "bin").mkdir(parents=True)
        (self.env_root / "svc" / "bin").mkdir(parents=True)
        self.fake_python = "#!/usr/bin/env bash\ncat >/dev/null || true\nexit 0\n"
        self._write_executable(self.env_root / "qwen" / "bin" / "python", self.fake_python)
        self._write_executable(self.env_root / "svc" / "bin" / "python", self.fake_python)
        self._write_executable(
            self.env_root / "qwen" / "bin" / "vllm",
            "#!/usr/bin/env bash\necho 'vLLM 0.28.0'\n",
        )
        self._write_executable(
            self.env_root / "qwen" / "bin" / "ninja",
            "#!/usr/bin/env bash\necho '1.13.0'\n",
        )
        self.versions = self.env_root / "VERSIONS.txt"
        self.repo_commit = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", "HEAD^{commit}"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        self.versions.write_text(
            "\n".join(
                [
                    "format=mindjourney-p1-persistent-v1",
                    "python_module=miniconda/py312_24.7.1-0",
                    "qwen.python=3.12.7",
                    "qwen.vllm=0.28.0",
                    "qwen.ninja=1.13.0",
                    "svc.python=3.12.7",
                    "svc.torch=2.9.0",
                    "svc.transformers=4.46.3",
                    "svc.diffusers=0.35.1",
                    "svc.huggingface-hub=0.35.0",
                    "svc.numpy=1.26.0",
                    "svc.numpy-quaternion=2024.0.3",
                    "svc.pipeline_import=ok",
                    f"repo.commit={self.repo_commit}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.qwen_freeze = self.env_root / "qwen.freeze.txt"
        self.svc_freeze = self.env_root / "svc.freeze.txt"
        self.qwen_freeze.write_text("vllm==0.28.0\n", encoding="utf-8")
        self.svc_freeze.write_text("torch==2.9.0\n", encoding="utf-8")
        self.complete = self.env_root / "COMPLETE"
        self._write_complete()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_executable(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def _write_complete(self, *, versions_sha: str | None = None) -> None:
        self.complete.write_text(
            "\n".join(
                [
                    "format=mindjourney-p1-persistent-v1",
                    f"versions_sha256={versions_sha or _sha(self.versions)}",
                    f"qwen_freeze_sha256={_sha(self.qwen_freeze)}",
                    f"svc_freeze_sha256={_sha(self.svc_freeze)}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def _source(self) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment.update(
            {
                "P1_PERSISTENT_ENV_ROOT": str(self.env_root),
                "P1_REPO_DIR": str(REPO_ROOT),
                "P1_CACHE_ROOT": str(self.root / "cache"),
            }
        )
        command = (
            f"source {PROLOG!s} || exit $?; "
            "printf '%s\\n' \"$P1_VLLM_BIN\" \"$P1_SVC_PYTHON\" \"$PYTHONPATH\" "
            "\"$SVC_REVISION\" \"$P1_ENV_COMPLETE_SHA256\" \"$P1_ENV_ID\""
        )
        return subprocess.run(
            ["bash", "-c", command],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_manifest_exports_account_owned_environment(self) -> None:
        completed = self._source()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = completed.stdout.splitlines()
        canonical_root = self.env_root.resolve()
        self.assertEqual(output[0], str(canonical_root / "qwen" / "bin" / "vllm"))
        self.assertEqual(output[1], str(canonical_root / "svc" / "bin" / "python"))
        self.assertTrue(output[2].startswith(f"{REPO_ROOT}:{REPO_ROOT}/pipelines:"))
        self.assertEqual(output[3], "e538e251c1009e9a41cf8b7fee5f21332a1960de")
        complete_sha = _sha(self.complete)
        self.assertEqual(output[4], complete_sha)
        self.assertEqual(output[5], f"mindjourney-p1-persistent-v1-{complete_sha}")

    def test_checksum_tampering_is_rejected(self) -> None:
        self._write_complete(versions_sha="0" * 64)
        completed = self._source()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("checksum mismatch", completed.stderr)

    def test_duplicate_pipeline_validation_record_is_rejected(self) -> None:
        with self.versions.open("a", encoding="utf-8") as handle:
            handle.write("svc.pipeline_import=ok\n")
        self._write_complete()
        completed = self._source()
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Expected exactly one svc.pipeline_import entry", completed.stderr)

    def test_prolog_uses_recorded_pipeline_validation_without_reimporting(self) -> None:
        prolog_source = PROLOG.read_text(encoding="utf-8")
        worker_source = RUN_PIPELINE.read_text(encoding="utf-8")
        self.assertIn(
            'p1_manifest_value "$p1_versions_file" svc.pipeline_import',
            prolog_source,
        )
        self.assertNotIn(
            "import pipelines.pipeline_svc_scaling_spatial_beam_search",
            prolog_source,
        )
        self.assertIn(
            'exec "$svc_python" pipelines/pipeline_svc_scaling_spatial_beam_search.py',
            worker_source,
        )
        self.assertNotIn('$p1_qwen_vllm --version', prolog_source)
        self.assertNotIn('"$p1_qwen_python" -', prolog_source)
        self.assertNotIn('"$p1_svc_python" -', prolog_source)

    def test_prolog_has_no_other_account_dependency(self) -> None:
        self.assertNotIn("tyjiang", PROLOG.read_text(encoding="utf-8"))

    def test_submit_forwards_explicit_persistent_root_into_slurm(self) -> None:
        completed = subprocess.run(
            [
                "bash",
                str(SUBMIT),
                "--mode",
                "smoke",
                "--model",
                "qwen35-9b",
                "--dataset",
                "mindcube",
                "--input-dir",
                str(self.root / "not-needed-for-dry-run"),
                "--runtime-root",
                str(self.root / "runtime"),
                "--num-questions",
                "1",
                "--max-images",
                "10",
                "--persistent-env-root",
                str(self.env_root),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f"P1_PERSISTENT_ENV_ROOT={self.env_root}", completed.stdout)
        self.assertIn(
            f"P1_EXPECTED_ENV_COMPLETE_SHA256={_sha(self.complete)}",
            completed.stdout,
        )
        self.assertIn(
            f"persistent_environment_complete_sha256={_sha(self.complete)}",
            completed.stdout,
        )
        self.assertIn(f"P1_JOB_PROLOG={PROLOG}", completed.stdout)
        self.assertIn("P1_EXPECTED_INPUT_SHA256=unavailable", completed.stdout)
        self.assertIn("P1_EXPECTED_PROVENANCE_SHA256=unavailable", completed.stdout)
        self.assertIn("P1_EXPECTED_MANIFEST_SHA256=", completed.stdout)
        self.assertIn("P1_EXPECTED_SOURCE_SHA256=", completed.stdout)
        self.assertIn("Dry run only", completed.stdout)

    def test_a100_plan_excludes_legacy_driver_nodes(self) -> None:
        registry = REPO_ROOT / "scripts" / "p1_model_registry.sh"
        completed = subprocess.run(
            ["bash", str(registry), "qwen35-27b", "a100"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "exclude=hkbugpudgx01,hkbugpusrv07,hkbugpusrv08",
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
