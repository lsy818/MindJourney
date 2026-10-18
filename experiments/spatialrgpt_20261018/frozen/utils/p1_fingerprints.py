#!/usr/bin/env python3
"""Deterministic fingerprints for the Priority-1 execution contract.

The source fingerprint intentionally uses an explicit, reviewed file list.
This makes additions and removals visible in code review and prevents a worker
from silently hashing a different set because of untracked files or caches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable


SOURCE_FINGERPRINT_FORMAT = "mindjourney-p1-explicit-files-v1"
SOURCE_FILES = (
    "configs/p1_svc_multiimage.json",
    "pipelines/pipeline_baseline.py",
    "pipelines/pipeline_svc_scaling_spatial_beam_search.py",
    "pipelines/pipeline_wan_scaling_beam_search_double_rank.py",
    "scripts/p1_array.sbatch",
    "scripts/p1_env_prolog.sh",
    "scripts/p1_experiment_contract.py",
    "scripts/p1_model_registry.sh",
    "scripts/p1_persistent_env_prolog.sh",
    "scripts/p1_run_chunk.sh",
    "scripts/p1_run_local_diagnostic_smoke.sh",
    "scripts/p1_run_pipeline.sh",
    "scripts/p1_serve_vllm.sh",
    "scripts/p1_stage_local_env.py",
    "scripts/p1_submit.sh",
    "scripts/p1_svc_assets.py",
    "scripts/p1_validate_input.py",
    "stable_virtual_camera/demo.py",
    "stable_virtual_camera/demo_teaser.py",
    "stable_virtual_camera/seva/__init__.py",
    "stable_virtual_camera/seva/data_io.py",
    "stable_virtual_camera/seva/eval.py",
    "stable_virtual_camera/seva/geometry.py",
    "stable_virtual_camera/seva/gui.py",
    "stable_virtual_camera/seva/model.py",
    "stable_virtual_camera/seva/modules/__init__.py",
    "stable_virtual_camera/seva/modules/autoencoder.py",
    "stable_virtual_camera/seva/modules/conditioner.py",
    "stable_virtual_camera/seva/modules/layers.py",
    "stable_virtual_camera/seva/modules/preprocessor.py",
    "stable_virtual_camera/seva/modules/transformer.py",
    "stable_virtual_camera/seva/sampling.py",
    "stable_virtual_camera/seva/utils.py",
    "utils/InternVL3.py",
    "utils/answer_parsing.py",
    "utils/api.py",
    "utils/args.py",
    "utils/data_process.py",
    "utils/p1_fingerprints.py",
    "utils/p1_results.py",
    "utils/p1_smoke_results.py",
    "utils/prepare_mindcube.py",
    "utils/prepare_mmsi_bench.py",
    "utils/prompt_formatting.py",
    "utils/vlm_wrapper.py",
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class FingerprintError(RuntimeError):
    """Raised when a pinned artifact differs from its submitted digest."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_sha256(repo_root: str | Path) -> str:
    """Hash the exact reviewed source set, including relative file names."""

    root = Path(repo_root).resolve()
    digest = hashlib.sha256()
    digest.update(SOURCE_FINGERPRINT_FORMAT.encode("utf-8") + b"\0")
    for relative_path in SOURCE_FILES:
        path = root / relative_path
        if not path.is_file():
            raise FingerprintError(
                f"source fingerprint file is missing: {relative_path}"
            )
        digest.update(relative_path.encode("utf-8") + b"\0")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        digest.update(b"\0")
    return digest.hexdigest()


def _require_sha256(value: str, label: str) -> None:
    if _SHA256_RE.fullmatch(value) is None:
        raise FingerprintError(f"{label} must be a lowercase SHA256")


def verify_file(path: str | Path, expected_sha256: str, label: str) -> str:
    _require_sha256(expected_sha256, f"expected {label} SHA256")
    resolved = Path(path)
    if not resolved.is_file():
        raise FingerprintError(f"{label} is not a readable file: {resolved}")
    actual = sha256_file(resolved)
    if actual != expected_sha256:
        raise FingerprintError(
            f"{label} SHA256 mismatch: expected {expected_sha256}, got {actual}"
        )
    return actual


def verify_runtime_fingerprints(
    *,
    repo_root: str | Path,
    expected_source_sha256: str,
    files: Iterable[tuple[str, str | Path, str]],
) -> dict[str, str]:
    _require_sha256(expected_source_sha256, "expected source SHA256")
    actual_source = source_sha256(repo_root)
    if actual_source != expected_source_sha256:
        raise FingerprintError(
            "source SHA256 mismatch: "
            f"expected {expected_source_sha256}, got {actual_source}"
        )
    verified = {"source_sha256": actual_source}
    for label, path, expected_sha256 in files:
        verified[f"{label}_sha256"] = verify_file(path, expected_sha256, label)
    return verified


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    source_parser = subparsers.add_parser("source")
    source_parser.add_argument("--repo-root", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify-runtime")
    verify_parser.add_argument("--repo-root", type=Path, required=True)
    verify_parser.add_argument("--expected-source-sha256", required=True)
    verify_parser.add_argument("--input-file", type=Path, required=True)
    verify_parser.add_argument("--expected-input-sha256", required=True)
    verify_parser.add_argument("--provenance-file", type=Path, required=True)
    verify_parser.add_argument("--expected-provenance-sha256", required=True)
    verify_parser.add_argument("--experiment-manifest", type=Path, required=True)
    verify_parser.add_argument("--expected-manifest-sha256", required=True)
    verify_parser.add_argument("--model-tree-manifest", type=Path)
    verify_parser.add_argument("--expected-model-tree-sha256")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "source":
        print(source_sha256(args.repo_root))
        return

    files: list[tuple[str, Path, str]] = [
        ("input", args.input_file, args.expected_input_sha256),
        ("provenance", args.provenance_file, args.expected_provenance_sha256),
        ("experiment_manifest", args.experiment_manifest, args.expected_manifest_sha256),
    ]
    if (args.model_tree_manifest is None) != (
        args.expected_model_tree_sha256 is None
    ):
        raise FingerprintError(
            "model-tree manifest and expected SHA256 must be supplied together"
        )
    if args.model_tree_manifest is not None:
        files.append(
            (
                "model_tree_manifest",
                args.model_tree_manifest,
                args.expected_model_tree_sha256,
            )
        )
    print(
        json.dumps(
            verify_runtime_fingerprints(
                repo_root=args.repo_root,
                expected_source_sha256=args.expected_source_sha256,
                files=files,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (FingerprintError, OSError) as error:
        raise SystemExit(str(error)) from error
