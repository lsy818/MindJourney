#!/usr/bin/env python3
"""Fail-closed validation for a prepared MindJourney benchmark split."""

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_FIELDS = (
    "database_idx",
    "question_type",
    "question",
    "answer_choices",
    "correct_answer",
    "img_paths",
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--expected-questions", type=int, required=True)
    parser.add_argument("--max-images", type=int, required=True)
    parser.add_argument("--allow-subset", action="store_true")
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    args = parse_args()
    if args.expected_questions <= 0:
        raise SystemExit("--expected-questions must be positive")
    if not 1 <= args.max_images <= 48:
        raise SystemExit("--max-images must be in [1, 48]")

    input_file = args.input_dir / f"{args.split}.json"
    if not input_file.is_file():
        raise SystemExit(f"prepared split does not exist: {input_file}")
    with input_file.open(encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list) or not records:
        raise SystemExit("prepared split must be a non-empty top-level JSON list")
    if args.allow_subset:
        if args.expected_questions > len(records):
            raise SystemExit(
                f"requested {args.expected_questions} questions, but split has {len(records)}"
            )
    elif len(records) != args.expected_questions:
        raise SystemExit(
            f"formal run expects exactly {args.expected_questions} records; found {len(records)}"
        )

    repo_root = args.repo_root.resolve()
    seen_ids = set()
    observed_max_images = 0
    for row_number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise SystemExit(f"record {row_number} is not an object")
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            raise SystemExit(f"record {row_number} is missing fields: {', '.join(missing)}")

        record_id = record.get("eval_id", record["database_idx"])
        if record_id in seen_ids:
            raise SystemExit(f"duplicate effective question ID: {record_id!r}")
        seen_ids.add(record_id)

        choices = record["answer_choices"]
        if not isinstance(choices, list) or len(choices) < 2:
            raise SystemExit(f"record {row_number} must have at least two answer choices")
        image_paths = record["img_paths"]
        if not isinstance(image_paths, list) or not image_paths:
            raise SystemExit(f"record {row_number} has no ordered img_paths list")
        if len(image_paths) > args.max_images:
            raise SystemExit(
                f"record {row_number} has {len(image_paths)} images, above --max-images={args.max_images}"
            )
        observed_max_images = max(observed_max_images, len(image_paths))
        for image_number, raw_path in enumerate(image_paths, start=1):
            if not isinstance(raw_path, str) or not raw_path:
                raise SystemExit(
                    f"record {row_number} image {image_number} is not a path string"
                )
            image_path = Path(raw_path)
            if not image_path.is_absolute():
                image_path = repo_root / image_path
            if not image_path.is_file():
                raise SystemExit(
                    f"record {row_number} image {image_number} is missing: {raw_path}"
                )

    print(
        json.dumps(
            {
                "input_file": str(input_file.resolve()),
                "sha256": sha256_file(input_file),
                "records": len(records),
                "max_images": observed_max_images,
                "order_check": "img_paths validated in stored order; no sorting performed",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
