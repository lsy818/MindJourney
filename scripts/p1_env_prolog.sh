#!/usr/bin/env bash

# Source-only Slurm prolog. It restores the pinned node-local Qwen/vLLM and
# SVC environments used by the validated SAT runs, then exports immutable SVC
# dependency metadata shared by all P1 jobs.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "Source scripts/p1_env_prolog.sh; do not execute it." >&2
  exit 2
fi

p1_env_helper="${P1_ENV_ARCHIVE_HELPER:-/home/comp/tyjiang/MindJourney/scripts/mindjourney_env_archive.sh}"
if [[ "$p1_env_helper" != /* || ! -r "$p1_env_helper" ]]; then
  echo "P1_ENV_ARCHIVE_HELPER must be a readable absolute path: $p1_env_helper" >&2
  return 1
fi
source "$p1_env_helper"
if ! declare -F mindjourney_restore_envs >/dev/null; then
  echo "Environment helper does not define mindjourney_restore_envs: $p1_env_helper" >&2
  return 1
fi
mindjourney_restore_envs

export P1_SVC_PYTHON="$SVC_PYTHON"
export P1_HF_PYTHON="$QWEN_PYTHON"
export P1_VLLM_BIN="$QWEN_VLLM_BIN"
export P1_CACHE_ROOT="${P1_CACHE_ROOT:-/home/datasets/shiyang/model_cache}"
export HF_HOME="${HF_HOME:-$P1_CACHE_ROOT/huggingface}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-$HF_HOME/datasets}"
export TORCH_HOME="${TORCH_HOME:-$P1_CACHE_ROOT/torch}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$P1_CACHE_ROOT/xdg}"
export PYTHONNOUSERSITE=1
export TOKENIZERS_PARALLELISM=false

export SVC_REVISION="e538e251c1009e9a41cf8b7fee5f21332a1960de"
export SVC_WEIGHT_SHA256="10e69ea003c313e6bdfc7ee40376d1c19ea6036c20bd384e94b483dec8350396"
export SVC_STRICT_LOAD=1
export SVC_VAE_REPO="sd2-community/stable-diffusion-2-1-base"
export SVC_VAE_REVISION="4e63672c03103b6c636b8fb4119ba982469b2955"
export SVC_VAE_SUBFOLDER="vae"
export SVC_VAE_SHA256="a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
export SVC_OPENCLIP_REPO="laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
export SVC_OPENCLIP_REVISION="1c2b8495b28150b8a4922ee1c8edee224c284c0c"
export SVC_OPENCLIP_FILENAME="open_clip_pytorch_model.bin"
export SVC_OPENCLIP_SHA256="9a78ef8e8c73fd0df621682e7a8e8eb36c6916cb3c16b291a082ecd52ab79cc4"
