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
#SBATCH --time=04:00:00
#SBATCH --constraint=cpu_xeon
#SBATCH --output=/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/dev-v2-slurm-%j.log
set -euo pipefail
umask 077
cd /home/comp/24482277/mindjourney_spatialrgpt_20261018_v2
source environment.sh
source stage_environment.sh
"$MJ_PYTHON" worker.py --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared-preflight --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/dev-v2 --keyfile /home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key --mode dev
"$MJ_PYTHON" audit.py --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared-preflight --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/dev-v2 --preflight
