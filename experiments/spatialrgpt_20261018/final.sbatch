#!/bin/bash
#SBATCH --job-name=mj-spatial-audit
#SBATCH --account=daai
#SBATCH --qos=daai_qos
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/final-slurm-%j.log
set -euo pipefail
umask 077
cd /home/comp/24482277/mindjourney_spatialrgpt_20261018_v2
source environment.sh
exec "$MJ_PYTHON" audit.py --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/full
