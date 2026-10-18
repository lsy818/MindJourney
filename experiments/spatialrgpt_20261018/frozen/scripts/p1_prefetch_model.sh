#!/usr/bin/env bash
set -euo pipefail
# Shared model directories are group-owned (2770); downloaded files must stay
# readable by both the download account and the experiment account.
umask 0007

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/p1_model_registry.sh"

if (( $# != 1 )); then
  echo "Usage: $0 MODEL_ALIAS" >&2
  exit 2
fi
p1_load_model_spec "$1"

model_root="${P1_MODEL_ROOT:-/home/datasets/chentao/models}"
target="$model_root/$P1_SPEC_MODEL_DIR"
cache_root="${P1_CACHE_ROOT:-/home/datasets/shiyang/model_cache}"
validation_root="${P1_MODEL_VALIDATION_ROOT:-/home/datasets/shiyang/model_validation}"
external_marker="$validation_root/${P1_SPEC_MODEL_DIR}.revision"
hf_python="${P1_HF_PYTHON:-python}"
mkdir -p "$cache_root/huggingface" "$validation_root"
export HF_HOME="${HF_HOME:-$cache_root/huggingface}"
export HF_HUB_DISABLE_TELEMETRY=1
if [[ -z "${HF_TOKEN:-}" && -n "${HF_TOKEN_PATH:-}" ]]; then
  if [[ ! -r "$HF_TOKEN_PATH" ]]; then
    echo "HF_TOKEN_PATH is not readable: $HF_TOKEN_PATH" >&2
    exit 1
  fi
  export HF_TOKEN="$(tr -d '\r\n' <"$HF_TOKEN_PATH")"
fi

validate_snapshot() {
  "$hf_python" - "$1" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
config = root / "config.json"
if not config.is_file():
    raise SystemExit(f"missing {config}")
index = root / "model.safetensors.index.json"
single = root / "model.safetensors"
if index.is_file():
    payload = json.loads(index.read_text())
    shards = sorted(set(payload.get("weight_map", {}).values()))
    if not shards:
        raise SystemExit(f"empty weight map in {index}")
    missing = [name for name in shards if not (root / name).is_file()]
    if missing:
        raise SystemExit(f"missing {len(missing)} model shards; first: {missing[0]}")
elif not single.is_file():
    raise SystemExit("missing model.safetensors or model.safetensors.index.json")
PY
}

write_external_marker() {
  marker_tmp="$external_marker.tmp.$$"
  printf '%s\n' "$P1_SPEC_REVISION" >"$marker_tmp"
  mv -- "$marker_tmp" "$external_marker"
}

if [[ ! -d "$target" ]]; then
  printf 'Target must be pre-created by its owner because %s is not writable by the download account: %s\n' \
    "$model_root" "$target" >&2
  exit 1
fi

if validate_snapshot "$target" 2>/dev/null; then
    found_marker=""
    for marker in "$target/.mindjourney_revision" "$target/revision.txt" "$external_marker"; do
      if [[ -r "$marker" ]]; then
        found_marker="$marker"
        break
      fi
    done
    if [[ -n "$found_marker" ]]; then
      recorded_revision="$(sed -n '1{s/[[:space:]]//g;p;}' "$found_marker")"
      if [[ "$recorded_revision" != "$P1_SPEC_REVISION" ]]; then
        printf 'Existing snapshot marker is %s, expected %s.\n' \
          "$recorded_revision" "$P1_SPEC_REVISION" >&2
        exit 1
      fi
      echo "$P1_SPEC_MODEL_ID at $P1_SPEC_REVISION is already complete: $target"
      exit 0
    fi
    if [[ "${P1_TRUST_EXISTING_MODEL:-0}" != "1" ]]; then
      printf 'A structurally complete but unpinned directory exists at %s; verifying it against the pinned Hub revision before writing a marker.\n' \
        "$target" >&2
    else
      write_external_marker
      echo "Recorded the verified existing revision in $external_marker."
      exit 0
    fi
fi

if [[ ! -w "$target" ]]; then
  echo "Incomplete target is not writable by this account: $target" >&2
  exit 1
fi
exec {download_lock_fd}>"$target/.p1_download.lock"
if command -v flock >/dev/null 2>&1; then
  flock "$download_lock_fd"
fi
# A concurrent/resumed downloader may have completed before this process took
# the lock.  Validate again before contacting Hugging Face.
if validate_snapshot "$target" 2>/dev/null; then
  if [[ "${P1_TRUST_EXISTING_MODEL:-0}" == "1" ]]; then
    write_external_marker
    echo "Recorded the verified existing revision in $external_marker."
    exit 0
  fi
  echo "Snapshot became structurally complete but remains unpinned; verifying the full pinned Hub snapshot." >&2
fi

export P1_DOWNLOAD_REPO_ID="$P1_SPEC_MODEL_ID"
export P1_DOWNLOAD_REVISION="$P1_SPEC_REVISION"
export P1_DOWNLOAD_TARGET="$target"
export P1_DOWNLOAD_WORKERS="${P1_DOWNLOAD_WORKERS:-4}"
export P1_DOWNLOAD_ATTEMPTS="${P1_DOWNLOAD_ATTEMPTS:-1}"
export P1_DOWNLOAD_RETRY_DELAY_SECONDS="${P1_DOWNLOAD_RETRY_DELAY_SECONDS:-60}"
"$hf_python" - <<'PY'
import os
import sys
import time

from huggingface_hub import snapshot_download

attempts = int(os.environ["P1_DOWNLOAD_ATTEMPTS"])
base_delay = int(os.environ["P1_DOWNLOAD_RETRY_DELAY_SECONDS"])
if attempts < 1 or base_delay < 0:
    raise SystemExit("P1_DOWNLOAD_ATTEMPTS must be >= 1 and retry delay must be >= 0")

for attempt in range(1, attempts + 1):
    try:
        snapshot_download(
            repo_id=os.environ["P1_DOWNLOAD_REPO_ID"],
            revision=os.environ["P1_DOWNLOAD_REVISION"],
            local_dir=os.environ["P1_DOWNLOAD_TARGET"],
            max_workers=int(os.environ["P1_DOWNLOAD_WORKERS"]),
            token=os.environ.get("HF_TOKEN") or None,
        )
        break
    except Exception as exc:
        if attempt == attempts:
            raise
        delay = min(base_delay * attempt, 300)
        print(
            f"Snapshot attempt {attempt}/{attempts} failed with "
            f"{type(exc).__name__}; retrying the preserved partial download "
            f"in {delay}s.",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(delay)
PY

validate_snapshot "$target"
write_external_marker
echo "Downloaded and pinned $P1_SPEC_MODEL_ID at $P1_SPEC_REVISION to $target."
