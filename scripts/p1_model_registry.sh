#!/usr/bin/env bash

# Shared immutable model/revision and DAAI resource matrix for priority-one
# MindJourney runs.  This file is sourced by the serving and Slurm scripts.

p1_load_model_spec() {
  local requested="${1:?model alias or official model ID is required}"
  case "$requested" in
    qwen35-27b|Qwen/Qwen3.5-27B)
      P1_SPEC_ALIAS="qwen35-27b"
      P1_SPEC_MODEL_ID="Qwen/Qwen3.5-27B"
      P1_SPEC_REVISION="fc05daec18b0a78c049392ed2e771dde82bdf654"
      P1_SPEC_MODEL_DIR="Qwen3.5-27B"
      P1_SPEC_THINKING="false"
      P1_SPEC_SIZE_CLASS="standard"
      ;;
    qwen25vl-72b|Qwen/Qwen2.5-VL-72B-Instruct)
      P1_SPEC_ALIAS="qwen25vl-72b"
      P1_SPEC_MODEL_ID="Qwen/Qwen2.5-VL-72B-Instruct"
      P1_SPEC_REVISION="89c86200743eec961a297729e7990e8f2ddbc4c5"
      P1_SPEC_MODEL_DIR="Qwen2.5-VL-72B-Instruct"
      # Qwen2.5-VL does not support Qwen3's enable_thinking argument.
      P1_SPEC_THINKING="unsupported"
      P1_SPEC_SIZE_CLASS="72b"
      ;;
    qwen35-9b|Qwen/Qwen3.5-9B)
      P1_SPEC_ALIAS="qwen35-9b"
      P1_SPEC_MODEL_ID="Qwen/Qwen3.5-9B"
      P1_SPEC_REVISION="c202236235762e1c871ad0ccb60c8ee5ba337b9a"
      P1_SPEC_MODEL_DIR="Qwen3.5-9B"
      P1_SPEC_THINKING="false"
      P1_SPEC_SIZE_CLASS="standard"
      ;;
    qwen38-27b|Qwen/Qwen3.8-27B)
      P1_SPEC_ALIAS="qwen38-27b"
      P1_SPEC_MODEL_ID="Qwen/Qwen3.8-27B"
      P1_SPEC_REVISION="1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
      P1_SPEC_MODEL_DIR="Qwen3.8-27B"
      P1_SPEC_THINKING="false"
      P1_SPEC_SIZE_CLASS="standard"
      ;;
    *)
      printf 'Unsupported P1 model %q. Use qwen35-27b, qwen25vl-72b, qwen35-9b, or qwen38-27b.\n' \
        "$requested" >&2
      return 2
      ;;
  esac
}

p1_load_resource_plan() {
  local accelerator="${1:?accelerator is required}"
  P1_SPEC_DIAGNOSTIC_ONLY=0
  case "$accelerator" in
    h20)
      P1_SPEC_ACCELERATOR="h20"
      P1_SPEC_EXCLUDE=""
      if [[ "$P1_SPEC_SIZE_CLASS" == "72b" ]]; then
        P1_SPEC_TP=2
        P1_SPEC_TOTAL_GPUS=3
        P1_SPEC_DEFAULT_CONCURRENCY=2
        P1_SPEC_CPUS_PER_TASK=16
      else
        P1_SPEC_TP=1
        P1_SPEC_TOTAL_GPUS=2
        P1_SPEC_DEFAULT_CONCURRENCY=4
        P1_SPEC_CPUS_PER_TASK=8
      fi
      ;;
    a100)
      P1_SPEC_ACCELERATOR="a100"
      # hkbugpudgx01 contains 40 GB A100s; all P1 fallback plans require the
      # 80 GB A100 nodes. srv07/srv08 use R555 drivers, which cannot load the
      # CUDA 13 build pinned by vLLM 0.28.0; the validated nodes use R580.
      P1_SPEC_EXCLUDE="hkbugpudgx01,hkbugpusrv07,hkbugpusrv08"
      if [[ "$P1_SPEC_SIZE_CLASS" == "72b" ]]; then
        # User-requested TP=2 trial to reduce the same-node GPU request.
        # Preserve BF16, context length and SVC's dedicated GPU.
        P1_SPEC_TP=2
        P1_SPEC_TOTAL_GPUS=3
        P1_SPEC_DEFAULT_CONCURRENCY=1
        P1_SPEC_CPUS_PER_TASK=16
      else
        P1_SPEC_TP=1
        P1_SPEC_TOTAL_GPUS=2
        P1_SPEC_DEFAULT_CONCURRENCY=4
        P1_SPEC_CPUS_PER_TASK=8
      fi
      ;;
    a10040)
      # A100-1/A100-2 are explicitly authorised for diagnostic smoke runs only.
      # Their 40 GB cards need TP=2 for either 27B model; the 9B model remains
      # TP=1.  The 72B configuration is intentionally not enabled here.
      P1_SPEC_ACCELERATOR="a10040"
      P1_SPEC_EXCLUDE=""
      P1_SPEC_DIAGNOSTIC_ONLY=1
      case "$P1_SPEC_ALIAS" in
        qwen35-9b)
          P1_SPEC_TP=1
          P1_SPEC_TOTAL_GPUS=2
          ;;
        qwen35-27b|qwen38-27b)
          P1_SPEC_TP=2
          P1_SPEC_TOTAL_GPUS=3
          ;;
        qwen25vl-72b)
          echo "Qwen2.5-VL-72B is not enabled for the A100 40 GB diagnostic profile." >&2
          return 2
          ;;
      esac
      P1_SPEC_DEFAULT_CONCURRENCY=1
      P1_SPEC_CPUS_PER_TASK=8
      ;;
    *)
      printf 'Unsupported accelerator %q. Use h20, a100 (80 GB), or a10040 (diagnostic smoke only).\n' \
        "$accelerator" >&2
      return 2
      ;;
  esac
  if [[ "$P1_SPEC_DIAGNOSTIC_ONLY" == "1" ]]; then
    P1_SPEC_GRES="not-applicable-nonslurm"
  else
    P1_SPEC_GRES="gpu:${P1_SPEC_ACCELERATOR}:${P1_SPEC_TOTAL_GPUS}"
  fi
}

p1_assert_priority_one_combo() {
  local dataset="${1:?dataset is required}"
  case "${dataset}:${P1_SPEC_ALIAS}" in
    mmsi:qwen35-27b|mmsi:qwen25vl-72b|mindcube:qwen35-9b|mindcube:qwen38-27b)
      return 0
      ;;
    *)
      printf '%s with %s is not one of the four registered P1 combinations.\n' \
        "$dataset" "$P1_SPEC_MODEL_ID" >&2
      return 2
      ;;
  esac
}

p1_print_model_spec() {
  printf '%s\n' \
    "alias=$P1_SPEC_ALIAS" \
    "model_id=$P1_SPEC_MODEL_ID" \
    "revision=$P1_SPEC_REVISION" \
    "thinking=$P1_SPEC_THINKING" \
    "accelerator=$P1_SPEC_ACCELERATOR" \
    "dtype=bfloat16" \
    "max_model_len=65536" \
    "tensor_parallel_size=$P1_SPEC_TP" \
    "svc_gpus=1" \
    "total_gpus=$P1_SPEC_TOTAL_GPUS" \
    "cpus_per_task=$P1_SPEC_CPUS_PER_TASK" \
    "gres=$P1_SPEC_GRES" \
    "exclude=${P1_SPEC_EXCLUDE:-none}" \
    "default_concurrency=$P1_SPEC_DEFAULT_CONCURRENCY"
  if [[ "$P1_SPEC_DIAGNOSTIC_ONLY" == "1" ]]; then
    echo "diagnostic_only=true"
  else
    echo "diagnostic_only=false"
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  if (( $# != 2 )); then
    echo "Usage: $0 MODEL_ALIAS ACCELERATOR" >&2
    exit 2
  fi
  p1_load_model_spec "$1" || exit $?
  p1_load_resource_plan "$2" || exit $?
  p1_print_model_spec
fi
