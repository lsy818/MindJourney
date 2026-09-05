#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
source "$script_dir/p1_model_registry.sh"

if (( $# < 1 || $# > 2 )); then
  echo "Usage: $0 MODEL_ALIAS [--submit]" >&2
  exit 2
fi
p1_load_model_spec "$1"
do_submit=0
if (( $# == 2 )); then
  if [[ "$2" != "--submit" ]]; then
    echo "The only optional argument is --submit." >&2
    exit 2
  fi
  do_submit=1
fi

model_root="${P1_MODEL_ROOT:-/home/datasets/chentao/models}"
cache_root="${P1_CACHE_ROOT:-/home/datasets/shiyang/model_cache}"
validation_root="${P1_MODEL_VALIDATION_ROOT:-/home/datasets/shiyang/model_validation}"
hf_python="${P1_HF_PYTHON:-python}"
token_path="${HF_TOKEN_PATH:-}"
job_prolog="${P1_JOB_PROLOG:-$repo_dir/scripts/p1_env_prolog.sh}"
trust_existing="${P1_TRUST_EXISTING_MODEL:-0}"
log_root="${P1_PREFETCH_LOG_ROOT:-/home/datasets/shiyang/model_download_logs}"
if [[ "$trust_existing" != "0" && "$trust_existing" != "1" ]]; then
  echo "P1_TRUST_EXISTING_MODEL must be 0 or 1." >&2
  exit 2
fi
for value in "$repo_dir" "$model_root" "$cache_root" "$validation_root" \
    "$hf_python" "$token_path" "$job_prolog" "$log_root"; do
  if [[ "$value" == *","* || "$value" == *$'\n'* ]]; then
    echo "Slurm export values cannot contain commas or newlines." >&2
    exit 2
  fi
done

export_spec="P1_REPO_DIR=$repo_dir,P1_MODEL_KEY=$P1_SPEC_ALIAS,P1_MODEL_ROOT=$model_root,P1_CACHE_ROOT=$cache_root,P1_MODEL_VALIDATION_ROOT=$validation_root,P1_HF_PYTHON=$hf_python,P1_TRUST_EXISTING_MODEL=$trust_existing"
if [[ -n "$token_path" ]]; then
  export_spec+=",HF_TOKEN_PATH=$token_path"
fi
if [[ -n "$job_prolog" ]]; then
  export_spec+=",P1_JOB_PROLOG=$job_prolog"
fi
command=(
  sbatch --parsable
  --account=daai
  --partition=short
  --exclude=hkbugpudgx01
  --job-name="mj-fetch-$P1_SPEC_ALIAS"
  --output="$log_root/%x-%j.out"
  --error="$log_root/%x-%j.err"
  --export="$export_spec"
  "$script_dir/p1_prefetch_model.sbatch"
)

printf 'model=%s\nrevision=%s\ntarget=%s/%s\ncommand=' \
  "$P1_SPEC_MODEL_ID" "$P1_SPEC_REVISION" "$model_root" "$P1_SPEC_MODEL_DIR"
printf '%q ' "${command[@]}"
printf '\n'
if (( do_submit == 0 )); then
  echo "Dry run only; add --submit to enqueue the pinned download."
  exit 0
fi
target="$model_root/$P1_SPEC_MODEL_DIR"
if [[ ! -d "$target" ]]; then
  echo "The target owner must pre-create a writable directory before submission: $target" >&2
  exit 1
fi
mkdir -p "$log_root"
response="$("${command[@]}")"
job_id="${response%%;*}"
if [[ ! "$job_id" =~ ^[0-9]+$ ]]; then
  echo "Unexpected sbatch response: $response" >&2
  exit 1
fi
printf 'Submitted %s download as Slurm job %s.\n' "$P1_SPEC_MODEL_ID" "$job_id"
