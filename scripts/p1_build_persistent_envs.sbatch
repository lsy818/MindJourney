#!/usr/bin/env bash
#SBATCH --account=daai
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --no-requeue

# Build the two immutable Python environments used by the P1 DAAI jobs.
# This file is itself an sbatch entry point; it deliberately refuses to run
# on a login node. A failed build can only be reused with an explicit
# --resume and a matching BUILDING marker/known builder-owned layout.
set -euo pipefail
umask 0027

usage() {
  echo "Usage: sbatch $0 [--resume] /absolute/shared/P1_PERSISTENT_ENV_ROOT" >&2
}

resume=0
if (( $# == 2 )) && [[ "$1" == "--resume" ]]; then
  resume=1
  shift
fi
if (( $# != 1 )); then
  usage
  exit 2
fi
if [[ ! "${SLURM_JOB_ID:-}" =~ ^[0-9]+$ || -z "${SLURM_JOB_NODELIST:-}" ]]; then
  echo "This environment builder must run inside a Slurm compute job." >&2
  exit 2
fi

target_root="$1"
if [[ "$target_root" != /* || "$target_root" == "/" || "$target_root" == *$'\n'* ]]; then
  echo "The target root must be a safe absolute path other than /." >&2
  exit 2
fi
target_parent="$(dirname -- "$target_root")"
target_name="$(basename -- "$target_root")"
if [[ "$target_name" == "." || "$target_name" == ".." || ! -d "$target_parent" ]]; then
  echo "The target parent must already exist, and the target name must be explicit." >&2
  exit 2
fi
target_parent="$(cd -P -- "$target_parent" && pwd)"
target_root="$target_parent/$target_name"
if [[ -L "$target_root" || ( -e "$target_root" && ! -d "$target_root" ) ]]; then
  echo "The target root must be a directory, not a file or symbolic link: $target_root" >&2
  exit 1
fi
if [[ ! -w "$target_parent" ]]; then
  echo "The target parent is not writable: $target_parent" >&2
  exit 1
fi

if ! command -v flock >/dev/null 2>&1; then
  echo "flock is required to serialize persistent environment builds." >&2
  exit 1
fi
build_lock="$target_parent/.${target_name}.p1-build.lock"
if [[ -L "$build_lock" || ( -e "$build_lock" && ! -f "$build_lock" ) ]]; then
  echo "The build lock must be a regular file: $build_lock" >&2
  exit 1
fi
exec 9>>"$build_lock"
if ! flock -n 9; then
  echo "Another build currently owns this target: $target_root" >&2
  exit 1
fi

if (( resume == 1 )); then
  if [[ ! -d "$target_root" || -L "$target_root" \
        || ! -d "$target_root/.BUILDING" || -L "$target_root/.BUILDING" ]]; then
    echo "--resume requires an existing partial target with a .BUILDING directory." >&2
    exit 1
  fi
  if [[ -e "$target_root/COMPLETE" ]]; then
    echo "Refusing to resume an environment already marked COMPLETE." >&2
    exit 1
  fi
  while IFS= read -r -d '' partial_entry; do
    partial_name="$(basename -- "$partial_entry")"
    case "$partial_name" in
      .BUILDING|.BUILD_CONTRACT.txt|.BUILD_CONTRACT.txt.tmp.*|qwen|svc|uv-cache|.build-cache|stable_virtual_camera.requirements.txt|qwen.freeze.txt|svc.freeze.txt|VERSIONS.txt|VERSIONS.txt.tmp.*|COMPLETE.tmp.*) ;;
      *)
        echo "Refusing unknown entry in partial environment: $partial_entry" >&2
        exit 1
        ;;
    esac
  done < <(find "$target_root" -mindepth 1 -maxdepth 1 -print0)
else
  if [[ -d "$target_root" ]] && find "$target_root" -mindepth 1 -print -quit | grep -q .; then
    echo "Refusing to overwrite a non-empty persistent environment root: $target_root" >&2
    exit 1
  fi
  if [[ ! -d "$target_root" ]]; then
    mkdir -- "$target_root"
  fi
  if ! mkdir -- "$target_root/.BUILDING"; then
    echo "The target stopped being empty before its BUILDING marker was created: $target_root" >&2
    exit 1
  fi
fi
if find "$target_root/.BUILDING" -mindepth 1 -print -quit | grep -q .; then
  echo "The .BUILDING marker must be an empty directory." >&2
  exit 1
fi

repo_dir="${P1_REPO_DIR:-${SLURM_SUBMIT_DIR:-}}"
if [[ "$repo_dir" != /* || ! -d "$repo_dir" ]]; then
  echo "P1_REPO_DIR (or SLURM_SUBMIT_DIR) must identify an absolute repository directory." >&2
  exit 1
fi
repo_dir="$(cd -P -- "$repo_dir" && pwd)"
requirements_file="$repo_dir/requirements_svc.txt"
svc_project="$repo_dir/stable_virtual_camera"
uv_bin="/home/comp/24482277/.local/bin/uv"
python_module="miniconda/py312_24.7.1-0"
if [[ ! -r "$requirements_file" || ! -r "$svc_project/pyproject.toml" ]]; then
  echo "The repository is missing requirements_svc.txt or stable_virtual_camera/pyproject.toml." >&2
  exit 1
fi
if [[ ! -x "$uv_bin" ]]; then
  echo "Required uv executable is unavailable: $uv_bin" >&2
  exit 1
fi

# Slurm shells do not always inherit the environment-modules shell function.
if ! type module >/dev/null 2>&1; then
  for module_init in /etc/profile.d/modules.sh /usr/share/Modules/init/bash; do
    if [[ -r "$module_init" ]]; then
      # shellcheck disable=SC1090
      source "$module_init"
      break
    fi
  done
fi
if ! type module >/dev/null 2>&1; then
  echo "The environment-modules command is unavailable inside this Slurm job." >&2
  exit 1
fi
module load "$python_module"
base_python="$(command -v python 2>/dev/null || true)"
if [[ -z "$base_python" || ! -x "$base_python" ]]; then
  echo "Module $python_module did not provide an executable python." >&2
  exit 1
fi
"$base_python" - <<'PY'
import sys

if sys.version_info[:2] != (3, 12):
    raise SystemExit(f"expected module Python 3.12, found {sys.version}")
PY

sha256_file() {
  "$base_python" - "$1" <<'PY'
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
print(digest.hexdigest())
PY
}

requirements_sha256="$(sha256_file "$requirements_file")"
svc_pyproject_sha256="$(sha256_file "$svc_project/pyproject.toml")"
build_contract_file="$target_root/.BUILD_CONTRACT.txt"
expected_build_contract="$(printf '%s\n' \
  "format=mindjourney-p1-persistent-build-v2" \
  "target_root=$target_root" \
  "repo_dir=$repo_dir" \
  "python_module=$python_module" \
  "uv_bin=$uv_bin" \
  "uv_version=$($uv_bin --version)" \
  "requirements_svc.sha256=$requirements_sha256" \
  "stable_virtual_camera.pyproject.sha256=$svc_pyproject_sha256")"
if [[ -e "$build_contract_file" ]]; then
  if [[ ! -f "$build_contract_file" || ! -r "$build_contract_file" \
        || "$(<"$build_contract_file")" != "$expected_build_contract" ]]; then
    echo "Partial environment build contract does not match this builder invocation." >&2
    exit 1
  fi
else
  contract_tmp="$build_contract_file.tmp.$$"
  printf '%s\n' "$expected_build_contract" >"$contract_tmp"
  mv -- "$contract_tmp" "$build_contract_file"
fi

build_cache_root="$target_root/.build-cache"
export UV_CACHE_DIR="$target_root/uv-cache"
export UV_PYTHON_DOWNLOADS=never
export UV_NO_PROGRESS=1
# puccinialin selects its Rust installation through the XDG cache location
# when cargo is absent. Setting both XDG_CACHE_HOME and CARGO_HOME keeps every
# Rust registry/toolchain file off the quota-limited login-home filesystem.
export XDG_CACHE_HOME="$build_cache_root/xdg-cache"
export CARGO_HOME="$XDG_CACHE_HOME/puccinialin/cargo"
export CARGO_TARGET_DIR="$build_cache_root/cargo-target"
export RUSTUP_HOME="$XDG_CACHE_HOME/puccinialin/rustup"
export TMPDIR="$build_cache_root/tmp"
export PIP_CACHE_DIR="$build_cache_root/pip-cache"
mkdir -p -- \
  "$UV_CACHE_DIR" "$XDG_CACHE_HOME" "$CARGO_HOME" "$CARGO_TARGET_DIR" \
  "$RUSTUP_HOME" "$TMPDIR" "$PIP_CACHE_DIR"

qwen_env="$target_root/qwen"
svc_env="$target_root/svc"
ensure_venv() {
  local env_path="$1"
  if [[ -e "$env_path" ]]; then
    if [[ -L "$env_path" || ! -d "$env_path" \
          || ! -r "$env_path/pyvenv.cfg" || ! -x "$env_path/bin/python" ]]; then
      echo "Refusing to reuse an invalid partial virtual environment: $env_path" >&2
      return 1
    fi
    "$env_path/bin/python" - "$env_path" <<'PY'
import pathlib
import sys

expected = pathlib.Path(sys.argv[1]).resolve()
actual = pathlib.Path(sys.prefix).resolve()
if sys.version_info[:2] != (3, 12) or actual != expected:
    raise SystemExit(
        f"partial environment mismatch: expected Python 3.12 at {expected}, "
        f"found {sys.version} at {actual}"
    )
PY
  else
    "$uv_bin" venv --python "$base_python" "$env_path"
  fi
}
ensure_venv "$qwen_env"
ensure_venv "$svc_env"
qwen_python="$qwen_env/bin/python"
svc_python="$svc_env/bin/python"

# Keep the serving stack completely separate from the SVC stack.  FlashInfer
# starts ninja by name, so ninja must be installed beside the vLLM entry point.
"$uv_bin" pip install --python "$qwen_python" \
  "vllm==0.28.0" \
  "ninja"

# The upstream SVC metadata pins NumPy 1.24.4, while the verified MindJourney
# combination intentionally uses NumPy 1.26.0.  Resolve every other declared
# SVC dependency directly from the checked-in pyproject, then install the
# checked-out SVC package itself without re-resolving that stale NumPy pin.
svc_project_requirements="$target_root/stable_virtual_camera.requirements.txt"
"$base_python" - "$svc_project/pyproject.toml" "$svc_project_requirements" <<'PY'
import pathlib
import re
import sys
import tomllib

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
dependencies = tomllib.loads(source.read_text(encoding="utf-8"))["project"]["dependencies"]
filtered = []
for dependency in dependencies:
    name = re.split(r"[\s\[<>=!~;]", dependency, maxsplit=1)[0]
    normalized = name.lower().replace("_", "-").replace(".", "-")
    if normalized != "numpy":
        filtered.append(dependency)
target.write_text("\n".join(filtered) + "\n", encoding="utf-8")
PY
"$uv_bin" pip install --python "$svc_python" \
  --requirement "$svc_project_requirements" \
  --requirement "$requirements_file" \
  "torch==2.9.0" \
  "transformers==4.46.3" \
  "diffusers==0.35.1" \
  "huggingface-hub==0.35.0" \
  "numpy==1.26.0" \
  "numpy-quaternion==2024.0.3"
"$uv_bin" pip install --python "$svc_python" --no-deps --editable "$svc_project"

if [[ ! -x "$qwen_env/bin/vllm" || ! -x "$qwen_env/bin/ninja" ]]; then
  echo "The Qwen environment is missing vllm or the adjacent ninja executable." >&2
  exit 1
fi

qwen_python_version="$($qwen_python -c 'import platform; print(platform.python_version())')"
qwen_vllm_version="$($qwen_python -c 'import importlib.metadata as m; print(m.version("vllm"))')"
qwen_ninja_version="$($qwen_env/bin/ninja --version)"
svc_python_version="$($svc_python -c 'import platform; print(platform.python_version())')"
svc_torch_version="$($svc_python -c 'import importlib.metadata as m; print(m.version("torch"))')"
svc_transformers_version="$($svc_python -c 'import importlib.metadata as m; print(m.version("transformers"))')"
svc_diffusers_version="$($svc_python -c 'import importlib.metadata as m; print(m.version("diffusers"))')"
svc_hf_hub_version="$($svc_python -c 'import importlib.metadata as m; print(m.version("huggingface-hub"))')"
svc_numpy_version="$($svc_python -c 'import importlib.metadata as m; print(m.version("numpy"))')"
svc_quaternion_version="$($svc_python -c 'import importlib.metadata as m; print(m.version("numpy-quaternion"))')"

[[ "$qwen_python_version" == 3.12.* ]] || { echo "Qwen environment is not Python 3.12." >&2; exit 1; }
[[ "$qwen_vllm_version" == "0.28.0" ]] || { echo "Expected vLLM 0.28.0, found $qwen_vllm_version." >&2; exit 1; }
[[ "$svc_python_version" == 3.12.* ]] || { echo "SVC environment is not Python 3.12." >&2; exit 1; }
[[ "$svc_torch_version" == "2.9.0" ]] || { echo "Expected torch 2.9.0, found $svc_torch_version." >&2; exit 1; }
[[ "$svc_transformers_version" == "4.46.3" ]] || { echo "Expected transformers 4.46.3, found $svc_transformers_version." >&2; exit 1; }
[[ "$svc_diffusers_version" == "0.35.1" ]] || { echo "Expected diffusers 0.35.1, found $svc_diffusers_version." >&2; exit 1; }
[[ "$svc_hf_hub_version" == "0.35.0" ]] || { echo "Expected huggingface-hub 0.35.0, found $svc_hf_hub_version." >&2; exit 1; }
[[ "$svc_numpy_version" == "1.26.0" ]] || { echo "Expected numpy 1.26.0, found $svc_numpy_version." >&2; exit 1; }
[[ "$svc_quaternion_version" == "2024.0.3" ]] || { echo "Expected numpy-quaternion 2024.0.3, found $svc_quaternion_version." >&2; exit 1; }

pipeline_pythonpath="$repo_dir:$repo_dir/pipelines:$repo_dir/stable_virtual_camera"
PYTHONPATH="$pipeline_pythonpath" "$svc_python" - <<'PY'
import pipelines.pipeline_svc_scaling_spatial_beam_search  # noqa: F401
PY

"$uv_bin" pip freeze --python "$qwen_python" | LC_ALL=C sort >"$target_root/qwen.freeze.txt"
"$uv_bin" pip freeze --python "$svc_python" | LC_ALL=C sort >"$target_root/svc.freeze.txt"
repo_commit="$(git -C "$repo_dir" rev-parse HEAD 2>/dev/null || echo unavailable)"
svc_project_requirements_sha256="$(sha256_file "$svc_project_requirements")"
build_contract_sha256="$(sha256_file "$build_contract_file")"
versions_tmp="$target_root/VERSIONS.txt.tmp.$$"
printf '%s\n' \
  "format=mindjourney-p1-persistent-v1" \
  "python_module=$python_module" \
  "uv=$($uv_bin --version)" \
  "qwen.python=$qwen_python_version" \
  "qwen.vllm=$qwen_vllm_version" \
  "qwen.ninja=$qwen_ninja_version" \
  "svc.python=$svc_python_version" \
  "svc.torch=$svc_torch_version" \
  "svc.transformers=$svc_transformers_version" \
  "svc.diffusers=$svc_diffusers_version" \
  "svc.huggingface-hub=$svc_hf_hub_version" \
  "svc.numpy=$svc_numpy_version" \
  "svc.numpy-quaternion=$svc_quaternion_version" \
  "svc.pipeline_import=ok" \
  "repo.commit=$repo_commit" \
  "requirements_svc.sha256=$requirements_sha256" \
  "stable_virtual_camera.pyproject.sha256=$svc_pyproject_sha256" \
  "stable_virtual_camera.requirements.sha256=$svc_project_requirements_sha256" \
  "build.contract.sha256=$build_contract_sha256" \
  "build.cache_root=$build_cache_root" \
  "build.cargo_home=$CARGO_HOME" \
  "build.cargo_target_dir=$CARGO_TARGET_DIR" \
  "build.xdg_cache_home=$XDG_CACHE_HOME" \
  >"$versions_tmp"
mv -- "$versions_tmp" "$target_root/VERSIONS.txt"

versions_sha256="$(sha256_file "$target_root/VERSIONS.txt")"
qwen_freeze_sha256="$(sha256_file "$target_root/qwen.freeze.txt")"
svc_freeze_sha256="$(sha256_file "$target_root/svc.freeze.txt")"
complete_tmp="$target_root/COMPLETE.tmp.$$"
printf '%s\n' \
  "format=mindjourney-p1-persistent-v1" \
  "versions_sha256=$versions_sha256" \
  "qwen_freeze_sha256=$qwen_freeze_sha256" \
  "svc_freeze_sha256=$svc_freeze_sha256" \
  "slurm_job_id=$SLURM_JOB_ID" \
  "built_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  >"$complete_tmp"
rmdir -- "$target_root/.BUILDING"
mv -- "$complete_tmp" "$target_root/COMPLETE"
echo "Persistent P1 environments are complete at $target_root."
