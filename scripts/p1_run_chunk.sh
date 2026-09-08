#!/usr/bin/env bash
set -euo pipefail
umask 077

export NO_PROXY="127.0.0.1,localhost${NO_PROXY:+,$NO_PROXY}"
export no_proxy="$NO_PROXY"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
source "$script_dir/p1_model_registry.sh"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$repo_dir"

if (( $# != 2 )); then
  echo "Usage: $0 MODEL_ALIAS QUESTION_CHUNK_INDEX" >&2
  exit 2
fi

p1_load_model_spec "$1"
p1_load_resource_plan "${P1_ACCELERATOR:-h20}"
dataset="${P1_DATASET:?P1_DATASET is required}"
p1_assert_priority_one_combo "$dataset"
chunk_index="$2"
run_id="${P1_RUN_ID:?P1_RUN_ID is required}"
run_root="${P1_RUN_ROOT:?P1_RUN_ROOT is required}"
num_chunks="${P1_NUM_CHUNKS:?P1_NUM_CHUNKS is required}"
run_mode="${P1_RUN_MODE:-array}"
execution_scope="${P1_EXECUTION_SCOPE:-formal}"
input_file="${P1_INPUT_DIR:?P1_INPUT_DIR is required}/${P1_SPLIT:?P1_SPLIT is required}.json"
expected_input_sha256="${P1_EXPECTED_INPUT_SHA256:?P1_EXPECTED_INPUT_SHA256 is required}"
expected_provenance_sha256="${P1_EXPECTED_PROVENANCE_SHA256:?P1_EXPECTED_PROVENANCE_SHA256 is required}"
expected_manifest_sha256="${P1_EXPECTED_MANIFEST_SHA256:?P1_EXPECTED_MANIFEST_SHA256 is required}"
expected_source_sha256="${P1_EXPECTED_SOURCE_SHA256:?P1_EXPECTED_SOURCE_SHA256 is required}"

if [[ "$P1_SPEC_DIAGNOSTIC_ONLY" == "1" ]]; then
  if [[ "$run_mode" != "smoke" || "$execution_scope" != "diagnostic_smoke" ]]; then
    echo "The A100 40 GB profile is restricted to diagnostic smoke runs." >&2
    exit 2
  fi
elif [[ "$execution_scope" == "diagnostic_smoke" ]]; then
  echo "diagnostic_smoke requires the a10040 resource profile." >&2
  exit 2
fi

if [[ ! "$run_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]]; then
  echo "P1_RUN_ID must contain 1-80 safe filename characters." >&2
  exit 2
fi
if [[ ! "$chunk_index" =~ ^[0-9]+$ \
      || ! "$num_chunks" =~ ^[1-9][0-9]*$ \
      || "$chunk_index" -ge "$num_chunks" ]]; then
  echo "Invalid chunk index or P1_NUM_CHUNKS." >&2
  exit 2
fi
if [[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "CUDA_VISIBLE_DEVICES is empty; this runner requires an explicit GPU allocation/mapping." >&2
  exit 1
fi

# Recheck every small, immutable launch artifact on the allocated node before
# starting either vLLM or SVC.  The optional model-tree input is Hugging Face's
# revision manifest, not the multi-gigabyte weights themselves.
fingerprint_args=(
  verify-runtime
  --repo-root "$repo_dir"
  --expected-source-sha256 "$expected_source_sha256"
  --input-file "$input_file"
  --expected-input-sha256 "$expected_input_sha256"
  --provenance-file "${P1_DATASET_PROVENANCE:?P1_DATASET_PROVENANCE is required}"
  --expected-provenance-sha256 "$expected_provenance_sha256"
  --experiment-manifest "${P1_MANIFEST:?P1_MANIFEST is required}"
  --expected-manifest-sha256 "$expected_manifest_sha256"
)
if [[ -n "${P1_MODEL_TREE_MANIFEST:-}" || -n "${P1_MODEL_TREE_SHA256:-}" ]]; then
  if [[ -z "${P1_MODEL_TREE_MANIFEST:-}" || -z "${P1_MODEL_TREE_SHA256:-}" ]]; then
    echo "P1_MODEL_TREE_MANIFEST and P1_MODEL_TREE_SHA256 must be supplied together." >&2
    exit 2
  fi
  fingerprint_args+=(
    --model-tree-manifest "$P1_MODEL_TREE_MANIFEST"
    --expected-model-tree-sha256 "$P1_MODEL_TREE_SHA256"
  )
fi
"${P1_SVC_PYTHON:?P1_SVC_PYTHON is required}" \
  "$repo_dir/utils/p1_fingerprints.py" "${fingerprint_args[@]}"
IFS=',' read -r -a allocated_devices <<<"$CUDA_VISIBLE_DEVICES"
if (( ${#allocated_devices[@]} != P1_SPEC_TOTAL_GPUS )); then
  printf 'Expected %s allocated GPUs for %s on %s, got %s (%s).\n' \
    "$P1_SPEC_TOTAL_GPUS" "$P1_SPEC_MODEL_ID" "$P1_SPEC_ACCELERATOR" \
    "${#allocated_devices[@]}" "$CUDA_VISIBLE_DEVICES" >&2
  exit 1
fi

vlm_devices="${allocated_devices[0]}"
for ((device_index = 1; device_index < P1_SPEC_TP; device_index += 1)); do
  vlm_devices+=",${allocated_devices[$device_index]}"
done
svc_device="${allocated_devices[$P1_SPEC_TP]}"

output_base="$run_root/results"
if (( num_chunks > 1 )); then
  chunk_dir="${output_base}_spatial_beam_search_qc${num_chunks}/question_chunk_${chunk_index}"
else
  # PipelineBase only adds the _qcN/question_chunk_N suffix when N > 1.
  # Smoke runs are intentionally a single logical chunk, so their result is
  # written directly below the scaling-strategy output directory.
  chunk_dir="${output_base}_spatial_beam_search"
fi
results_file="$chunk_dir/results.json"
completion_file="$chunk_dir/COMPLETE"
attempt_id="${SLURM_JOB_ID:-manual}-$(date -u +%Y%m%dT%H%M%SZ)"
attempt_dir="$run_root/attempts/question_chunk_${chunk_index}/$attempt_id"
mkdir -p "$attempt_dir" "$chunk_dir" "$run_root/locks"

exec {chunk_lock_fd}>"$run_root/locks/question_chunk_${chunk_index}.lock"
if command -v flock >/dev/null 2>&1; then
  if ! flock -n "$chunk_lock_fd"; then
    echo "Another process already owns chunk $chunk_index for run $run_id." >&2
    exit 1
  fi
fi
if [[ -f "$completion_file" && -f "$results_file" ]]; then
  if [[ "$run_mode" == "array" ]]; then
    "$P1_SVC_PYTHON" -m utils.p1_results \
      --run-root "$run_root" \
      --input-file "$input_file" \
      --dataset "$dataset" \
      --chunk-index "$chunk_index" \
      --results-file "$results_file"
  elif [[ "$execution_scope" == "diagnostic_smoke" ]]; then
    "$P1_SVC_PYTHON" -m utils.p1_smoke_results \
      --run-root "$run_root" \
      --input-file "$input_file" \
      --dataset "$dataset" \
      --results-file "$results_file" \
      --complete-file "$completion_file"
  fi
  echo "Chunk $chunk_index already has valid results.json and COMPLETE; leaving it unchanged."
  exit 0
fi
if [[ -f "$completion_file" && ! -f "$results_file" ]]; then
  echo "Chunk $chunk_index has COMPLETE but no results.json; refusing inconsistent state." >&2
  exit 1
fi

if [[ -n "${P1_VLM_PORT:-}" ]]; then
  vlm_port="$P1_VLM_PORT"
elif [[ "${SLURM_JOB_ID:-}" =~ ^[0-9]+$ ]]; then
  array_offset="${SLURM_ARRAY_TASK_ID:-0}"
  vlm_port=$((20000 + (SLURM_JOB_ID + array_offset) % 20000))
else
  vlm_port=8000
fi
if [[ ! "$vlm_port" =~ ^[0-9]+$ ]] || (( vlm_port < 1 || vlm_port > 65535 )); then
  echo "P1_VLM_PORT must be an integer in [1, 65535]." >&2
  exit 2
fi
if (exec 3<>"/dev/tcp/127.0.0.1/$vlm_port") 2>/dev/null; then
  exec 3>&-
  exec 3<&-
  echo "TCP port $vlm_port is already in use." >&2
  exit 1
fi

export P1_TP_SIZE="$P1_SPEC_TP"
export P1_VLM_PORT="$vlm_port"
export P1_VLM_API_BASE="http://127.0.0.1:${vlm_port}/v1"
export P1_VLM_API_KEY="EMPTY"
export P1_MAX_MODEL_LEN=65536
export P1_OUTPUT_BASE="$output_base"

qwen_log="$attempt_dir/vllm.log"
pipeline_log="$attempt_dir/pipeline.log"
qwen_pid=""
pipeline_pid=""
cleanup() {
  if [[ -n "$pipeline_pid" ]] && kill -0 "$pipeline_pid" 2>/dev/null; then
    kill "$pipeline_pid" 2>/dev/null || true
    wait "$pipeline_pid" 2>/dev/null || true
  fi
  if [[ -n "$qwen_pid" ]] && kill -0 "$qwen_pid" 2>/dev/null; then
    kill "$qwen_pid" 2>/dev/null || true
    for _ in {1..30}; do
      kill -0 "$qwen_pid" 2>/dev/null || break
      sleep 1
    done
    if kill -0 "$qwen_pid" 2>/dev/null; then
      kill -KILL "$qwen_pid" 2>/dev/null || true
    fi
    wait "$qwen_pid" 2>/dev/null || true
  fi
}
terminate() {
  trap - INT TERM
  cleanup
  exit 143
}
trap cleanup EXIT
trap terminate INT TERM

printf '%s\n' \
  "run_id=$run_id" \
  "dataset=$dataset" \
  "model=$P1_SPEC_MODEL_ID" \
  "revision=$P1_SPEC_REVISION" \
  "thinking=$P1_SPEC_THINKING" \
  "accelerator=$P1_SPEC_ACCELERATOR" \
  "dtype=bfloat16" \
  "max_model_len=65536" \
  "tensor_parallel_size=$P1_SPEC_TP" \
  "cpus_per_task=${SLURM_CPUS_PER_TASK:-unknown}" \
  "execution_scope=$execution_scope" \
  "local_environment_root=${P1_LOCAL_ENV_ROOT:-none}" \
  "diagnostic_host=${P1_DIAGNOSTIC_HOST:-none}" \
  "vlm_devices=$vlm_devices" \
  "svc_device=$svc_device" \
  "host=$(hostname)" \
  "job_id=${SLURM_JOB_ID:-none}" \
  "array_task_id=${SLURM_ARRAY_TASK_ID:-none}" \
  >"$attempt_dir/attempt.txt"

CUDA_VISIBLE_DEVICES="$vlm_devices" \
  "$script_dir/p1_serve_vllm.sh" "$P1_SPEC_ALIAS" \
  >"$qwen_log" 2>&1 &
qwen_pid=$!

ready_timeout="${P1_READY_TIMEOUT_SECONDS:-21600}"
if [[ ! "$ready_timeout" =~ ^[1-9][0-9]*$ ]]; then
  echo "P1_READY_TIMEOUT_SECONDS must be a positive integer." >&2
  exit 2
fi
ready=0
for ((elapsed = 0; elapsed < ready_timeout; elapsed += 5)); do
  if ! kill -0 "$qwen_pid" 2>/dev/null; then
    echo "vLLM exited before becoming ready; see $qwen_log." >&2
    exit 1
  fi
  if curl --silent --fail --connect-timeout 2 --max-time 5 \
      "http://127.0.0.1:${vlm_port}/v1/models" >/dev/null; then
    ready=1
    break
  fi
  sleep 5
done
if (( ready != 1 )); then
  echo "vLLM was not ready within ${ready_timeout}s; see $qwen_log." >&2
  exit 1
fi

CUDA_VISIBLE_DEVICES="$svc_device" \
  "$script_dir/p1_run_pipeline.sh" "$P1_SPEC_ALIAS" "$chunk_index" \
  >"$pipeline_log" 2>&1 &
pipeline_pid=$!
set +e
wait "$pipeline_pid"
pipeline_status=$?
set -e
pipeline_pid=""
if (( pipeline_status != 0 )); then
  printf 'P1 pipeline failed with status %s; see %s.\n' \
    "$pipeline_status" "$pipeline_log" >&2
  exit "$pipeline_status"
fi
if [[ ! -s "$results_file" ]]; then
  echo "Pipeline exited successfully but did not produce $results_file." >&2
  exit 1
fi

if [[ "$run_mode" == "array" ]]; then
  "$P1_SVC_PYTHON" -m utils.p1_results \
    --run-root "$run_root" \
    --input-file "$input_file" \
    --dataset "$dataset" \
    --chunk-index "$chunk_index" \
    --results-file "$results_file"
elif [[ "$execution_scope" == "diagnostic_smoke" ]]; then
  "$P1_SVC_PYTHON" -m utils.p1_smoke_results \
    --run-root "$run_root" \
    --input-file "$input_file" \
    --dataset "$dataset" \
    --results-file "$results_file"
fi

results_sha256="$(sha256sum "$results_file" | awk '{print $1}')"
completion_tmp="$completion_file.tmp.${SLURM_JOB_ID:-$$}"
printf '%s\n' \
  "run_id=$run_id" \
  "dataset=$dataset" \
  "model=$P1_SPEC_MODEL_ID" \
  "revision=$P1_SPEC_REVISION" \
  "execution_scope=$execution_scope" \
  "diagnostic_host=${P1_DIAGNOSTIC_HOST:-none}" \
  "chunk_index=$chunk_index" \
  "results_sha256=$results_sha256" \
  "completed_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"$completion_tmp"
mv -- "$completion_tmp" "$completion_file"
echo "Completed $dataset / $P1_SPEC_MODEL_ID chunk $chunk_index."
