#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/p1_model_registry.sh"

if (( $# != 1 )); then
  echo "Usage: $0 MODEL_ALIAS" >&2
  exit 2
fi

p1_load_model_spec "$1"
p1_load_resource_plan "${P1_ACCELERATOR:-h20}"

tensor_parallel_size="${P1_TP_SIZE:-$P1_SPEC_TP}"
if [[ "$tensor_parallel_size" != "$P1_SPEC_TP" ]]; then
  printf 'TP=%s is invalid for %s on %s; the fixed plan requires TP=%s.\n' \
    "$tensor_parallel_size" "$P1_SPEC_MODEL_ID" "$P1_SPEC_ACCELERATOR" \
    "$P1_SPEC_TP" >&2
  exit 2
fi
if [[ "${P1_MAX_MODEL_LEN:-65536}" != "65536" ]]; then
  echo "P1_MAX_MODEL_LEN is fixed at 65536 for these runs." >&2
  exit 2
fi

model_root="${P1_MODEL_ROOT:-/home/datasets/chentao/models}"
default_model_path="$model_root/$P1_SPEC_MODEL_DIR"
model_source="${P1_MODEL_PATH:-$default_model_path}"
allow_network="${P1_ALLOW_NETWORK:-0}"
revision_args=()
if [[ -d "$model_source" ]]; then
  if [[ ! -r "$model_source/config.json" ]]; then
    echo "Local model snapshot has no readable config.json: $model_source" >&2
    exit 1
  fi
  if [[ ! -r "$model_source/model.safetensors.index.json" \
        && ! -r "$model_source/model.safetensors" ]]; then
    echo "Local model snapshot has no safetensors weights or index: $model_source" >&2
    exit 1
  fi
  validation_root="${P1_MODEL_VALIDATION_ROOT:-/home/datasets/shiyang/model_validation}"
  external_marker="${P1_MODEL_REVISION_FILE:-$validation_root/${P1_SPEC_MODEL_DIR}.revision}"
  found_revision_marker=0
  for marker in "$model_source/.mindjourney_revision" "$model_source/revision.txt" "$external_marker"; do
    if [[ -r "$marker" ]]; then
      recorded_revision="$(sed -n '1{s/[[:space:]]//g;p;}' "$marker")"
      if [[ "$recorded_revision" != "$P1_SPEC_REVISION" ]]; then
        printf 'Local revision marker %s contains %s, expected %s.\n' \
          "$marker" "$recorded_revision" "$P1_SPEC_REVISION" >&2
        exit 1
      fi
      found_revision_marker=1
      break
    fi
  done
  if [[ "$found_revision_marker" != "1" \
        && "${P1_REQUIRE_REVISION_MARKER:-1}" == "1" ]]; then
    printf 'No revision marker proves that %s is %s. Expected %s or set P1_MODEL_REVISION_FILE.\n' \
      "$model_source" "$P1_SPEC_REVISION" "$external_marker" >&2
    exit 1
  fi
  export HF_HUB_OFFLINE=1
  export TRANSFORMERS_OFFLINE=1
else
  if [[ -n "${P1_MODEL_PATH:-}" ]]; then
    echo "P1_MODEL_PATH is not an existing model directory: $model_source" >&2
    exit 1
  fi
  if [[ "$allow_network" != "1" ]]; then
    printf 'Pinned local model is unavailable at %s. Download revision %s first, or set P1_ALLOW_NETWORK=1 explicitly.\n' \
      "$default_model_path" "$P1_SPEC_REVISION" >&2
    exit 1
  fi
  model_source="$P1_SPEC_MODEL_ID"
  revision_args=(--revision "$P1_SPEC_REVISION")
fi

cache_root="${P1_CACHE_ROOT:-/home/datasets/shiyang/model_cache}"
mkdir -p "$cache_root/huggingface" "$cache_root/torch"
export HF_HOME="${HF_HOME:-$cache_root/huggingface}"
export TORCH_HOME="${TORCH_HOME:-$cache_root/torch}"

vllm_bin="${P1_VLLM_BIN:-vllm}"
resolved_vllm_bin="$(command -v -- "$vllm_bin" 2>/dev/null || true)"
if [[ -z "$resolved_vllm_bin" || ! -x "$resolved_vllm_bin" ]]; then
  echo "P1_VLLM_BIN is not executable: $vllm_bin" >&2
  exit 1
fi
vllm_bin="$resolved_vllm_bin"
vllm_bin_dir="$(cd -- "$(dirname -- "$vllm_bin")" && pwd)"

# FlashInfer invokes `ninja` by name from a vLLM worker subprocess.  Several
# DAAI compute nodes do not install it system-wide, but it is pinned inside the
# archived Qwen environment alongside vLLM.  Scope this PATH change to the
# serving process so it cannot change which interpreter runs the SVC pipeline.
if [[ ! -x "$vllm_bin_dir/ninja" ]]; then
  echo "Pinned vLLM environment is missing ninja: $vllm_bin_dir/ninja" >&2
  exit 1
fi
export PATH="$vllm_bin_dir:$PATH"

expected_vllm_version="0.28.0"
actual_vllm_version="$("$vllm_bin" --version)"
if [[ "$actual_vllm_version" != *"$expected_vllm_version"* ]]; then
  printf 'Expected vLLM %s, found: %s\n' \
    "$expected_vllm_version" "$actual_vllm_version" >&2
  exit 1
fi

host="${P1_VLM_HOST:-127.0.0.1}"
port="${P1_VLM_PORT:-8000}"
gpu_memory_utilization="${P1_GPU_MEMORY_UTILIZATION:-0.90}"
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
  echo "P1_VLM_PORT must be an integer in [1, 65535]." >&2
  exit 2
fi

serve_args=(
  serve "$model_source"
  --served-model-name "$P1_SPEC_MODEL_ID"
  "${revision_args[@]}"
  --host "$host"
  --port "$port"
  --dtype bfloat16
  --tensor-parallel-size "$tensor_parallel_size"
  --max-model-len 65536
  --gpu-memory-utilization "$gpu_memory_utilization"
  --max-num-seqs 1
  # Three SVC search steps can retain up to 45 helpful imagined views.  MMSI
  # contributes as many as 10 ordered source images, so the final prompt can
  # contain 55 image items without changing the paper-aligned search policy.
  --limit-mm-per-prompt '{"image":64}'
  --generation-config vllm
)

if [[ "$P1_SPEC_THINKING" == "false" ]]; then
  serve_args+=(
    --reasoning-parser qwen3
    --default-chat-template-kwargs '{"enable_thinking":false}'
  )
fi

printf 'Serving %s at revision %s (%s, BF16, TP=%s, max_model_len=65536).\n' \
  "$P1_SPEC_MODEL_ID" "$P1_SPEC_REVISION" "$P1_SPEC_ACCELERATOR" \
  "$tensor_parallel_size" >&2
exec "$vllm_bin" "${serve_args[@]}"
