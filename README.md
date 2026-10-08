<h1 align="center">🤖 RoboWorld 2026 Track 2: HA-VLN<br>Human-Aware Vision-and-Language Navigation</h1>

<div align="center" markdown="1">

**Official participant toolkit for RoboWorld 2026 Track 2**

*Built on [HA-VLN 2.0](https://uwmilab.github.io/HA-VLN-webpage/) and co-organized with the [RoboPAD Workshop at NeurIPS 2026](https://robotpad2026.github.io/)*

[![RoboWorld](https://img.shields.io/badge/RoboWorld-2026-blue)](https://roboworld2026.github.io/)
[![Track 2](https://img.shields.io/badge/Track_2-HA--VLN-green)](https://roboworld2026.github.io/track2)
[![CodaBench](https://img.shields.io/badge/CodaBench-Submit-purple)](https://www.codabench.org/competitions/18135/)
[![RoboPAD](https://img.shields.io/badge/Jointly_with-RoboPAD_2026-red)](https://robotpad2026.github.io/)
[![Paper](https://img.shields.io/badge/arXiv-2503.14229-b31b1b)](https://arxiv.org/abs/2503.14229)

<p align="center">
  <img src="assets/media/track2-havln-poster.png" alt="RoboWorld 2026 Track 2: HA-VLN Poster" width="460" />
</p>

**🏆 Awards: Official Certificates for Top 5 Teams & NeurIPS 2026 RoboPAD Workshop Oral Presentations**

</div>

## 🌍 Challenge Overview

HA-VLN evaluates embodied agents on **human-aware vision-and-language navigation**
in continuous 3D environments populated by dynamic people. Unlike static VLN
benchmarks, [HA-VLN 2.0](https://arxiv.org/abs/2503.14229) requires agents to
ground human-referenced route instructions, adapt to moving bystanders, and
reach the goal without human collisions. Official scoring replays submitted
action sequences in the released HA-VLN 2.0 Habitat 0.1.7 runtime, and any
policy, planner, world model, or VLA method that outputs valid actions is welcome.

<p align="center">
  <img src="assets/media/teaser.webp" alt="HA-VLN task overview" width="90%" />
</p>

### 🎯 Task Definition

| Component | Description |
|:--|:--|
| Input | Episode ID, initial position and yaw, navigation instruction, and released human-aware episode inputs. |
| Output | One sequence made from six discrete VLN-CE actions. |
| Actions | `STOP`, `MOVE_FORWARD`, `TURN_LEFT`, `TURN_RIGHT`, `LOOK_UP`, `LOOK_DOWN`. |
| Budget | 1–500 actions; all six actions count toward the limit. |
| Evaluation | Trusted simulator replay measuring navigation and human-aware safety. |

`LOOK_UP` and `LOOK_DOWN` are legal pitch-changing actions from VLN-CE. They do
not move the agent and have no binding to human animation frames.

## 📅 Competition Details

- **Event:** [RoboWorld Challenge 2026, Track 2](https://roboworld2026.github.io/track2).
- **Associated workshop:** [RoboPAD Workshop at NeurIPS 2026](https://robotpad2026.github.io/).
- **Registration:** register through the [Google Form](https://roboworld2026.github.io/#registration) (registration opens Oct 08, 2026) to be eligible for the leaderboard, certificates, and awards.
- **Submission platform:** [CodaBench — HA-VLN](https://www.codabench.org/competitions/18135/).
- **Submission limits:** five per day and 100 per phase; the best score is retained.

### 🗓️ Timeline

| Event | Date |
|:--|:--|
| Registration opens | October 08, 2026 (via [Google Form](https://roboworld2026.github.io/#registration)) |
| Data, baselines & servers online (Phase 1 opens) | October 15, 2026 |
| Phase 1 deadline / Phase 2 opens | October 30, 2026 |
| Final submission deadline (Phase 2 closes) | November 30, 2026 |
| Award decision announcement | December 12, 2026 |

*Follow the [competition page](https://www.codabench.org/competitions/18135/) and [track website](https://roboworld2026.github.io/track2) for any updates.*

### 🗂️ Phases

| Phase | Duration | Submission | Leaderboard role |
|:--|:--|:--|:--|
| Phase 1: Validation | Oct 15 – Oct 30, 2026 | Released `val_seen` and `val_unseen` action sequences | Reports both splits; ranks by full-precision `val_unseen` Score. |
| Phase 2: Final Test | Oct 30 – Nov 30, 2026 | Action sequences for the held-out phase bundle | Determines final ranking and awards. |

Both phases use the same six-action JSON contract and Score. Phase 1 and Phase
2 results are not combined.

### 🏆 Awards & Recognition

| Recognition | Description |
|:--|:--|
| 📜 **Certificates of Recognition** | Official certificates awarded to the **Top 5 teams** in Track 2 |
| 💡 **Best Innovative Solution** | Certificate recognizing outstanding creativity and technical innovation |
| 🎤 **Oral Presentations** | Selected top-performing teams will be invited to give oral presentations at the **RoboPAD Workshop @ NeurIPS 2026** |

The [RoboWorld Rising Star Award](https://roboworld2026.github.io/) is also available; see the event site for eligibility and details.

## 📊 Dataset

The challenge uses released HA-VLN 2.0 resources: HA-R2R navigation episodes
and instructions, HAPS2.0 human assets, multi-human annotations, and licensed
Matterport3D scenes. Challenge datasets are external to the Docker image.

| HA-R2R split | Instructions | Distinct trajectories | Human-influenced episodes ($\beta L$) |
|:--|--:|--:|--:|
| Train | 10,819 | 3,603 | — |
| Validation Seen (`val_seen`) | 778 | 259 | 682 |
| Validation Unseen (`val_unseen`) | 1,839 | 613 | 1,593 |
| Test | 3,408 | — | — |
| **Total** | **16,844** | — | — |

The complete HA-R2R benchmark spans 90 scenes, and HAPS 2.0 provides 910
human models and 486 motion sequences (120 frames each). Phase 1 requires one
action sequence for each of the 778 `val_seen` and 1,839 `val_unseen` episodes.
Phase 2 provides test inputs for final evaluation, while reference trajectories
and collision annotations remain withheld.

```text
/data/havln2/
├── HA-R2R/
│   ├── val_seen/val_seen_bertidx.json.gz
│   └── val_unseen/val_unseen_bertidx.json.gz
├── HA-R2R-tools/
│   ├── collision_num_val_seen.json
│   └── collision_num_val_unseen.json
├── Multi-Human-Annotations/human_motion.json
├── HAPS2_0/<released-human-assets>
├── scene_datasets/mp3d/<licensed-scene-assets>
├── checkpoints/HA-VLN-CMA/ckpt.39.pth # optional reference policy
└── recompute_navmesh/                 # writable replay cache
```

To obtain Matterport3D, visit the [official dataset page](https://niessner.github.io/Matterport/),
sign its [Terms of Use](https://kaldir.vc.in.tum.de/matterport/MP_TOS.pdf), and send
the signed form to `matterport3d@googlegroups.com` to request access. Once
approved, obtain the official `download_mp.py` script and follow the
[HA-VLN 2.0 VLN-CE scene instructions](https://github.com/UWMILab/HA-VLN/blob/main/agent/VLN-CE/README.md#scenes-matterport3d)
to download the Habitat scene assets:

```bash
python3 download_mp.py -o /absolute/path/to/havln2-data/scene_datasets --task_data habitat
# After task-data download finishes, press Ctrl-C at the prompt for the main dataset.
# Extract habitat scene meshes so they reside at scene_datasets/mp3d/<scan>/<scan>.glb
unzip /absolute/path/to/havln2-data/scene_datasets/v1/tasks/mp3d_habitat.zip -d /absolute/path/to/havln2-data/scene_datasets
```

The resulting layout must include
`<host-data-root>/scene_datasets/mp3d/<scan>/<scan>.glb`. Your host data root
can be anywhere. When using the challenge Docker image, mount it at
`/data/havln2` and run `havln-check-data`.
Matterport3D is not included in this repository, helper script, image, or
submission kit.

## 🚀 Getting Started

This walkthrough runs the released CMA checkpoint, records the actions actually
executed, and produces a validated submission ZIP. You may instead use any agent
that follows the [submission contract](#-submission-format).

### 1. Download data and the CMA checkpoint

Use Python 3 and `curl` on a Linux/WSL filesystem to download from
[Hugging Face](https://huggingface.co/datasets/fly1113/HA-VLN).
The helper pins resource revisions, verifies SHA-256 checksums, resumes interrupted
downloads, and extracts HAPS 2.0 into the required layout:

```bash
DATA_ROOT=/absolute/path/to/havln2-data
bash scripts/download_data.sh --destination "$DATA_ROOT" --target all
```

Use the Linux filesystem rather than a Windows-mounted drive for HAPS 2.0:
released asset directory names contain colons.

`--target core` (the default) downloads replay data and human assets;
`--target cma` downloads the checkpoint and its matching instruction-token inputs.
Small annotation files come from the released GitHub repository. Add your
separately licensed Matterport3D scenes under
`$DATA_ROOT/scene_datasets/mp3d/<scan>/<scan>.glb`.
For the older dataset mirrors, use `--source gdrive` with `gdown` installed;
the CMA checkpoint still comes from Hugging Face. Existing files with a different
checksum are rejected rather than overwritten.

### 2. Start a development container and install CMA dependencies

From this toolkit's root directory, create a named container with persistent
data and output mounts:

```bash
IMAGE=ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556
WORK_ROOT=/absolute/path/to/havln-workspace
mkdir -p "$DATA_ROOT" "$WORK_ROOT"
docker pull "$IMAGE"
docker run --name havln-cma --gpus all -it --shm-size 16g \
  --mount type=bind,source="$DATA_ROOT",target=/data/havln2 \
  --mount type=bind,source="$WORK_ROOT",target=/workspace \
  --mount type=bind,source="$(pwd)",target=/toolkit,readonly \
  "$IMAGE" bash
```

Inside the container:

```bash
bash /toolkit/scripts/setup_cma.sh
havln-check-data
```

The setup script retrieves pinned public policy sources and installs the inference
dependencies while retaining the image's Habitat core. Re-enter with
`docker start -ai havln-cma` after exiting. Keep this named container to reuse
installed dependencies; removing it removes that installation, but not the
mounted data, sources, or exported results. Data symlinks require their targets
to be mounted too. For scenes stored elsewhere, bind-mount them into a real
`/data/havln2/scene_datasets/mp3d` directory rather than a nested directory symlink.

### 3. Run CMA and export the executed actions

First run a diagnostic on two episodes **per split**:

```bash
python /toolkit/scripts/export_cma_submission.py \
  --output-dir /workspace/cma-smoke --episode-limit 2
```

This writes diagnostic JSON files only, not a submission ZIP.
For the complete validation sets, run:

```bash
python /toolkit/scripts/export_cma_submission.py \
  --output-dir /workspace/cma-submission
```

For multiple GPUs, append `--gpu-ids 0 1` (container-visible GPU indices).
The exporter retains completed scan shards, so the same command can resume an
interrupted run. Changed inputs require a new output directory. Local multi-GPU subprocess logs and export metadata are saved alongside the results.
For native simulator diagnostics, rerun with `HAVLN_CMA_VERBOSE=1` set.

The published [CMA checkpoint](https://huggingface.co/datasets/fly1113/HA-VLN/tree/main/checkpoints/HA-VLN-CMA)
contains the complete policy state, including instruction embeddings and visual
encoders; this exporter needs no additional encoder initialization weights.
Its four-action output head uses a valid subset of the six-action environment.
No trainer edits or conversion from predicted positions are needed.

Only complete coverage of all **778 `val_seen` and 1,839 `val_unseen` episodes**
produces `val_seen.json`, `val_unseen.json`, and `submission.zip`.
The ZIP is validated before publication.

### 4. Validate, replay, and submit

Inside the container:

```bash
havln-validate /workspace/cma-submission/submission.zip
havln-score-phase1 \
  --submission /workspace/cma-submission/submission.zip \
  --output-dir /workspace/cma-submission/replay --gpu-ids 0
```

Validation checks format and exact coverage; replay computes the challenge
metrics and Score. To replay with the unchanged public image in a separate
container, use [Local Docker Replay](#-local-docker-replay).
Upload `$WORK_ROOT/cma-submission/submission.zip` on the host to
[CodaBench](https://www.codabench.org/competitions/18135/).
The public-test and final phases use the same task and scoring algorithm;
this walkthrough uses the released validation splits.

## 🐳 Local Docker Replay

The public runtime image is optional for participants. It contains the
HA-VLN 2.0 / Habitat 0.1.7 replay environment, but no challenge data or
licensed Matterport3D scenes. The immutable image reference is:

```text
ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556
```

Install Docker and NVIDIA Container Toolkit for GPU replay.
Validation and environment checks do not need a GPU:

```bash
IMAGE=ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556
DATA_ROOT=/absolute/path/to/havln2-data
NAVMESH_ROOT=/absolute/path/to/writable-navmesh-cache
WORK_ROOT=/absolute/path/to/participant-workspace

docker pull "$IMAGE"
docker run --rm "$IMAGE" havln-check-environment
docker run --rm \
  -v "$DATA_ROOT:/data/havln2:ro" \
  -v "$NAVMESH_ROOT:/data/havln2/recompute_navmesh" \
  "$IMAGE" havln-check-data
docker run --rm -v "$WORK_ROOT:/workspace" "$IMAGE" \
  havln-validate /workspace/submission.zip
```

For optional complete Phase 1 replay, expose the GPUs selected on your host.
The `--gpu-ids` values are GPU ordinals as seen *inside* the container:

```bash
docker run --rm --gpus '"device=0,1"' \
  -v "$DATA_ROOT:/data/havln2:ro" \
  -v "$NAVMESH_ROOT:/data/havln2/recompute_navmesh" \
  -v "$WORK_ROOT:/workspace" \
  "$IMAGE" havln-score-phase1 \
  --submission /workspace/submission.zip \
  --output-dir /workspace/results \
  --gpu-ids 0 1
```

Local replay may generate navmeshes in the separately writable cache mount.
Participant code may live anywhere and may be mounted read-only at any path;
there is no required launcher or agent directory. Local results help with
development, but only CodaBench's official replay determines leaderboard
scores.

## 🧠 Baseline Model

We provide **HA-VLN-CMA**, the released VLN-CE cross-modal attention agent
adapted by HA-VLN 2.0, as the executable reference baseline for this challenge
(alongside HA-VLN-VL and external methods such as BEVBert, ETPNav, NaVid, and
NaVILA evaluated in the paper). Participants are free to use any model or
planning approach that outputs valid action sequences.

Example local replay of the CMA walkthrough above produced:

| Split | SR ↑ | NE ↓ | CR ↓ | TCR ↓ | Score ↑ |
|:--|--:|--:|--:|--:|--:|
| `val_seen` | 0.180 | 6.223 | 0.623 | 13.726 | 16.509450 |
| `val_unseen` | 0.129 | 6.387 | 0.684 | 17.536 | 12.945387 |

Score is calculated from unrounded metrics; the displayed component metrics are
rounded. Humans move in real time, so repeat runs can differ. These are reference
results; only CodaBench's official replay determines leaderboard scores.

## 📏 Evaluation

| Metric | Direction | Meaning |
|:--|:--|:--|
| SR (Success Rate) | Higher | Collision-free success rate over all episodes. |
| NE (Navigation Error) | Lower | Mean final navigation error in metres. |
| CR (Collision Rate) | Lower | Collision-episode rate over released human-influenced episodes. |
| TCR (Total Collision Rate) | Lower | Mean adjusted human-collision count over all episodes. |

Let $L$ be the number of episodes, $s_i$ the navigation-success indicator,
$d_i$ the final goal distance, and $e_i$ the adjusted human-collision count.
The released human-influenced episode count is $\beta L$:

$$
\begin{aligned}
\mathrm{SR} &= \frac{1}{L}\sum_{i=1}^{L}s_i\mathbf{1}[e_i=0], &
\mathrm{NE} &= \frac{1}{L}\sum_{i=1}^{L}d_i, \\
\mathrm{CR} &= \frac{\sum_{i=1}^{L}\min(e_i,1)}{\beta L}, &
\mathrm{TCR} &= \frac{1}{L}\sum_{i=1}^{L}e_i.
\end{aligned}
$$

In particular, CR divides by the released human-influenced episode count
$\beta L$, while SR, NE, and TCR divide by all $L$ episodes.

### 🏁 Composite Score

The composite Score uses the full-precision metrics (higher is better):

$$
\begin{aligned}
\mathrm{Navigation} &= 0.80 \times \mathrm{SR} + 0.20 \times \frac{3}{3 + \mathrm{NE}}, \\
\mathrm{Social} &= 0.75 \times (1 - \mathrm{CR}) + 0.25 \times \frac{1}{1 + \mathrm{TCR}}, \\
\mathrm{Score} &= 100 \times \mathrm{Navigation} \times (0.70 + 0.30 \times \mathrm{Social}).
\end{aligned}
$$

Higher Score ranks first. Exact ties use higher SR, lower NE, lower CR, lower
TCR, then earlier submission time. Calculation and comparison retain full
precision.

## 📥 Submission Format

Phase 1 requires one valid prediction JSON for each validation split. The
following ZIP is the recommended layout, not a filename restriction:

```text
submission.zip
├── val_seen.json
└── val_unseen.json
```

Each file follows this schema (the invented ID is only an illustration):

```json
{
  "format_version": 1,
  "split": "val_unseen",
  "episodes": [
    {
      "episode_id": "synthetic-example-001",
      "actions": ["MOVE_FORWARD", "TURN_LEFT", "LOOK_UP", "LOOK_DOWN", "STOP"]
    }
  ]
}
```

Include every official episode ID exactly once. `STOP`, if present, occurs once
at the end; sequences shorter than 500 actions require it. The examples in
[`examples/submission`](examples/submission) demonstrate schema only and do not
have complete manifest coverage.

The validator identifies predictions by each JSON object's `split` value, so
you may rename the files and include harmless extra root files. It rejects
missing or duplicate required splits, invalid prediction content, unsafe ZIP
members, and nested paths. Phase 2 follows the same rule with its single
required `test` split when that phase opens.

## ❓ Frequently Asked Questions

**Q1. Must I use CMA or a particular architecture?**

No. Any method is eligible if it exports legal official action sequences.

**Q2. Do I submit code, weights, or a container?**

For CodaBench scoring, submit only the required JSON action-sequence files in
one ZIP; no code, weights, or container are part of that upload. However, if
your team earns an award, you will be expected to contribute to a technical
report explaining your method and innovations, including relevant model,
training, and implementation details. Organizers may request code or model
information to verify an awarded result.

**Q3. Are `LOOK_UP` and `LOOK_DOWN` valid?**

Yes. Both are original VLN-CE pitch actions and count toward 500 task steps.

**Q4. Does an action advance a human animation frame?**

No. Human animation follows released wall-clock behavior independently.

**Q5. Does local validation compute a Score?**

`havln-validate` checks structure and coverage only. Local replay can compute
metrics for development, but only the official replay result published on
CodaBench for the submitted archive determines leaderboard scores and awards.
Results from another machine are not accepted as official scores.

**Q6. Why did my ZIP fail validation?**

`SUBMISSION REJECTED:` means the ZIP needs correction: check for a parent
folder, missing or duplicate split, duplicate/missing episode IDs (778
`val_seen` and 1,839 `val_unseen` are required), invalid action names, or
incorrect `STOP` placement. `PASS:` means validation or replay succeeded.
`SCORING DATA ERROR (organizer):` indicates a scoring-side problem; report
the submission identifier rather than changing valid predictions.

**Q7. Can the image download Matterport3D for me?**

No. Request access through the [Matterport3D dataset page](https://niessner.github.io/Matterport/):
sign its Terms of Use and email the form to `matterport3d@googlegroups.com`.
After approval, use the [HA-VLN 2.0 VLN-CE scene guide](https://github.com/UWMILab/HA-VLN/blob/main/agent/VLN-CE/README.md#scenes-matterport3d),
and place the licensed scenes under your host data root's
`scene_datasets/mp3d/`. That root can be anywhere on your machine. When using
the challenge Docker image, mount it at `/data/havln2` inside the container.

## 🔗 Contact and Resources

For technical support, use [GitHub Issues](https://github.com/F1y1113/havln-challenge/issues).
For event and registration questions, email
[roboworld2026@outlook.com](mailto:roboworld2026@outlook.com).

| Resource | Link |
|:--|:--|
| RoboWorld 2026 | [Challenge website](https://roboworld2026.github.io/) |
| Starting kits, submissions, and leaderboard | [CodaBench](https://www.codabench.org/competitions/18135/) |
| Track website | [HA-VLN Challenge](https://roboworld2026.github.io/track2) |
| Challenge repository and participant toolkit | [GitHub](https://github.com/F1y1113/havln-challenge) |
| Associated workshop | [RoboPAD 2026](https://robotpad2026.github.io/) |
| HA-VLN 2.0 | [Project page](https://uwmilab.github.io/HA-VLN-webpage/) |
| HA-VLN 2.0 code and CMA | [Official repository](https://github.com/UWMILab/HA-VLN) |
| Released data and CMA checkpoint | [Hugging Face](https://huggingface.co/datasets/fly1113/HA-VLN) |
| VLN-CE | [Original repository](https://github.com/jacobkrantz/VLN-CE) |
| Challenge rules and submission details | [CodaBench](https://www.codabench.org/competitions/18135/) and this README |
| HA-VLN 2.0 Get Started | [Project documentation](https://jostarxiong.github.io/havln2-docs/) |

## 📄 License and Terms

HA-VLN 2.0, HA-R2R, HAPS2.0, pretrained weights, and source assets retain their upstream
licenses. Matterport3D requires separate authorized access. Participation is
governed by the Terms displayed on the official CodaBench competition.

## 📚 Citation

If you use HA-VLN 2.0 or this challenge toolkit, cite the benchmark paper:

```bibtex
@inproceedings{dong2026havln,
  author    = {Dong, Yifei and Wu, Fengyi and He, Qi and Kong, Lingdong and Li, Heng and Li, Minghan and Cheng, Zebang and Zhou, Yuxuan and Sun, Jingdong and Dai, Qi and Hauptmann, Alexander G. and Cheng, Zhi-Qi},
  title     = {{HA-VLN 2.0: An Open Benchmark and Leaderboard for Human-Aware Navigation in Discrete and Continuous Environments with Dynamic Multi-Human Interactions}},
  booktitle = {2026 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
  year      = {2026},
}

@misc{roboworld2026track2,
  title={Track 2 | HA-VLN: Human-Aware Vision-and-Language Navigation},
  author={RoboWorld Challenge 2026 Organizers},
  year={2026},
  howpublished={https://roboworld2026.github.io/track2}
}
```

## 🤝 Acknowledgements

The track is organized by the RoboWorld Challenge 2026 team and jointly held
with RoboPAD 2026. We thank the HA-VLN 2.0 and VLN-CE authors, dataset and
simulator contributors, Matterport3D, and CodaBench.
