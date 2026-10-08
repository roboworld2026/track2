"""Standard-library tests for the participant download/export helpers."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


download = module('download_resources')
export = module('export_cma_submission')


class OnboardingTests(unittest.TestCase):
    def test_manifest_is_pinned_and_has_no_private_test_inputs(self):
        manifest = download.MANIFEST
        self.assertEqual(len(manifest['hf_revision']), 40)
        self.assertEqual(len(manifest['github_revision']), 40)
        for item in manifest['files']:
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')
            self.assertNotIn('val_test', item['path'])
            self.assertNotIn('/train/', item['path'])
        checkpoint = [i for i in manifest['files'] if i['path'].endswith('ckpt.39.pth')]
        self.assertEqual(checkpoint[0]['sha256'], export.CHECKPOINT_SHA)

    def test_existing_verified_download_avoids_network(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'data'
            file.write_bytes(b'public asset')
            with patch.object(download.subprocess, 'run') as curl:
                download.fetch('https://example.invalid', file, download.digest(file))
                curl.assert_not_called()

    def test_existing_mismatch_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'data'
            file.write_bytes(b'existing')
            with self.assertRaises(ValueError):
                download.fetch('unused', file, '0' * 64)
            self.assertEqual(file.read_bytes(), b'existing')

    def test_complete_partial_download_is_committed_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'data'
            partial = file.with_name('data.partial')
            partial.write_bytes(b'complete')
            with patch.object(download.subprocess, 'run') as curl:
                download.fetch('unused', file, download.digest(partial))
                curl.assert_not_called()
            self.assertEqual(file.read_bytes(), b'complete')
            self.assertFalse(partial.exists())

    def test_symlink_download_does_not_touch_target(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'original'
            target.write_bytes(b'keep')
            link = Path(folder) / 'link'
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                download.fetch('unused', link, download.digest(target))
            self.assertEqual(target.read_bytes(), b'keep')

    def test_haps_layout_normalization_and_repeat_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'downloads').mkdir()
            archive = root / 'downloads/HAPS2_0.zip'
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('human_motion_glbs_v3/scan/person/0.glb', b'asset')
            sha = download.digest(archive)
            download.unpack_haps(archive, root, sha)
            download.unpack_haps(archive, root, sha)
            self.assertEqual((root / 'HAPS2_0/scan/person/0.glb').read_bytes(), b'asset')

    def test_zip_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'unsafe.zip'
            with zipfile.ZipFile(file, 'w') as handle:
                handle.writestr('../outside', b'no')
            with zipfile.ZipFile(file) as handle, self.assertRaises(ValueError):
                list(download.safe_members(handle))

    def test_released_category_colons_are_legal_but_drive_paths_are_not(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'colon.zip'
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('human_motion_glbs_v3/bedroom:Walking_0/frame000.glb', b'asset')
            with zipfile.ZipFile(archive) as handle:
                self.assertEqual(len(list(download.safe_members(handle))), 1)
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('C:/outside', b'no')
            with zipfile.ZipFile(archive) as handle, self.assertRaises(ValueError):
                list(download.safe_members(handle))

    def test_changed_same_size_haps_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'downloads').mkdir()
            archive = root / 'downloads/HAPS2_0.zip'
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('HAPS2_0/sequence/frame.glb', b'asset')
            sha = download.digest(archive)
            download.unpack_haps(archive, root, sha)
            (root / 'HAPS2_0/sequence/frame.glb').write_bytes(b'wrong')
            with self.assertRaises(ValueError):
                download.unpack_haps(archive, root, sha)

    def test_duplicate_normalized_zip_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'unsafe.zip'
            with zipfile.ZipFile(archive, 'w') as handle:
                handle.writestr('human_motion_glbs_v3/a', b'one')
                handle.writestr('HAPS2_0/a', b'two')
            with self.assertRaises(ValueError):
                download.unpack_haps(archive, root, download.digest(archive))

    def test_six_actions_and_budget_boundary(self):
        rows = [{'episode_id': '1', 'actions': ['LOOK_UP', 'LOOK_DOWN', 'STOP']},
                {'episode_id': '2', 'actions': ['MOVE_FORWARD'] * 500}]
        export.check_rows(rows, ['1', '2'])
        for actions in ([], ['MOVE_FORWARD'], ['STOP', 'STOP'], ['STOP'] * 501, ['WAIT']):
            with self.assertRaises(ValueError):
                export.check_rows([{'episode_id': '1', 'actions': actions}], ['1'])

    def test_exact_coverage_rejects_missing_extra_and_duplicate_ids(self):
        row = {'episode_id': '1', 'actions': ['STOP']}
        for rows, expected in (([row], ['1', '2']), ([row], ['2']), ([row, row], ['1'])):
            with self.assertRaises(ValueError):
                export.check_rows(rows, expected)

    def test_readme_has_no_manual_trainer_patch_and_keeps_named_container(self):
        readme = (ROOT / 'README.md').read_text()
        quickstart = readme.split('## 🚀 Getting Started', 1)[1].split('## 🐳', 1)[0]
        self.assertNotIn('base_il_trainer.py', quickstart)
        self.assertIn('--name havln-cma', quickstart)
        self.assertNotIn('--rm', quickstart)
        self.assertIn('--episode-limit 2', quickstart)
        self.assertIn('not a submission ZIP', quickstart)
        self.assertIn('havln-validate', quickstart)


if __name__ == '__main__':
    unittest.main()
