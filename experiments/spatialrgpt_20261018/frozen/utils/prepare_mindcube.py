#!/usr/bin/env python3
"""Prepare the official MindCube tinybench for MindJourney.

The MindCube question text assigns semantics to ``Image 1`` ... ``Image N``.
Consequently, the order of the official ``images`` array is part of the data and
must never be inferred from, or replaced by, filename sorting.  This converter
copies that array in order, resolves each relative path below an operator-supplied
image root, and emits the ``test.json`` schema consumed by MindJourney.

The pinned revisions and hashes below identify the official artifacts audited on
2026-09-05.  Strict official-size validation is the default; the public Python API
accepts alternate expectations only to support small unit fixtures.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


OFFICIAL_CODE_REPOSITORY = "https://github.com/mll-lab-nu/MindCube"
OFFICIAL_CODE_REVISION = "b8b7062adf6d3e49d588a7d014a0a787553d09ec"
OFFICIAL_DATASET_REPOSITORY = "MLL-Lab/MindCube"
OFFICIAL_DATASET_REVISION = "9c941b46a6bd65b6914669ef7a579948fc9c8467"
OFFICIAL_DATA_ARCHIVE_SHA256 = (
    "714c8961d66e9662c826d2202493a7d86cbe31797cf41e3a0567cb4d72b0aaa8"
)
OFFICIAL_TINYBENCH_SHA256 = (
    "0289eb82d81ff9aa0201ae75f86da7fd1924cf23dc202856d0579a0effd22ac8"
)

CHOICE_PATTERN = re.compile(r"([A-Z]\.\s+.*?)(?=[A-Z]\.|$)")
ALLOWED_SETTINGS = frozenset({"among", "around", "rotation"})


class MindCubePreparationError(ValueError):
    """Raised when a source or prepared dataset violates the locked contract."""


@dataclasses.dataclass(frozen=True)
class DatasetExpectations:
    records: int
    image_references: int
    unique_images: int
    image_count_distribution: tuple[tuple[int, int], ...]
    setting_distribution: tuple[tuple[str, int], ...]

    def image_counts(self) -> dict[int, int]:
        return dict(self.image_count_distribution)

    def setting_counts(self) -> dict[str, int]:
        return dict(self.setting_distribution)


OFFICIAL_EXPECTATIONS = DatasetExpectations(
    records=1050,
    image_references=3307,
    unique_images=428,
    image_count_distribution=((2, 274), (3, 345), (4, 431)),
    setting_distribution=(("among", 600), ("around", 250), ("rotation", 200)),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise MindCubePreparationError(
                    f"Invalid JSON at {path}:{line_number}: {error}"
                ) from error
            if not isinstance(row, dict):
                raise MindCubePreparationError(
                    f"Expected an object at {path}:{line_number}."
                )
            rows.append(row)
    return rows


def parse_question_and_choices(question: str) -> tuple[str, list[str]]:
    """Split the official inline choices without changing their text or order."""

    matches = list(CHOICE_PATTERN.finditer(question))
    if not matches:
        raise MindCubePreparationError("Question has no parseable answer choices.")

    choices = [match.group(1).strip() for match in matches]
    labels = [choice.split(".", 1)[0] for choice in choices]
    expected_labels = [chr(ord("A") + index) for index in range(len(choices))]
    if labels != expected_labels:
        raise MindCubePreparationError(
            f"Answer labels are not consecutive A..N: {labels!r}."
        )

    question_without_choices = question[: matches[0].start()].rstrip()
    if not question_without_choices:
        raise MindCubePreparationError("Question stem is empty after splitting choices.")
    return question_without_choices, choices


def setting_from_id(record_id: str) -> str:
    setting = record_id.split("_", 1)[0]
    if setting not in ALLOWED_SETTINGS:
        raise MindCubePreparationError(
            f"Unsupported MindCube tinybench setting {setting!r} for {record_id!r}."
        )
    return setting


def resolve_source_image(image_root: Path, relative_path: str) -> Path:
    """Resolve one official POSIX relative path while rejecting path traversal."""

    source_path = PurePosixPath(relative_path)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise MindCubePreparationError(
            f"Official image paths must be safe relative POSIX paths: {relative_path!r}."
        )
    if not source_path.parts:
        raise MindCubePreparationError("Official image path must not be empty.")

    root = image_root.resolve()
    resolved = root.joinpath(*source_path.parts).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise MindCubePreparationError(
            f"Image path escapes image root: {relative_path!r}."
        ) from error
    return resolved


def build_prepared_rows(
    source_rows: Sequence[Mapping[str, Any]], image_root: Path
) -> list[dict[str, Any]]:
    """Convert records while preserving the source record and image-list order."""

    prepared: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source_index, source in enumerate(source_rows):
        record_id = source.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise MindCubePreparationError(
                f"Source row {source_index} has no non-empty string id."
            )
        if record_id in seen_ids:
            raise MindCubePreparationError(f"Duplicate MindCube id: {record_id!r}.")
        seen_ids.add(record_id)

        question = source.get("question")
        if not isinstance(question, str) or not question:
            raise MindCubePreparationError(
                f"Source row {record_id!r} has no non-empty question."
            )
        question_stem, choices = parse_question_and_choices(question)

        answer_letter = source.get("gt_answer")
        if not isinstance(answer_letter, str):
            raise MindCubePreparationError(
                f"Source row {record_id!r} has no string gt_answer."
            )
        answer_letter = answer_letter.strip().upper()
        full_answers = [
            choice for choice in choices if choice.startswith(answer_letter + ".")
        ]
        if len(full_answers) != 1:
            raise MindCubePreparationError(
                f"Source row {record_id!r} answer {answer_letter!r} does not map "
                "to exactly one option."
            )

        source_images = source.get("images")
        if not isinstance(source_images, list) or not all(
            isinstance(path, str) and path for path in source_images
        ):
            raise MindCubePreparationError(
                f"Source row {record_id!r} has an invalid images array."
            )
        if not 2 <= len(source_images) <= 4:
            raise MindCubePreparationError(
                f"Source row {record_id!r} has {len(source_images)} images; expected 2-4."
            )

        # Deliberately iterate the official list directly.  Never use sorted(),
        # glob(), directory enumeration, or set iteration to construct img_paths.
        source_images_copy = list(source_images)
        image_paths = [
            str(resolve_source_image(image_root, path)) for path in source_images_copy
        ]
        setting = setting_from_id(record_id)

        prepared.append(
            {
                "database_idx": source_index,
                "eval_id": record_id,
                "id": record_id,
                "question_type": setting,
                "question": question_stem,
                "answer_choices": choices,
                "correct_answer": full_answers[0],
                "correct_answer_letter": answer_letter,
                "gt_answer": answer_letter,
                "img_paths": image_paths,
                "source_images": source_images_copy,
                "source_question": question,
                "category": source.get("category"),
                "type": source.get("type"),
                "meta_info": source.get("meta_info"),
            }
        )
    return prepared


def _first_seen(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def ordered_image_sequence_sha256(
    rows: Sequence[Mapping[str, Any]], image_key: str
) -> str:
    sequence = [
        {"id": row["id"], "images": list(row[image_key])}
        for row in rows
    ]
    return canonical_sha256(sequence)


def validate_prepared_rows(
    source_rows: Sequence[Mapping[str, Any]],
    prepared_rows: Sequence[Mapping[str, Any]],
    image_root: Path,
    expectations: DatasetExpectations = OFFICIAL_EXPECTATIONS,
) -> dict[str, Any]:
    """Strictly validate counts, files, answers, and exact per-record image order."""

    if len(source_rows) != expectations.records:
        raise MindCubePreparationError(
            f"Expected {expectations.records} source rows, found {len(source_rows)}."
        )
    if len(prepared_rows) != len(source_rows):
        raise MindCubePreparationError(
            f"Prepared row count {len(prepared_rows)} != source row count {len(source_rows)}."
        )

    reference_paths: list[str] = []
    relative_references: list[str] = []
    image_count_distribution: collections.Counter[int] = collections.Counter()
    setting_distribution: collections.Counter[str] = collections.Counter()
    seen_ids: set[str] = set()

    for index, (source, prepared) in enumerate(zip(source_rows, prepared_rows)):
        source_id = source.get("id")
        if prepared.get("database_idx") != index:
            raise MindCubePreparationError(
                f"database_idx changed at source row {index}."
            )
        if prepared.get("id") != source_id or prepared.get("eval_id") != source_id:
            raise MindCubePreparationError(f"ID changed at source row {index}.")
        if source_id in seen_ids:
            raise MindCubePreparationError(f"Duplicate prepared id: {source_id!r}.")
        seen_ids.add(source_id)

        official_images = source.get("images")
        source_images = prepared.get("source_images")
        if source_images != official_images:
            raise MindCubePreparationError(
                f"Official image order changed for {source_id!r}: "
                f"source={official_images!r}, prepared={source_images!r}."
            )
        expected_paths = [
            str(resolve_source_image(image_root, path)) for path in official_images
        ]
        if prepared.get("img_paths") != expected_paths:
            raise MindCubePreparationError(
                f"Resolved image order changed for {source_id!r}: "
                f"expected={expected_paths!r}, prepared={prepared.get('img_paths')!r}."
            )

        question_stem, choices = parse_question_and_choices(source["question"])
        if prepared.get("question") != question_stem:
            raise MindCubePreparationError(f"Question stem changed for {source_id!r}.")
        if prepared.get("answer_choices") != choices:
            raise MindCubePreparationError(f"Answer choices changed for {source_id!r}.")
        answer_letter = str(source["gt_answer"]).strip().upper()
        expected_answer = next(
            (choice for choice in choices if choice.startswith(answer_letter + ".")),
            None,
        )
        if (
            prepared.get("correct_answer_letter") != answer_letter
            or prepared.get("gt_answer") != answer_letter
            or prepared.get("correct_answer") != expected_answer
        ):
            raise MindCubePreparationError(f"Correct answer changed for {source_id!r}.")

        setting = setting_from_id(str(source_id))
        if prepared.get("question_type") != setting:
            raise MindCubePreparationError(f"Setting changed for {source_id!r}.")

        image_count_distribution[len(official_images)] += 1
        setting_distribution[setting] += 1
        relative_references.extend(official_images)
        reference_paths.extend(expected_paths)

    if len(reference_paths) != expectations.image_references:
        raise MindCubePreparationError(
            f"Expected {expectations.image_references} image references, "
            f"found {len(reference_paths)}."
        )
    if dict(image_count_distribution) != expectations.image_counts():
        raise MindCubePreparationError(
            "Image-count distribution differs from official tinybench: "
            f"{dict(sorted(image_count_distribution.items()))!r}."
        )
    if dict(setting_distribution) != expectations.setting_counts():
        raise MindCubePreparationError(
            "Setting distribution differs from official tinybench: "
            f"{dict(sorted(setting_distribution.items()))!r}."
        )

    unique_relative_images = _first_seen(relative_references)
    unique_paths = _first_seen(reference_paths)
    if len(unique_paths) != expectations.unique_images:
        raise MindCubePreparationError(
            f"Expected {expectations.unique_images} unique images, found {len(unique_paths)}."
        )

    missing = [path for path in unique_paths if not Path(path).is_file()]
    if missing:
        raise MindCubePreparationError(
            f"Found {len(missing)} missing MindCube images; first: {missing[:5]!r}."
        )

    source_order_sha256 = ordered_image_sequence_sha256(source_rows, "images")
    prepared_order_sha256 = ordered_image_sequence_sha256(
        prepared_rows, "source_images"
    )
    if source_order_sha256 != prepared_order_sha256:
        raise MindCubePreparationError(
            "Ordered image-sequence digest changed during conversion."
        )

    return {
        "records": len(prepared_rows),
        "image_references": len(reference_paths),
        "unique_images": len(unique_paths),
        "missing_images": len(missing),
        "image_count_distribution": {
            str(key): image_count_distribution[key]
            for key in sorted(image_count_distribution)
        },
        "setting_distribution": {
            key: setting_distribution[key] for key in sorted(setting_distribution)
        },
        "ordered_image_sequence_sha256": source_order_sha256,
        "unique_relative_images_first_seen": unique_relative_images,
        "unique_absolute_images_first_seen": unique_paths,
    }


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _verified_git_revision(code_dir: Path, expected_revision: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(code_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise MindCubePreparationError(
            f"Could not read Git revision from {code_dir}: {error}"
        ) from error
    revision = result.stdout.strip()
    if revision != expected_revision:
        raise MindCubePreparationError(
            f"Official code revision mismatch: expected {expected_revision}, got {revision}."
        )
    return revision


def prepare_mindcube(
    *,
    raw_path: Path,
    image_root: Path,
    output_dir: Path,
    expectations: DatasetExpectations = OFFICIAL_EXPECTATIONS,
    expected_raw_sha256: str = OFFICIAL_TINYBENCH_SHA256,
    official_code_revision: str = OFFICIAL_CODE_REVISION,
    dataset_revision: str = OFFICIAL_DATASET_REVISION,
    data_archive_sha256: str = OFFICIAL_DATA_ARCHIVE_SHA256,
    data_archive: Path | None = None,
    official_code_dir: Path | None = None,
) -> dict[str, Any]:
    """Prepare ``test.json`` and an integrity-rich provenance sidecar."""

    raw_path = raw_path.resolve()
    image_root = image_root.resolve()
    output_dir = output_dir.resolve()
    if not raw_path.is_file():
        raise MindCubePreparationError(f"Raw JSONL does not exist: {raw_path}")
    if not image_root.is_dir():
        raise MindCubePreparationError(f"Image root does not exist: {image_root}")

    actual_raw_sha256 = sha256_file(raw_path)
    if actual_raw_sha256 != expected_raw_sha256:
        raise MindCubePreparationError(
            f"Raw tinybench SHA256 mismatch: expected {expected_raw_sha256}, "
            f"got {actual_raw_sha256}."
        )

    archive_verified = False
    archive_path: str | None = None
    if data_archive is not None:
        resolved_archive = data_archive.resolve()
        if not resolved_archive.is_file():
            raise MindCubePreparationError(
                f"Official data archive does not exist: {resolved_archive}"
            )
        actual_archive_sha256 = sha256_file(resolved_archive)
        if actual_archive_sha256 != data_archive_sha256:
            raise MindCubePreparationError(
                f"Official data archive SHA256 mismatch: expected {data_archive_sha256}, "
                f"got {actual_archive_sha256}."
            )
        archive_verified = True
        archive_path = str(resolved_archive)

    code_revision_verified = False
    code_path: str | None = None
    if official_code_dir is not None:
        resolved_code_dir = official_code_dir.resolve()
        _verified_git_revision(resolved_code_dir, official_code_revision)
        code_revision_verified = True
        code_path = str(resolved_code_dir)

    source_rows = load_jsonl(raw_path)
    prepared_rows = build_prepared_rows(source_rows, image_root)
    validation = validate_prepared_rows(
        source_rows, prepared_rows, image_root, expectations
    )

    output_path = output_dir / "test.json"
    provenance_path = output_dir / "test_provenance.json"
    _write_json_atomic(output_path, prepared_rows)

    image_manifest = []
    for relative_path, absolute_path in zip(
        validation.pop("unique_relative_images_first_seen"),
        validation.pop("unique_absolute_images_first_seen"),
    ):
        path = Path(absolute_path)
        image_manifest.append(
            {
                "relative_path": relative_path,
                "absolute_path": absolute_path,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    provenance = {
        "schema_version": 1,
        "dataset": {
            "repository": OFFICIAL_DATASET_REPOSITORY,
            "revision": dataset_revision,
            "data_archive_sha256": data_archive_sha256,
            "data_archive_verified": archive_verified,
            "data_archive_path": archive_path,
            "raw_jsonl_path": str(raw_path),
            "raw_jsonl_sha256": actual_raw_sha256,
        },
        "official_code": {
            "repository": OFFICIAL_CODE_REPOSITORY,
            "revision": official_code_revision,
            "revision_verified": code_revision_verified,
            "path": code_path,
        },
        "conversion": {
            "script": str(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "output_path": str(output_path),
            "output_sha256": sha256_file(output_path),
            "image_root": str(image_root),
            "order_contract": (
                "For every row, img_paths[i] is the resolved official images[i]. "
                "No filename, path, glob, or directory sorting is permitted."
            ),
        },
        "validation": validation,
        # First-seen order is intentional: this manifest also proves that no set
        # or lexical sort was used while traversing the semantic image sequence.
        "unique_image_manifest_first_seen": image_manifest,
    }
    _write_json_atomic(provenance_path, provenance)
    return {
        "output": str(output_path),
        "provenance": str(provenance_path),
        "validation": validation,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare official MindCube tinybench data for MindJourney."
    )
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument(
        "--image-root",
        type=Path,
        required=True,
        help="Directory containing the official other_all_image/ tree.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination directory; writes test.json and test_provenance.json.",
    )
    parser.add_argument(
        "--data-archive",
        type=Path,
        help="Optional official data.zip; when supplied, its pinned SHA256 is verified.",
    )
    parser.add_argument(
        "--official-code-dir",
        type=Path,
        help="Optional clean official clone; when supplied, HEAD must equal the pinned commit.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        summary = prepare_mindcube(
            raw_path=args.raw,
            image_root=args.image_root,
            output_dir=args.output_dir,
            data_archive=args.data_archive,
            official_code_dir=args.official_code_dir,
        )
    except MindCubePreparationError as error:
        raise SystemExit(f"MindCube preparation failed: {error}") from error
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
