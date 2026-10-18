#!/bin/bash
#SBATCH --job-name=mj-spatial-dev
#SBATCH --account=daai
#SBATCH --qos=daai_qos
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --constraint=cpu_xeon
#SBATCH --output=/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/dev-v3-slurm-%j.log
set -euo pipefail
umask 077
cd /home/comp/24482277/mindjourney_spatialrgpt_20261018_v3
source environment.sh
source stage_environment.sh
export MJ_PROXY_RESOLVE="$("$MJ_PYTHON" -c 'import json; from pathlib import Path; d=json.loads(Path("/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/RECOVERY_V3/PROXY_ROUTE.json").read_text()); assert d["passed"] and d["host"]=="proxy.hkbu.edu.hk" and d["port"]==8080; print(d["resolve"])')"
mj_proxy_status="$(curl --silent --head --resolve "$MJ_PROXY_RESOLVE" --output /dev/null --connect-timeout 10 --max-time 20 --write-out '%{http_code}' https://openrouter.ai/api/v1/models)"
test "$mj_proxy_status" = 200
"$MJ_PYTHON" worker.py --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared-preflight --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/dev-v2 --keyfile /home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key --mode dev --recovery-baseline /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/RECOVERY_V3/BASELINE.json
"$MJ_PYTHON" audit.py --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared-preflight --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/dev-v2 --preflight
