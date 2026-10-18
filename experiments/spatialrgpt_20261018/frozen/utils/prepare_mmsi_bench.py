#!/usr/bin/env python3
"""Prepare and validate the official MMSI-Bench test split for MindJourney.

The input expected by this utility is the extracted JSONL snapshot whose rows
contain ``id``, ``type``/``question_type``, ``question``, ``answer``, and an
ordered ``images`` list.  Image files may have moved to another machine: only
their basenames are rebound under ``--image-root``.  The order of the source
``images`` list is authoritative and is never reconstructed from a directory
listing or filename sort.

The default expectations pin the official 1,000-question snapshot used for the
MMSI-Bench experiments.  The generated MindJourney rows retain labelled A-D
choices and ``correct_answer_letter``.  Official scoring must compare that
letter; ``correct_answer`` is also emitted as a labelled choice for compatibility
with MindJourney's existing input schema.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Mapping, Sequence


OFFICIAL_DATASET_ID = "RunsenXu/MMSI-Bench"
OFFICIAL_DATASET_REVISION = "ec7c92bfaf7728fcca1d61e3e224e190af309436"
OFFICIAL_DATASET_SPLIT = "test"
OFFICIAL_CODE_REPOSITORY = "https://github.com/InternRobotics/MMSI-Bench.git"
OFFICIAL_CODE_REVISION = "13e58a2b8b30d880d7e8a1e4a6aa1c0feda94cac"

# Hashes below identify the already extracted, byte-verified snapshot on A100-2.
# The metadata hash is path-independent and was matched against all 1,000 rows
# exposed by the official Hugging Face Dataset Viewer at the pinned revision.
OFFICIAL_SOURCE_JSONL_SHA256 = (
    "9448f3ffc9c2364d396ab29bfc5a66ecab26fcc076ce1b6b364bdcad7c721601"
)
OFFICIAL_METADATA_SHA256 = (
    "22eb8a59a75e318f52c7cc83eb0714952397e84d9bc092ef8837747599d64b1d"
)
OFFICIAL_IMAGE_TREE_SHA256 = (
    "1915bcb705e661d46bab44dd8fe9513153466bca458bef26d030235d9e9c07d9"
)
OFFICIAL_ORDERED_DIMENSIONS_SHA256 = (
    "c01388907641fba54742c7fe87e7b78650b8803ba975cef18a66b2a572f5a425"
)
OFFICIAL_IMAGE_BYTES = 293_321_646

OFFICIAL_IMAGE_COUNT_DISTRIBUTION = {
    2: 810,
    3: 58,
    4: 40,
    5: 19,
    6: 38,
    7: 15,
    8: 15,
    9: 2,
    10: 3,
}
OFFICIAL_ANSWER_COUNTS = {"A": 265, "B": 250, "C": 255, "D": 230}
OFFICIAL_QUESTION_TYPE_COUNTS = {
    "Attribute (Appr.)": 66,
    "Attribute (Meas.)": 64,
    "MSR": 198,
    "Motion (Cam.)": 74,
    "Motion (Obj.)": 76,
    "Positional Relationship (Cam.–Cam.)": 93,
    "Positional Relationship (Cam.–Obj.)": 86,
    "Positional Relationship (Cam.–Reg.)": 83,
    "Positional Relationship (Obj.–Obj.)": 94,
    "Positional Relationship (Obj.–Reg.)": 85,
    "Positional Relationship (Reg.–Reg.)": 81,
}

OPTION_RE = re.compile(
    r"([A-D])\s*:\s*(.*?)(?=\s+[A-D]\s*:|,\s*[A-D]\s*:|$)",
    flags=re.DOTALL,
)
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class DatasetValidationError(ValueError):
    """Raised when an input cannot be proven to be the pinned official split."""


@dataclasses.dataclass(frozen=True)
class DatasetExpectations:
    """Expected invariants for a dataset snapshot.

    Optional hashes/count maps make the same validation machinery useful in
    lightweight unit tests without weakening the strict CLI defaults.
    """

    row_count: int
    image_count: int
    min_images_per_question: int
    max_images_per_question: int
    source_jsonl_sha256: str | None = None
    metadata_sha256: str | None = None
    image_tree_sha256: str | None = None
    ordered_dimensions_sha256: str | None = None
    total_image_bytes: int | None = None
    image_count_distribution: Mapping[int, int] | None = None
    answer_counts: Mapping[str, int] | None = None
    question_type_counts: Mapping[str, int] | None = None


OFFICIAL_EXPECTATIONS = DatasetExpectations(
    row_count=1_000,
    image_count=2_550,
    min_images_per_question=2,
    max_images_per_question=10,
    source_jsonl_sha256=OFFICIAL_SOURCE_JSONL_SHA256,
    metadata_sha256=OFFICIAL_METADATA_SHA256,
    image_tree_sha256=OFFICIAL_IMAGE_TREE_SHA256,
    ordered_dimensions_sha256=OFFICIAL_ORDERED_DIMENSIONS_SHA256,
    total_image_bytes=OFFICIAL_IMAGE_BYTES,
    image_count_distribution=OFFICIAL_IMAGE_COUNT_DISTRIBUTION,
    answer_counts=OFFICIAL_ANSWER_COUNTS,
    question_type_counts=OFFICIAL_QUESTION_TYPE_COUNTS,
)


def sha256_file(path: os.PathLike[str] | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetValidationError(message)


def _check_optional_hash(name: str, value: str | None) -> None:
    if value is not None and not SHA256_RE.fullmatch(value):
        raise DatasetValidationError(f"{name} must be a lowercase SHA256 hex digest")


def parse_official_question(question: str) -> tuple[str, list[tuple[str, str]]]:
    """Split an official MMSI question into its stem and four labelled choices."""

    _require(isinstance(question, str) and question.strip() != "", "empty question")
    stem, separator, option_text = question.partition("Options:")
    _require(separator != "", "question is missing the exact 'Options:' delimiter")
    _require(stem.strip() != "", "question stem is empty")

    matches = OPTION_RE.findall(option_text.strip())
    choices = [
        (label, value.strip().rstrip(",;").strip()) for label, value in matches
    ]
    labels = [label for label, _ in choices]
    _require(labels == ["A", "B", "C", "D"], f"expected A-D choices, found {labels}")
    _require(all(value for _, value in choices), "one or more answer choices are empty")
    return stem.strip(), choices


def _normalise_id(value: object, expected_position: int) -> tuple[int, str]:
    if isinstance(value, bool):
        raise DatasetValidationError(f"row {expected_position}: boolean id is invalid")
    if isinstance(value, int):
        numeric_id = value
        source_id = f"mmsif_{value:04d}"
    elif isinstance(value, str) and re.fullmatch(r"mmsif_\d{4}", value):
        numeric_id = int(value.removeprefix("mmsif_"))
        source_id = value
    elif isinstance(value, str) and value.isdigit():
        numeric_id = int(value)
        source_id = f"mmsif_{numeric_id:04d}"
    else:
        raise DatasetValidationError(f"row {expected_position}: invalid id {value!r}")

    _require(
        numeric_id == expected_position,
        f"row order/id mismatch: position {expected_position}, id {numeric_id}",
    )
    return numeric_id, source_id


def _read_source_rows(source_jsonl: Path) -> list[dict]:
    rows: list[dict] = []
    with source_jsonl.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DatasetValidationError(
                    f"invalid JSON on source line {line_number}: {exc}"
                ) from exc
            _require(isinstance(value, dict), f"source line {line_number} is not an object")
            rows.append(value)
    return rows


def _metadata_sha256(rows: Sequence[dict]) -> str:
    """Return the path-independent digest matched against the official viewer."""

    digest = hashlib.sha256()
    for position, row in enumerate(rows):
        numeric_id, _ = _normalise_id(row.get("id"), position)
        images = row.get("images")
        _require(isinstance(images, list), f"row {position}: images is not a list")
        question_type = row.get("question_type", row.get("type"))
        payload = {
            "answer": str(row.get("answer", "")).strip(),
            "id": numeric_id,
            "images": len(images),
            "question": row.get("question"),
            "type": question_type,
        }
        digest.update(
            (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
                "utf-8"
            )
        )
    return digest.hexdigest()


def _tree_sha256(names: Iterable[str], file_hashes: Mapping[str, str]) -> str:
    """Hash GNU sha256sum-compatible manifest lines sorted by basename."""

    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(f"{file_hashes[name]}  {name}\n".encode("utf-8"))
    return digest.hexdigest()


def _ordered_dimensions_sha256(
    ordered_names: Sequence[tuple[int, Sequence[str]]], image_root: Path
) -> str:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised in the formal environment
        raise DatasetValidationError(
            "Pillow is required to validate the pinned ordered-dimensions hash"
        ) from exc

    digest = hashlib.sha256()
    for numeric_id, names in ordered_names:
        dimensions: list[list[int]] = []
        for name in names:
            try:
                with Image.open(image_root / name) as image:
                    dimensions.append([image.height, image.width])
            except Exception as exc:
                raise DatasetValidationError(f"cannot decode image {name}: {exc}") from exc
        payload = {"id": numeric_id, "dims": dimensions}
        digest.update(
            (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        )
    return digest.hexdigest()


def _atomic_json_dump(path: Path, value: object, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")

    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def prepare_mmsi_bench(
    source_jsonl: os.PathLike[str] | str,
    image_root: os.PathLike[str] | str,
    output_json: os.PathLike[str] | str,
    provenance_json: os.PathLike[str] | str,
    *,
    expectations: DatasetExpectations = OFFICIAL_EXPECTATIONS,
    overwrite: bool = False,
) -> dict:
    """Validate an MMSI snapshot, convert it, and return its provenance record."""

    for name in (
        expectations.source_jsonl_sha256,
        expectations.metadata_sha256,
        expectations.image_tree_sha256,
        expectations.ordered_dimensions_sha256,
    ):
        _check_optional_hash("expected hash", name)

    source_path = Path(source_jsonl).expanduser().absolute()
    root_path = Path(image_root).expanduser().absolute()
    output_path = Path(output_json).expanduser().absolute()
    provenance_path = Path(provenance_json).expanduser().absolute()

    _require(source_path.is_file(), f"source JSONL not found: {source_path}")
    _require(root_path.is_dir(), f"image root not found: {root_path}")
    _require(output_path != provenance_path, "output and provenance paths must differ")
    if not overwrite:
        for path in (output_path, provenance_path):
            if path.exists():
                raise FileExistsError(f"refusing to overwrite existing file: {path}")

    source_sha256 = sha256_file(source_path)
    if expectations.source_jsonl_sha256 is not None:
        _require(
            source_sha256 == expectations.source_jsonl_sha256,
            "source JSONL SHA256 mismatch: "
            f"expected {expectations.source_jsonl_sha256}, got {source_sha256}",
        )

    source_rows = _read_source_rows(source_path)
    _require(
        len(source_rows) == expectations.row_count,
        f"expected {expectations.row_count} rows, found {len(source_rows)}",
    )

    metadata_sha256 = _metadata_sha256(source_rows)
    if expectations.metadata_sha256 is not None:
        _require(
            metadata_sha256 == expectations.metadata_sha256,
            "official metadata SHA256 mismatch: "
            f"expected {expectations.metadata_sha256}, got {metadata_sha256}",
        )

    converted_rows: list[dict] = []
    ordered_names: list[tuple[int, list[str]]] = []
    referenced_names: list[str] = []
    image_count_distribution: collections.Counter[int] = collections.Counter()
    answer_counts: collections.Counter[str] = collections.Counter()
    question_type_counts: collections.Counter[str] = collections.Counter()

    for position, row in enumerate(source_rows):
        numeric_id, source_id = _normalise_id(row.get("id"), position)
        question_type = row.get("question_type", row.get("type"))
        _require(
            isinstance(question_type, str) and question_type.strip() != "",
            f"row {position}: missing question type",
        )

        original_question = row.get("question")
        stem, choices = parse_official_question(original_question)
        answer_letter = str(row.get("answer", "")).strip().upper()
        _require(answer_letter in "ABCD", f"row {position}: invalid answer {answer_letter!r}")
        if row.get("gt_answer") is not None:
            _require(
                str(row["gt_answer"]).strip().upper() == answer_letter,
                f"row {position}: answer and gt_answer disagree",
            )

        images = row.get("images")
        _require(isinstance(images, list), f"row {position}: images is not a list")
        _require(
            expectations.min_images_per_question
            <= len(images)
            <= expectations.max_images_per_question,
            f"row {position}: expected "
            f"{expectations.min_images_per_question}-{expectations.max_images_per_question} "
            f"images, found {len(images)}",
        )

        names: list[str] = []
        for image_position, reference in enumerate(images):
            _require(
                isinstance(reference, str) and reference.strip() != "",
                f"row {position} image {image_position}: invalid path",
            )
            basename = Path(reference).name
            expected_basename = f"{numeric_id:04d}_{image_position}.jpg"
            _require(
                basename == expected_basename,
                f"row {position} image order mismatch at position {image_position}: "
                f"expected {expected_basename}, found {basename}",
            )
            names.append(basename)

        labelled_choices = [f"{label}: {value}" for label, value in choices]
        choice_by_label = dict(zip((label for label, _ in choices), labelled_choices))
        absolute_image_paths = [str(root_path / name) for name in names]
        converted_rows.append(
            {
                "database_idx": numeric_id,
                "source_id": source_id,
                "dataset_id": OFFICIAL_DATASET_ID,
                "dataset_revision": OFFICIAL_DATASET_REVISION,
                "question_type": question_type,
                "question": stem,
                "original_question": original_question,
                "answer_choices": labelled_choices,
                "correct_answer": choice_by_label[answer_letter],
                "correct_answer_letter": answer_letter,
                "img_paths": absolute_image_paths,
                "official_image_order": names,
            }
        )
        ordered_names.append((numeric_id, names))
        referenced_names.extend(names)
        image_count_distribution[len(names)] += 1
        answer_counts[answer_letter] += 1
        question_type_counts[question_type] += 1

    _require(
        len(referenced_names) == expectations.image_count,
        f"expected {expectations.image_count} image references, found {len(referenced_names)}",
    )
    _require(
        len(set(referenced_names)) == len(referenced_names),
        "duplicate image basenames found in source image lists",
    )

    disk_names = sorted(path.name for path in root_path.iterdir() if path.is_file())
    referenced_set = set(referenced_names)
    disk_set = set(disk_names)
    missing_names = sorted(referenced_set - disk_set)
    extra_names = sorted(disk_set - referenced_set)
    _require(
        not missing_names,
        f"missing {len(missing_names)} referenced images; first: {missing_names[:5]}",
    )
    _require(
        not extra_names,
        f"found {len(extra_names)} unreferenced files in image root; first: {extra_names[:5]}",
    )

    file_hashes = {name: sha256_file(root_path / name) for name in disk_names}
    total_image_bytes = sum((root_path / name).stat().st_size for name in disk_names)
    image_tree_sha256 = _tree_sha256(disk_names, file_hashes)
    if expectations.total_image_bytes is not None:
        _require(
            total_image_bytes == expectations.total_image_bytes,
            "image byte count mismatch: "
            f"expected {expectations.total_image_bytes}, got {total_image_bytes}",
        )
    if expectations.image_tree_sha256 is not None:
        _require(
            image_tree_sha256 == expectations.image_tree_sha256,
            "image tree SHA256 mismatch: "
            f"expected {expectations.image_tree_sha256}, got {image_tree_sha256}",
        )

    ordered_reference_digest = hashlib.sha256()
    for numeric_id, names in ordered_names:
        for image_position, name in enumerate(names):
            ordered_reference_digest.update(
                f"{numeric_id}\t{image_position}\t{name}\t{file_hashes[name]}\n".encode(
                    "utf-8"
                )
            )
    ordered_reference_sha256 = ordered_reference_digest.hexdigest()

    ordered_dimensions_sha256: str | None = None
    if expectations.ordered_dimensions_sha256 is not None:
        ordered_dimensions_sha256 = _ordered_dimensions_sha256(ordered_names, root_path)
        _require(
            ordered_dimensions_sha256 == expectations.ordered_dimensions_sha256,
            "ordered image dimensions SHA256 mismatch: "
            f"expected {expectations.ordered_dimensions_sha256}, "
            f"got {ordered_dimensions_sha256}",
        )

    actual_image_distribution = dict(sorted(image_count_distribution.items()))
    actual_answer_counts = dict(sorted(answer_counts.items()))
    actual_question_type_counts = dict(sorted(question_type_counts.items()))
    if expectations.image_count_distribution is not None:
        _require(
            actual_image_distribution == dict(expectations.image_count_distribution),
            "image-count distribution mismatch",
        )
    if expectations.answer_counts is not None:
        _require(
            actual_answer_counts == dict(expectations.answer_counts),
            "answer-letter distribution mismatch",
        )
    if expectations.question_type_counts is not None:
        _require(
            actual_question_type_counts == dict(expectations.question_type_counts),
            "question-type distribution mismatch",
        )

    _atomic_json_dump(output_path, converted_rows, overwrite=overwrite)
    output_sha256 = sha256_file(output_path)
    provenance = {
        "schema_version": 1,
        "dataset": {
            "id": OFFICIAL_DATASET_ID,
            "revision": OFFICIAL_DATASET_REVISION,
            "split": OFFICIAL_DATASET_SPLIT,
            "rows": len(converted_rows),
            "question_type_counts": actual_question_type_counts,
            "answer_letter_counts": actual_answer_counts,
        },
        "official_code": {
            "repository": OFFICIAL_CODE_REPOSITORY,
            "revision": OFFICIAL_CODE_REVISION,
        },
        "source": {
            "jsonl": str(source_path),
            "sha256": source_sha256,
            "metadata_sha256": metadata_sha256,
        },
        "images": {
            "root": str(root_path),
            "count": len(referenced_names),
            "missing": 0,
            "extra": 0,
            "total_bytes": total_image_bytes,
            "per_question_min": min(image_count_distribution),
            "per_question_max": max(image_count_distribution),
            "count_distribution": actual_image_distribution,
            "tree_sha256": image_tree_sha256,
            "ordered_reference_sha256": ordered_reference_sha256,
            "ordered_dimensions_sha256": ordered_dimensions_sha256,
            "order_policy": "source images list order; never directory or lexical order",
        },
        "conversion": {
            "output_json": str(output_path),
            "output_sha256": output_sha256,
            "tool": str(Path(__file__).absolute()),
            "tool_sha256": sha256_file(__file__),
            "answer_policy": "retain labelled A-D choices and score correct_answer_letter",
        },
        "validation": {
            "status": "passed",
            "rows_expected": expectations.row_count,
            "images_expected": expectations.image_count,
        },
    }
    _atomic_json_dump(provenance_path, provenance, overwrite=overwrite)
    provenance["provenance_json"] = str(provenance_path)
    provenance["provenance_sha256"] = sha256_file(provenance_path)
    return provenance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-jsonl", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--provenance-json", required=True)
    parser.add_argument(
        "--expected-source-sha256",
        default=OFFICIAL_SOURCE_JSONL_SHA256,
        help="Pinned extracted JSONL hash (default: audited A100-2 snapshot)",
    )
    parser.add_argument(
        "--expected-image-tree-sha256",
        default=OFFICIAL_IMAGE_TREE_SHA256,
        help="Pinned basename-sorted image tree hash",
    )
    parser.add_argument("--force", action="store_true", help="replace existing outputs")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    expectations = dataclasses.replace(
        OFFICIAL_EXPECTATIONS,
        source_jsonl_sha256=args.expected_source_sha256,
        image_tree_sha256=args.expected_image_tree_sha256,
    )
    provenance = prepare_mmsi_bench(
        args.source_jsonl,
        args.image_root,
        args.output_json,
        args.provenance_json,
        expectations=expectations,
        overwrite=args.force,
    )
    print(
        json.dumps(
            {
                "status": provenance["validation"]["status"],
                "rows": provenance["dataset"]["rows"],
                "images": provenance["images"]["count"],
                "output_sha256": provenance["conversion"]["output_sha256"],
                "provenance_sha256": provenance["provenance_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
