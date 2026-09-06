"""Fail-closed validation for one-question, cross-host P1 diagnostic smokes.

These results are useful for diagnosing whether a P1 configuration can start
and finish on A100-1/A100-2.  They are deliberately marked non-formal and are
never accepted by :mod:`utils.p1_results`, which remains the full-dataset DAAI
validator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from utils.p1_results import (
    P1ResultsError,
    _id_key,
    _load_json,
    _question_id,
    _read_launch_manifest,
    _require_list,
    _require_mapping,
    _sha256_file,
    _validate_complete_marker,
)


DIAGNOSTIC_HOSTS = {"A100-1", "A100-2"}
DATASET_MAX_IMAGES = {"mindcube": 4, "mmsi": 10}
MODEL_PROFILES = {
    ("mindcube", "Qwen/Qwen3.5-27B"): {
        "revision": "fc05daec18b0a78c049392ed2e771dde82bdf654",
        "tp": "2",
        "total_gpus": "3",
    },
    ("mmsi", "Qwen/Qwen3.5-9B"): {
        "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "tp": "1",
        "total_gpus": "2",
    },
    ("mmsi", "Qwen/Qwen3.8-27B"): {
        "revision": "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0",
        "tp": "2",
        "total_gpus": "3",
    },
}
SVC_REVISION = "e538e251c1009e9a41cf8b7fee5f21332a1960de"
SVC_WEIGHT_SHA256 = (
    "10e69ea003c313e6bdfc7ee40376d1c19ea6036c20bd384e94b483dec8350396"
)


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_manifest_value(
    manifest: Mapping[str, str], key: str, expected: str
) -> None:
    actual = manifest.get(key)
    if actual != expected:
        raise P1ResultsError(
            f"launch_manifest.txt {key}={actual!r}, expected {expected!r}."
        )


def _expected_arguments(
    *, dataset: str, model: str, input_dir: Path
) -> dict[str, Any]:
    return {
        "task": "img2trajvid_s-prob",
        "replace_or_include_input": True,
        "cfg": 4.0,
        "guider": 1,
        "L_short": 576,
        "num_targets": 8,
        "use_traj_prior": True,
        "chunk_strategy": "interp",
        "input_dir": str(input_dir),
        "scaling_strategy": "spatial_beam_search",
        "question_type": "None",
        "sampling_interval_angle": 9,
        "sampling_interval_meter": 0.25,
        "fixed_rotation_magnitudes": 27,
        "fixed_forward_magnitudes": 0.75,
        "max_steps_per_question": 3,
        "max_tries_gpt": 5,
        "num_questions": 1,
        "num_frames": 9,
        "frame_interval": 3,
        "split": "test",
        "max_turn_angle": 60.0,
        "max_forward_distance": 1.5,
        "num_top_candidates": 18,
        "max_inference_batch_size": 1,
        "num_beams": 2,
        "max_images": DATASET_MAX_IMAGES[dataset],
        "helpful_score_threshold": 8,
        "exploration_score_threshold": 8,
        "vlm_model_name": model,
        "vlm_qa_model_name": "None",
        "num_question_chunks": 1,
        "camera_mixed": False,
    }


def validate_diagnostic_smoke(
    *,
    run_root: str | os.PathLike[str],
    input_file: str | os.PathLike[str],
    dataset: str,
    results_file: str | os.PathLike[str] | None = None,
    complete_file: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Validate one diagnostic result, optionally including ``COMPLETE``."""

    if dataset not in DATASET_MAX_IMAGES:
        raise P1ResultsError(f"Unsupported diagnostic dataset: {dataset!r}.")

    run_root_path = Path(run_root).expanduser().resolve()
    input_path = Path(input_file).expanduser().resolve()
    manifest_path = run_root_path / "launch_manifest.txt"
    manifest = _read_launch_manifest(manifest_path)

    _require_manifest_value(manifest, "dataset", dataset)
    _require_manifest_value(manifest, "method", "SVC")
    _require_manifest_value(manifest, "execution_scope", "diagnostic_smoke")
    _require_manifest_value(manifest, "formal_eligible", "false")
    _require_manifest_value(manifest, "formal_execution_cluster", "DAAI only")
    _require_manifest_value(manifest, "accelerator", "a10040")
    _require_manifest_value(manifest, "dtype", "bfloat16")
    _require_manifest_value(manifest, "thinking", "false")
    _require_manifest_value(manifest, "max_model_len", "65536")
    _require_manifest_value(manifest, "num_questions", "1")
    _require_manifest_value(manifest, "num_chunks", "1")
    _require_manifest_value(
        manifest, "max_images", str(DATASET_MAX_IMAGES[dataset])
    )
    _require_manifest_value(manifest, "split", "test")
    _require_manifest_value(manifest, "svc_gpus", "1")

    host = manifest.get("diagnostic_host")
    if host not in DIAGNOSTIC_HOSTS:
        raise P1ResultsError(
            f"launch_manifest.txt diagnostic_host={host!r}; expected A100-1/A100-2."
        )
    model = manifest.get("model")
    profile = MODEL_PROFILES.get((dataset, model or ""))
    if profile is None:
        raise P1ResultsError(
            f"{dataset}/{model!r} is not an enabled A100-40 diagnostic profile."
        )
    _require_manifest_value(manifest, "revision", profile["revision"])
    _require_manifest_value(manifest, "tensor_parallel_size", profile["tp"])
    _require_manifest_value(manifest, "total_gpus", profile["total_gpus"])

    expected_hardware = f"{host}:A100-40GB:TP{profile['tp']}+SVC1:diagnostic-smoke"
    _require_manifest_value(manifest, "hardware", expected_hardware)

    input_manifest_path = Path(manifest.get("input_file", "")).expanduser().resolve()
    if input_manifest_path != input_path:
        raise P1ResultsError("Input path does not match launch_manifest.txt.")
    input_sha256 = _sha256_file(input_path)
    _require_manifest_value(manifest, "input_sha256", input_sha256)

    provenance_path = Path(
        manifest.get("dataset_provenance", "")
    ).expanduser().resolve()
    provenance_sha256 = _sha256_file(provenance_path)
    _require_manifest_value(
        manifest, "dataset_provenance_sha256", provenance_sha256
    )
    experiment_manifest_path = Path(
        manifest.get("experiment_manifest", "")
    ).expanduser().resolve()
    experiment_manifest_sha256 = _sha256_file(experiment_manifest_path)
    _require_manifest_value(
        manifest, "experiment_manifest_sha256", experiment_manifest_sha256
    )
    source_sha256 = manifest.get("source_sha256")
    if not isinstance(source_sha256, str) or re.fullmatch(
        r"[0-9a-f]{64}", source_sha256
    ) is None:
        raise P1ResultsError("launch_manifest.txt has no valid source_sha256.")

    questions = _load_json(input_path)
    if not isinstance(questions, list) or len(questions) != 1:
        raise P1ResultsError(
            f"Diagnostic smoke input must contain exactly one record, found "
            f"{len(questions) if isinstance(questions, list) else 'non-list'}."
        )
    question = _require_mapping(questions[0], "Diagnostic input row 0")
    question_id = _question_id(question, 0)
    _id_key(question_id, "Diagnostic input row 0")
    question_type = question.get("question_type")
    if not isinstance(question_type, str) or not question_type:
        raise P1ResultsError("Diagnostic input question_type must be non-empty.")
    images = _require_list(question.get("img_paths"), "Diagnostic input img_paths")
    if not images or len(images) > DATASET_MAX_IMAGES[dataset]:
        raise P1ResultsError(
            f"Diagnostic input must have 1-{DATASET_MAX_IMAGES[dataset]} images."
        )

    result_path = (
        Path(results_file).expanduser().resolve()
        if results_file is not None
        else run_root_path / "results_spatial_beam_search" / "results.json"
    )
    result = _require_mapping(_load_json(result_path), str(result_path))
    experiment = _require_mapping(result.get("experiment"), "result experiment")
    configuration = _require_mapping(
        experiment.get("configuration"), "result experiment.configuration"
    )
    run_group = _require_mapping(
        configuration.get("run_group"), "result run_group"
    )
    arguments = _require_mapping(run_group.get("arguments"), "result arguments")

    expected_arguments = _expected_arguments(
        dataset=dataset, model=model or "", input_dir=input_path.parent
    )
    if dict(arguments) != expected_arguments:
        differing = sorted(
            key
            for key in set(arguments) | set(expected_arguments)
            if arguments.get(key) != expected_arguments.get(key)
        )
        raise P1ResultsError(
            "Diagnostic result arguments differ from the fixed SVC profile: "
            + ", ".join(differing)
        )
    if configuration.get("question_chunk_idx") != 0:
        raise P1ResultsError("Diagnostic result question_chunk_idx must be 0.")
    expected_output_dir = str(run_root_path / "results_spatial_beam_search")
    if Path(str(configuration.get("output_dir", ""))).resolve() != Path(
        expected_output_dir
    ).resolve():
        raise P1ResultsError("Diagnostic result output_dir does not match run root.")

    expected_run_group = {
        "arguments": expected_arguments,
        "dataset_json_sha256": input_sha256,
        "dataset_provenance_sha256": provenance_sha256,
        "manifest_sha256": experiment_manifest_sha256,
        "source_sha256": source_sha256,
        "submitted_source_sha256": source_sha256,
        "model_revision": profile["revision"],
        "model_tree_sha256": manifest.get("model_tree_sha256"),
        "model_dtype": "bfloat16",
        "qwen_enable_thinking": False,
        "qwen_context_limit": "65536",
        "qwen_max_tokens": "1024",
        "vllm_version": "0.28.0",
        "svc_revision": SVC_REVISION,
        "svc_weight_sha256": SVC_WEIGHT_SHA256,
        "svc_strict_load": "1",
        "runtime_environment": manifest.get("runtime_environment"),
        "hardware": expected_hardware,
        "protocol": "paper-aligned SVC multi-image adaptation",
    }
    if not expected_run_group["runtime_environment"]:
        raise P1ResultsError("launch_manifest.txt runtime_environment is empty.")
    if dict(run_group) != expected_run_group:
        differing = sorted(
            key
            for key in set(run_group) | set(expected_run_group)
            if run_group.get(key) != expected_run_group.get(key)
        )
        raise P1ResultsError(
            "Diagnostic result run_group differs from the pinned profile: "
            + ", ".join(differing)
        )

    run_group_fingerprint = _canonical_sha256(run_group)
    if experiment.get("run_group_fingerprint") != run_group_fingerprint:
        raise P1ResultsError("Diagnostic run_group_fingerprint mismatch.")
    fingerprint = _canonical_sha256(configuration)
    if experiment.get("fingerprint") != fingerprint:
        raise P1ResultsError("Diagnostic experiment fingerprint mismatch.")

    skips = _require_list(result.get("skip_indices"), "result skip_indices")
    if skips:
        raise P1ResultsError("Diagnostic result must contain zero skips.")
    progress = _require_mapping(result.get("progress"), "result progress")
    if set(progress) != {question_type}:
        raise P1ResultsError("Diagnostic progress question type is not exact.")
    buckets = _require_mapping(progress[question_type], "result progress buckets")
    if set(buckets) != {"correct", "wrong"}:
        raise P1ResultsError("Diagnostic progress must contain correct/wrong only.")
    correct = _require_list(buckets["correct"], "result correct")
    wrong = _require_list(buckets["wrong"], "result wrong")
    ids = correct + wrong
    if len(ids) != 1 or _id_key(ids[0], "Diagnostic result ID") != _id_key(
        question_id, "Diagnostic input ID"
    ):
        raise P1ResultsError(
            "Diagnostic result must contain the unique selected ID exactly once."
        )
    if result.get("current") != "1 / 1":
        raise P1ResultsError("Diagnostic result current must be '1 / 1'.")
    evaluation = _require_mapping(result.get("evaluation"), "result evaluation")
    expected_evaluation = {
        "underlying_questions": 1,
        "evaluated_in_chunk": 1,
        "aggregation": "top1_accuracy_over_questions",
    }
    if dict(evaluation) != expected_evaluation:
        raise P1ResultsError("Diagnostic result evaluation metadata is not exact.")

    expected_accuracy = 1.0 if correct else 0.0
    accuracy = _require_mapping(result.get("accuracy"), "result accuracy")
    types = _require_mapping(accuracy.get("types"), "result accuracy.types")
    if accuracy.get("all") != expected_accuracy or types != {
        question_type: expected_accuracy
    }:
        raise P1ResultsError("Diagnostic result accuracy is inconsistent.")

    results_sha256 = _sha256_file(result_path)
    if complete_file is not None:
        complete_path = Path(complete_file).expanduser().resolve()
        _validate_complete_marker(
            complete_path,
            result_path,
            chunk_index=0,
            run_id=manifest.get("run_id"),
        )
        complete = _read_launch_manifest(complete_path)
        for key, expected in (
            ("dataset", dataset),
            ("model", model or ""),
            ("revision", profile["revision"]),
            ("execution_scope", "diagnostic_smoke"),
            ("diagnostic_host", host),
        ):
            if complete.get(key) != expected:
                raise P1ResultsError(f"COMPLETE {key} mismatch.")

    return {
        "status": "passed",
        "dataset": dataset,
        "model": model,
        "diagnostic_host": host,
        "effective_id": question_id,
        "correct": len(correct),
        "wrong": len(wrong),
        "run_group_fingerprint": run_group_fingerprint,
        "experiment_fingerprint": fingerprint,
        "results_sha256": results_sha256,
        "results_file": str(result_path),
        "formal_eligible": False,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--dataset", required=True, choices=sorted(DATASET_MAX_IMAGES))
    parser.add_argument("--results-file")
    parser.add_argument("--complete-file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summary = validate_diagnostic_smoke(
            run_root=args.run_root,
            input_file=args.input_file,
            dataset=args.dataset,
            results_file=args.results_file,
            complete_file=args.complete_file,
        )
    except (P1ResultsError, OSError) as exc:
        print(f"P1 diagnostic smoke validation failed: {exc}", file=os.sys.stderr)
        return 1
    print(
        f"Validated non-formal diagnostic smoke {summary['effective_id']!r} on "
        f"{summary['diagnostic_host']}."
    )
    print(f"results_sha256={summary['results_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
