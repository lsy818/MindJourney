#!/usr/bin/env python3
"""Dispatch additional r8 shards; count every active array, preserve workers.

This is an external scheduler, not part of the frozen worker source set.
Default is read-only. --submit writes an append-only journal and submits jobs.
Pending shards count toward each experiment's cap, conservatively preventing
multiple arrays from exceeding the combined running limit.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
from datetime import datetime, timezone

ROOT = Path('/home/datasets/shiyang/daai_runtime/p1_runs')
REPO = Path('/home/comp/24482277/shiyang/MindJourney-p1-startup-r8-20260908')
SOURCE = 'e6d08e5a782bbf8f2521d25637cb197f52b7d8dfc1edf7cd29d403b6ac123e64'
PLANS = [
    ('mindcube', 'qwen35-27b', 'a100', 3, 11, 'submit-fast-r8-qwen35-27b-66831.out'),
    ('mindcube', 'qwen25vl-72b', 'h20', 2, 11, 'submit-h20-r8-qwen25vl-72b-66853.out'),
    ('mmsi', 'qwen38-27b', 'a100', 2, 10, 'submit-fast-r8-qwen38-27b-66833.out'),
    ('mmsi', 'qwen35-9b', 'a100', 1, 10, 'submit-fast-r8-qwen35-9b-66832.out'),
]


def queue():
    out = subprocess.check_output(['squeue', '-r', '-h', '-u', '24482277',
                                   '-o', '%i|%j|%T|%R'], text=True)
    return [dict(zip(('id', 'name', 'state', 'reason'), line.split('|', 3)))
            for line in out.splitlines() if line.strip()]


def key_values(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)


def prepare(plan, jobs, submit_limit):
    dataset, model, accelerator, cap, chunks, log = plan
    run_id = 'mj-p1-{}-{}-{}-fast-r8-20260908'.format(dataset, model, accelerator)
    run = ROOT / run_id
    manifest = key_values(run / 'launch_manifest.txt')
    assert manifest['run_id'] == run_id and manifest['source_sha256'] == SOURCE
    assert manifest['dtype'] == 'bfloat16' and manifest['max_model_len'] == '65536'
    assert manifest['accelerator'] == accelerator and manifest['num_chunks'] == str(chunks)
    job_name = 'mj-p1-{}-{}-array'.format(dataset, model)
    active = [j for j in jobs if j['name'] == job_name]
    active_indices = set()
    for job in active:
        # -r expands arrays. Refuse ambiguous/non-array jobs instead of guessing.
        index = job['id'].rsplit('_', 1)[-1]
        assert '_' in job['id'] and index.isdigit(), job
        assert int(index) not in active_indices, 'Duplicate active shard: ' + str(job)
        active_indices.add(int(index))
    parent = run / ('results_spatial_beam_search_qc' + str(chunks))
    completed = {i for i in range(chunks) if (parent / ('question_chunk_' + str(i)) / 'COMPLETE').exists()}
    # A previously successful scored question suffices; no imports or asset scans.
    successful = False
    for result in parent.glob('question_chunk_*/results.json'):
        data = json.loads(result.read_text())
        assert not data.get('skip_indices'), 'Skipped question requires review: ' + str(result)
        successful |= any(v.get('correct') or v.get('wrong') for v in data.get('progress', {}).values())
    assert successful, 'No successful inference evidence: ' + run_id
    capacity = min(max(0, cap - len(active)), max(0, submit_limit - len(jobs)))
    missing = [i for i in range(chunks) if i not in completed and i not in active_indices][:capacity]
    record = dict(run_id=run_id, cap=cap, completed=sorted(completed), active=active,
                  new_indices=missing, account_active=len(jobs))
    if not missing:
        return record, None
    lines = (ROOT / log).read_text().splitlines()
    commands = [line[8:] for line in lines if line.startswith('command=')]
    assert len(commands) == 1
    cmd = shlex.split(commands[0])
    assert cmd[0] == 'sbatch' and cmd[-1] == str(REPO / 'scripts/p1_array.sbatch')
    export_index = next(i for i, value in enumerate(cmd) if value.startswith('--export='))
    exports = dict(item.split('=', 1) for item in cmd[export_index][9:].split(','))
    assert exports['P1_RUN_ID'] == run_id and exports['P1_REPO_DIR'] == str(REPO)
    assert exports['P1_EXPECTED_SOURCE_SHA256'] == SOURCE
    if model == 'qwen25vl-72b':
        assert manifest['tensor_parallel_size'] == '2' and manifest['total_gpus'] == '3'
        assert '--gres=gpu:h20:3' in cmd
        exports['P1_GPU_MEMORY_UTILIZATION'] = '0.93'
        cmd[export_index] = '--export=' + ','.join(k + '=' + v for k, v in exports.items())
    else:
        assert '--gres=gpu:a100:2' in cmd
        # Restrict A100 additions to observed compatible 80GB nodes 11/12/15.
        index = next(i for i, value in enumerate(cmd) if value.startswith('--exclude='))
        cmd[index] = '--exclude=hkbugpudgx01,hkbugpusrv07,hkbugpusrv08,hkbugpusrv13,hkbugpusrv14'
    index = next(i for i, value in enumerate(cmd) if value.startswith('--array='))
    cmd[index] = '--array=' + ','.join(map(str, missing)) + '%' + str(capacity)
    record['command'] = shlex.join(cmd)
    return record, cmd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit', action='store_true')
    parser.add_argument('--submit-limit', type=int, default=10)
    args = parser.parse_args()
    assert 1 <= args.submit_limit <= 10
    lock = None
    journal = None
    if args.submit:
        os.umask(0o077)
        lock = (ROOT / 'parallel-dispatch.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        journal = (ROOT / ('parallel-dispatch-' + timestamp + '.jsonl')).open('x')
    known_submitted = []
    for plan in PLANS:
        jobs = queue()
        # Guard against scheduler visibility lag after an accepted submission.
        visible_ids = {job['id'] for job in jobs}
        jobs += [job for job in known_submitted if job['id'] not in visible_ids]
        record, cmd = prepare(plan, jobs, args.submit_limit)
        record['utc'] = datetime.now(timezone.utc).isoformat()
        if journal:
            journal.write(json.dumps(dict(event='intent', **record)) + '\n')
            journal.flush()
        if cmd and args.submit:
            response = subprocess.check_output(cmd, text=True).strip()
            job_id = response.split(';')[0]
            assert job_id.isdigit(), response
            record['submitted_job_id'] = job_id
            for i in record['new_indices']:
                known_submitted.append(dict(id=job_id + '_' + str(i), name='mj-p1-{}-{}-array'.format(plan[0], plan[1]), state='PENDING', reason='just submitted'))
            if journal:
                journal.write(json.dumps(dict(event='submitted', **record)) + '\n')
                journal.flush()
        print(json.dumps(record), flush=True)
    if journal:
        journal.close()
        lock.close()


if __name__ == '__main__':
    main()
