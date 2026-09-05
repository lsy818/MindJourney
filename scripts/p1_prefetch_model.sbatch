#!/usr/bin/env bash
#SBATCH --account=daai
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=5-00:00:00
#SBATCH --no-requeue

set -euo pipefail
umask 0007
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

repo_dir="${P1_REPO_DIR:?P1_REPO_DIR is required}"
if [[ -n "${P1_JOB_PROLOG:-}" ]]; then
  if [[ "$P1_JOB_PROLOG" != /* || ! -r "$P1_JOB_PROLOG" ]]; then
    echo "P1_JOB_PROLOG must be a readable absolute path." >&2
    exit 2
  fi
  source "$P1_JOB_PROLOG"
fi
exec "$repo_dir/scripts/p1_prefetch_model.sh" \
  "${P1_MODEL_KEY:?P1_MODEL_KEY is required}"
