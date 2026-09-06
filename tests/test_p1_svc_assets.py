from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
UTILITY_PATH = REPO_ROOT / "scripts" / "p1_svc_assets.py"
ARRAY_SCRIPT = REPO_ROOT / "scripts" / "p1_array.sbatch"
SUBMIT_SCRIPT = REPO_ROOT / "scripts" / "p1_submit.sh"
PREFETCH_SCRIPT = REPO_ROOT / "scripts" / "p1_prefetch_svc_assets.sh"
PREFETCH_SBATCH = REPO_ROOT / "scripts" / "p1_prefetch_svc_assets.sbatch"
PROLOG = REPO_ROOT / "scripts" / "p1_persistent_env_prolog.sh"

module_spec = importlib.util.spec_from_file_location("p1_svc_assets", UTILITY_PATH)
assert module_spec is not None and module_spec.loader is not None
p1_svc_assets = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = p1_svc_assets
module_spec.loader.exec_module(p1_svc_assets)


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class FakeHub:
    __version__ = "0.35.0-test"

    def __init__(self, specs, contents, *, gate_svc=False):
        self.specs = tuple(specs)
        self.contents = dict(contents)
        self.gate_svc = gate_svc
        self.snapshot_calls = []
        self.local_calls = []

    @staticmethod
    def _path(cache_dir, spec):
        safe_repo = spec.repo_id.replace("/", "--")
        return Path(cache_dir) / "fake" / safe_repo / spec.revision / spec.filename

    def snapshot_download(self, **kwargs):
        self.snapshot_calls.append(dict(kwargs))
        if (
            self.gate_svc
            and kwargs["repo_id"] == "stabilityai/stable-virtual-camera"
        ):
            raise PermissionError("gated test repository")
        allowed = set(kwargs["allow_patterns"])
        for spec in self.specs:
            if (
                spec.repo_id == kwargs["repo_id"]
                and spec.revision == kwargs["revision"]
                and spec.filename in allowed
            ):
                path = self._path(kwargs["cache_dir"], spec)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(self.contents[spec.name])
        return str(Path(kwargs["cache_dir"]) / "fake-snapshot")

    def hf_hub_download(self, **kwargs):
        self.local_calls.append(dict(kwargs))
        if kwargs.get("local_files_only") is not True:
            raise AssertionError("validation must always use local_files_only=True")
        for spec in self.specs:
            if (
                spec.repo_id == kwargs["repo_id"]
                and spec.revision == kwargs["revision"]
                and spec.filename == kwargs["filename"]
            ):
                path = self._path(kwargs["cache_dir"], spec)
                if not path.is_file():
                    raise FileNotFoundError(path)
                return str(path)
        raise FileNotFoundError(kwargs["filename"])


def _test_assets():
    contents = {
        "svc_config": b"",
        "svc_weights": b"svc-test-weights",
        "vae_config": b'{"_class_name":"AutoencoderKL"}\n',
        "vae_weights": b"vae-test-weights",
        "openclip_weights": b"openclip-test-weights",
    }
    specs = (
        p1_svc_assets.AssetSpec(
            "svc_config",
            "stabilityai/stable-virtual-camera",
            "e538e251c1009e9a41cf8b7fee5f21332a1960de",
            "config.yaml",
            p1_svc_assets.EMPTY_SHA256,
            True,
        ),
        p1_svc_assets.AssetSpec(
            "svc_weights",
            "stabilityai/stable-virtual-camera",
            "e538e251c1009e9a41cf8b7fee5f21332a1960de",
            "model.safetensors",
            _digest(contents["svc_weights"]),
        ),
        p1_svc_assets.AssetSpec(
            "vae_config", "public/vae", "b" * 40, "vae/config.json"
        ),
        p1_svc_assets.AssetSpec(
            "vae_weights",
            "public/vae",
            "b" * 40,
            "vae/diffusion_pytorch_model.safetensors",
            _digest(contents["vae_weights"]),
        ),
        p1_svc_assets.AssetSpec(
            "openclip_weights",
            "public/openclip",
            "c" * 40,
            "open_clip_pytorch_model.bin",
            _digest(contents["openclip_weights"]),
        ),
    )
    return specs, contents


class SvcAssetCacheTests(unittest.TestCase):
    def test_prefetch_downloads_public_repositories_before_gated_svc(self):
        specs, contents = _test_assets()
        fake = FakeHub(specs, contents, gate_svc=True)
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary).resolve() / "cache"
            with self.assertRaisesRegex(
                p1_svc_assets.AssetValidationError,
                "already cached public assets were preserved",
            ):
                p1_svc_assets.prefetch_cache(
                    cache_root, specs=specs, api=fake, token=None
                )

            repositories = [call["repo_id"] for call in fake.snapshot_calls]
            self.assertEqual(repositories[-1], "stabilityai/stable-virtual-camera")
            self.assertEqual(
                set(repositories[:-1]), {"public/openclip", "public/vae"}
            )
            self.assertTrue(
                FakeHub._path(
                    cache_root / "huggingface" / "hub", specs[3]
                ).is_file()
            )
            state = cache_root / "mindjourney" / "svc-assets-v1"
            self.assertFalse((state / "manifest.json").exists())
            self.assertFalse((state / "COMPLETE").exists())

    def test_success_is_offline_resolvable_and_tampering_is_rejected(self):
        specs, contents = _test_assets()
        fake = FakeHub(specs, contents)
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary).resolve() / "cache"
            payload = p1_svc_assets.prefetch_cache(
                cache_root, specs=specs, api=fake, token="not-recorded"
            )
            self.assertEqual(len(payload["assets"]), 5)
            self.assertEqual(payload["assets"][0]["size_bytes"], 0)
            self.assertTrue(payload["assets"][0]["allow_empty"])
            self.assertEqual(
                payload["assets"][0]["sha256"], p1_svc_assets.EMPTY_SHA256
            )
            state = cache_root / "mindjourney" / "svc-assets-v1"
            self.assertTrue((state / "manifest.json").is_file())
            self.assertTrue((state / "COMPLETE").is_file())
            self.assertNotIn(
                "not-recorded", (state / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(fake.local_calls)
            self.assertTrue(
                all(call["local_files_only"] is True for call in fake.local_calls)
            )

            validated = p1_svc_assets.validate_cache(
                cache_root, specs=specs, api=fake
            )
            self.assertEqual(validated, payload)

            weight_path = FakeHub._path(
                cache_root / "huggingface" / "hub", specs[4]
            )
            weight_path.write_bytes(b"tampered")
            with self.assertRaisesRegex(
                p1_svc_assets.AssetValidationError, "SHA256 mismatch"
            ):
                p1_svc_assets.validate_cache(cache_root, specs=specs, api=fake)

    def test_no_other_asset_may_be_empty(self):
        empty = p1_svc_assets.AssetSpec(
            "not_upstream_config",
            "public/weights",
            "d" * 40,
            "weights.bin",
            p1_svc_assets.EMPTY_SHA256,
        )
        fake = FakeHub((empty,), {empty.name: b""})
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary).resolve() / "cache"
            with self.assertRaisesRegex(
                p1_svc_assets.AssetValidationError, "cached file is empty"
            ):
                p1_svc_assets.prefetch_cache(
                    cache_root, specs=(empty,), api=fake
                )
            state = cache_root / "mindjourney" / "svc-assets-v1"
            self.assertFalse((state / "manifest.json").exists())
            self.assertFalse((state / "COMPLETE").exists())

    def test_vae_snapshot_is_minimal(self):
        specs, contents = _test_assets()
        fake = FakeHub(specs, contents)
        with tempfile.TemporaryDirectory() as temporary:
            p1_svc_assets.prefetch_cache(
                Path(temporary).resolve() / "cache", specs=specs, api=fake
            )
        vae_call = next(
            call for call in fake.snapshot_calls if call["repo_id"] == "public/vae"
        )
        self.assertEqual(
            vae_call["allow_patterns"],
            ["vae/config.json", "vae/diffusion_pytorch_model.safetensors"],
        )

    def test_validate_missing_cache_is_read_only(self):
        specs, contents = _test_assets()
        fake = FakeHub(specs, contents)
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary).resolve() / "missing"
            with self.assertRaises(p1_svc_assets.AssetValidationError):
                p1_svc_assets.validate_cache(cache_root, specs=specs, api=fake)
            self.assertFalse(cache_root.exists())


class SvcAssetIntegrationTests(unittest.TestCase):
    def test_pins_match_persistent_prolog(self):
        source = PROLOG.read_text(encoding="utf-8")
        for variable, value in p1_svc_assets.ENVIRONMENT_EXPECTATIONS.items():
            self.assertIn(f'export {variable}="{value}"', source)

    def test_shell_entry_points_have_valid_syntax(self):
        for script in (ARRAY_SCRIPT, SUBMIT_SCRIPT, PREFETCH_SCRIPT, PREFETCH_SBATCH):
            with self.subTest(script=script.name):
                subprocess.run(["bash", "-n", str(script)], check=True)

    def test_formal_array_revalidates_before_forcing_offline(self):
        source = ARRAY_SCRIPT.read_text(encoding="utf-8")
        validate_at = source.index('p1_svc_assets.py" validate')
        hub_offline_at = source.index("export HF_HUB_OFFLINE=1")
        transformers_offline_at = source.index("export TRANSFORMERS_OFFLINE=1")
        chunk_at = source.index("p1_run_chunk.sh")
        self.assertLess(validate_at, hub_offline_at)
        self.assertLess(validate_at, transformers_offline_at)
        self.assertLess(hub_offline_at, chunk_at)
        self.assertIn('P1_ALLOW_NETWORK:-0}" != "0"', source)

    def test_real_submit_validates_cache_but_dry_run_does_not(self):
        source = SUBMIT_SCRIPT.read_text(encoding="utf-8")
        dry_run_at = source.index("if (( do_submit == 0 ))")
        validate_at = source.index('p1_svc_assets.py" validate')
        sbatch_at = source.index('submission_response="$(')
        self.assertLess(dry_run_at, validate_at)
        self.assertLess(validate_at, sbatch_at)

    def test_prefetch_entry_point_is_networked_and_cpu_only(self):
        wrapper = PREFETCH_SCRIPT.read_text(encoding="utf-8")
        sbatch = PREFETCH_SBATCH.read_text(encoding="utf-8")
        self.assertIn("unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE", wrapper)
        self.assertIn('P1_ALLOW_NETWORK:-1}" != "1"', sbatch)
        self.assertNotIn("--gres", sbatch)
        self.assertNotIn("P1_JOB_PROLOG", sbatch)


if __name__ == "__main__":
    unittest.main()
