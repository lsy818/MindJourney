#!/bin/bash
set -euo pipefail
umask 077
cd /home/comp/24482277/mindjourney_spatialrgpt_20261018_v5
source environment.sh
source stage_environment.sh
export MJ_CONNECT_TO=openrouter.ai:443:172.27.244.19:18447
r=/home/datasets/shiyang/mindjourney_spatialrgpt_20261018
if [ "${1:-}" = replay ]; then
    "$MJ_PYTHON" -m unittest test_adapter test_recovery > "$r/RECOVERY_V5/tests.private.log" 2>&1
    "$MJ_PYTHON" worker.py --shared "$r/shared-preflight" --output "$r/dev-v2" --keyfile /home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key --mode dev --recovery-baseline "$r/RECOVERY_V5/BASELINE.json" --replay-check > "$r/RECOVERY_V5/replay-summary.json" 2> "$r/RECOVERY_V5/replay.private.log"
    "$MJ_PYTHON" - <<'PY'
import json,time
from pathlib import Path
from common import atomic,sha,code_identity
r=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/RECOVERY_V5')
s=json.loads((r/'replay-summary.json').read_text())
assert s['offline_replay_passed'] and s['checked_saved_items']==2 and s['network_calls']==s['gpu_calls']==0
atomic(r/'OFFLINE_REPLAY.json',{'passed':True,'summary':s,'baseline_sha256':sha(r/'BASELINE.json'),'code_identity':code_identity(),'unix':time.time()})
print(json.dumps({'offline_replay_passed':True,'saved_items':2,'network_calls':0,'gpu_calls':0,'proof_sha256':sha(r/'OFFLINE_REPLAY.json')}))
PY
else
    shard="${1:?shard required}"
    "$MJ_PYTHON" - <<'PY'
import json
from pathlib import Path
from common import sha,code_identity
r=Path('/home/datasets/shiyang/mindjourney_spatialrgpt_20261018/RECOVERY_V5')
p=json.loads((r/'OFFLINE_REPLAY.json').read_text());assert p['passed'] and p['baseline_sha256']==sha(r/'BASELINE.json') and p['code_identity']==code_identity()
t=json.loads((r/'TRANSPORT_PASSED.json').read_text());assert t['passed'] and t['authenticated'] is False and t['uploaded_all']
PY
    exec 9>"$r/RECOVERY_V5/dev-shard-$shard.lock"
    flock -n 9
    test ! -e "$r/RECOVERY_V5/dev-shard-$shard.started"
    date -u > "$r/RECOVERY_V5/dev-shard-$shard.started"
    "$MJ_PYTHON" worker.py --shared "$r/shared-preflight" --output "$r/dev-v2" --keyfile /home/comp/24482277/.config/mindjourney-spatialrgpt-20261018/openrouter.key --mode dev --recovery-baseline "$r/RECOVERY_V5/BASELINE.json" --shard "$shard" --shards 4
fi
