#!/bin/bash
# Node-local copy of already validated dependencies, using the original locked stager.
test -n "${SLURM_JOB_ID:-}"
mj_env_source=/home/datasets/shiyang/daai_runtime/envs/p1-01ef26c-v1
mj_env_sha=4c3ccc5763b452719ee9564c6afbff63c9e13bfc1f0b6513ddfbfa0b4e5dec50
mj_base_python="$(readlink -f "$MJ_PYTHON")"
mj_local_root="$("$mj_base_python" -S frozen/scripts/p1_stage_local_env.py --source "$mj_env_source" --expected-sha256 "$mj_env_sha" --archive /home/datasets/shiyang/mindjourney_storage/deepseek_p3_environment_copy_20260922/4c3ccc5763b452719ee9564c6afbff63c9e13bfc1f0b6513ddfbfa0b4e5dec50.tar.zst)"
export MJ_PYTHON="$mj_local_root/svc/bin/python"
export XDG_CACHE_HOME="$mj_local_root/runtime-cache/xdg"
export TRITON_CACHE_DIR="$mj_local_root/runtime-cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$mj_local_root/runtime-cache/inductor"
mkdir -p "$XDG_CACHE_HOME" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR"
