#!/bin/bash
#SBATCH --job-name=mj-spatial-full
#SBATCH --account=daai
#SBATCH --qos=daai_qos
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:a100:1
#SBATCH --constraint=cpu_xeon
#SBATCH --mem=128G
#SBATCH --time=1-00:00:00
#SBATCH --array=0-3%4
#SBATCH --output=/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/full-slurm-%A_%a.log
set -euo pipefail
umask 077
cd /home/comp/24482277/mindjourney_spatialrgpt_20261018
source environment.sh
source stage_environment.sh
exec "$MJ_PYTHON" worker.py --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/full --keyfile /home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key --mode full --shard "$SLURM_ARRAY_TASK_ID" --shards 4
