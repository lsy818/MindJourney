#!/usr/bin/env python3
"""Copy the installed P1 environments to node-local storage; never install/import ML.

The shared COMPLETE identifies the already validated installation. Only small
launch scripts and internal absolute links are relocated; package binaries are
copied unchanged. A locked, per-user cache is published only after copy succeeds.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time

METADATA = ("COMPLETE", "VERSIONS.txt", "qwen.freeze.txt", "svc.freeze.txt")


def build_archive(local_root, source, archive, expected):
    """Publish once from an ALREADY complete local copy, as in the SAT runs."""
    local_root, source, archive = Path(local_root), Path(source).resolve(), Path(archive)
    record = json.loads((local_root / "LOCAL_READY.json").read_text())
    if record["source_complete_sha256"] != expected or record["source_root"] != str(source):
        raise RuntimeError("archive source is not the validated local installation")
    metadata = {name: digest(local_root / name) for name in METADATA}
    if metadata["COMPLETE"] != expected or metadata != {name: digest(source / name) for name in METADATA}:
        raise RuntimeError("archive source metadata mismatch")
    archive.parent.mkdir(parents=True, exist_ok=True)
    receipt = archive.with_name(archive.name + ".json")
    with archive.with_name(archive.name + ".lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if receipt.is_file() and archive.is_file():
            prior = json.loads(receipt.read_text())
            if prior["source_complete_sha256"] != expected or prior["metadata"] != metadata or prior["size_bytes"] != archive.stat().st_size:
                raise RuntimeError("existing archive has a different identity; do not overwrite")
            return archive
        temporary = archive.with_name(archive.name + f".partial.{os.getpid()}")
        print(f"Packing complete local dependencies: {local_root} -> {archive}", file=sys.stderr, flush=True)
        hasher = hashlib.sha256()
        with temporary.open("xb") as output:
            pack = subprocess.Popen(["tar", "-C", str(local_root), "-cf", "-", "qwen", "svc", *METADATA], stdout=subprocess.PIPE)
            compress = subprocess.Popen(["zstd", "-T4", "-3", "-c"], stdin=pack.stdout, stdout=subprocess.PIPE)
            pack.stdout.close()
            for block in iter(lambda: compress.stdout.read(4 * 1024**2), b""):
                output.write(block)
                hasher.update(block)
            compress.stdout.close()
            compressed_status, packed_status = compress.wait(), pack.wait()
        if compressed_status or packed_status:
            raise RuntimeError("environment archive creation failed; partial preserved")
        payload = {"source_root": str(source), "source_complete_sha256": expected,
                   "packed_root": str(local_root), "metadata": metadata,
                   "sha256": hasher.hexdigest(), "size_bytes": temporary.stat().st_size}
        temporary.replace(archive)
        pending = receipt.with_name(receipt.name + ".tmp")
        pending.write_text(json.dumps(payload, indent=2) + "\n")
        pending.replace(receipt)
        print(f"Environment archive ready: {archive}", file=sys.stderr, flush=True)
        return archive


def restore_archive(archive, root, source, expected):
    archive, root = Path(archive), Path(root)
    receipt = json.loads(archive.with_name(archive.name + ".json").read_text())
    if receipt["source_complete_sha256"] != expected or receipt["source_root"] != str(source):
        raise RuntimeError("archive environment identity mismatch")
    if receipt["metadata"] != {name: digest(source / name) for name in METADATA}:
        raise RuntimeError("archive metadata differs from installed environment")
    if archive.stat().st_size != receipt["size_bytes"]:
        raise RuntimeError("incomplete environment archive")
    local_archive = root.parent / (root.name + ".tar.zst.partial")
    print(f"Copying single environment archive to node: {archive}", file=sys.stderr, flush=True)
    hasher = hashlib.sha256()
    with archive.open("rb") as src, local_archive.open("wb") as dst:
        for block in iter(lambda: src.read(4 * 1024**2), b""):
            dst.write(block)
            hasher.update(block)
    if hasher.hexdigest() != receipt["sha256"]:
        raise RuntimeError("copied archive checksum mismatch; partial preserved")
    extracted = Path(tempfile.mkdtemp(prefix=root.name + ".extract.", dir=root.parent))
    unpack = subprocess.Popen(["zstd", "-dc", str(local_archive)], stdout=subprocess.PIPE)
    extract = subprocess.run(["tar", "-C", str(extracted), "-xf", "-"], stdin=unpack.stdout)
    unpack.stdout.close()
    if unpack.wait() or extract.returncode:
        raise RuntimeError("archive extraction failed; partial preserved")
    for name in METADATA:
        if digest(extracted / name) != receipt["metadata"][name]:
            raise RuntimeError("extracted environment metadata mismatch")
    # Keep old interrupted loose-file copies, but never overwrite a ready env.
    if root.exists():
        root.rename(root.with_name(root.name + f".partial-preserved.{time.time_ns()}"))
    extracted.rename(root)
    relocate(root, receipt["packed_root"])
    local_archive.unlink()  # Only the verified temporary transport copy.
    return receipt["sha256"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relocate(root, source):
    changes = []
    old, new = str(source).encode(), str(root).encode()
    for env in ("qwen", "svc"):
        for path in (root / env / "bin").iterdir():
            if path.is_symlink() or not path.is_file():
                continue
            with path.open("rb") as f:
                if not f.read(2) == b"#!":
                    continue
                f.seek(0)
                before = f.read()
            after = before.replace(old, new)
            if after != before:
                path.write_bytes(after)
                changes.append(str(path.relative_to(root)))
    return changes


def copy_tree(source, target, workers=8):
    """Bounded parallel file copies avoid serial NFS metadata latency."""
    pending = set()
    copied = 0
    last_report = time.monotonic()

    def copy_link(src, dst):
        link = os.readlink(src)
        prefix = str(source) + "/"
        if link.startswith(prefix):
            link = str(target) + link[len(str(source)):]
        if not dst.is_symlink() or os.readlink(dst) != link:
            if dst.exists() and not dst.is_symlink():
                raise RuntimeError(f"refusing to replace non-link {dst}")
            if dst.is_symlink():
                dst.unlink()
            dst.symlink_to(link)

    def copy_one(src, dst):
        # File metadata must be fetched by workers too: a serial lstat per
        # file otherwise recreates the NFS import bottleneck during copying.
        if src.is_symlink():
            copy_link(src, dst)
            return
        info = src.stat()
        if dst.is_file() and not dst.is_symlink():
            current = dst.stat()
            if current.st_size == info.st_size and current.st_mtime_ns == info.st_mtime_ns:
                return
        if dst.is_symlink():
            dst.unlink()
        # Replace atomically so interrupted copies never look complete.
        temporary = dst.with_name(dst.name + ".p1-copy-partial")
        shutil.copyfile(src, temporary)
        os.chmod(temporary, stat.S_IMODE(info.st_mode))
        os.utime(temporary, ns=(info.st_atime_ns, info.st_mtime_ns))
        os.replace(temporary, dst)

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for folder, dirs, files in os.walk(source, followlinks=False):
            src_dir = Path(folder)
            dst_dir = target / src_dir.relative_to(source)
            dst_dir.mkdir(parents=True, exist_ok=True)
            for name in list(dirs):
                src, dst = src_dir / name, dst_dir / name
                if src.is_symlink():
                    copy_link(src, dst)
                    dirs.remove(name)
            for name in files:
                pending.add(pool.submit(copy_one, src_dir / name, dst_dir / name))
                if len(pending) >= workers * 4:
                    done, pending = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
                    for result in done:
                        result.result()
                    copied += len(done)
                    if time.monotonic() - last_report >= 30:
                        print(f"Local copy {source.name}: {copied} files processed", file=sys.stderr, flush=True)
                        last_report = time.monotonic()
        for result in cf.as_completed(pending):
            result.result()


def stage(source, parent, expected, workers=8, seed=None, min_free_gib=60, archive=None):
    source = Path(source).resolve(strict=True)
    if digest(source / "COMPLETE") != expected:
        raise RuntimeError("source COMPLETE differs from the submitted installation")
    parent = Path(parent)
    if parent.is_symlink():
        raise RuntimeError("node-local cache parent must not be a symlink")
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = parent.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError("node-local cache must be private and owned by this user")
    root = parent / ("env-" + expected)
    marker = root / "LOCAL_READY.json"
    with (parent / (expected + ".lock")).open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if marker.is_file():
            record = json.loads(marker.read_text())
            if record.get("source_complete_sha256") != expected or record.get("source_root") != str(source):
                raise RuntimeError("local installation identity mismatch")
            for name in METADATA:
                if digest(root / name) != digest(source / name):
                    raise RuntimeError(f"local metadata differs: {name}")
            print(f"Reusing local dependencies: {root}", file=sys.stderr, flush=True)
            return root
        if shutil.disk_usage(parent).free < min_free_gib * 1024**3:
            raise RuntimeError("insufficient node-local space for dependency copy")
        if seed and not root.exists():
            seed = Path(seed)
            if seed.is_symlink() or seed.stat().st_uid != os.getuid() or (seed / "LOCAL_READY.json").exists():
                raise RuntimeError("invalid partial-copy seed")
            # Seed is a previously interrupted copy made for this task.
            seed.rename(root)
        root.mkdir(mode=0o700, exist_ok=True)
        print(f"Preparing installed dependencies at {root}", file=sys.stderr, flush=True)
        start = time.monotonic()
        archive_sha256 = None
        if archive is not None:
            archive_sha256 = restore_archive(archive, root, source, expected)
        else:
            # Legacy API for already-running copies; new CLI uses an archive.
            for env in ("qwen", "svc"):
                copy_tree(source / env, root / env, workers)
            for name in METADATA:
                shutil.copyfile(source / name, root / name)
        changes = relocate(root, source)
        record = {"source_root": str(source), "source_complete_sha256": expected,
                  "local_root": str(root), "host": os.uname().nodename,
                  "relocated_launchers": changes, "copy_seconds": round(time.monotonic() - start, 2)}
        record["archive_sha256"] = archive_sha256
        temporary = root / "LOCAL_READY.json.tmp"
        temporary.write_text(json.dumps(record, indent=2) + "\n")
        temporary.replace(marker)
        print(f"Local dependencies ready in {record['copy_seconds']}s: {root}", file=sys.stderr, flush=True)
        return root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--parent", default=f"/dev/shm/mj-p1-{os.getuid()}")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed")
    parser.add_argument("--archive", help="published SAT-style tar.zst transport archive")
    parser.add_argument("--build-archive-from", help="publish from this already-ready node-local environment")
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("dependency copies must run in a Slurm allocation")
    archive = args.archive or str(Path(args.source).parent / "archives" / (args.expected_sha256 + ".tar.zst"))
    if args.build_archive_from:
        print(build_archive(args.build_archive_from, args.source, archive, args.expected_sha256))
        return
    if not 1 <= args.workers <= 16:
        raise SystemExit("workers must be between 1 and 16")
    # Reject NFS and noexec destinations before copying anything.
    import subprocess
    mount = subprocess.check_output(["findmnt", "-n", "-T", str(Path(args.parent).parent), "-o", "FSTYPE,OPTIONS"], text=True)
    fs_type, options = mount.split(maxsplit=1)
    if fs_type not in ("tmpfs", "xfs", "ext4", "btrfs") or "noexec" in options.strip().split(","):
        raise SystemExit("dependency cache requires executable node-local storage")
    print(stage(args.source, args.parent, args.expected_sha256, args.workers, args.seed, archive=archive))


if __name__ == "__main__":
    main()
