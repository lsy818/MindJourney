import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("stage_local", Path(__file__).resolve().parents[1] / "scripts/p1_stage_local_env.py")
stage_local = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage_local)


class LocalDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "source"
        for env in ("qwen", "svc"):
            root = self.source / env
            (root / "bin").mkdir(parents=True)
            (root / "bin/python").symlink_to(sys.executable)
            (root / "pyvenv.cfg").write_text(f"home = {Path(sys.executable).parent}\ninclude-system-site-packages = false\n")
            script = root / "bin/runner"
            script.write_text(f"#!{root}/bin/python\nimport sys\nprint(sys.prefix)\n")
            script.chmod(0o755)
            (root / "binary.so").write_bytes(b"\x7fELF\x00unchanged payload")
        for name in stage_local.METADATA:
            (self.source / name).write_text(name + "\n")
        self.expected = stage_local.digest(self.source / "COMPLETE")

    def tearDown(self):
        self.temp.cleanup()

    def stage(self, **kwargs):
        return stage_local.stage(self.source, self.base / "cache", self.expected, min_free_gib=0, **kwargs)

    def test_launchers_use_local_python_and_binaries_are_unchanged(self):
        root = self.stage()
        for env in ("qwen", "svc"):
            output = subprocess.check_output([str(root / env / "bin/runner")], text=True).strip()
            self.assertEqual(output, str(root / env))
            self.assertEqual((root / env / "binary.so").read_bytes(), (self.source / env / "binary.so").read_bytes())
            self.assertTrue((self.source / env / "bin/runner").read_text().startswith(f"#!{self.source}/{env}/bin/python"))
        self.assertEqual(self.stage(), root)

    def test_partial_seed_is_completed_before_ready_marker(self):
        seed = self.base / "seed"
        (seed / "qwen/bin").mkdir(parents=True)
        (seed / "qwen/bin/runner").write_text("truncated")
        root = self.stage(seed=seed)
        self.assertTrue((root / "LOCAL_READY.json").is_file())
        self.assertIn(str(root), (root / "qwen/bin/runner").read_text())

    def test_wrong_identity_does_not_create_local_cache(self):
        self.expected = "0" * 64
        with self.assertRaises(RuntimeError):
            self.stage()
        self.assertFalse((self.base / "cache").exists())


if __name__ == "__main__":
    unittest.main()
