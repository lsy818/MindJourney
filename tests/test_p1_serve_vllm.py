from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class P1ServeVllmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bin_dir = self.root / "qwen" / "bin"
        self.bin_dir.mkdir(parents=True)
        self.path_capture = self.root / "path.txt"
        self.args_capture = self.root / "args.txt"
        self.script = Path(__file__).resolve().parents[1] / "scripts" / "p1_serve_vllm.sh"
        self.vllm = self.bin_dir / "vllm"
        self.vllm.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--version" ]]; then
  echo "vLLM 0.28.0"
  exit 0
fi
printf '%s\n' "$PATH" >"$P1_TEST_PATH_CAPTURE"
printf '%s\n' "$@" >"$P1_TEST_ARGS_CAPTURE"
""",
            encoding="utf-8",
        )
        self.vllm.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                "P1_ACCELERATOR": "h20",
                "P1_ALLOW_NETWORK": "1",
                "P1_CACHE_ROOT": str(self.root / "cache"),
                "P1_VLLM_BIN": str(self.vllm),
                "P1_TEST_PATH_CAPTURE": str(self.path_capture),
                "P1_TEST_ARGS_CAPTURE": str(self.args_capture),
            }
        )
        return subprocess.run(
            ["bash", str(self.script), "qwen35-9b"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_scopes_pinned_ninja_path_to_vllm_server(self) -> None:
        ninja = self.bin_dir / "ninja"
        ninja.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        ninja.chmod(0o755)

        completed = self._run()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            self.path_capture.read_text(encoding="utf-8").split(":", 1)[0],
            str(self.bin_dir),
        )
        arguments = self.args_capture.read_text(encoding="utf-8").splitlines()
        self.assertIn("bfloat16", arguments)
        self.assertIn('{"enable_thinking":false}', arguments)
        self.assertIn('{"image":64}', arguments)

    def test_fails_before_loading_model_when_pinned_ninja_is_missing(self) -> None:
        completed = self._run()

        self.assertEqual(completed.returncode, 1)
        self.assertIn("Pinned vLLM environment is missing ninja", completed.stderr)
        self.assertFalse(self.path_capture.exists())
class P1ResourcePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = (
            Path(__file__).resolve().parents[1] / "scripts" / "p1_model_registry.sh"
        )

    def _spec(self, model: str, accelerator: str) -> dict[str, str]:
        completed = subprocess.run(
            ["bash", str(self.registry), model, accelerator],
            text=True,
            capture_output=True,
            check=True,
        )
        return dict(line.split("=", 1) for line in completed.stdout.splitlines())

    def test_standard_models_request_eight_cpus(self) -> None:
        for accelerator in ("h20", "a100"):
            with self.subTest(accelerator=accelerator):
                spec = self._spec("qwen35-9b", accelerator)
                self.assertEqual(spec["cpus_per_task"], "8")
                self.assertEqual(spec["total_gpus"], "2")

    def test_72b_model_keeps_sixteen_cpus(self) -> None:
        for accelerator, expected_gpus in (("h20", "3"), ("a100", "5")):
            with self.subTest(accelerator=accelerator):
                spec = self._spec("qwen25vl-72b", accelerator)
                self.assertEqual(spec["cpus_per_task"], "16")
                self.assertEqual(spec["total_gpus"], expected_gpus)


if __name__ == "__main__":
    unittest.main()
