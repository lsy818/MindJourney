#!/bin/bash
set -euo pipefail
umask 077
c=/home/comp/24482277/mindjourney_spatialrgpt_20261018_v5
v=/home/comp/24482277/mindjourney_spatialrgpt_continuation_v7
cd "$c"
source "$c/environment.sh"
source "$c/stage_environment.sh"
export MJ_CONNECT_TO=openrouter.ai:443:172.27.244.19:18447
if [ "$1" = audit ]; then
    exec "$MJ_PYTHON" "$v/audit_v6.py" --shared /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/shared --output /home/datasets/shiyang/mindjourney_spatialrgpt_20261018/full-v5
fi
exec "$MJ_PYTHON" "$v/run_remaining.py" "$1"
