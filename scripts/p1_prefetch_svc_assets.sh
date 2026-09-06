#!/usr/bin/env bash
set -euo pipefail

# Keep shared cache entries readable by the DAAI experiment group.
umask 0007

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if (( $# != 1 )); then
  echo "Usage: $0 /absolute/P1_CACHE_ROOT" >&2
  exit 2
fi
cache_root="$1"
if [[ "$cache_root" != /* || "$cache_root" == "/" || "$cache_root" == *$'\n'* ]]; then
  echo "P1_CACHE_ROOT must be a safe absolute path other than /." >&2
  exit 2
fi
hf_python="${P1_HF_PYTHON:-python}"
if [[ "$hf_python" == *$'\n'* || ! -x "$hf_python" ]]; then
  echo "P1_HF_PYTHON must be an executable path." >&2
  exit 2
fi
if [[ -z "${HF_TOKEN:-}" && -n "${HF_TOKEN_PATH:-}" ]]; then
  if [[ ! -r "$HF_TOKEN_PATH" ]]; then
    echo "HF_TOKEN_PATH is not readable." >&2
    exit 1
  fi
  export HF_TOKEN="$(tr -d '\r\n' <"$HF_TOKEN_PATH")"
fi

# This is the networked population phase.  Formal P1 array jobs take the
# separate validate-only path and force these switches back to offline mode.
unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE HF_DATASETS_OFFLINE
export HF_HOME="$cache_root/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false

exec "$hf_python" "$script_dir/p1_svc_assets.py" prefetch \
  --cache-root "$cache_root" \
  --workers "${P1_DOWNLOAD_WORKERS:-4}"
