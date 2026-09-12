"""Strict validation and deterministic merging for formal P1 result shards.

The P1 runners split questions inside :class:`PipelineBase`: first they call
``random.sample(..., seed=10)`` and then divide that sampled list into
contiguous chunks, assigning any remainder to the final chunk.  This module
reconstructs that exact assignment before accepting a result.  A successful
merge therefore proves that every effective question was scored exactly once,
without relying on the summary counts stored by the workers themselves.

The command-line interface validates and merges in one operation::

    python -m utils.p1_results \
      --dataset mindcube \
      --input-file /path/to/prepared/test.json \
      --run-root /path/to/formal/run

By default an existing ``results_merged.json`` is never replaced.  Pass
``--overwrite`` only when replacement is intentional.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


EXPECTED_DATASET_TOTALS = {
    "mindcube": 1050,
    "mmsi": 1000,
}


class P1ResultsError(RuntimeError):
    """Raised when a formal result set is incomplete or internally inconsistent."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise P1ResultsError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise P1ResultsError(f"Invalid JSON in {path}: {exc}") from exc


def _as_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise P1ResultsError(f"{label} must be a positive integer, got {value!r}.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise P1ResultsError(
            f"{label} must be a positive integer, got {value!r}."
        ) from exc
    if parsed <= 0 or str(parsed) != str(value):
        raise P1ResultsError(f"{label} must be a positive integer, got {value!r}.")
    return parsed


def _as_nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise P1ResultsError(f"{label} must be a non-negative integer, got {value!r}.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise P1ResultsError(
            f"{label} must be a non-negative integer, got {value!r}."
        ) from exc
    if parsed < 0 or str(parsed) != str(value):
        raise P1ResultsError(
            f"{label} must be a non-negative integer, got {value!r}."
        )
    return parsed


def _question_id(question: Mapping[str, Any], row_index: int) -> Any:
    if "eval_id" in question:
        value = question["eval_id"]
        field = "eval_id"
    elif "database_idx" in question:
        value = question["database_idx"]
        field = "database_idx"
    else:
        raise P1ResultsError(
            f"Input row {row_index} has neither eval_id nor database_idx."
        )
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise P1ResultsError(
            f"Input row {row_index} {field} must be a string or integer, "
            f"got {value!r}."
        )
    return value


def _id_key(value: Any, label: str) -> tuple[type, Any]:
    """Return a type-sensitive key while preserving string evaluation IDs."""

    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise P1ResultsError(
            f"{label} must contain only string or integer question IDs; got {value!r}."
        )
    return (type(value), value)


def _read_launch_manifest(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise P1ResultsError(f"Missing launch manifest: {path}") from exc

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise P1ResultsError(
                f"Malformed launch manifest line {line_number}: {raw_line!r}."
            )
        key, value = line.split("=", 1)
        if not key or key in values:
            raise P1ResultsError(
                f"Duplicate or empty launch manifest key on line {line_number}: "
                f"{key!r}."
            )
        values[key] = value
    return values


def reconstruct_effective_chunks(
    questions: Sequence[Mapping[str, Any]],
    *,
    num_questions: int,
    num_chunks: int,
    seed: int = 10,
) -> list[list[Mapping[str, Any]]]:
    """Reproduce ``PipelineBase`` question selection and contiguous slicing."""

    if num_questions <= 0:
        raise P1ResultsError("num_questions must be positive.")
    if num_chunks <= 0:
        raise P1ResultsError("num_chunks must be positive.")

    num_to_select = min(num_questions, len(questions))
    if num_chunks > num_to_select:
        raise P1ResultsError(
            f"num_chunks={num_chunks} exceeds effective questions={num_to_select}."
        )
    selected = random.Random(seed).sample(list(questions), k=num_to_select)
    chunk_size = len(selected) // num_chunks
    chunks: list[list[Mapping[str, Any]]] = []
    for chunk_index in range(num_chunks):
        start = chunk_index * chunk_size
        end = len(selected) if chunk_index == num_chunks - 1 else start + chunk_size
        chunks.append(selected[start:end])
    return chunks


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise P1ResultsError(f"{label} must be a JSON object.")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise P1ResultsError(f"{label} must be a JSON list.")
    return value


def _validate_complete_marker(
    complete_path: Path,
    results_path: Path,
    *,
    chunk_index: int,
    run_id: str | None,
) -> str:
    marker = _read_launch_manifest(complete_path)
    marker_index = _as_nonnegative_int(
        marker.get("chunk_index"), f"{complete_path} chunk_index"
    )
    if marker_index != chunk_index:
        raise P1ResultsError(
            f"{complete_path} records chunk_index={marker_index}, expected {chunk_index}."
        )
    if run_id is not None and marker.get("run_id") != run_id:
        raise P1ResultsError(
            f"{complete_path} run_id does not match launch_manifest.txt."
        )
    actual_sha256 = _sha256_file(results_path)
    if marker.get("results_sha256") != actual_sha256:
        raise P1ResultsError(
            f"{complete_path} checksum does not match {results_path}."
        )
    return actual_sha256


def _chunk_root(run_root: Path, num_chunks: int, chunks_dir: Path | None) -> Path:
    if chunks_dir is not None:
        return chunks_dir
    runtime_layout = run_root / f"results_spatial_beam_search_qc{num_chunks}"
    archived_layout = run_root / "chunks"
    runtime_exists = runtime_layout.is_dir()
    archived_exists = archived_layout.is_dir()
    if runtime_exists and archived_exists:
        raise P1ResultsError(
            "Both runtime and archived chunk layouts exist; pass --chunks-dir "
            "to select one explicitly."
        )
    if archived_exists:
        return archived_layout
    return runtime_layout


def _run_group_from_result(
    result: Mapping[str, Any], results_path: Path
) -> tuple[Mapping[str, Any], str, Mapping[str, Any], int]:
    experiment = _require_mapping(result.get("experiment"), f"{results_path} experiment")
    configuration = _require_mapping(
        experiment.get("configuration"), f"{results_path} experiment.configuration"
    )
    run_group = _require_mapping(
        configuration.get("run_group"),
        f"{results_path} experiment.configuration.run_group",
    )
    arguments = _require_mapping(
        run_group.get("arguments"), f"{results_path} run_group.arguments"
    )
    fingerprint = experiment.get("run_group_fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        raise P1ResultsError(f"{results_path} has no run_group_fingerprint.")
    encoded = json.dumps(run_group, sort_keys=True, separators=(",", ":"))
    recomputed = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    if fingerprint != recomputed:
        raise P1ResultsError(
            f"{results_path} run_group_fingerprint does not match its run_group."
        )
    chunk_index = configuration.get("question_chunk_idx")
    if isinstance(chunk_index, bool) or not isinstance(chunk_index, int):
        raise P1ResultsError(
            f"{results_path} configuration.question_chunk_idx must be an integer."
        )
    return run_group, fingerprint, arguments, chunk_index


def _first_seen_types(questions: Iterable[Mapping[str, Any]]) -> list[str]:
    types: list[str] = []
    seen: set[str] = set()
    for row_index, question in enumerate(questions):
        question_type = question.get("question_type")
        if not isinstance(question_type, str) or not question_type:
            raise P1ResultsError(
                f"Input row {row_index} question_type must be a non-empty string."
            )
        if question_type not in seen:
            seen.add(question_type)
            types.append(question_type)
    return types


def _validate_output_budget(run_group, manifest):
    # Old archived runs have no explicit launch budget; their own frozen
    # validator remains usable. New runs must match the declared budget.
    expected = manifest.get("max_output_tokens")
    if expected is not None and str(run_group.get("qwen_max_tokens")) != expected:
        raise P1ResultsError("Result output-token budget differs from launch manifest.")


def validate_single_chunk(
    *,
    run_root: str | os.PathLike[str],
    input_file: str | os.PathLike[str],
    dataset: str,
    chunk_index: int,
    results_file: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Validate one shard before a runner creates its ``COMPLETE`` marker.

    This performs the same formal dataset, parameter, fingerprint, and exact
    effective-ID checks as the full merge, but intentionally does not require
    a ``COMPLETE`` file.  The returned checksum is suitable for writing into
    that marker after validation succeeds.
    """

    if dataset not in EXPECTED_DATASET_TOTALS:
        allowed = ", ".join(sorted(EXPECTED_DATASET_TOTALS))
        raise P1ResultsError(f"Unknown dataset {dataset!r}; expected one of: {allowed}.")
    if isinstance(chunk_index, bool) or not isinstance(chunk_index, int):
        raise P1ResultsError(f"chunk_index must be a non-negative integer, got {chunk_index!r}.")

    run_root_path = Path(run_root).expanduser().resolve()
    input_path = Path(input_file).expanduser().resolve()
    manifest = _read_launch_manifest(run_root_path / "launch_manifest.txt")
    if manifest.get("dataset") != dataset:
        raise P1ResultsError(
            f"Manifest dataset={manifest.get('dataset')!r}, requested dataset={dataset!r}."
        )

    expected_total = EXPECTED_DATASET_TOTALS[dataset]
    num_questions = _as_positive_int(
        manifest.get("num_questions"), "manifest num_questions"
    )
    num_chunks = _as_positive_int(manifest.get("num_chunks"), "manifest num_chunks")
    max_images = _as_positive_int(manifest.get("max_images"), "manifest max_images")
    if num_questions != expected_total:
        raise P1ResultsError(
            f"Formal {dataset} results require {expected_total} questions, "
            f"but the manifest records {num_questions}."
        )
    if chunk_index < 0 or chunk_index >= num_chunks:
        raise P1ResultsError(
            f"chunk_index={chunk_index} is outside [0, {num_chunks - 1}]."
        )

    questions_value = _load_json(input_path)
    if not isinstance(questions_value, list):
        raise P1ResultsError(f"Prepared dataset {input_path} must be a JSON list.")
    questions = questions_value
    if len(questions) != expected_total:
        raise P1ResultsError(
            f"Prepared {dataset} dataset must contain {expected_total} rows, "
            f"found {len(questions)}."
        )

    observed_max_images = 0
    type_by_key: dict[tuple[type, Any], str] = {}
    for row_index, question_value in enumerate(questions):
        question = _require_mapping(question_value, f"Input row {row_index}")
        qid = _question_id(question, row_index)
        key = _id_key(qid, f"Input row {row_index}")
        if key in type_by_key:
            raise P1ResultsError(f"Duplicate input question ID {qid!r}.")
        question_type = question.get("question_type")
        if not isinstance(question_type, str) or not question_type:
            raise P1ResultsError(
                f"Input row {row_index} question_type must be a non-empty string."
            )
        type_by_key[key] = question_type
        images = _require_list(question.get("img_paths"), f"Input row {row_index} img_paths")
        observed_max_images = max(observed_max_images, len(images))
    if observed_max_images != max_images:
        raise P1ResultsError(
            f"Manifest max_images={max_images}, but prepared data requires "
            f"max_images={observed_max_images}."
        )

    chunks = reconstruct_effective_chunks(
        questions, num_questions=num_questions, num_chunks=num_chunks, seed=10
    )
    expected_questions = chunks[chunk_index]
    if results_file is None:
        result_path = (
            run_root_path
            / f"results_spatial_beam_search_qc{num_chunks}"
            / f"question_chunk_{chunk_index}"
            / "results.json"
        )
    else:
        result_path = Path(results_file).expanduser().resolve()
    result = _require_mapping(_load_json(result_path), str(result_path))

    run_group, fingerprint, arguments, recorded_chunk_index = _run_group_from_result(
        result, result_path
    )
    if recorded_chunk_index != chunk_index:
        raise P1ResultsError(
            f"{result_path} records question_chunk_idx={recorded_chunk_index}, "
            f"expected {chunk_index}."
        )
    for argument_name, expected_value in (
        ("num_questions", num_questions),
        ("num_question_chunks", num_chunks),
        ("max_images", max_images),
    ):
        actual_value = arguments.get(argument_name)
        if actual_value != expected_value:
            raise P1ResultsError(
                f"{result_path} run_group.arguments.{argument_name}="
                f"{actual_value!r}, expected {expected_value}."
            )
    dataset_sha256 = _sha256_file(input_path)
    if run_group.get("dataset_json_sha256") != dataset_sha256:
        raise P1ResultsError(
            f"{result_path} dataset_json_sha256 does not match {input_path}."
        )
    manifest_model = manifest.get("model")
    _validate_output_budget(run_group, manifest)
    if manifest_model is not None and arguments.get("vlm_model_name") != manifest_model:
        raise P1ResultsError(
            f"{result_path} model {arguments.get('vlm_model_name')!r} "
            f"does not match manifest model {manifest_model!r}."
        )

    skips = _require_list(result.get("skip_indices"), f"{result_path} skip_indices")
    if skips:
        raise P1ResultsError(
            f"{result_path} contains {len(skips)} skipped question(s); "
            "formal P1 validation requires zero skips."
        )
    progress = _require_mapping(result.get("progress"), f"{result_path} progress")
    expected_keys: dict[tuple[type, Any], Any] = {}
    expected_types: set[str] = set()
    for local_index, question in enumerate(expected_questions):
        qid = _question_id(question, local_index)
        expected_keys[_id_key(qid, f"Expected chunk {chunk_index}")] = qid
        expected_types.add(question["question_type"])
    if set(progress) != expected_types:
        raise P1ResultsError(
            f"{result_path} progress question types do not match effective chunk "
            f"{chunk_index}."
        )

    seen: dict[tuple[type, Any], tuple[str, str]] = {}
    correct_count = 0
    wrong_count = 0
    for question_type, buckets_value in progress.items():
        buckets = _require_mapping(
            buckets_value, f"{result_path} progress[{question_type!r}]"
        )
        if set(buckets) != {"correct", "wrong"}:
            raise P1ResultsError(
                f"{result_path} progress[{question_type!r}] must contain "
                "exactly correct and wrong lists."
            )
        for outcome in ("correct", "wrong"):
            ids = _require_list(
                buckets.get(outcome),
                f"{result_path} progress[{question_type!r}][{outcome!r}]",
            )
            for qid in ids:
                key = _id_key(qid, f"{result_path} {outcome}")
                if key in seen:
                    prior_type, prior_outcome = seen[key]
                    raise P1ResultsError(
                        f"{result_path} repeats question ID {qid!r} in "
                        f"{prior_type}/{prior_outcome} and {question_type}/{outcome}."
                    )
                if key not in expected_keys:
                    raise P1ResultsError(
                        f"{result_path} contains unexpected question ID {qid!r}."
                    )
                if type_by_key[key] != question_type:
                    raise P1ResultsError(
                        f"{result_path} places question ID {qid!r} under "
                        f"{question_type!r}; expected {type_by_key[key]!r}."
                    )
                seen[key] = (question_type, outcome)
                if outcome == "correct":
                    correct_count += 1
                else:
                    wrong_count += 1
    if set(seen) != set(expected_keys):
        missing = [expected_keys[key] for key in set(expected_keys) - set(seen)]
        raise P1ResultsError(
            f"{result_path} is not exhaustive for effective chunk {chunk_index}; "
            f"missing={missing[:10]!r}."
        )

    evaluation = result.get("evaluation")
    if isinstance(evaluation, Mapping):
        if "underlying_questions" in evaluation and evaluation[
            "underlying_questions"
        ] != num_questions:
            raise P1ResultsError(
                f"{result_path} evaluation.underlying_questions does not match "
                f"{num_questions}."
            )
        if "evaluated_in_chunk" in evaluation and evaluation[
            "evaluated_in_chunk"
        ] != len(expected_questions):
            raise P1ResultsError(
                f"{result_path} evaluation.evaluated_in_chunk does not match "
                f"{len(expected_questions)}."
            )

    return {
        "status": "passed",
        "dataset": dataset,
        "chunk_index": chunk_index,
        "expected": len(expected_questions),
        "correct": correct_count,
        "wrong": wrong_count,
        "run_group_fingerprint": fingerprint,
        "dataset_json_sha256": dataset_sha256,
        "results_sha256": _sha256_file(result_path),
        "results_file": str(result_path),
    }


def validate_and_merge(
    *,
    run_root: str | os.PathLike[str],
    input_file: str | os.PathLike[str],
    dataset: str,
    output_file: str | os.PathLike[str] | None = None,
    chunks_dir: str | os.PathLike[str] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Validate every formal shard and atomically write one merged result.

    ``eval_id`` values are retained verbatim, including string IDs.  Validation
    is deliberately strict: no skipped, duplicate, missing, unexpected, or
    mis-typed question can be hidden by otherwise plausible aggregate counts.
    """

    if dataset not in EXPECTED_DATASET_TOTALS:
        allowed = ", ".join(sorted(EXPECTED_DATASET_TOTALS))
        raise P1ResultsError(f"Unknown dataset {dataset!r}; expected one of: {allowed}.")

    run_root_path = Path(run_root).expanduser().resolve()
    input_path = Path(input_file).expanduser().resolve()
    output_path = (
        Path(output_file).expanduser().resolve()
        if output_file is not None
        else run_root_path / "results_merged.json"
    )
    explicit_chunks_path = (
        Path(chunks_dir).expanduser().resolve() if chunks_dir is not None else None
    )
    manifest_path = run_root_path / "launch_manifest.txt"
    manifest = _read_launch_manifest(manifest_path)

    manifest_dataset = manifest.get("dataset")
    if manifest_dataset != dataset:
        raise P1ResultsError(
            f"Manifest dataset={manifest_dataset!r}, requested dataset={dataset!r}."
        )
    expected_total = EXPECTED_DATASET_TOTALS[dataset]
    num_questions = _as_positive_int(
        manifest.get("num_questions"), "manifest num_questions"
    )
    num_chunks = _as_positive_int(manifest.get("num_chunks"), "manifest num_chunks")
    max_images = _as_positive_int(manifest.get("max_images"), "manifest max_images")
    if num_questions != expected_total:
        raise P1ResultsError(
            f"Formal {dataset} results require {expected_total} questions, "
            f"but the manifest records {num_questions}."
        )

    questions = _load_json(input_path)
    if not isinstance(questions, list):
        raise P1ResultsError(f"Prepared dataset {input_path} must be a JSON list.")
    if len(questions) != expected_total:
        raise P1ResultsError(
            f"Prepared {dataset} dataset must contain {expected_total} rows, "
            f"found {len(questions)}."
        )
    if not questions:
        raise P1ResultsError(f"Prepared dataset is empty: {input_path}")

    observed_max_images = 0
    all_id_keys: dict[tuple[type, Any], int] = {}
    for row_index, question_value in enumerate(questions):
        question = _require_mapping(question_value, f"Input row {row_index}")
        qid = _question_id(question, row_index)
        key = _id_key(qid, f"Input row {row_index}")
        if key in all_id_keys:
            raise P1ResultsError(
                f"Duplicate input question ID {qid!r} at rows "
                f"{all_id_keys[key]} and {row_index}."
            )
        all_id_keys[key] = row_index
        images = _require_list(question.get("img_paths"), f"Input row {row_index} img_paths")
        observed_max_images = max(observed_max_images, len(images))
    if max_images != observed_max_images:
        raise P1ResultsError(
            f"Manifest max_images={max_images}, but prepared data requires "
            f"max_images={observed_max_images}."
        )

    expected_chunks = reconstruct_effective_chunks(
        questions, num_questions=num_questions, num_chunks=num_chunks, seed=10
    )
    selected_questions = [question for chunk in expected_chunks for question in chunk]
    type_order = _first_seen_types(selected_questions)
    expected_type_by_key: dict[tuple[type, Any], str] = {}
    for row_index, question in enumerate(questions):
        qid = _question_id(question, row_index)
        expected_type_by_key[_id_key(qid, f"Input row {row_index}")] = question[
            "question_type"
        ]

    dataset_sha256 = _sha256_file(input_path)
    results_root = _chunk_root(run_root_path, num_chunks, explicit_chunks_path)
    common_fingerprint: str | None = None
    common_run_group: Mapping[str, Any] | None = None
    global_seen: dict[tuple[type, Any], tuple[int, str, str]] = {}
    merged_progress: OrderedDict[str, dict[str, list[Any]]] = OrderedDict(
        (question_type, {"correct": [], "wrong": []})
        for question_type in type_order
    )
    source_chunks: list[str] = []
    chunk_summaries: list[dict[str, Any]] = []
    parsing_scores = 0
    parsing_answers = 0
    parsing_score_qids: list[Any] = []
    parsing_answer_qids: list[Any] = []

    for chunk_index, expected_questions in enumerate(expected_chunks):
        chunk_directory = results_root / f"question_chunk_{chunk_index}"
        results_path = chunk_directory / "results.json"
        complete_path = chunk_directory / "COMPLETE"
        result_value = _load_json(results_path)
        result = _require_mapping(result_value, str(results_path))
        results_sha256 = _validate_complete_marker(
            complete_path,
            results_path,
            chunk_index=chunk_index,
            run_id=manifest.get("run_id"),
        )

        run_group, fingerprint, arguments, recorded_chunk_index = _run_group_from_result(
            result, results_path
        )
        if recorded_chunk_index != chunk_index:
            raise P1ResultsError(
                f"{results_path} records question_chunk_idx={recorded_chunk_index}, "
                f"expected {chunk_index}."
            )
        if common_fingerprint is None:
            common_fingerprint = fingerprint
            common_run_group = run_group
        elif fingerprint != common_fingerprint:
            raise P1ResultsError(
                f"{results_path} run_group_fingerprint differs from earlier chunks."
            )

        parameter_pairs = (
            ("num_questions", num_questions),
            ("num_question_chunks", num_chunks),
            ("max_images", max_images),
        )
        for argument_name, expected_value in parameter_pairs:
            actual_value = arguments.get(argument_name)
            if actual_value != expected_value:
                raise P1ResultsError(
                    f"{results_path} run_group.arguments.{argument_name}="
                    f"{actual_value!r}, expected {expected_value}."
                )
        if run_group.get("dataset_json_sha256") != dataset_sha256:
            raise P1ResultsError(
                f"{results_path} dataset_json_sha256 does not match {input_path}."
            )
        manifest_model = manifest.get("model")
        _validate_output_budget(run_group, manifest)
        if manifest_model is not None and arguments.get("vlm_model_name") != manifest_model:
            raise P1ResultsError(
                f"{results_path} model {arguments.get('vlm_model_name')!r} "
                f"does not match manifest model {manifest_model!r}."
            )

        skips = _require_list(result.get("skip_indices"), f"{results_path} skip_indices")
        if skips:
            raise P1ResultsError(
                f"{results_path} contains {len(skips)} skipped question(s); "
                "formal P1 merges require zero skips."
            )
        progress = _require_mapping(result.get("progress"), f"{results_path} progress")

        expected_chunk_keys: dict[tuple[type, Any], Any] = {}
        expected_chunk_types: set[str] = set()
        for local_index, question in enumerate(expected_questions):
            qid = _question_id(question, local_index)
            expected_chunk_keys[_id_key(qid, f"Expected chunk {chunk_index}")] = qid
            expected_chunk_types.add(question["question_type"])
        if set(progress) != expected_chunk_types:
            missing_types = sorted(expected_chunk_types - set(progress))
            extra_types = sorted(set(progress) - expected_chunk_types)
            raise P1ResultsError(
                f"{results_path} progress question types do not match the effective "
                f"chunk (missing={missing_types}, extra={extra_types})."
            )

        chunk_seen: dict[tuple[type, Any], tuple[str, str]] = {}
        chunk_correct = 0
        chunk_wrong = 0
        for question_type, buckets_value in progress.items():
            buckets = _require_mapping(
                buckets_value, f"{results_path} progress[{question_type!r}]"
            )
            if set(buckets) != {"correct", "wrong"}:
                raise P1ResultsError(
                    f"{results_path} progress[{question_type!r}] must contain "
                    "exactly correct and wrong lists."
                )
            for outcome in ("correct", "wrong"):
                ids = _require_list(
                    buckets.get(outcome),
                    f"{results_path} progress[{question_type!r}][{outcome!r}]",
                )
                for qid in ids:
                    key = _id_key(qid, f"{results_path} {outcome}")
                    if key in chunk_seen:
                        prior_type, prior_outcome = chunk_seen[key]
                        raise P1ResultsError(
                            f"{results_path} repeats question ID {qid!r} in "
                            f"{prior_type}/{prior_outcome} and {question_type}/{outcome}."
                        )
                    if key not in expected_chunk_keys:
                        raise P1ResultsError(
                            f"{results_path} contains unexpected question ID {qid!r}."
                        )
                    expected_type = expected_type_by_key[key]
                    if question_type != expected_type:
                        raise P1ResultsError(
                            f"{results_path} places question ID {qid!r} under "
                            f"{question_type!r}; expected {expected_type!r}."
                        )
                    if key in global_seen:
                        prior_chunk, prior_type, prior_outcome = global_seen[key]
                        raise P1ResultsError(
                            f"Question ID {qid!r} appears in chunks {prior_chunk} "
                            f"({prior_type}/{prior_outcome}) and {chunk_index} "
                            f"({question_type}/{outcome})."
                        )
                    chunk_seen[key] = (question_type, outcome)
                    global_seen[key] = (chunk_index, question_type, outcome)
                    merged_progress[question_type][outcome].append(qid)
                    if outcome == "correct":
                        chunk_correct += 1
                    else:
                        chunk_wrong += 1

        actual_keys = set(chunk_seen)
        expected_keys = set(expected_chunk_keys)
        if actual_keys != expected_keys:
            missing = [
                expected_chunk_keys[key]
                for key in expected_keys - actual_keys
            ]
            unexpected = [
                key[1] for key in actual_keys - expected_keys
            ]
            raise P1ResultsError(
                f"{results_path} is not exhaustive for effective chunk {chunk_index}: "
                f"missing={missing[:10]!r}, unexpected={unexpected[:10]!r}."
            )

        evaluation = result.get("evaluation")
        if isinstance(evaluation, Mapping):
            if "underlying_questions" in evaluation and evaluation[
                "underlying_questions"
            ] != num_questions:
                raise P1ResultsError(
                    f"{results_path} evaluation.underlying_questions does not "
                    f"match {num_questions}."
                )
            if "evaluated_in_chunk" in evaluation and evaluation[
                "evaluated_in_chunk"
            ] != len(expected_questions):
                raise P1ResultsError(
                    f"{results_path} evaluation.evaluated_in_chunk does not "
                    f"match {len(expected_questions)}."
                )

        parsing = result.get("parsing_err_stats", {})
        if isinstance(parsing, Mapping):
            parsing_scores += int(parsing.get("scores", 0))
            parsing_answers += int(parsing.get("answer", 0))
            score_qids = parsing.get("scores_qid", [])
            answer_qids = parsing.get("answer_qid", [])
            if isinstance(score_qids, list):
                parsing_score_qids.extend(score_qids)
            if isinstance(answer_qids, list):
                parsing_answer_qids.extend(answer_qids)

        source_chunks.append(str(results_path))
        chunk_summaries.append(
            {
                "chunk_index": chunk_index,
                "expected": len(expected_questions),
                "correct": chunk_correct,
                "wrong": chunk_wrong,
                "results_sha256": results_sha256,
                "source": str(results_path),
            }
        )

    expected_global_keys = set(all_id_keys)
    if set(global_seen) != expected_global_keys:
        missing = [questions[all_id_keys[key]] for key in expected_global_keys - set(global_seen)]
        raise P1ResultsError(
            f"Merged result is missing {len(missing)} prepared question(s)."
        )
    if common_fingerprint is None or common_run_group is None:
        raise P1ResultsError("No result chunks were validated.")

    accuracy_types: OrderedDict[str, float] = OrderedDict()
    correct_total = 0
    wrong_total = 0
    for question_type, buckets in merged_progress.items():
        correct_count = len(buckets["correct"])
        wrong_count = len(buckets["wrong"])
        type_total = correct_count + wrong_count
        if type_total == 0:
            raise P1ResultsError(
                f"Merged question type {question_type!r} unexpectedly has no results."
            )
        accuracy_types[question_type] = correct_count / type_total
        correct_total += correct_count
        wrong_total += wrong_count

    merged: dict[str, Any] = {
        "evaluation": {
            "underlying_questions": num_questions,
            "evaluated_in_chunks": correct_total + wrong_total,
            "aggregation": "top1_accuracy_over_questions",
            "source_chunks": source_chunks,
        },
        "experiment": {
            "run_group_fingerprint": common_fingerprint,
            "configuration": {"run_group": common_run_group},
        },
        "current": f"{correct_total + wrong_total} / {num_questions}",
        "parsing_err_stats": {
            "scores": parsing_scores,
            "answer": parsing_answers,
            "answer_qid": parsing_answer_qids,
            "scores_qid": parsing_score_qids,
        },
        "accuracy": {
            "all": correct_total / (correct_total + wrong_total),
            "types": accuracy_types,
        },
        "counts": {
            "correct": correct_total,
            "wrong": wrong_total,
            "total": correct_total + wrong_total,
        },
        "skip_indices": [],
        "progress": merged_progress,
        "validation": {
            "status": "passed",
            "dataset": dataset,
            "expected_total": expected_total,
            "num_chunks": num_chunks,
            "max_images": max_images,
            "dataset_json_sha256": dataset_sha256,
            "launch_manifest_sha256": _sha256_file(manifest_path),
            "checks": [
                "pipeline_seed_10_effective_chunk_membership",
                "zero_skips",
                "correct_wrong_exhaustive_and_unique",
                "run_group_fingerprint_consistency",
                "formal_parameter_consistency",
                "chunk_completion_checksums",
            ],
            "chunks": chunk_summaries,
        },
    }
    _atomic_write_json(output_path, merged, overwrite=overwrite)
    return merged


def _atomic_write_json(path: Path, payload: Mapping[str, Any], *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary_path, path)
        else:
            try:
                os.link(temporary_path, path)
            except FileExistsError as exc:
                raise P1ResultsError(
                    f"Refusing to overwrite existing merged result: {path}"
                ) from exc
            temporary_path.unlink()
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Strictly validate and merge a formal MindJourney P1 run."
    )
    parser.add_argument("--run-root", required=True, help="Formal run directory")
    parser.add_argument("--input-file", required=True, help="Prepared test.json")
    parser.add_argument(
        "--dataset", required=True, choices=sorted(EXPECTED_DATASET_TOTALS)
    )
    parser.add_argument(
        "--output-file",
        help="Merged output (default: RUN_ROOT/results_merged.json)",
    )
    parser.add_argument(
        "--chunks-dir",
        help="Explicit question_chunk_* parent for an archived/nonstandard layout",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Intentionally replace an existing merged output",
    )
    parser.add_argument(
        "--chunk-index",
        type=int,
        help="Validate only this chunk without requiring COMPLETE",
    )
    parser.add_argument(
        "--results-file",
        help="Explicit results.json for --chunk-index mode",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.results_file is not None and args.chunk_index is None:
        parser.error("--results-file requires --chunk-index")
    try:
        if args.chunk_index is not None:
            summary = validate_single_chunk(
                run_root=args.run_root,
                input_file=args.input_file,
                dataset=args.dataset,
                chunk_index=args.chunk_index,
                results_file=args.results_file,
            )
        else:
            merged = validate_and_merge(
                run_root=args.run_root,
                input_file=args.input_file,
                dataset=args.dataset,
                output_file=args.output_file,
                chunks_dir=args.chunks_dir,
                overwrite=args.overwrite,
            )
    except P1ResultsError as exc:
        print(f"P1 result validation failed: {exc}", file=os.sys.stderr)
        return 1
    if args.chunk_index is not None:
        print(
            f"Validated chunk {summary['chunk_index']}: {summary['expected']} questions, "
            f"{summary['correct']} correct, {summary['wrong']} wrong."
        )
        print(f"results_sha256={summary['results_sha256']}")
        return 0
    counts = merged["counts"]
    print(
        f"Validated {counts['total']} questions: {counts['correct']} correct, "
        f"{counts['wrong']} wrong, accuracy={merged['accuracy']['all']:.4%}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
