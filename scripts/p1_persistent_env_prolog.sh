#!/usr/bin/env bash

# Source-only prolog for P1 jobs owned by the DAAI 24482277 account.  Unlike
# p1_env_prolog.sh, this reads only an explicitly selected shared environment
# root and has no dependency on another user's home directory.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "Source scripts/p1_persistent_env_prolog.sh; do not execute it." >&2
  exit 2
fi

p1_persistent_env_root="${P1_PERSISTENT_ENV_ROOT:-}"
if [[ "$p1_persistent_env_root" != /* || ! -d "$p1_persistent_env_root" ]]; then
  echo "P1_PERSISTENT_ENV_ROOT must be an existing absolute directory." >&2
  return 1
fi
p1_persistent_env_root="$(cd -P -- "$p1_persistent_env_root" && pwd)"
p1_complete_file="$p1_persistent_env_root/COMPLETE"
p1_versions_file="$p1_persistent_env_root/VERSIONS.txt"
p1_qwen_freeze="$p1_persistent_env_root/qwen.freeze.txt"
p1_svc_freeze="$p1_persistent_env_root/svc.freeze.txt"
p1_qwen_python="$p1_persistent_env_root/qwen/bin/python"
p1_qwen_vllm="$p1_persistent_env_root/qwen/bin/vllm"
p1_qwen_ninja="$p1_persistent_env_root/qwen/bin/ninja"
p1_svc_python="$p1_persistent_env_root/svc/bin/python"

for p1_required_file in "$p1_complete_file" "$p1_versions_file" \
    "$p1_qwen_freeze" "$p1_svc_freeze"; do
  if [[ ! -r "$p1_required_file" ]]; then
    echo "Persistent environment is incomplete; missing $p1_required_file." >&2
    return 1
  fi
done
for p1_required_executable in "$p1_qwen_python" "$p1_qwen_vllm" \
    "$p1_qwen_ninja" "$p1_svc_python"; do
  if [[ ! -x "$p1_required_executable" ]]; then
    echo "Persistent environment is incomplete; not executable: $p1_required_executable" >&2
    return 1
  fi
done

p1_manifest_value() {
  local p1_manifest="$1"
  local p1_key="$2"
  local p1_matches
  p1_matches="$(grep -F -- "$p1_key=" "$p1_manifest" || true)"
  if [[ -z "$p1_matches" || "$p1_matches" == *$'\n'* ]]; then
    printf 'Expected exactly one %s entry in %s.\n' "$p1_key" "$p1_manifest" >&2
    return 1
  fi
  printf '%s\n' "${p1_matches#*=}"
}

p1_sha256_file() {
  local p1_path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$p1_path" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$p1_path" | awk '{print $1}'
  else
    echo "Neither sha256sum nor shasum is available for manifest validation." >&2
    return 1
  fi
}

if [[ "$(p1_manifest_value "$p1_complete_file" format)" != "mindjourney-p1-persistent-v1" \
      || "$(p1_manifest_value "$p1_versions_file" format)" != "mindjourney-p1-persistent-v1" ]]; then
  echo "Persistent environment manifest format is unsupported." >&2
  return 1
fi
for p1_checked_file in \
    "versions_sha256:$p1_versions_file" \
    "qwen_freeze_sha256:$p1_qwen_freeze" \
    "svc_freeze_sha256:$p1_svc_freeze"; do
  p1_checksum_key="${p1_checked_file%%:*}"
  p1_checksum_path="${p1_checked_file#*:}"
  p1_expected_checksum="$(p1_manifest_value "$p1_complete_file" "$p1_checksum_key")" || return 1
  p1_actual_checksum="$(p1_sha256_file "$p1_checksum_path")" || return 1
  if [[ "$p1_expected_checksum" != "$p1_actual_checksum" ]]; then
    echo "Persistent environment checksum mismatch for $p1_checksum_path." >&2
    return 1
  fi
done

for p1_expected_version in \
    "python_module=miniconda/py312_24.7.1-0" \
    "qwen.vllm=0.28.0" \
    "svc.torch=2.9.0" \
    "svc.transformers=4.46.3" \
    "svc.diffusers=0.35.1" \
    "svc.huggingface-hub=0.35.0" \
    "svc.numpy=1.26.0" \
    "svc.numpy-quaternion=2024.0.3" \
    "svc.pipeline_import=ok"; do
  if ! grep -Fqx -- "$p1_expected_version" "$p1_versions_file"; then
    echo "Persistent environment does not contain required version: $p1_expected_version" >&2
    return 1
  fi
done
if [[ "$(p1_manifest_value "$p1_versions_file" qwen.python)" != 3.12.* \
      || "$(p1_manifest_value "$p1_versions_file" svc.python)" != 3.12.* ]]; then
  echo "Both persistent environments must use Python 3.12." >&2
  return 1
fi

p1_vllm_cli_version="$($p1_qwen_vllm --version)" || return 1
if [[ "$p1_vllm_cli_version" != *"0.28.0"* ]]; then
  echo "Expected persistent vLLM 0.28.0, found: $p1_vllm_cli_version" >&2
  return 1
fi
p1_ninja_cli_version="$($p1_qwen_ninja --version)" || return 1
p1_recorded_ninja_version="$(p1_manifest_value "$p1_versions_file" qwen.ninja)" || return 1
if [[ -z "$p1_ninja_cli_version" || "$p1_ninja_cli_version" != "$p1_recorded_ninja_version" ]]; then
  echo "Persistent ninja version does not match VERSIONS.txt." >&2
  return 1
fi
"$p1_qwen_python" - <<'PY' || return 1
import importlib.metadata as metadata
import sys

assert sys.version_info[:2] == (3, 12), sys.version
assert metadata.version("vllm") == "0.28.0"
PY

p1_repo_dir="${P1_REPO_DIR:-}"
if [[ "$p1_repo_dir" != /* || ! -d "$p1_repo_dir/pipelines" \
      || ! -d "$p1_repo_dir/stable_virtual_camera" ]]; then
  echo "P1_REPO_DIR must identify the checked-out MindJourney repository." >&2
  return 1
fi
p1_repo_dir="$(cd -P -- "$p1_repo_dir" && pwd)"
export PYTHONPATH="$p1_repo_dir:$p1_repo_dir/pipelines:$p1_repo_dir/stable_virtual_camera${PYTHONPATH:+:$PYTHONPATH}"
"$p1_svc_python" - <<'PY' || return 1
import importlib.metadata as metadata
import sys

expected = {
    "torch": "2.9.0",
    "transformers": "4.46.3",
    "diffusers": "0.35.1",
    "huggingface-hub": "0.35.0",
    "numpy": "1.26.0",
    "numpy-quaternion": "2024.0.3",
}
assert sys.version_info[:2] == (3, 12), sys.version
for distribution, version in expected.items():
    actual = metadata.version(distribution)
    if actual != version:
        raise SystemExit(f"expected {distribution} {version}, found {actual}")
import pipelines.pipeline_svc_scaling_spatial_beam_search  # noqa: F401,E402
PY

export P1_SVC_PYTHON="$p1_svc_python"
export P1_HF_PYTHON="$p1_qwen_python"
export P1_VLLM_BIN="$p1_qwen_vllm"
export P1_ENV_ID="mindjourney-p1-persistent-v1"
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

unset p1_actual_checksum p1_checked_file p1_checksum_key p1_checksum_path
unset p1_complete_file p1_expected_checksum p1_expected_version
unset p1_ninja_cli_version p1_recorded_ninja_version
unset p1_persistent_env_root p1_qwen_freeze p1_qwen_ninja p1_qwen_python
unset p1_qwen_vllm p1_repo_dir p1_required_executable p1_required_file
unset p1_svc_freeze p1_svc_python p1_versions_file p1_vllm_cli_version
unset -f p1_manifest_value p1_sha256_file
