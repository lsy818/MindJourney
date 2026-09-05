#!/usr/bin/env bash
#SBATCH --account=daai
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=160G
#SBATCH --time=5-00:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@300

set -euo pipefail
umask 077
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"

repo_dir="${P1_REPO_DIR:?P1_REPO_DIR is required}"
if [[ "$repo_dir" != /* || ! -d "$repo_dir" ]]; then
  echo "P1_REPO_DIR must be an existing absolute directory." >&2
  exit 2
fi
if [[ -n "${P1_JOB_PROLOG:-}" ]]; then
  if [[ "$P1_JOB_PROLOG" != /* || ! -r "$P1_JOB_PROLOG" ]]; then
    echo "P1_JOB_PROLOG must be a readable absolute path." >&2
    exit 2
  fi
  source "$P1_JOB_PROLOG"
fi

chunk_index="${SLURM_ARRAY_TASK_ID:-0}"
exec "$repo_dir/scripts/p1_run_chunk.sh" \
  "${P1_MODEL_KEY:?P1_MODEL_KEY is required}" "$chunk_index"
