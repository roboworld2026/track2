"""Install verified public source archives without Git or a compiler."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import urllib.request

SOURCES = (
    ('HA-VLN', 'UWMILab/HA-VLN', 'f46f93642d7ab96cc49611f8cfea09cecf2fa7f9',
     '2ea43d01ee2274a97ffd0d12f2017d849c65e6334396512daf60fe35ebee6f11'),
    ('habitat-lab', 'facebookresearch/habitat-lab', 'd6ed1c0a0e786f16f261de2beafe347f4186d0d8',
     'eb9a121a15ed58f788154f4e0ff8db80535b8a07bb057a0927d4ea600db2bf1b'),
)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name, repo, revision, expected in SOURCES:
        destination = root / name
        marker = destination / '.release.json'
        if marker.exists():
            state = json.loads(marker.read_text())
            if state['revision'] != revision or any(digest(destination / p) != sha for p, sha in state['files'].items()):
                raise ValueError('Source changed; use a fresh dependency directory: ' + str(destination))
            continue
        if destination.exists():
            raise ValueError('Unrecognized/incomplete source directory; move it aside: ' + str(destination))
        cache = root / (name + '.tar.gz')
        if not cache.exists():
            partial = cache.with_name(cache.name + '.partial')
            with urllib.request.urlopen('https://codeload.github.com/' + repo + '/tar.gz/' + revision,
                                        timeout=120) as response, partial.open('wb') as output:
                shutil.copyfileobj(response, output)
            os.replace(partial, cache)
        if digest(cache) != expected:
            raise ValueError('Source archive checksum mismatch: ' + str(cache))
        destination.mkdir()
        files = {}
        with tarfile.open(cache) as archive:
            for member in archive.getmembers():
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
                    raise ValueError('Unsafe source archive member')
                relative = Path(*path.parts[1:])
                target = destination / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as source, target.open('xb') as out:
                        shutil.copyfileobj(source, out)
                    if target.suffix == '.py':
                        files[str(relative)] = digest(target)
        marker.write_text(json.dumps({'revision': revision, 'sha256': expected, 'files': files}, indent=2) + '\n')


if __name__ == '__main__':
    prepare(sys.argv[1])
