"""Run the released CMA policy in the image runtime and export executed actions."""
import argparse
from contextlib import nullcontext
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

SPLITS = ('val_seen', 'val_unseen')
ACTIONS = ('STOP', 'MOVE_FORWARD', 'TURN_LEFT', 'TURN_RIGHT', 'LOOK_UP', 'LOOK_DOWN')
CHECKPOINT_SHA = 'e70dce940c6ae16aa63c41f3b2411884448a3ccd083b06da156d297b5f4a52dc'
SOURCE_REVISION = 'f46f93642d7ab96cc49611f8cfea09cecf2fa7f9'
CONFIG = Path(__file__).resolve().parents[1] / 'cma/inference.yaml'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def check_rows(rows, expected):
    ids = [r['episode_id'] for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Export episode coverage is not exact')
    for row in rows:
        actions = row['actions']
        if (not 1 <= len(actions) <= 500 or any(a not in ACTIONS for a in actions)
                or (len(actions) < 500 and actions[-1] != 'STOP')
                or 'STOP' in actions[:-1]):
            raise ValueError('Exported action sequence violates the task contract')


def policy_runtime(source):
    # Load the image's patched Habitat and runtime packages first. Extend only
    # the curated baseline package with public policy modules, not trainer imports.
    import habitat
    import habitat_sim
    if habitat.__version__ != '0.1.7' or habitat_sim.__version__ != '0.1.7':
        raise ValueError('HA-VLN 2.0 requires Habitat-Lab/Sim 0.1.7')
    import habitat_extensions
    import vlnce_baselines
    import vlnce_baselines.common
    baseline = source / 'agent/VLN-CE/vlnce_baselines'
    vlnce_baselines.__path__.append(str(baseline))
    vlnce_baselines.common.__path__.append(str(baseline / 'common'))
    from vlnce_baselines.models.cma_policy import CMAPolicy
    return CMAPolicy


def run_worker(task_path):
    task = json.loads(Path(task_path).read_text())
    import random
    import numpy as np
    import torch
    import yaml
    from unittest.mock import patch
    from gym import spaces
    from habitat import Config
    from havln_scoring.runtime import quiet_runtime
    source = Path(task['source'])
    policy_class = policy_runtime(source)
    from vlnce_baselines.config.default import get_config
    from vlnce_baselines.common.environments import HAVLNCEDaggerEnv
    from vlnce_baselines.common.utils import extract_instruction_tokens
    from habitat_baselines.utils.common import batch_obs
    import torchvision.models
    spec = yaml.safe_load(CONFIG.read_text())
    device = torch.device('cuda', task['gpu'])
    torch.cuda.set_device(device)
    torch.set_num_threads(1)
    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    checkpoint = torch.load(task['checkpoint'], map_location='cpu', weights_only=True)
    if set(checkpoint) != {'state_dict'} or len(checkpoint['state_dict']) != 521:
        raise ValueError('Expected the published inference-only CMA checkpoint')
    policy = None
    for job in task['jobs']:
        shard = Path(task['output']) / 'shards' / (job['key'] + '.json')
        if shard.exists():
            existing = json.loads(shard.read_text())
            if existing['fingerprint'] != task['fingerprint']:
                raise ValueError('Shard provenance differs')
            check_rows(existing['rows'], job['ids'])
            continue
        with (nullcontext() if os.environ.get('HAVLN_CMA_VERBOSE') == '1' else quiet_runtime()):
            config = get_config('/app/config/challenge_submission.yaml')
            config.defrost()
            config.MODEL = Config(spec['MODEL'])
            config.EVAL.SPLIT = job['split']
            cfg = config.TASK_CONFIG
            cfg.DATASET.SPLIT = job['split']
            cfg.DATASET.DATA_PATH = task['data'] + '/HA-R2R/{split}/{split}.json.gz'
            cfg.DATASET.SCENES_DIR = task['data'] + '/scene_datasets'
            cfg.DATASET.EPISODES_ALLOWED = job['ids']
            cfg.SIMULATOR.HABITAT_SIM_V0.GPU_DEVICE_ID = task['gpu']
            cfg.SIMULATOR.HUMAN_GLB_PATH = task['data'] + '/HAPS2_0'
            cfg.SIMULATOR.HUMAN_INFO_PATH = task['data'] + '/Multi-Human-Annotations/human_motion.json'
            cfg.SIMULATOR.RECOMPUTE_NAVMESH_PATH = task['data'] + '/recompute_navmesh'
            cfg.TASK.SENSORS = ['INSTRUCTION_SENSOR']
            cfg.TASK.MEASUREMENTS = []
            cfg.ENVIRONMENT.ITERATOR_OPTIONS.SHUFFLE = False
            cfg.ENVIRONMENT.ITERATOR_OPTIONS.MAX_SCENE_REPEAT_STEPS = -1
            cfg.SEED = 0
            config.freeze()
            if list(cfg.TASK.POSSIBLE_ACTIONS) != list(ACTIONS):
                raise ValueError('Image six-action vocabulary differs')
            with HAVLNCEDaggerEnv(config=config) as env:
                episodes = sorted(env.episodes, key=lambda e: int(e.episode_id))
                if set(str(e.episode_id) for e in episodes) != set(job['ids']):
                    raise ValueError('Runtime dataset coverage differs')
                env.habitat_env.episode_iterator = iter(episodes)
                if policy is None:
                    # No ImageNet download: every encoder parameter/buffer is
                    # subsequently replaced by the complete checkpoint, strictly.
                    factory = torchvision.models.resnet50
                    with patch.object(torchvision.models, 'resnet50',
                                      side_effect=lambda *a, **k: factory(weights=None)):
                        policy = policy_class.from_config(config, env.observation_space, spaces.Discrete(4))
                    policy.load_state_dict(checkpoint['state_dict'], strict=True)
                    policy.to(device).eval()
                rows = []
                for episode in episodes:
                    observation = env.reset()
                    if str(env.current_episode.episode_id) != str(episode.episode_id):
                        raise ValueError('Reset resolved the wrong episode')
                    hidden = torch.zeros(1, policy.net.num_recurrent_layers, 512, device=device)
                    previous = torch.zeros(1, 1, dtype=torch.long, device=device)
                    mask = torch.zeros(1, 1, dtype=torch.uint8, device=device)
                    trace = []
                    for step in range(500):
                        tokens = observation['instruction']['tokens']
                        if not tokens or max(tokens) >= 5401 or min(tokens) < 0:
                            raise ValueError('CMA requires vocabulary tokens, not BERT indices')
                        batch = batch_obs(extract_instruction_tokens([observation], 'instruction'), device)
                        with torch.no_grad():
                            action, hidden = policy.act(batch, hidden, previous, mask, deterministic=True)
                        index = int(action.item())
                        if not 0 <= index < 4:
                            raise ValueError('CMA produced an invalid action index')
                        name = spec['INFERENCE']['POLICY_ACTIONS'][index]
                        # Capture exactly the action sent to the simulator.
                        trace.append(name)
                        observation, _, done, _ = env.step(name)
                        previous.copy_(action)
                        mask.fill_(1)
                        if done:
                            if name != 'STOP' and env.habitat_env._elapsed_steps != 500:
                                raise ValueError('Unexpected early termination')
                            break
                    if not done:
                        raise ValueError('Runtime did not reach STOP or the official step limit')
                    rows.append({'episode_id': str(episode.episode_id), 'actions': trace})
                check_rows(rows, job['ids'])
                atomic_json(shard, {'fingerprint': task['fingerprint'], 'rows': rows})
        print('Completed ' + job['key'] + ': ' + str(len(rows)) + ' episodes', flush=True)


def export(args):
    source = args.source_root.resolve()
    state = json.loads((source / '.release.json').read_text())
    if state['revision'] != SOURCE_REVISION or any(sha256(source / p) != digest for p, digest in state['files'].items()):
        raise ValueError('Run setup_cma.sh to obtain the pinned public policy source')
    if sha256(args.checkpoint) != CHECKPOINT_SHA:
        raise ValueError('Checkpoint SHA-256 differs from the published ckpt.39')
    data, output = args.data_root.resolve(), args.output_dir.resolve()
    for relative in ('HAPS2_0', 'Multi-Human-Annotations/human_motion.json'):
        if not (data / relative).exists():
            raise ValueError('Missing data or unmounted symlink target: ' + str(data / relative))
    output.mkdir(parents=True, exist_ok=True)
    from havln_scoring.submission_contract import load_manifest
    manifest = load_manifest('/opt/havln-challenge/codabench/phase1/reference/public_reference_manifest.json')
    specs = {s.split: set(s.episode_ids) for s in manifest.splits}
    expected, jobs = {}, []
    hashes = {}
    for split in SPLITS:
        path = data / f'HA-R2R/{split}/{split}.json.gz'
        hashes[split] = sha256(path)
        episodes = json.load(gzip.open(path, 'rt'))['episodes']
        ids = [str(e['episode_id']) for e in episodes]
        if len(ids) != len(set(ids)) or set(ids) != specs[split]:
            raise ValueError('CMA input episode IDs differ from the released manifest')
        episodes.sort(key=lambda e: int(e['episode_id']))
        if args.episode_limit is not None:
            episodes = episodes[:args.episode_limit]
        expected[split] = [str(e['episode_id']) for e in episodes]
        scans = {}
        for episode in episodes:
            scan = Path(episode['scene_id']).parent.name
            scene = data / 'scene_datasets/mp3d' / scan / (scan + '.glb')
            if not scene.is_file():
                raise ValueError('Missing licensed scene or unmounted symlink target: ' + str(scene))
            scans.setdefault(scan, []).append(str(episode['episode_id']))
        jobs.extend({'key': split + '-' + scan, 'split': split, 'ids': ids}
                    for scan, ids in sorted(scans.items()))
    import habitat
    import habitat_sim
    import torch
    runtime = {'habitat': habitat.__version__, 'habitat_sim': habitat_sim.__version__,
               'torch': torch.__version__,
               'simulator': sha256(Path(habitat.__file__).parent / 'sims/habitat_simulator/habitat_simulator.py'),
               'task': sha256('/opt/havln-challenge/scoring/havln_scoring/config/six_action_task.yaml')}
    if runtime['habitat'] != '0.1.7' or runtime['habitat_sim'] != '0.1.7':
        raise ValueError('Use the released HA-VLN 2.0 Habitat 0.1.7 image')
    identity = {'checkpoint': CHECKPOINT_SHA, 'source': SOURCE_REVISION, 'runtime': runtime,
                'config': sha256(CONFIG), 'datasets': hashes, 'episode_limit': args.episode_limit,
                'data_root': str(data),
                'human_annotations': sha256(data / 'Multi-Human-Annotations/human_motion.json'),
                'exporter': sha256(__file__)}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    receipt = output / 'export_metadata.json'
    if receipt.exists() and json.loads(receipt.read_text())['fingerprint'] != fingerprint:
        raise ValueError('Output directory belongs to a different export; use a fresh directory')
    atomic_json(receipt, {'fingerprint': fingerprint, 'identity': identity, 'complete': False})
    processes, logs = [], []
    try:
        for i, gpu in enumerate(args.gpu_ids):
            task = dict(data=str(data), output=str(output), source=str(source),
                        checkpoint=str(args.checkpoint.resolve()), gpu=gpu,
                        fingerprint=fingerprint, jobs=jobs[i::len(args.gpu_ids)])
            task_path = output / f'worker-{gpu}.json'
            atomic_json(task_path, task)
            log = (output / f'worker-{gpu}.log').open('a')
            logs.append(log)
            processes.append(subprocess.Popen([sys.executable, __file__, '--worker-task', str(task_path)],
                                              stdout=log, stderr=subprocess.STDOUT))
        codes = [p.wait() for p in processes]
        if any(codes):
            raise RuntimeError('CMA worker failed (exit codes ' + str(codes) +
                               '); inspect worker logs. Completed scan shards are retained.')
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                p.wait()
        for log in logs:
            log.close()
    filenames = []
    for split in SPLITS:
        rows = []
        for job in jobs:
            if job['split'] == split:
                shard = json.loads((output / 'shards' / (job['key'] + '.json')).read_text())
                if shard['fingerprint'] != fingerprint:
                    raise ValueError('Shard fingerprint differs')
                rows.extend(shard['rows'])
        check_rows(rows, expected[split])
        rows.sort(key=lambda row: int(row['episode_id']))
        filename = split + ('.diagnostic.json' if args.episode_limit is not None else '.json')
        atomic_json(output / filename, {'format_version': 1, 'split': split, 'episodes': rows})
        filenames.append(filename)
    if args.episode_limit is None:
        archive = output / 'submission.zip'
        partial = output / 'submission.zip.partial'
        with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_DEFLATED) as handle:
            for name in filenames:
                handle.write(output / name, arcname=name)
        subprocess.run(['havln-validate', str(partial)], check=True)
        os.replace(partial, archive)
        print('Validated submission: ' + str(archive))
    else:
        print('Diagnostic only: no submission ZIP is produced.')
    atomic_json(receipt, {'fingerprint': fingerprint, 'identity': identity,
                         'complete': args.episode_limit is None,
                         'episodes': {s: len(expected[s]) for s in SPLITS}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, default=Path('/data/havln2/checkpoints/HA-VLN-CMA/ckpt.39.pth'))
    parser.add_argument('--data-root', type=Path, default=Path('/data/havln2'))
    parser.add_argument('--source-root', type=Path, default=Path('/workspace/cma-deps/HA-VLN'))
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--gpu-ids', nargs='+', type=int, default=[0])
    parser.add_argument('--episode-limit', type=int, help='Diagnostic episodes per split; never produces a submission ZIP')
    parser.add_argument('--worker-task', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_task:
        run_worker(args.worker_task)
    else:
        if args.output_dir is None or (args.episode_limit is not None and args.episode_limit <= 0):
            parser.error('--output-dir is required and episode limit must be positive')
        if len(set(args.gpu_ids)) != len(args.gpu_ids) or any(g < 0 for g in args.gpu_ids):
            parser.error('GPU IDs must be distinct nonnegative container ordinals')
        export(args)


if __name__ == '__main__':
    main()
