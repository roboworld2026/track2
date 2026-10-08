#!/usr/bin/env bash
set -euo pipefail
toolkit=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
destination=${1:-/workspace/cma-deps}
mkdir -p "$destination"
destination=$(cd "$destination" && pwd)
# Resolve the image core explicitly; never add the whole upstream Lab tree.
core_before=$(PYTHONPATH="/app/habitat-lab:${PYTHONPATH:-}" python -c 'import habitat; assert habitat.__version__ == "0.1.7"; print(habitat.__file__)')
python -c 'import torch; assert torch.__version__ == "2.0.1+cu118", torch.__version__'
python "$toolkit/scripts/prepare_cma_sources.py" "$destination"
python -m pip install -r "$toolkit/cma/requirements.txt" \
  --extra-index-url https://download.pytorch.org/whl/cu118
# Restore the missing baseline package without replacing the image's Habitat core.
python - "$destination" <<'PY'
from pathlib import Path
import site, sys
source = Path(sys.argv[1]) / 'habitat-lab'
packages = Path(sys.argv[1]) / 'baseline-packages'
packages.mkdir(exist_ok=True)
link = packages / 'habitat_baselines'
if not link.exists():
    link.symlink_to(source / 'habitat_baselines', target_is_directory=True)
if link.resolve() != (source / 'habitat_baselines').resolve():
    raise ValueError('Unexpected habitat_baselines link')
Path(site.getsitepackages()[0], 'havln_cma_baselines.pth').write_text(str(packages) + '\n')
PY
core_after=$(python -c 'import habitat; print(habitat.__file__)')
[[ "$core_before" == "$core_after" ]] || { echo "Habitat core was unexpectedly replaced." >&2; exit 1; }
python -m pip check
echo "CMA dependencies ready: $destination"
