#!/usr/bin/env bash
set -euo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
source "$script_dir/p1_model_registry.sh"

usage() {
  cat >&2 <<'USAGE'
Usage:
  p1_run_local_diagnostic_smoke.sh --host-label A100-1|A100-2 \
    --model MODEL_ALIAS --dataset mindcube|mmsi --gpus GPU[,GPU...] \
    --input-dir ONE_RECORD_DIR --runtime-root DIR --model-path DIR \
    --model-revision-file FILE --svc-python PATH --vllm-bin PATH \
    [--provenance FILE] [--cache-root DIR] [--run-id ID] [--port N] \
    [--env-id ID] [--ready-timeout-seconds N] [--dry-run]

This launcher is only for one-question diagnostic smokes on the non-Slurm
A100-1/A100-2 hosts.  It checks that every selected A100-40 GPU is idle and
has no compute process immediately before launch.  It cannot run formal data.
USAGE
}

host_label=""
model_key=""
dataset=""
gpu_csv=""
input_dir=""
runtime_root=""
model_path=""
model_revision_file=""
svc_python=""
vllm_bin=""
dataset_provenance=""
cache_root=""
run_id=""
port="8000"
env_id="qwen0280-svc-v1-a10040-diagnostic"
ready_timeout="7200"
dry_run=0

while (( $# > 0 )); do
  case "$1" in
    --host-label) host_label="${2:?missing value for --host-label}"; shift 2 ;;
    --model) model_key="${2:?missing value for --model}"; shift 2 ;;
    --dataset) dataset="${2:?missing value for --dataset}"; shift 2 ;;
    --gpus) gpu_csv="${2:?missing value for --gpus}"; shift 2 ;;
    --input-dir) input_dir="${2:?missing value for --input-dir}"; shift 2 ;;
    --runtime-root) runtime_root="${2:?missing value for --runtime-root}"; shift 2 ;;
    --model-path) model_path="${2:?missing value for --model-path}"; shift 2 ;;
    --model-revision-file) model_revision_file="${2:?missing value for --model-revision-file}"; shift 2 ;;
    --svc-python) svc_python="${2:?missing value for --svc-python}"; shift 2 ;;
    --vllm-bin) vllm_bin="${2:?missing value for --vllm-bin}"; shift 2 ;;
    --provenance) dataset_provenance="${2:?missing value for --provenance}"; shift 2 ;;
    --cache-root) cache_root="${2:?missing value for --cache-root}"; shift 2 ;;
    --run-id) run_id="${2:?missing value for --run-id}"; shift 2 ;;
    --port) port="${2:?missing value for --port}"; shift 2 ;;
    --env-id) env_id="${2:?missing value for --env-id}"; shift 2 ;;
    --ready-timeout-seconds) ready_timeout="${2:?missing value for --ready-timeout-seconds}"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done

for required_name in host_label model_key dataset gpu_csv input_dir runtime_root \
    model_path model_revision_file svc_python vllm_bin; do
  if [[ -z "${!required_name}" ]]; then
    printf -- '--%s is required.\n' "${required_name//_/-}" >&2
    usage
    exit 2
  fi
done
if [[ "$host_label" != "A100-1" && "$host_label" != "A100-2" ]]; then
  echo "--host-label must be A100-1 or A100-2." >&2
  exit 2
fi
if [[ "$dataset" != "mindcube" && "$dataset" != "mmsi" ]]; then
  echo "--dataset must be mindcube or mmsi." >&2
  exit 2
fi
for absolute_name in input_dir runtime_root model_path model_revision_file \
    svc_python vllm_bin; do
  if [[ "${!absolute_name}" != /* ]]; then
    printf -- '--%s must be an absolute path.\n' "${absolute_name//_/-}" >&2
    exit 2
  fi
done
if [[ -n "$dataset_provenance" && "$dataset_provenance" != /* ]]; then
  echo "--provenance must be an absolute path." >&2
  exit 2
fi
if [[ -n "$cache_root" && "$cache_root" != /* ]]; then
  echo "--cache-root must be an absolute path." >&2
  exit 2
fi
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
  echo "--port must be an integer in [1, 65535]." >&2
  exit 2
fi
if [[ ! "$ready_timeout" =~ ^[1-9][0-9]*$ ]]; then
  echo "--ready-timeout-seconds must be a positive integer." >&2
  exit 2
fi

p1_load_model_spec "$model_key"
p1_load_resource_plan a10040
p1_assert_priority_one_combo "$dataset"
if [[ "$P1_SPEC_DIAGNOSTIC_ONLY" != "1" ]]; then
  echo "Internal error: a10040 did not resolve to a diagnostic-only plan." >&2
  exit 1
fi

case "$dataset" in
  mindcube) max_images=4 ;;
  mmsi) max_images=10 ;;
esac
input_dir="$(cd -- "$input_dir" 2>/dev/null && pwd)" || {
  echo "--input-dir is not an existing directory." >&2
  exit 1
}
runtime_root="$(cd -- "$runtime_root" 2>/dev/null && pwd)" || {
  echo "--runtime-root must already exist." >&2
  exit 1
}
model_path="$(cd -- "$model_path" 2>/dev/null && pwd)" || {
  echo "--model-path is not an existing directory." >&2
  exit 1
}
if [[ ! -x "$svc_python" || ! -x "$vllm_bin" ]]; then
  echo "--svc-python and --vllm-bin must be executable absolute files." >&2
  exit 1
fi
svc_python="$(cd -- "$(dirname -- "$svc_python")" && pwd)/$(basename -- "$svc_python")"
vllm_bin="$(cd -- "$(dirname -- "$vllm_bin")" && pwd)/$(basename -- "$vllm_bin")"
if [[ ! -r "$model_revision_file" ]]; then
  echo "--model-revision-file is not readable." >&2
  exit 1
fi
model_revision_parent="$(cd -- "$(dirname -- "$model_revision_file")" && pwd)"
model_revision_file="$model_revision_parent/$(basename -- "$model_revision_file")"
if [[ "$(sed -n '1{s/[[:space:]]//g;p;}' "$model_revision_file")" != "$P1_SPEC_REVISION" ]]; then
  echo "Model revision marker does not match the pinned model revision." >&2
  exit 1
fi
if [[ ! -r "$model_path/config.json" \
      || ( ! -r "$model_path/model.safetensors.index.json" \
           && ! -r "$model_path/model.safetensors" ) ]]; then
  echo "Pinned local model is missing config.json or safetensors weights." >&2
  exit 1
fi
"$svc_python" - "$model_path" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
index = root / "model.safetensors.index.json"
if index.is_file():
    payload = json.loads(index.read_text(encoding="utf-8"))
    shards = set(payload.get("weight_map", {}).values())
    if not shards:
        raise SystemExit("model safetensors index has no shards")
    missing = sorted(name for name in shards if not (root / name).is_file())
    if missing:
        raise SystemExit(f"model snapshot is missing shard: {missing[0]}")
PY

vllm_dir="$(cd -- "$(dirname -- "$vllm_bin")" && pwd)"
if [[ ! -x "$vllm_dir/ninja" ]]; then
  echo "Pinned vLLM environment must contain executable ninja beside vllm." >&2
  exit 1
fi
vllm_version="$($vllm_bin --version)"
if [[ "$vllm_version" != *"0.28.0"* ]]; then
  printf 'Expected vLLM 0.28.0, found: %s\n' "$vllm_version" >&2
  exit 1
fi

input_file="$input_dir/test.json"
if [[ ! -r "$input_file" ]]; then
  echo "Diagnostic input directory must contain test.json." >&2
  exit 1
fi
if [[ -z "$dataset_provenance" ]]; then
  if [[ -r "$input_dir/test_provenance.json" ]]; then
    dataset_provenance="$input_dir/test_provenance.json"
  elif [[ -r "$input_dir/provenance.json" ]]; then
    dataset_provenance="$input_dir/provenance.json"
  else
    echo "No readable test_provenance.json or provenance.json; pass --provenance." >&2
    exit 1
  fi
fi
if [[ ! -r "$dataset_provenance" ]]; then
  echo "Dataset provenance is not readable." >&2
  exit 1
fi
dataset_provenance_parent="$(cd -- "$(dirname -- "$dataset_provenance")" && pwd)"
dataset_provenance="$dataset_provenance_parent/$(basename -- "$dataset_provenance")"
experiment_manifest="$repo_dir/configs/p1_svc_multiimage.json"
"$svc_python" "$script_dir/p1_validate_input.py" \
  --input-dir "$input_dir" --split test --repo-root "$repo_dir" \
  --expected-questions 1 --max-images "$max_images"

IFS=',' read -r -a selected_gpus <<<"$gpu_csv"
if (( ${#selected_gpus[@]} != P1_SPEC_TOTAL_GPUS )); then
  printf 'The %s profile requires exactly %s GPU IDs (TP=%s + SVC=1).\n' \
    "$P1_SPEC_MODEL_ID" "$P1_SPEC_TOTAL_GPUS" "$P1_SPEC_TP" >&2
  exit 2
fi
seen_gpu_list=","
for gpu in "${selected_gpus[@]}"; do
  if [[ ! "$gpu" =~ ^[0-9]+$ || "$seen_gpu_list" == *",${gpu},"* ]]; then
    echo "--gpus must contain unique non-negative numeric GPU IDs." >&2
    exit 2
  fi
  seen_gpu_list+="${gpu},"
done
if [[ -n "${CUDA_VISIBLE_DEVICES:-}" && "$CUDA_VISIBLE_DEVICES" != "$gpu_csv" ]]; then
  echo "Existing CUDA_VISIBLE_DEVICES differs from --gpus; refusing ambiguous mapping." >&2
  exit 1
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi is required for the mandatory idle-GPU check." >&2
  exit 1
fi

gpu_observations=()
for gpu in "${selected_gpus[@]}"; do
  inventory="$(nvidia-smi --id="$gpu" \
    --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits)" || {
      echo "Could not query GPU $gpu." >&2
      exit 1
    }
  if [[ "$inventory" == *$'\n'* ]]; then
    echo "GPU $gpu query returned multiple devices; refusing ambiguous mapping." >&2
    exit 1
  fi
  IFS=',' read -r gpu_name gpu_total gpu_used <<<"$inventory"
  gpu_name="${gpu_name#${gpu_name%%[![:space:]]*}}"
  gpu_total="${gpu_total//[[:space:]]/}"
  gpu_used="${gpu_used//[[:space:]]/}"
  if [[ "$gpu_name" != *"A100"* || ! "$gpu_total" =~ ^[0-9]+$ \
        || gpu_total -lt 38000 || gpu_total -gt 50000 ]]; then
    printf 'GPU %s is not an A100 40 GB device: %s\n' "$gpu" "$inventory" >&2
    exit 1
  fi
  if [[ ! "$gpu_used" =~ ^[0-9]+$ || gpu_used -gt 512 ]]; then
    printf 'GPU %s is not idle (memory.used=%s MiB; limit=512 MiB).\n' \
      "$gpu" "$gpu_used" >&2
    exit 1
  fi
  compute_pids="$(nvidia-smi --id="$gpu" --query-compute-apps=pid \
    --format=csv,noheader,nounits 2>/dev/null || true)"
  compute_pids="${compute_pids//[[:space:]]/}"
  if [[ -n "$compute_pids" ]]; then
    printf 'GPU %s has an active compute process (%s); refusing launch.\n' \
      "$gpu" "$compute_pids" >&2
    exit 1
  fi
  gpu_observations+=("${gpu}:${gpu_name}:${gpu_total}MiB:${gpu_used}MiB")
done
gpu_idle_observations="$(IFS=';'; printf '%s' "${gpu_observations[*]}")"

if [[ -z "$run_id" ]]; then
  host_slug="$(printf '%s' "$host_label" | tr '[:upper:]' '[:lower:]')"
  run_id="mj-p1-diag-${host_slug}-${dataset}-${P1_SPEC_ALIAS}-$(date -u +%Y%m%dT%H%M%SZ)"
fi
if [[ ! "$run_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]]; then
  echo "--run-id must contain 1-80 safe filename characters." >&2
  exit 2
fi
run_root="$runtime_root/$run_id"
if [[ -e "$run_root" ]]; then
  echo "Diagnostic run already exists; use a new Run ID (resume is intentionally disabled)." >&2
  exit 1
fi

file_sha256() {
  "$svc_python" - "$1" <<'PY'
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
print(digest.hexdigest())
PY
}
source_sha256="$($svc_python - "$repo_dir" <<'PY'
import hashlib
import os
import sys

repo_root = os.path.abspath(sys.argv[1])
digest = hashlib.sha256()
for source_root in ("pipelines", "utils", "stable_virtual_camera"):
    absolute_root = os.path.join(repo_root, source_root)
    for directory, dirnames, filenames in os.walk(absolute_root):
        dirnames.sort()
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(directory, filename)
                digest.update(os.path.relpath(path, repo_root).encode())
                with open(path, "rb") as handle:
                    digest.update(handle.read())
print(digest.hexdigest())
PY
)"
input_sha256="$(file_sha256 "$input_file")"
provenance_sha256="$(file_sha256 "$dataset_provenance")"
manifest_sha256="$(file_sha256 "$experiment_manifest")"
cache_root="${cache_root:-$runtime_root/cache}"
actual_hostname="$(hostname -f 2>/dev/null || hostname)"
hardware="${host_label}:A100-40GB:TP${P1_SPEC_TP}+SVC1:diagnostic-smoke"

p1_print_model_spec
printf '%s\n' \
  "execution_scope=diagnostic_smoke" \
  "formal_eligible=false" \
  "diagnostic_host=$host_label" \
  "actual_hostname=$actual_hostname" \
  "dataset=$dataset" \
  "input_file=$input_file" \
  "input_sha256=$input_sha256" \
  "gpu_mapping=$gpu_csv" \
  "gpu_idle_observations=$gpu_idle_observations" \
  "run_root=$run_root"
if (( dry_run == 1 )); then
  echo "Dry run only; no run directory or result was created."
  exit 0
fi

mkdir "$run_root"
launch_manifest="$run_root/launch_manifest.txt"
launch_manifest_tmp="$launch_manifest.tmp.$$"
printf '%s\n' \
  "run_id=$run_id" \
  "dataset=$dataset" \
  "method=SVC" \
  "model=$P1_SPEC_MODEL_ID" \
  "revision=$P1_SPEC_REVISION" \
  "thinking=false" \
  "dtype=bfloat16" \
  "max_model_len=65536" \
  "execution_scope=diagnostic_smoke" \
  "formal_eligible=false" \
  "formal_execution_cluster=DAAI only" \
  "diagnostic_host=$host_label" \
  "actual_hostname=$actual_hostname" \
  "accelerator=a10040" \
  "tensor_parallel_size=$P1_SPEC_TP" \
  "svc_gpus=1" \
  "total_gpus=$P1_SPEC_TOTAL_GPUS" \
  "gpu_mapping=$gpu_csv" \
  "gpu_idle_observations=$gpu_idle_observations" \
  "hardware=$hardware" \
  "input_file=$input_file" \
  "input_sha256=$input_sha256" \
  "dataset_provenance=$dataset_provenance" \
  "dataset_provenance_sha256=$provenance_sha256" \
  "experiment_manifest=$experiment_manifest" \
  "experiment_manifest_sha256=$manifest_sha256" \
  "source_sha256=$source_sha256" \
  "split=test" \
  "num_questions=1" \
  "num_chunks=1" \
  "max_images=$max_images" \
  "runtime_environment=$env_id" \
  "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"$launch_manifest_tmp"
mv -- "$launch_manifest_tmp" "$launch_manifest"

export CUDA_VISIBLE_DEVICES="$gpu_csv"
export P1_ACCELERATOR=a10040
export P1_DATASET="$dataset"
export P1_RUN_MODE=smoke
export P1_EXECUTION_SCOPE=diagnostic_smoke
export P1_DIAGNOSTIC_HOST="$host_label"
export P1_RUN_ID="$run_id"
export P1_RUN_ROOT="$run_root"
export P1_INPUT_DIR="$input_dir"
export P1_SPLIT=test
export P1_NUM_QUESTIONS=1
export P1_NUM_CHUNKS=1
export P1_MAX_IMAGES="$max_images"
export P1_MODEL_PATH="$model_path"
export P1_MODEL_REVISION_FILE="$model_revision_file"
export P1_REQUIRE_REVISION_MARKER=1
export P1_CACHE_ROOT="$cache_root"
export P1_MANIFEST="$experiment_manifest"
export P1_DATASET_PROVENANCE="$dataset_provenance"
export P1_EXPECTED_SOURCE_SHA256="$source_sha256"
export P1_SVC_PYTHON="$svc_python"
export P1_VLLM_BIN="$vllm_bin"
export P1_ALLOW_NETWORK=0
export P1_VLM_PORT="$port"
export P1_READY_TIMEOUT_SECONDS="$ready_timeout"
export P1_ENV_ID="$env_id"
export HF_HOME="$cache_root/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export TORCH_HOME="$cache_root/torch"
export XDG_CACHE_HOME="$cache_root/xdg"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONNOUSERSITE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export SVC_REVISION="e538e251c1009e9a41cf8b7fee5f21332a1960de"
export SVC_WEIGHT_SHA256="10e69ea003c313e6bdfc7ee40376d1c19ea6036c20bd384e94b483dec8350396"
export SVC_STRICT_LOAD=1
export SVC_VAE_REPO="sd2-community/stable-diffusion-2-1-base"
export SVC_VAE_REVISION="4e63672c03103b6c636b8fb4119ba982469b2955"
export SVC_VAE_SUBFOLDER=vae
export SVC_VAE_SHA256="a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
export SVC_OPENCLIP_REPO="laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
export SVC_OPENCLIP_REVISION="1c2b8495b28150b8a4922ee1c8edee224c284c0c"
export SVC_OPENCLIP_FILENAME="open_clip_pytorch_model.bin"
export SVC_OPENCLIP_SHA256="9a78ef8e8c73fd0df621682e7a8e8eb36c6916cb3c16b291a082ecd52ab79cc4"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$repo_dir"

mkdir -p "$cache_root/huggingface" "$cache_root/torch" "$cache_root/xdg"
"$script_dir/p1_run_chunk.sh" "$P1_SPEC_ALIAS" 0
"$svc_python" -m utils.p1_smoke_results \
  --run-root "$run_root" --input-file "$input_file" --dataset "$dataset" \
  --results-file "$run_root/results_spatial_beam_search/results.json" \
  --complete-file "$run_root/results_spatial_beam_search/COMPLETE"
