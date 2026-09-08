#!/usr/bin/env python3
"""Prefetch and strictly validate the immutable SVC Hugging Face assets.

The formal P1 jobs are intentionally offline.  This utility is the only
networked path used to populate their shared Hugging Face cache.  A COMPLETE
marker is published only after every required file can be resolved from that
cache with ``local_files_only=True`` and all three pinned weight digests match.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import pathlib
import re
import sys
from collections.abc import Iterable, Sequence
from typing import Any, Protocol


FORMAT = "mindjourney-p1-svc-assets-v1"
STATE_DIRECTORY = pathlib.PurePosixPath("mindjourney", "svc-assets-v1")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"[0-9a-f]{40}")
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EMPTY_ASSET_IDENTITY = (
    "stabilityai/stable-virtual-camera",
    "e538e251c1009e9a41cf8b7fee5f21332a1960de",
    "config.yaml",
)


@dataclasses.dataclass(frozen=True)
class AssetSpec:
    name: str
    repo_id: str
    revision: str
    filename: str
    expected_sha256: str | None = None
    allow_empty: bool = False


# These values intentionally mirror scripts/p1_persistent_env_prolog.sh.
# tests/test_p1_svc_assets.py prevents either copy from drifting silently.
ASSETS: tuple[AssetSpec, ...] = (
    AssetSpec(
        name="svc_config",
        repo_id="stabilityai/stable-virtual-camera",
        revision="e538e251c1009e9a41cf8b7fee5f21332a1960de",
        filename="config.yaml",
        expected_sha256=EMPTY_SHA256,
        allow_empty=True,
    ),
    AssetSpec(
        name="svc_weights",
        repo_id="stabilityai/stable-virtual-camera",
        revision="e538e251c1009e9a41cf8b7fee5f21332a1960de",
        filename="model.safetensors",
        expected_sha256="10e69ea003c313e6bdfc7ee40376d1c19ea6036c20bd384e94b483dec8350396",
    ),
    AssetSpec(
        name="vae_config",
        repo_id="sd2-community/stable-diffusion-2-1-base",
        revision="4e63672c03103b6c636b8fb4119ba982469b2955",
        filename="vae/config.json",
    ),
    AssetSpec(
        name="vae_weights",
        repo_id="sd2-community/stable-diffusion-2-1-base",
        revision="4e63672c03103b6c636b8fb4119ba982469b2955",
        filename="vae/diffusion_pytorch_model.safetensors",
        expected_sha256="a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815",
    ),
    AssetSpec(
        name="openclip_weights",
        repo_id="laion/CLIP-ViT-H-14-laion2B-s32B-b79K",
        revision="1c2b8495b28150b8a4922ee1c8edee224c284c0c",
        filename="open_clip_pytorch_model.bin",
        expected_sha256="9a78ef8e8c73fd0df621682e7a8e8eb36c6916cb3c16b291a082ecd52ab79cc4",
    ),
)

ENVIRONMENT_EXPECTATIONS = {
    "SVC_REVISION": ASSETS[0].revision,
    "SVC_WEIGHT_SHA256": ASSETS[1].expected_sha256,
    "SVC_VAE_REPO": ASSETS[2].repo_id,
    "SVC_VAE_REVISION": ASSETS[2].revision,
    "SVC_VAE_SUBFOLDER": "vae",
    "SVC_VAE_SHA256": ASSETS[3].expected_sha256,
    "SVC_OPENCLIP_REPO": ASSETS[4].repo_id,
    "SVC_OPENCLIP_REVISION": ASSETS[4].revision,
    "SVC_OPENCLIP_FILENAME": ASSETS[4].filename,
    "SVC_OPENCLIP_SHA256": ASSETS[4].expected_sha256,
}


class HubApi(Protocol):
    __version__: str

    def snapshot_download(self, **kwargs: Any) -> str: ...

    def hf_hub_download(self, **kwargs: Any) -> str: ...


class AssetValidationError(RuntimeError):
    """The cache cannot prove that it contains the pinned SVC assets."""


def _hub_api() -> HubApi:
    try:
        import huggingface_hub
    except ImportError as error:  # pragma: no cover - exercised by the CLI
        raise AssetValidationError(
            "huggingface_hub is required to prefetch or validate SVC assets"
        ) from error
    return huggingface_hub  # type: ignore[return-value]


def _canonical_root(cache_root: os.PathLike[str] | str) -> pathlib.Path:
    root = pathlib.Path(cache_root)
    if not root.is_absolute() or root == pathlib.Path("/"):
        raise AssetValidationError("cache root must be an absolute path other than /")
    return root.resolve(strict=False)


def _paths(cache_root: os.PathLike[str] | str) -> tuple[pathlib.Path, ...]:
    root = _canonical_root(cache_root)
    state = root.joinpath(*STATE_DIRECTORY.parts)
    return root, root / "huggingface" / "hub", state, state / "manifest.json", state / "COMPLETE"


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write(path: pathlib.Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o660,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            try:
                os.fsync(directory_descriptor)
            except OSError as error:
                # Some shared/NFS mounts do not implement directory fsync;
                # the same-filesystem os.replace above remains atomic there.
                if error.errno not in (errno.EINVAL, errno.ENOTSUP):
                    raise
        finally:
            os.close(directory_descriptor)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _parse_complete(path: pathlib.Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise AssetValidationError(f"missing regular completion marker: {path}")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            raise AssetValidationError(f"malformed completion marker: {path}")
        key, value = line.split("=", 1)
        if key in values or not key or not value:
            raise AssetValidationError(f"malformed completion marker: {path}")
        values[key] = value
    if set(values) != {"format", "manifest_sha256"}:
        raise AssetValidationError(f"unexpected completion marker fields: {path}")
    if values["format"] != FORMAT or not SHA256_RE.fullmatch(
        values["manifest_sha256"]
    ):
        raise AssetValidationError(f"invalid completion marker: {path}")
    return values


def _check_environment(specs: Sequence[AssetSpec]) -> None:
    if specs != ASSETS:
        return
    for variable, expected in ENVIRONMENT_EXPECTATIONS.items():
        actual = os.environ.get(variable)
        if actual is not None and actual != expected:
            raise AssetValidationError(
                f"{variable} disagrees with the pinned SVC asset registry"
            )


def _validate_specs(specs: Sequence[AssetSpec]) -> None:
    if not specs:
        raise AssetValidationError("SVC asset registry must not be empty")
    names: set[str] = set()
    identities: set[tuple[str, str, str]] = set()
    for spec in specs:
        identity = (spec.repo_id, spec.revision, spec.filename)
        filename = pathlib.PurePosixPath(spec.filename)
        if not spec.name or spec.name in names:
            raise AssetValidationError("SVC asset names must be non-empty and unique")
        if identity in identities:
            raise AssetValidationError("SVC asset identities must be unique")
        if not REVISION_RE.fullmatch(spec.revision):
            raise AssetValidationError(f"revision must be a 40-character commit for {spec.name}")
        if filename.is_absolute() or ".." in filename.parts or not filename.name:
            raise AssetValidationError(f"unsafe Hugging Face filename for {spec.name}")
        if spec.expected_sha256 is not None and not SHA256_RE.fullmatch(
            spec.expected_sha256
        ):
            raise AssetValidationError(f"invalid pinned SHA256 for {spec.name}")
        if not isinstance(spec.allow_empty, bool):
            raise AssetValidationError(f"allow_empty must be boolean for {spec.name}")
        if spec.allow_empty and (
            identity != EMPTY_ASSET_IDENTITY
            or spec.expected_sha256 != EMPTY_SHA256
        ):
            raise AssetValidationError(
                "only the pinned upstream stable-virtual-camera config may be empty"
            )
        names.add(spec.name)
        identities.add(identity)


def _validate_payload(payload: Any, specs: Sequence[AssetSpec], hub_cache: pathlib.Path) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {
        "format",
        "generated_utc",
        "huggingface_hub_version",
        "hub_cache_dir",
        "assets",
    }:
        raise AssetValidationError("SVC asset manifest has an unexpected schema")
    if payload["format"] != FORMAT:
        raise AssetValidationError("SVC asset manifest format is unsupported")
    if payload["hub_cache_dir"] != str(hub_cache):
        raise AssetValidationError("SVC asset manifest belongs to another cache root")
    if not isinstance(payload["generated_utc"], str) or not payload[
        "generated_utc"
    ].endswith("Z"):
        raise AssetValidationError("SVC asset manifest has an invalid timestamp")
    if not isinstance(payload["huggingface_hub_version"], str) or not payload[
        "huggingface_hub_version"
    ]:
        raise AssetValidationError("SVC asset manifest has no hub client version")
    assets = payload["assets"]
    if not isinstance(assets, list) or len(assets) != len(specs):
        raise AssetValidationError("SVC asset manifest has the wrong asset count")
    required_record_keys = {
        "name",
        "repo_id",
        "revision",
        "filename",
        "cache_path",
        "size_bytes",
        "sha256",
        "allow_empty",
    }
    for spec, record in zip(specs, assets):
        if not isinstance(record, dict) or set(record) != required_record_keys:
            raise AssetValidationError(f"invalid manifest record for {spec.name}")
        for key in ("name", "repo_id", "revision", "filename"):
            if record[key] != getattr(spec, key):
                raise AssetValidationError(f"manifest identity mismatch for {spec.name}")
        if record["allow_empty"] is not spec.allow_empty:
            raise AssetValidationError(f"manifest empty-file policy mismatch for {spec.name}")
        if type(record["size_bytes"]) is not int or record["size_bytes"] < 0:
            raise AssetValidationError(f"invalid recorded size for {spec.name}")
        if record["size_bytes"] == 0 and not spec.allow_empty:
            raise AssetValidationError(f"unexpected empty asset in manifest for {spec.name}")
        if not isinstance(record["sha256"], str) or not SHA256_RE.fullmatch(
            record["sha256"]
        ):
            raise AssetValidationError(f"invalid recorded SHA256 for {spec.name}")
        if spec.expected_sha256 and record["sha256"] != spec.expected_sha256:
            raise AssetValidationError(f"pinned SHA256 mismatch in manifest for {spec.name}")
        cache_path = record["cache_path"]
        if not isinstance(cache_path, str) or not cache_path or cache_path.startswith("/"):
            raise AssetValidationError(f"invalid cache path for {spec.name}")
    return assets


def _resolve_records(
    root: pathlib.Path,
    hub_cache: pathlib.Path,
    specs: Sequence[AssetSpec],
    api: HubApi,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in specs:
        try:
            resolved_value = api.hf_hub_download(
                repo_id=spec.repo_id,
                revision=spec.revision,
                filename=spec.filename,
                cache_dir=str(hub_cache),
                local_files_only=True,
            )
        except Exception as error:
            raise AssetValidationError(
                f"{spec.name} is not locally resolvable at revision {spec.revision}"
            ) from error
        logical_path = pathlib.Path(resolved_value)
        if not logical_path.is_absolute():
            logical_path = (pathlib.Path.cwd() / logical_path).absolute()
        if logical_path.is_symlink() and not logical_path.exists():
            raise AssetValidationError(f"broken cache link for {spec.name}")
        if not logical_path.is_file():
            raise AssetValidationError(f"missing cached file for {spec.name}")
        try:
            cache_path = logical_path.relative_to(root)
            logical_path.resolve(strict=True).relative_to(root)
        except ValueError as error:
            raise AssetValidationError(
                f"resolved file for {spec.name} escapes the selected cache root"
            ) from error
        size_bytes = logical_path.stat().st_size
        if size_bytes == 0 and not spec.allow_empty:
            raise AssetValidationError(f"cached file is empty for {spec.name}")
        digest = _sha256_file(logical_path)
        if spec.expected_sha256 and digest != spec.expected_sha256:
            raise AssetValidationError(
                f"SHA256 mismatch for {spec.name}: expected {spec.expected_sha256}, got {digest}"
            )
        if spec.name == "vae_config":
            try:
                config = json.loads(logical_path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AssetValidationError("VAE config is not valid JSON") from error
            if not isinstance(config, dict) or not config:
                raise AssetValidationError("VAE config must be a non-empty JSON object")
        records.append(
            {
                "name": spec.name,
                "repo_id": spec.repo_id,
                "revision": spec.revision,
                "filename": spec.filename,
                "cache_path": cache_path.as_posix(),
                "size_bytes": size_bytes,
                "sha256": digest,
                "allow_empty": spec.allow_empty,
            }
        )
    return records


def _validate_unlocked(
    root: pathlib.Path,
    hub_cache: pathlib.Path,
    manifest_path: pathlib.Path,
    complete_path: pathlib.Path,
    specs: Sequence[AssetSpec],
    api: HubApi,
) -> dict[str, Any]:
    complete = _parse_complete(complete_path)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise AssetValidationError(f"missing regular SVC asset manifest: {manifest_path}")
    actual_manifest_sha256 = _sha256_file(manifest_path)
    if complete["manifest_sha256"] != actual_manifest_sha256:
        raise AssetValidationError("SVC asset manifest SHA256 does not match COMPLETE")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AssetValidationError("SVC asset manifest is not valid JSON") from error
    manifest_records = _validate_payload(payload, specs, hub_cache)
    resolved_records = _resolve_records(root, hub_cache, specs, api)
    if resolved_records != manifest_records:
        raise AssetValidationError("cached SVC assets do not match their signed manifest")
    _check_environment(specs)
    return payload


def validate_cache(
    cache_root: os.PathLike[str] | str,
    *,
    specs: Sequence[AssetSpec] = ASSETS,
    api: HubApi | None = None,
) -> dict[str, Any]:
    _validate_specs(specs)
    root, hub_cache, state, manifest_path, complete_path = _paths(cache_root)
    lock_path = state / ".lock"
    if not state.is_dir() or not lock_path.is_file():
        raise AssetValidationError(f"SVC asset cache has no completion state under {state}")
    active_api = api or _hub_api()
    with lock_path.open("rb") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_SH)
        return _validate_unlocked(
            root,
            hub_cache,
            manifest_path,
            complete_path,
            specs,
            active_api,
        )


def _startup_record(root, hub_cache, manifest_path, complete_path, specs):
    """Read the existing full-validation receipt and stat only required files.

    This is deliberately not a content-integrity scan. The user authorizes
    trusting unchanged, previously validated assets during routine startup.
    Changes to identity, size or timestamps fall back to a full offline scan.
    """
    complete = _parse_complete(complete_path)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise AssetValidationError("missing regular SVC asset manifest")
    if _sha256_file(manifest_path) != complete["manifest_sha256"]:
        raise AssetValidationError("manifest differs from full-validation receipt")
    payload = json.loads(manifest_path.read_text())
    records = _validate_payload(payload, specs, hub_cache)
    validated_at = dt.datetime.fromisoformat(payload["generated_utc"].replace("Z", "+00:00")).timestamp()
    # Legacy receipts have second precision; allow that rounding only.
    for record in records:
        relative = pathlib.PurePosixPath(record["cache_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise AssetValidationError("unsafe recorded asset path")
        path = root / relative
        try:
            path.resolve(strict=True).relative_to(root)
            info = path.stat()
        except (OSError, ValueError) as error:
            raise AssetValidationError("required SVC asset missing or outside cache") from error
        if not path.is_file() or info.st_size != record["size_bytes"]:
            raise AssetValidationError("required SVC asset missing or changed size")
        if max(info.st_mtime, info.st_ctime) >= validated_at + 1:
            raise AssetValidationError("SVC asset changed since full validation")
    _check_environment(specs)
    return payload


def startup_cache(cache_root, *, specs=ASSETS, api=None):
    """Fast unchanged-cache path; on a miss fully validate offline and renew."""
    _validate_specs(specs)
    _check_environment(specs)
    root, hub_cache, state, manifest_path, complete_path = _paths(cache_root)
    state.mkdir(parents=True, exist_ok=True)
    lock_path = state / ".lock"
    lock_path.touch(mode=0o660, exist_ok=True)
    with lock_path.open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        try:
            return _startup_record(root, hub_cache, manifest_path, complete_path, specs)
        except (AssetValidationError, OSError, ValueError, TypeError):
            pass
    with lock_path.open("r+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return _startup_record(root, hub_cache, manifest_path, complete_path, specs)
        except (AssetValidationError, OSError, ValueError, TypeError):
            pass
        print("SVC receipt missing or assets changed; full offline validation required.", file=sys.stderr)
        active_api = api or _hub_api()
        records = _resolve_records(root, hub_cache, specs, active_api)
        payload = {
            "format": FORMAT,
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "huggingface_hub_version": str(active_api.__version__),
            "hub_cache_dir": str(hub_cache), "assets": records,
        }
        content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
        _atomic_write(manifest_path, content)
        _atomic_write(complete_path, (f"format={FORMAT}\nmanifest_sha256={hashlib.sha256(content).hexdigest()}\n").encode())
        return payload


def _download_groups(specs: Iterable[AssetSpec]) -> dict[tuple[str, str], list[str]]:
    groups: dict[tuple[str, str], list[str]] = {}
    for spec in specs:
        groups.setdefault((spec.repo_id, spec.revision), []).append(spec.filename)
    # Fetch public dependencies first.  The Stability AI repository may be
    # gated, so a missing token must not discard useful VAE/OpenCLIP progress.
    return dict(
        sorted(
            groups.items(),
            key=lambda item: (
                item[0][0] == "stabilityai/stable-virtual-camera",
                item[0][0],
            ),
        )
    )


def prefetch_cache(
    cache_root: os.PathLike[str] | str,
    *,
    workers: int = 4,
    token: str | None = None,
    specs: Sequence[AssetSpec] = ASSETS,
    api: HubApi | None = None,
) -> dict[str, Any]:
    if workers < 1 or workers > 32:
        raise AssetValidationError("workers must be in [1, 32]")
    _validate_specs(specs)
    root, hub_cache, state, manifest_path, complete_path = _paths(cache_root)
    root.mkdir(parents=True, exist_ok=True)
    hub_cache.mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True)
    lock_path = state / ".lock"
    lock_path.touch(mode=0o660, exist_ok=True)
    active_api = api or _hub_api()
    # Linux/NFS requires a write-capable descriptor for LOCK_EX; a read-only
    # descriptor can raise EBADF even though macOS accepts it.
    with lock_path.open("r+b") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        try:
            return _validate_unlocked(
                root,
                hub_cache,
                manifest_path,
                complete_path,
                specs,
                active_api,
            )
        except AssetValidationError:
            pass

        for (repo_id, revision), filenames in _download_groups(specs).items():
            try:
                active_api.snapshot_download(
                    repo_id=repo_id,
                    revision=revision,
                    cache_dir=str(hub_cache),
                    allow_patterns=filenames,
                    max_workers=workers,
                    token=token,
                )
            except Exception as error:
                raise AssetValidationError(
                    f"download failed for {repo_id} at revision {revision}; "
                    "already cached public assets were preserved"
                ) from error

        records = _resolve_records(root, hub_cache, specs, active_api)
        _check_environment(specs)
        payload: dict[str, Any] = {
            "format": FORMAT,
            "generated_utc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "huggingface_hub_version": str(active_api.__version__),
            "hub_cache_dir": str(hub_cache),
            "assets": records,
        }
        manifest_bytes = (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        ).encode("utf-8")
        _atomic_write(manifest_path, manifest_bytes)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        complete_bytes = (
            f"format={FORMAT}\nmanifest_sha256={manifest_sha256}\n"
        ).encode("utf-8")
        _atomic_write(complete_path, complete_bytes)
        return _validate_unlocked(
            root,
            hub_cache,
            manifest_path,
            complete_path,
            specs,
            active_api,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prefetch = subparsers.add_parser("prefetch", help="download and validate assets")
    prefetch.add_argument("--cache-root", required=True)
    prefetch.add_argument("--workers", type=int, default=4)
    validate = subparsers.add_parser("validate", help="strictly validate offline cache")
    validate.add_argument("--cache-root", required=True)
    validate.add_argument("--quiet", action="store_true")
    validate.add_argument("--startup", action="store_true", help="reuse unchanged full-validation receipt; scan only on change")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prefetch":
            payload = prefetch_cache(
                args.cache_root,
                workers=args.workers,
                token=os.environ.get("HF_TOKEN") or None,
            )
            print(
                f"SVC assets are complete: {len(payload['assets'])} files at "
                f"{_canonical_root(args.cache_root)}"
            )
        else:
            payload = (startup_cache if args.startup else validate_cache)(args.cache_root)
            if not args.quiet:
                print(
                    f"SVC asset cache is valid: {len(payload['assets'])} files at "
                    f"{_canonical_root(args.cache_root)}"
                )
    except AssetValidationError as error:
        print(f"SVC asset cache validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
