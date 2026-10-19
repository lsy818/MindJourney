#!/bin/bash
set -euo pipefail
umask 077
cd /home/comp/24482277/mindjourney_spatialrgpt_20261018_v5
source environment.sh
source stage_environment.sh
export MJ_CONNECT_TO=openrouter.ai:443:172.27.244.19:18447
r=/home/datasets/shiyang/mindjourney_spatialrgpt_20261018
if [ "$1" = audit-dev ]; then
    "$MJ_PYTHON" audit.py --shared "$r/shared-preflight" --output "$r/dev-v2" --preflight
elif [ "$1" = audit-full ]; then
    test ! -e "$r/FINAL_VERIFIED.json"
    "$MJ_PYTHON" audit.py --shared "$r/shared" --output "$r/full-v5"
else
    shard="${1:?shard required}"
    exec 9>"$r/RECOVERY_V5/full-shard-$shard.lock"
    flock -n 9
    test ! -e "$r/RECOVERY_V5/full-shard-$shard.started"
    date -u > "$r/RECOVERY_V5/full-shard-$shard.started"
    "$MJ_PYTHON" worker.py --shared "$r/shared" --output "$r/full-v5" --keyfile /home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key --mode full --shard "$shard" --shards 4
fi
