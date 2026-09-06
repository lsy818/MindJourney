#!/usr/bin/env bash
#SBATCH --account=daai
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=1-00:00:00
#SBATCH --no-requeue

set -euo pipefail
umask 0007
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

repo_dir="${P1_REPO_DIR:?P1_REPO_DIR is required}"
cache_root="${P1_CACHE_ROOT:?P1_CACHE_ROOT is required}"
hf_python="${P1_HF_PYTHON:?P1_HF_PYTHON is required}"
if [[ "$repo_dir" != /* || ! -d "$repo_dir/scripts" ]]; then
  echo "P1_REPO_DIR must identify an absolute MindJourney checkout." >&2
  exit 2
fi
if [[ "$cache_root" != /* || "$cache_root" == "/" ]]; then
  echo "P1_CACHE_ROOT must be a safe absolute path other than /." >&2
  exit 2
fi
if [[ "$hf_python" != /* || ! -x "$hf_python" ]]; then
  echo "P1_HF_PYTHON must be an executable absolute path." >&2
  exit 2
fi
if [[ "${P1_ALLOW_NETWORK:-1}" != "1" ]]; then
  echo "The SVC prefetch job requires P1_ALLOW_NETWORK=1." >&2
  exit 2
fi

exec "$repo_dir/scripts/p1_prefetch_svc_assets.sh" "$cache_root"
