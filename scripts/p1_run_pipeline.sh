#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$script_dir/.." && pwd)"
source "$script_dir/p1_model_registry.sh"

if (( $# != 2 )); then
  echo "Usage: $0 MODEL_ALIAS QUESTION_CHUNK_INDEX" >&2
  exit 2
fi

p1_load_model_spec "$1"
p1_load_resource_plan "${P1_ACCELERATOR:-h20}"
chunk_index="$2"
dataset="${P1_DATASET:?P1_DATASET is required}"
p1_assert_priority_one_combo "$dataset"

input_dir="${P1_INPUT_DIR:?P1_INPUT_DIR is required}"
split="${P1_SPLIT:?P1_SPLIT is required}"
num_questions="${P1_NUM_QUESTIONS:?P1_NUM_QUESTIONS is required}"
num_chunks="${P1_NUM_CHUNKS:?P1_NUM_CHUNKS is required}"
max_images="${P1_MAX_IMAGES:?P1_MAX_IMAGES is required}"
output_base="${P1_OUTPUT_BASE:?P1_OUTPUT_BASE is required}"
run_mode="${P1_RUN_MODE:-array}"
experiment_manifest="${P1_MANIFEST:?P1_MANIFEST is required}"
dataset_provenance="${P1_DATASET_PROVENANCE:?P1_DATASET_PROVENANCE is required}"
expected_source_sha256="${P1_EXPECTED_SOURCE_SHA256:?P1_EXPECTED_SOURCE_SHA256 is required}"

for value_name in num_questions num_chunks max_images; do
  value="${!value_name}"
  if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
    printf '%s must be a positive integer; got %q.\n' "$value_name" "$value" >&2
    exit 2
  fi
done
if [[ ! "$chunk_index" =~ ^[0-9]+$ ]] || (( chunk_index >= num_chunks )); then
  printf 'QUESTION_CHUNK_INDEX must be in [0, %s].\n' "$((num_chunks - 1))" >&2
  exit 2
fi
if [[ "$split" != "train" && "$split" != "val" && "$split" != "test" ]]; then
  echo "P1_SPLIT must be train, val, or test." >&2
  exit 2
fi
if [[ "$run_mode" != "array" && "$run_mode" != "smoke" ]]; then
  echo "P1_RUN_MODE must be array or smoke." >&2
  exit 2
fi
if [[ ! -r "$experiment_manifest" || ! -r "$dataset_provenance" ]]; then
  echo "P1_MANIFEST and P1_DATASET_PROVENANCE must be readable." >&2
  exit 1
fi
if [[ ! "$expected_source_sha256" =~ ^[0-9a-f]{64}$ ]]; then
  echo "P1_EXPECTED_SOURCE_SHA256 must be a lowercase SHA256." >&2
  exit 2
fi

preflight_args=(
  --input-dir "$input_dir"
  --split "$split"
  --repo-root "$repo_dir"
  --expected-questions "$num_questions"
  --max-images "$max_images"
)
if [[ "$run_mode" == "smoke" ]]; then
  preflight_args+=(--allow-subset)
fi

svc_python="${P1_SVC_PYTHON:-python}"
cd "$repo_dir"
"$svc_python" scripts/p1_validate_input.py "${preflight_args[@]}"

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$repo_dir"
export WORLD_MODEL_TYPE="svc"
export QUESTION_DATASET_TYPE="$dataset"
export MINDJOURNEY_MULTIIMAGE_ADAPTATION=1
export P1_VLM_API_BASE="${P1_VLM_API_BASE:-http://127.0.0.1:${P1_VLM_PORT:-8000}/v1}"
export P1_VLM_API_KEY="${P1_VLM_API_KEY:-EMPTY}"
export P1_VLM_MAX_TOKENS=1024
export MINDJOURNEY_EXPERIMENT_MANIFEST="$experiment_manifest"
export MINDJOURNEY_DATASET_PROVENANCE="$dataset_provenance"
export MINDJOURNEY_EXPECTED_SOURCE_SHA256="$expected_source_sha256"
export MINDJOURNEY_MODEL_DTYPE="bfloat16"
export MINDJOURNEY_ENABLE_THINKING="false"
if [[ "${P1_EXECUTION_SCOPE:-formal}" == "diagnostic_smoke" ]]; then
  diagnostic_host="${P1_DIAGNOSTIC_HOST:?P1_DIAGNOSTIC_HOST is required for diagnostic smoke}"
  if [[ "$P1_SPEC_DIAGNOSTIC_ONLY" != "1" \
        || ( "$diagnostic_host" != "A100-1" && "$diagnostic_host" != "A100-2" ) ]]; then
    echo "Diagnostic smoke requires the a10040 profile and host A100-1 or A100-2." >&2
    exit 2
  fi
  export MINDJOURNEY_HARDWARE="${diagnostic_host}:A100-40GB:TP${P1_SPEC_TP}+SVC1:diagnostic-smoke"
else
  export MINDJOURNEY_HARDWARE="DAAI:${P1_SPEC_ACCELERATOR}:TP${P1_SPEC_TP}+SVC1"
fi
export MINDJOURNEY_ENV_ID="${P1_ENV_ID:-qwen0280-svc-v1}"
export QWEN_REVISION="$P1_SPEC_REVISION"
export QWEN_CONTEXT_LIMIT=65536
export QWEN_MAX_TOKENS=1024
export QWEN_VLLM_VERSION=0.28.0
export SVC_REVISION="e538e251c1009e9a41cf8b7fee5f21332a1960de"
export SVC_WEIGHT_SHA256="10e69ea003c313e6bdfc7ee40376d1c19ea6036c20bd384e94b483dec8350396"
export SVC_STRICT_LOAD=1

# These are the settings used by the paper-aligned SVC SAT reproduction.  They
# are intentionally literal here so scheduling overrides cannot silently
# change the method while moving between H20 and A100-80 nodes.
exec "$svc_python" pipelines/pipeline_svc_scaling_spatial_beam_search.py \
  --vlm_model_name "$P1_SPEC_MODEL_ID" \
  --vlm_qa_model_name "None" \
  --num_questions "$num_questions" \
  --output_dir "$output_base" \
  --input_dir "$input_dir" \
  --scaling_strategy "spatial_beam_search" \
  --question_type "None" \
  --helpful_score_threshold 8 \
  --exploration_score_threshold 8 \
  --max_images "$max_images" \
  --sampling_interval_angle 9 \
  --sampling_interval_meter 0.25 \
  --fixed_rotation_magnitudes 27 \
  --fixed_forward_magnitudes 0.75 \
  --max_turn_angle 60 \
  --max_forward_distance 1.5 \
  --max_steps_per_question 3 \
  --num_top_candidates 18 \
  --num_beams 2 \
  --max_tries_gpt 5 \
  --num_frames 9 \
  --frame_interval 3 \
  --max_inference_batch_size 1 \
  --split "$split" \
  --num_question_chunks "$num_chunks" \
  --question_chunk_idx "$chunk_index" \
  --task "img2trajvid_s-prob" \
  --replace_or_include_input True \
  --cfg 4.0 \
  --guider 1 \
  --L_short 576 \
  --num_targets 8 \
  --use_traj_prior True \
  --chunk_strategy "interp"
