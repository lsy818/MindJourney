#!/usr/bin/env python3
"""Create a provenance-bound, one-record P1 smoke-test split.

The selected prepared record is copied without changing its field or image
ordering.  Existing output files are never replaced unless ``--force`` is
explicitly supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class SmokeSubsetError(ValueError):
    """Raised when a smoke subset cannot be created safely."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json_bytes(path: Path, description: str) -> tuple[Any, bytes]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise SmokeSubsetError(f"cannot read {description} {path}: {exc}") from exc
    try:
        return json.loads(payload.decode("utf-8")), payload
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeSubsetError(f"{description} is not valid UTF-8 JSON: {path}") from exc


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: bytes, *, overwrite: bool) -> None:
    """Atomically publish *payload*, with an atomic no-clobber default."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        if overwrite:
            os.replace(temporary_path, path)
        else:
            # Linking a fully written temporary file publishes it atomically and
            # fails with EEXIST instead of racing into an accidental overwrite.
            try:
                os.link(temporary_path, path)
            except FileExistsError as exc:
                raise SmokeSubsetError(
                    f"refusing to overwrite existing output: {path}; use --force"
                ) from exc
            temporary_path.unlink()
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _resolve_file(path: Path, description: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_file():
        raise SmokeSubsetError(f"{description} does not exist or is not a file: {path}")
    return expanded.resolve()


def _find_parent_provenance(input_file: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return _resolve_file(explicit, "parent provenance")

    candidates = [
        candidate
        for candidate in (
            input_file.parent / "test_provenance.json",
            input_file.parent / "provenance.json",
        )
        if candidate.is_file()
    ]
    if len(candidates) != 1:
        found = ", ".join(str(path) for path in candidates) or "none"
        raise SmokeSubsetError(
            "could not identify exactly one parent provenance file "
            f"(found: {found}); pass --parent-provenance explicitly"
        )
    return candidates[0].resolve()


def _record_id(record: dict[str, Any]) -> tuple[str, str | int]:
    field = "eval_id" if "eval_id" in record else "database_idx"
    if field not in record:
        raise SmokeSubsetError("selected record has neither eval_id nor database_idx")
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise SmokeSubsetError(f"selected record has invalid {field}: {value!r}")
    if isinstance(value, str) and not value:
        raise SmokeSubsetError(f"selected record has empty {field}")
    return field, value


def _source_id(record: dict[str, Any], effective_id: str | int) -> tuple[str, str | int]:
    if "source_id" in record:
        field = "source_id"
    elif "id" in record:
        field = "id"
    else:
        field = "effective_id"
    value = effective_id if field == "effective_id" else record[field]
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise SmokeSubsetError(f"selected record has invalid {field}: {value!r}")
    if isinstance(value, str) and not value:
        raise SmokeSubsetError(f"selected record has empty {field}")
    return field, value


def make_smoke_subset(
    *,
    input_file: Path,
    output_dir: Path,
    record_index: int,
    parent_provenance: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Write a one-record ``test.json`` and its provenance sidecar."""

    if isinstance(record_index, bool) or not isinstance(record_index, int):
        raise SmokeSubsetError("record index must be an integer")
    if record_index < 0:
        raise SmokeSubsetError("record index must be non-negative")

    input_file = _resolve_file(input_file, "parent test JSON")
    provenance_file = _find_parent_provenance(input_file, parent_provenance)
    if provenance_file == input_file:
        raise SmokeSubsetError("parent provenance and parent test JSON must differ")

    output_dir = output_dir.expanduser().resolve()
    output_file = output_dir / "test.json"
    output_provenance = output_dir / "test_provenance.json"
    protected_inputs = {input_file, provenance_file}
    if output_file in protected_inputs or output_provenance in protected_inputs:
        raise SmokeSubsetError("output directory would overwrite a parent input")

    if not force:
        existing = [path for path in (output_file, output_provenance) if path.exists()]
        if existing:
            rendered = ", ".join(str(path) for path in existing)
            raise SmokeSubsetError(
                f"refusing to overwrite existing output: {rendered}; use --force"
            )

    records, parent_bytes = _read_json_bytes(input_file, "parent test JSON")
    if not isinstance(records, list) or not records:
        raise SmokeSubsetError("parent test JSON must be a non-empty top-level list")
    if record_index >= len(records):
        raise SmokeSubsetError(
            f"record index {record_index} is out of range for {len(records)} records"
        )

    record = records[record_index]
    if not isinstance(record, dict):
        raise SmokeSubsetError(f"record at index {record_index} is not an object")
    effective_id_field, effective_id = _record_id(record)
    source_id_field, source_id = _source_id(record, effective_id)
    image_paths = record.get("img_paths")
    if not isinstance(image_paths, list) or not image_paths:
        raise SmokeSubsetError("selected record must have a non-empty img_paths list")
    if any(not isinstance(path, str) or not path for path in image_paths):
        raise SmokeSubsetError("selected record contains an invalid img_paths entry")

    parent_provenance_value, parent_provenance_bytes = _read_json_bytes(
        provenance_file, "parent provenance"
    )
    if not isinstance(parent_provenance_value, dict):
        raise SmokeSubsetError("parent provenance must be a top-level JSON object")

    subset_bytes = _json_bytes([record])
    subset_sha256 = _sha256(subset_bytes)
    provenance = {
        "schema_version": 1,
        "kind": "p1_smoke_subset",
        "parent": {
            "test_json_path": str(input_file),
            "test_json_sha256": _sha256(parent_bytes),
            "provenance_path": str(provenance_file),
            "provenance_sha256": _sha256(parent_provenance_bytes),
        },
        "selection": {
            "record_index": record_index,
            "effective_id_field": effective_id_field,
            "effective_id": effective_id,
            "source_id_field": source_id_field,
            "source_id": source_id,
            "image_count": len(image_paths),
        },
        "subset": {
            "test_json_path": str(output_file),
            "test_json_sha256": subset_sha256,
            "records": 1,
        },
    }
    provenance_bytes = _json_bytes(provenance)

    _atomic_write(output_file, subset_bytes, overwrite=force)
    if sha256_file(output_file) != subset_sha256:
        raise SmokeSubsetError(f"published subset checksum mismatch: {output_file}")
    _atomic_write(output_provenance, provenance_bytes, overwrite=force)

    return provenance


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-file", type=Path, help="Prepared parent test.json")
    source.add_argument(
        "--input-dir", type=Path, help="Prepared parent directory containing test.json"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--record-index", type=int, required=True)
    parser.add_argument(
        "--parent-provenance",
        type=Path,
        help="Parent provenance JSON; otherwise auto-detect a unique sibling sidecar",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_file = args.input_file or (args.input_dir / "test.json")
    try:
        provenance = make_smoke_subset(
            input_file=input_file,
            output_dir=args.output_dir,
            record_index=args.record_index,
            parent_provenance=args.parent_provenance,
            force=args.force,
        )
    except (SmokeSubsetError, OSError) as exc:
        raise SystemExit(f"p1_make_smoke_subset: {exc}") from exc
    print(json.dumps(provenance, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
