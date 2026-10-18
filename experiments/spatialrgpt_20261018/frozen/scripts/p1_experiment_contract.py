#!/usr/bin/env python3
"""Fail closed on the user's original P1 matrix, independently of run names.

Only small JSON inputs are read. Never import ML packages or scan weights.
The older r8 worker and all its results remain immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_P1 = [
    "MMSI-Bench 1000 / Qwen3.5-27B",
    "MMSI-Bench 1000 / Qwen2.5-VL-72B-Instruct",
    "MindCube 1050 / Qwen3.5-9B",
    "MindCube 1050 / Qwen3.8-27B",
]
DATASETS = {
    "mmsi": {
        "models": ("Qwen/Qwen3.5-27B", "Qwen/Qwen2.5-VL-72B-Instruct"),
        "questions": 1000, "images": 10,
        "sha256": "5de75a94eebb2ad31b44ab0f33d7225c56157165292d8112e287c410f56180c9",
    },
    "mindcube": {
        "models": ("Qwen/Qwen3.5-9B", "Qwen/Qwen3.8-27B"),
        "questions": 1050, "images": 4,
        "sha256": "03a62d4928f790eb2dad9e18a9f5f65643342100b93955de80debea171e88083",
    },
}
SEARCH = dict(search_depth=3, beam_size=2, exploration_score_threshold=8,
              helpful_score_threshold=8, maximum_trajectory_length=8,
              primitive_repetitions_per_expansion=3,
              forward_primitive_meters=0.25, rotation_primitive_degrees=9)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(dataset, model, input_file, manifest, num_questions, max_images):
    require(dataset in DATASETS, "Unregistered dataset")
    spec = DATASETS[dataset]
    require(model in spec["models"], "Model/dataset is NOT in the user's P1 list")
    require(num_questions == spec["questions"], "Wrong formal question count")
    require(max_images == spec["images"], "Wrong maximum source image count")
    config = json.loads(Path(manifest).read_text())
    require(config["priority_1"] == EXPECTED_P1, "Manifest P1 matrix is wrong")
    require(config["paper_specified"] == SEARCH, "Paper search settings changed")
    require(config["models"][model]["dtype"] == "bfloat16", "BF16 required")
    require(config["models"][model]["enable_thinking"] is False, "No-thinking required")
    require(config["generation"]["context_limit"] == 65536, "Context must be 65536")
    require(config["generation"]["max_output_tokens"] == 8192,
            "User-requested maximum output must be 8192")
    input_file = Path(input_file)
    require(input_file.name == "test.json", "Official test split required")
    payload = input_file.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    require(digest == spec["sha256"], "Input is NOT the audited dataset snapshot")
    rows = json.loads(payload)
    require(len(rows) == num_questions, "Input length mismatch")
    ids = [r.get("eval_id", r["database_idx"]) for r in rows]
    require(len(set(ids)) == num_questions, "Duplicate question IDs")
    require(max(len(r["img_paths"]) for r in rows) == max_images, "Image count mismatch")
    for i, row in enumerate(rows):
        require(row["database_idx"] == i, "Source row order changed")
        if dataset == "mmsi":
            require(row["dataset_id"] == "RunsenXu/MMSI-Bench", "Not MMSI data")
            require([Path(p).name for p in row["img_paths"]] == row["official_image_order"],
                    "MMSI image order mismatch")
        else:
            require(row["question_type"] in ("among", "around", "rotation"),
                    "Not MindCube tinybench data")
            require([Path(p).name for p in row["img_paths"]] ==
                    [Path(p).name for p in row["source_images"]], "MindCube image order mismatch")
    return dict(status="passed", dataset=dataset, model=model,
                questions=num_questions, max_images=max_images, input_sha256=digest)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("dataset", "model", "input-file", "manifest"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--num-questions", type=int, required=True)
    p.add_argument("--max-images", type=int, required=True)
    args = vars(p.parse_args())
    try:
        print(json.dumps(validate(**args), sort_keys=True))
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit("P1 CONTRACT REJECTED: " + str(exc))


if __name__ == "__main__":
    main()
