#!/usr/bin/env bash
set -euo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
source "$script_dir/p1_model_registry.sh"

usage() {
  cat >&2 <<'USAGE'
Usage:
  p1_submit.sh --mode smoke|array --model MODEL_ALIAS --dataset mindcube|mmsi \
    --accelerator h20|a100 --input-dir DIR --split train|val|test \
    --runtime-root DIR [--provenance FILE] [--max-images N] \
    [--num-questions N] [--num-chunks N] \
    [--max-concurrent N] [--array SPEC] [--model-path DIR] \
    [--svc-python PATH] [--vllm-bin PATH] [--job-prolog PATH] \
    [--persistent-env-root DIR] \
    [--run-id ID] [--resume] [--submit]

The default is a read-only dry run.  H20 is the default accelerator; use
--accelerator a100 only for the A100-80 fallback (the 40 GB DGX is excluded).
USAGE
}

mode="array"
model_key=""
dataset=""
accelerator="h20"
input_dir=""
split="test"
runtime_root=""
dataset_provenance=""
max_images=""
num_questions=""
num_chunks=""
max_concurrent=""
array_spec=""
model_path=""
svc_python="${P1_SVC_PYTHON:-python}"
vllm_bin="${P1_VLLM_BIN:-vllm}"
job_prolog="${P1_JOB_PROLOG:-$repo_dir/scripts/p1_env_prolog.sh}"
job_prolog_explicit=0
if [[ -n "${P1_JOB_PROLOG:-}" ]]; then
  job_prolog_explicit=1
fi
persistent_env_root="${P1_PERSISTENT_ENV_ROOT:-}"
run_id=""
resume=0
do_submit=0

while (( $# > 0 )); do
  case "$1" in
    --mode) mode="${2:?missing value for --mode}"; shift 2 ;;
    --model) model_key="${2:?missing value for --model}"; shift 2 ;;
    --dataset) dataset="${2:?missing value for --dataset}"; shift 2 ;;
    --accelerator) accelerator="${2:?missing value for --accelerator}"; shift 2 ;;
    --input-dir) input_dir="${2:?missing value for --input-dir}"; shift 2 ;;
    --split) split="${2:?missing value for --split}"; shift 2 ;;
    --runtime-root) runtime_root="${2:?missing value for --runtime-root}"; shift 2 ;;
    --provenance) dataset_provenance="${2:?missing value for --provenance}"; shift 2 ;;
    --max-images) max_images="${2:?missing value for --max-images}"; shift 2 ;;
    --num-questions) num_questions="${2:?missing value for --num-questions}"; shift 2 ;;
    --num-chunks) num_chunks="${2:?missing value for --num-chunks}"; shift 2 ;;
    --max-concurrent) max_concurrent="${2:?missing value for --max-concurrent}"; shift 2 ;;
    --array) array_spec="${2:?missing value for --array}"; shift 2 ;;
    --model-path) model_path="${2:?missing value for --model-path}"; shift 2 ;;
    --svc-python) svc_python="${2:?missing value for --svc-python}"; shift 2 ;;
    --vllm-bin) vllm_bin="${2:?missing value for --vllm-bin}"; shift 2 ;;
    --job-prolog) job_prolog="${2:?missing value for --job-prolog}"; job_prolog_explicit=1; shift 2 ;;
    --persistent-env-root) persistent_env_root="${2:?missing value for --persistent-env-root}"; shift 2 ;;
    --run-id) run_id="${2:?missing value for --run-id}"; shift 2 ;;
    --resume) resume=1; shift ;;
    --submit) do_submit=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done
if [[ -n "$persistent_env_root" && "$job_prolog_explicit" == "0" ]]; then
  job_prolog="$repo_dir/scripts/p1_persistent_env_prolog.sh"
fi

if [[ -z "$model_key" || -z "$dataset" || -z "$input_dir" || -z "$runtime_root" ]]; then
  usage
  exit 2
fi
p1_load_model_spec "$model_key"
p1_load_resource_plan "$accelerator"
p1_assert_priority_one_combo "$dataset"
if [[ "$P1_SPEC_DIAGNOSTIC_ONLY" == "1" ]]; then
  echo "The A100 40 GB profile is non-Slurm diagnostic-smoke only; use p1_run_local_diagnostic_smoke.sh." >&2
  exit 2
fi

if [[ "$mode" != "smoke" && "$mode" != "array" ]]; then
  echo "--mode must be smoke or array." >&2
  exit 2
fi
if [[ "$split" != "train" && "$split" != "val" && "$split" != "test" ]]; then
  echo "--split must be train, val, or test." >&2
  exit 2
fi
if [[ "$input_dir" != /* || "$runtime_root" != /* ]]; then
  echo "--input-dir and --runtime-root must be absolute paths." >&2
  exit 2
fi
if [[ -n "$persistent_env_root" && "$persistent_env_root" != /* ]]; then
  echo "--persistent-env-root must be an absolute path." >&2
  exit 2
fi

input_file="$input_dir/$split.json"
if [[ -z "$dataset_provenance" ]]; then
  if [[ -r "$input_dir/${split}_provenance.json" ]]; then
    dataset_provenance="$input_dir/${split}_provenance.json"
  else
    dataset_provenance="$input_dir/provenance.json"
  fi
fi
if [[ -z "$num_questions" || -z "$max_images" ]]; then
  if [[ ! -r "$input_file" ]]; then
    echo "Read $input_file or supply both --num-questions and --max-images for a dry run." >&2
    exit 1
  fi
  input_summary="$(python3 -c 'import json,sys; rows=json.load(open(sys.argv[1])); assert isinstance(rows,list) and rows; print(len(rows), max(len(row.get("img_paths") or []) for row in rows))' "$input_file")"
  read -r detected_questions detected_max_images <<<"$input_summary"
  num_questions="${num_questions:-$detected_questions}"
  max_images="${max_images:-$detected_max_images}"
fi
if [[ ! "$num_questions" =~ ^[1-9][0-9]*$ ]]; then
  echo "--num-questions must be a positive integer." >&2
  exit 2
fi
if [[ ! "$max_images" =~ ^[1-9][0-9]*$ ]] || (( max_images > 48 )); then
  echo "--max-images must be an integer in [1, 48]." >&2
  exit 2
fi

source_questions="$num_questions"
if [[ "$mode" == "smoke" ]]; then
  effective_questions=1
  effective_chunks=1
  array_spec="0"
  max_concurrent=1
  time_limit="08:00:00"
else
  effective_questions="$num_questions"
  if [[ "$dataset" == "mindcube" && "$effective_questions" != "1050" ]]; then
    echo "Formal MindCube P1 arrays require exactly 1050 prepared records." >&2
    exit 2
  fi
  if [[ "$dataset" == "mmsi" && "$effective_questions" != "1000" ]]; then
    echo "Formal MMSI-Bench P1 arrays require exactly 1000 prepared records." >&2
    exit 2
  fi
  if [[ "$dataset" == "mindcube" ]]; then
    default_chunks=11
  else
    default_chunks=10
  fi
  effective_chunks="${num_chunks:-$default_chunks}"
  if [[ ! "$effective_chunks" =~ ^[1-9][0-9]*$ \
        || "$effective_chunks" -gt "$effective_questions" ]]; then
    echo "--num-chunks must be a positive integer no larger than the question count." >&2
    exit 2
  fi
  array_spec="${array_spec:-0-$((effective_chunks - 1))}"
  max_concurrent="${max_concurrent:-$P1_SPEC_DEFAULT_CONCURRENCY}"
  time_limit="5-00:00:00"
fi

if [[ ! "$max_concurrent" =~ ^[1-9][0-9]*$ \
      || "$max_concurrent" -gt "$P1_SPEC_DEFAULT_CONCURRENCY" ]]; then
  printf -- '--max-concurrent must be in [1, %s] for the stable %s/%s plan.\n' \
    "$P1_SPEC_DEFAULT_CONCURRENCY" "$P1_SPEC_MODEL_ID" "$accelerator" >&2
  exit 2
fi
if [[ ! "$array_spec" =~ ^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$ ]]; then
  echo "--array must be a Slurm index/range list such as 0-20 or 1,3." >&2
  exit 2
fi

if [[ -z "$run_id" ]]; then
  run_id="mj-p1-${dataset}-${P1_SPEC_ALIAS}-${mode}-$(date -u +%Y%m%dT%H%M%SZ)"
fi
if [[ ! "$run_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]]; then
  echo "--run-id must contain 1-80 safe filename characters." >&2
  exit 2
fi
run_root="$runtime_root/$run_id"
model_path="${model_path:-${P1_MODEL_ROOT:-/home/datasets/chentao/models}/$P1_SPEC_MODEL_DIR}"
cache_root="${P1_CACHE_ROOT:-/home/datasets/shiyang/model_cache}"
validation_root="${P1_MODEL_VALIDATION_ROOT:-/home/datasets/shiyang/model_validation}"
experiment_manifest="$repo_dir/configs/p1_svc_multiimage.json"

source_sha256="$(
  python3 "$repo_dir/utils/p1_fingerprints.py" source --repo-root "$repo_dir"
)"
file_sha256() {
  python3 - "$1" <<'PY'
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
print(digest.hexdigest())
PY
}
input_sha256="unavailable"
provenance_sha256="unavailable"
manifest_sha256="unavailable"
model_tree_manifest="unavailable"
model_tree_sha256="unavailable"
if [[ -r "$input_file" ]]; then
  input_sha256="$(file_sha256 "$input_file")"
fi
if [[ -r "$dataset_provenance" ]]; then
  provenance_sha256="$(file_sha256 "$dataset_provenance")"
fi
if [[ -r "$experiment_manifest" ]]; then
  manifest_sha256="$(file_sha256 "$experiment_manifest")"
fi
model_tree_candidate="${P1_MODEL_TREE_MANIFEST:-$model_path/.cache/huggingface/trees/$P1_SPEC_REVISION.json}"
if [[ -n "${P1_MODEL_TREE_MANIFEST:-}" && ! -r "$model_tree_candidate" ]]; then
  echo "P1_MODEL_TREE_MANIFEST is not readable: $model_tree_candidate" >&2
  exit 1
fi
if [[ -r "$model_tree_candidate" ]]; then
  model_tree_manifest="$model_tree_candidate"
  model_tree_sha256="$(file_sha256 "$model_tree_manifest")"
fi

for export_value in "$repo_dir" "$input_dir" "$run_root" "$model_path" \
    "$cache_root" "$validation_root" "$dataset_provenance" \
    "$experiment_manifest" "$svc_python" "$vllm_bin" "$job_prolog" \
    "$model_tree_manifest"; do
  if [[ "$export_value" == *","* || "$export_value" == *$'\n'* ]]; then
    echo "Paths and commands passed through Slurm cannot contain commas or newlines." >&2
    exit 2
  fi
done
if [[ "$persistent_env_root" == *","* || "$persistent_env_root" == *$'\n'* ]]; then
  echo "Paths passed through Slurm cannot contain commas or newlines." >&2
  exit 2
fi

if [[ "$P1_SPEC_SIZE_CLASS" == "72b" ]]; then
  memory="240G"
else
  memory="160G"
fi
job_name="mj-p1-${dataset}-${P1_SPEC_ALIAS}-${mode}"
array_request="${array_spec}%${max_concurrent}"
export_spec="P1_REPO_DIR=$repo_dir,P1_MODEL_KEY=$P1_SPEC_ALIAS,P1_DATASET=$dataset,P1_ACCELERATOR=$accelerator,P1_RUN_MODE=$mode,P1_RUN_ID=$run_id,P1_RUN_ROOT=$run_root,P1_INPUT_DIR=$input_dir,P1_SPLIT=$split,P1_NUM_QUESTIONS=$effective_questions,P1_NUM_CHUNKS=$effective_chunks,P1_MAX_IMAGES=$max_images,P1_MODEL_PATH=$model_path,P1_CACHE_ROOT=$cache_root,P1_MODEL_VALIDATION_ROOT=$validation_root,P1_REQUIRE_REVISION_MARKER=1,P1_MANIFEST=$experiment_manifest,P1_DATASET_PROVENANCE=$dataset_provenance,P1_EXPECTED_INPUT_SHA256=$input_sha256,P1_EXPECTED_PROVENANCE_SHA256=$provenance_sha256,P1_EXPECTED_MANIFEST_SHA256=$manifest_sha256,P1_EXPECTED_SOURCE_SHA256=$source_sha256,P1_SVC_PYTHON=$svc_python,P1_VLLM_BIN=$vllm_bin,P1_ALLOW_NETWORK=0"
if [[ "$model_tree_sha256" != "unavailable" ]]; then
  export_spec+=",P1_MODEL_TREE_MANIFEST=$model_tree_manifest,P1_MODEL_TREE_SHA256=$model_tree_sha256"
fi
if [[ -n "$job_prolog" ]]; then
  export_spec+=",P1_JOB_PROLOG=$job_prolog"
fi
if [[ -n "$persistent_env_root" ]]; then
  export_spec+=",P1_PERSISTENT_ENV_ROOT=$persistent_env_root"
fi

sbatch_cmd=(
  sbatch --parsable
  --account=daai
  --partition=short
  --job-name="$job_name"
  --array="$array_request"
  --gres="$P1_SPEC_GRES"
  --cpus-per-task="$P1_SPEC_CPUS_PER_TASK"
  --mem="$memory"
  --time="$time_limit"
  --output="$run_root/logs/%x-%A_%a.out"
  --error="$run_root/logs/%x-%A_%a.err"
  --export="$export_spec"
)
if [[ -n "$P1_SPEC_EXCLUDE" ]]; then
  sbatch_cmd+=(--exclude="$P1_SPEC_EXCLUDE")
fi
sbatch_cmd+=("$script_dir/p1_array.sbatch")

p1_print_model_spec
printf '%s\n' \
  "mode=$mode" \
  "dataset=$dataset" \
  "input_file=$input_file" \
  "input_sha256=$input_sha256" \
  "dataset_provenance=$dataset_provenance" \
  "dataset_provenance_sha256=$provenance_sha256" \
  "experiment_manifest=$experiment_manifest" \
  "experiment_manifest_sha256=$manifest_sha256" \
  "model_tree_manifest=$model_tree_manifest" \
  "model_tree_sha256=$model_tree_sha256" \
  "source_sha256=$source_sha256" \
  "source_questions=$source_questions" \
  "run_questions=$effective_questions" \
  "num_chunks=$effective_chunks" \
  "array=$array_request" \
  "run_root=$run_root"
printf 'command='
printf '%q ' "${sbatch_cmd[@]}"
printf '\n'

if (( do_submit == 0 )); then
  echo "Dry run only; add --submit after reviewing this plan."
  exit 0
fi
if [[ ! -r "$input_file" ]]; then
  echo "Prepared split is unavailable: $input_file" >&2
  exit 1
fi
if [[ ! -r "$dataset_provenance" || ! -r "$experiment_manifest" ]]; then
  echo "Formal submission requires readable dataset provenance and experiment manifest files." >&2
  exit 1
fi
validation_args=(
  --input-dir "$input_dir"
  --split "$split"
  --repo-root "$repo_dir"
  --expected-questions "$effective_questions"
  --max-images "$max_images"
)
if [[ "$mode" == "smoke" ]]; then
  validation_args+=(--allow-subset)
fi
python3 "$script_dir/p1_validate_input.py" "${validation_args[@]}"
asset_validator_python="$svc_python"
if [[ -n "$persistent_env_root" \
      && -x "$persistent_env_root/svc/bin/python" ]]; then
  asset_validator_python="$persistent_env_root/svc/bin/python"
fi
resolved_asset_validator_python="$(command -v -- "$asset_validator_python" 2>/dev/null || true)"
if [[ -z "$resolved_asset_validator_python" \
      || ! -x "$resolved_asset_validator_python" ]]; then
  echo "SVC cache validator Python is not executable: $asset_validator_python" >&2
  exit 1
fi
"$resolved_asset_validator_python" "$script_dir/p1_svc_assets.py" validate \
  --cache-root "$cache_root" --quiet
if [[ ! -d "$model_path" || ! -r "$model_path/config.json" ]]; then
  printf 'Pinned local model is unavailable at %s (expected revision %s).\n' \
    "$model_path" "$P1_SPEC_REVISION" >&2
  exit 1
fi
revision_marker="$validation_root/${P1_SPEC_MODEL_DIR}.revision"
if [[ -r "$model_path/.mindjourney_revision" ]]; then
  revision_marker="$model_path/.mindjourney_revision"
elif [[ -r "$model_path/revision.txt" ]]; then
  revision_marker="$model_path/revision.txt"
fi
if [[ ! -r "$revision_marker" \
      || "$(sed -n '1{s/[[:space:]]//g;p;}' "$revision_marker")" != "$P1_SPEC_REVISION" ]]; then
  printf 'Missing or mismatched validated revision marker for %s; expected %s.\n' \
    "$model_path" "$P1_SPEC_REVISION" >&2
  exit 1
fi
if [[ -e "$run_root" && "$resume" != "1" ]]; then
  echo "Run already exists; use --resume with the same run ID to keep existing results." >&2
  exit 1
fi

manifest="$run_root/launch_manifest.txt"
if [[ -e "$run_root" ]]; then
  if [[ ! -r "$manifest" ]]; then
    echo "Existing run has no launch_manifest.txt; refusing ambiguous resume." >&2
    exit 1
  fi
  expected_resume_lines=(
    "run_id=$run_id"
    "dataset=$dataset"
    "model=$P1_SPEC_MODEL_ID"
    "revision=$P1_SPEC_REVISION"
    "accelerator=$accelerator"
    "input_sha256=$input_sha256"
    "source_sha256=$source_sha256"
    "dataset_provenance_sha256=$provenance_sha256"
    "experiment_manifest_sha256=$manifest_sha256"
    "num_questions=$effective_questions"
    "num_chunks=$effective_chunks"
    "persistent_environment_root=${persistent_env_root:-none}"
  )
  if [[ "$model_tree_sha256" != "unavailable" ]]; then
    expected_resume_lines+=("model_tree_sha256=$model_tree_sha256")
  elif grep -q '^model_tree_sha256=' "$manifest"; then
    echo "Resume model-tree manifest is no longer available; refusing ambiguous resume." >&2
    exit 1
  fi
  for expected_line in "${expected_resume_lines[@]}"; do
    if ! grep -Fqx -- "$expected_line" "$manifest"; then
      printf 'Resume manifest mismatch: expected line %s\n' "$expected_line" >&2
      exit 1
    fi
  done
else
  mkdir -p "$run_root/logs" "$run_root/submissions"
  manifest_tmp="$manifest.tmp.$$"
  model_tree_manifest_line=""
  model_tree_sha256_line=""
  if [[ "$model_tree_sha256" != "unavailable" ]]; then
    model_tree_manifest_line="model_tree_manifest=$model_tree_manifest"
    model_tree_sha256_line="model_tree_sha256=$model_tree_sha256"
  fi
  printf '%s\n' \
    "run_id=$run_id" \
    "dataset=$dataset" \
    "method=SVC" \
    "model=$P1_SPEC_MODEL_ID" \
    "revision=$P1_SPEC_REVISION" \
    "thinking=$P1_SPEC_THINKING" \
    "dtype=bfloat16" \
    "max_model_len=65536" \
    "accelerator=$accelerator" \
    "tensor_parallel_size=$P1_SPEC_TP" \
    "svc_gpus=1" \
    "total_gpus=$P1_SPEC_TOTAL_GPUS" \
    "input_file=$input_file" \
    "input_sha256=$input_sha256" \
    "dataset_provenance=$dataset_provenance" \
    "dataset_provenance_sha256=$provenance_sha256" \
    "experiment_manifest=$experiment_manifest" \
    "experiment_manifest_sha256=$manifest_sha256" \
    "$model_tree_manifest_line" \
    "$model_tree_sha256_line" \
    "source_sha256=$source_sha256" \
    "split=$split" \
    "num_questions=$effective_questions" \
    "num_chunks=$effective_chunks" \
    "max_images=$max_images" \
    "persistent_environment_root=${persistent_env_root:-none}" \
    "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    >"$manifest_tmp"
  mv -- "$manifest_tmp" "$manifest"
fi
mkdir -p "$run_root/logs" "$run_root/submissions"

submission_response="$("${sbatch_cmd[@]}")"
job_id="${submission_response%%;*}"
if [[ ! "$job_id" =~ ^[0-9]+$ ]]; then
  echo "Unexpected sbatch response: $submission_response" >&2
  exit 1
fi
submission_record="$run_root/submissions/$(date -u +%Y%m%dT%H%M%SZ)-${job_id}.txt"
printf '%s\n' \
  "job_id=$job_id" \
  "array=$array_request" \
  "submitted_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"$submission_record"
printf 'Submitted run_id=%s job_id=%s; results remain under %s.\n' \
  "$run_id" "$job_id" "$run_root"
