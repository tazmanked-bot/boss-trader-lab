"""Inert ELF-shaped fixtures and local Git plumbing only. No compiler or model."""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from research import portable_runtime_036 as r


def inert(needed=(), paths=(), soname=None, interpreter=None):
    strings = b'\0'; tags = []
    for tag, values in ((1, needed), (29, paths), (14, [soname] if soname else [])):
        for value in values:
            tags.append((tag, len(strings))); strings += value.encode()+b'\0'
    tags += [(5, 0x400000+2048), (10, len(strings)), (0, 0)]
    data = bytearray(4096); count = 3 if interpreter else 2
    data[:64] = struct.pack('<16sHHIQQQIHHHHHH', b'\x7fELF\x02\x01'+b'\0'*10, 3, 62, 1, 0, 64, 0, 0, 64, 56, count, 0, 0, 0)
    data[64:120] = struct.pack('<IIQQQQQQ', 1, 5, 0, 0x400000, 0, len(data), len(data), 4096)
    data[120:176] = struct.pack('<IIQQQQQQ', 2, 4, 512, 0x400200, 0, len(tags)*16, len(tags)*16, 8)
    if interpreter:
        value = interpreter.encode()+b'\0'; data[1024:1024+len(value)] = value
        data[176:232] = struct.pack('<IIQQQQQQ', 3, 4, 1024, 0x400400, 0, len(value), len(value), 1)
    for index, pair in enumerate(tags): struct.pack_into('<qQ', data, 512+index*16, *pair)
    data[2048:2048+len(strings)] = strings
    return bytes(data)


class PortableTests(unittest.TestCase):
    def setUp(self):
        previous_umask = os.umask(0o077); self.addCleanup(os.umask, previous_umask)
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.source = self.root/'original'; self.source.mkdir(mode=0o700)
        (self.source/'LICENSE').write_text('SYNTHETIC NOT UPSTREAM'); (self.source/'empty').touch()
        (self.source/'tool').write_text('INERT NOT EXECUTED'); (self.source/'tool').chmod(0o700)
        for args in (('init', '-q'), ('add', '.'), ('-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.invalid', 'commit', '-qm', 'inert fixture')):
            subprocess.run(['/usr/bin/git', '-C', str(self.source), *args], check=True, capture_output=True,
                           env={'PATH': '/usr/bin:/bin', 'HOME': str(self.root), 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'})
        self.commit = r.git(self.source, 'rev-parse', 'HEAD').decode().strip()
        self.tree = r.git(self.source, 'rev-parse', 'HEAD^{tree}').decode().strip()
        self.addCleanup(patch.stopall)
        patch.object(r, 'COMMIT', self.commit).start(); patch.object(r, 'TREE', self.tree).start()
        patch.object(r, 'resources', return_value=6*1024**3).start()
        patch.object(r, 'compatibility', return_value={'synthetic': True}).start()
        patch.object(r.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 12*1024**3})()).start()
        self.destination = self.root/'dedicated'

    def prepare(self, **kw):
        return r.prepare(str(self.source), str(self.destination), [str(self.root/'recorder')], **kw)

    def stage(self):
        root = self.root/'artifacts'; root.mkdir(mode=0o700)
        blobs = {'bin/llama-cli': inert(('libfake.so.1',), ('$ORIGIN/../lib',), interpreter='/lib/ld-inert.so'),
                 'lib/libfake.so.1.0': inert(soname='libfake.so.1'), 'lib/ld-inert.so': inert()}
        entries = []
        for name, data in blobs.items():
            path = root/name; path.parent.mkdir(mode=0o700, exist_ok=True); path.write_bytes(data)
            entries.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)})
        (root/'lib/libfake.so.1').symlink_to('libfake.so.1.0')
        entries.append({'path': 'lib/libfake.so.1', 'link': 'libfake.so.1.0'})
        manifest = {'version': 'portable-artifacts-036-v1', 'source_commit': self.commit, 'source_tree': self.tree,
                    'compiler': 'SYNTHETIC', 'cmake': 'SYNTHETIC', 'build_flags': r.FLAGS,
                    'environment': {'synthetic': True}, 'commands': ['NO_COMPILATION'],
                    'dependencies': ['INERT_NOT_A_PACKAGE'], 'license_evidence': 'ORIGINAL_INERT_FIXTURE',
                    'build_record': 'SYNTHETIC_ONLY', 'entries': entries}
        return root, manifest

    def test_exact_source_empty_file_untracked_excluded(self):
        (self.source/'untracked').write_text('EXCLUDE')
        result = r.source_manifest(self.source)
        self.assertEqual(len(result['entries']), 3)
        self.assertEqual(result['commit'], self.commit)

    def test_wrong_source_commit_refused(self):
        with patch.object(r, 'COMMIT', '0'*40), self.assertRaisesRegex(ValueError, 'WRONG_SOURCE_COMMIT'):
            r.source_manifest(self.source)

    def test_wrong_tree_refused(self):
        with patch.object(r, 'TREE', '0'*40), self.assertRaisesRegex(ValueError, 'WRONG_SOURCE_TREE'):
            r.source_manifest(self.source)

    def test_dirty_tracked_source_refused(self):
        (self.source/'LICENSE').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'DIRTY_TRACKED_SOURCE'): self.prepare()

    def test_dirty_mode_refused(self):
        (self.source/'tool').chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'DIRTY_SOURCE_MODE'): self.prepare()

    def test_source_symlink_refused(self):
        (self.source/'LICENSE').unlink(); (self.source/'LICENSE').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError, 'SYMLINK'): self.prepare()

    def test_dry_run_does_not_write(self):
        result = self.prepare(); self.assertEqual(result['writes'], 0); self.assertFalse(self.destination.exists())
        self.assertEqual(result['gates']['real'], 'REAL_NOT_RUN')

    def test_prepare_private_copy_original_unchanged_and_umask_restored(self):
        before = r.source_manifest(self.source); old = os.umask(0o027)
        try:
            result = self.prepare(apply=True); current = os.umask(0o027); self.assertEqual(current, 0o027)
        finally: os.umask(old)
        self.assertEqual(r.source_manifest(self.source), before)
        self.assertEqual(self.destination.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.destination/'source/tool').stat().st_mode & 0o777, 0o700)
        self.assertFalse((self.destination/'source/.git').exists())
        self.assertEqual(result['operation'], 'PREPARED_ONLY')

    def test_existing_or_overlapping_paths_refused(self):
        with self.assertRaises(ValueError): r.prepare(str(self.source), str(self.source/'new'), [str(self.root/'recorder')])
        self.destination.mkdir()
        with self.assertRaisesRegex(ValueError, 'NEW_DESTINATION'): self.prepare()

    def test_incompatible_cpu_refuses_preparation(self):
        with patch.object(r, 'compatibility', side_effect=ValueError('AVX2_FMA_COMPATIBILITY_HOLD')):
            with self.assertRaisesRegex(ValueError, 'COMPATIBILITY_HOLD'): self.prepare()

    def test_memory_and_disk_fail_closed(self):
        with patch.object(r, 'resources', return_value=1), self.assertRaisesRegex(ValueError, 'RAM'): self.prepare()
        with patch.object(r.shutil, 'disk_usage', return_value=type('D', (), {'free': 1})()), self.assertRaisesRegex(ValueError, 'DISK'): self.prepare()

    def test_rollback_dry_and_apply_only_owned(self):
        result = self.prepare(apply=True)
        self.assertEqual(r.rollback(str(self.destination), result['receipt_sha256'])['operation'], 'ROLLBACK_DRY_RUN')
        r.rollback(str(self.destination), result['receipt_sha256'], apply=True)
        self.assertFalse(self.destination.exists()); self.assertTrue(self.source.exists())

    def test_rollback_foreign_file_refuses(self):
        result = self.prepare(apply=True); (self.destination/'owner-not-ours').write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'FOREIGN_PATH'): r.rollback(str(self.destination), result['receipt_sha256'], apply=True)
        self.assertEqual((self.destination/'owner-not-ours').read_text(), 'preserve')

    def test_receipt_tampering_refused(self):
        result = self.prepare(apply=True); (self.destination/r.RECEIPT).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'RECEIPT_HASH'): r.rollback(str(self.destination), result['receipt_sha256'], apply=True)

    def test_recipe_exact_flags_no_shell_or_network_download(self):
        configure, build = r.recipe(self.destination)
        self.assertIn('-S', configure); self.assertIn('-B', configure)
        self.assertIn('-DCMAKE_INSTALL_RPATH=$ORIGIN;$ORIGIN/../lib', configure)
        self.assertIn('-DLLAMA_USE_PREBUILT_UI=OFF', configure)
        self.assertIn('-DLLAMA_BUILD_SERVER=ON', configure)
        self.assertNotIn('-DLLAMA_CURL=OFF', configure)
        self.assertEqual(build[-4:], ['--target', 'llama-cli', '--parallel', '1'])
        self.assertEqual(r.LIMITS['jobs'], 1); self.assertEqual(r.LIMITS['swap_max_bytes'], 0)

    def test_unsafe_search_elements(self):
        for value in ('', '/original/lib', '$ORIGIN:', ':$ORIGIN', '$ORIGIN::x', '.', '$ORIGIN/../../../escape', '${ORIGIN}', '$ORIGIN/$LIB'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.check_search(self.root, self.root/'bin/cli', [value])
        r.check_search(self.root, self.root/'bin/cli', ['$ORIGIN:$ORIGIN/../lib'])

    def test_passive_complete_inert_inventory_stays_hold(self):
        root, manifest = self.stage(); report = r.inventory(root, manifest)
        self.assertEqual(report['artifacts']['lib/libfake.so.1.0']['soname'], 'libfake.so.1')
        self.assertEqual(report['provisioner_035'], 'HOLD_INDEPENDENT_EXPECTATIONS_AND_MODEL_REQUIRED')
        self.assertEqual(report['gates']['inference'], 'HOLD')

    def test_corrupted_artifact_fails(self):
        root, manifest = self.stage(); (root/'bin/llama-cli').write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'HASH_SIZE'): r.inventory(root, manifest)

    def test_unlisted_dynamic_file_fails(self):
        root, manifest = self.stage(); (root/'lib/hidden.so').write_bytes(inert())
        with self.assertRaisesRegex(ValueError, 'UNLISTED'): r.inventory(root, manifest)

    def test_missing_transitive_dependency_fails(self):
        root, manifest = self.stage()
        path = root/'lib/libfake.so.1.0'; data = inert(('libmissing.so',), ('$ORIGIN',), soname='libfake.so.1'); path.write_bytes(data)
        entry = manifest['entries'][1]; entry.update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
        with self.assertRaisesRegex(ValueError, 'MISSING_OR_AMBIGUOUS'): r.inventory(root, manifest)

    def test_missing_interpreter_fails(self):
        root, manifest = self.stage(); (root/'lib/ld-inert.so').unlink(); manifest['entries'].pop(2)
        with self.assertRaisesRegex(ValueError, 'INTERPRETER_NOT_INVENTORIED'): r.inventory(root, manifest)

    def test_soname_mismatch_fails(self):
        root, manifest = self.stage(); path = root/'lib/libfake.so.1.0'; data = inert(soname='wrong.so'); path.write_bytes(data)
        manifest['entries'][1].update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
        with self.assertRaisesRegex(ValueError, 'SONAME_MISMATCH'): r.inventory(root, manifest)

    def test_provenance_required(self):
        root, manifest = self.stage()
        for key in ('compiler', 'cmake', 'build_flags', 'dependencies', 'license_evidence', 'environment', 'commands', 'build_record'):
            bad = copy.deepcopy(manifest); bad.pop(key)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'PROVENANCE'): r.inventory(root, bad)

    def test_repeat_does_not_promote_trust_and_detects_difference(self):
        root, manifest = self.stage(); first = r.inventory(root, manifest); second = copy.deepcopy(first)
        self.assertEqual(r.repeat(first, second)['independent_reproducibility'], 'UNVERIFIED')
        second['artifacts']['bin/llama-cli']['sha256'] = '0'*64
        self.assertEqual(r.repeat(first, second)['byte_comparison'], 'NONDETERMINISM_OR_INPUT_DIFFERENCE')

    def test_unsafe_runpath_artifact_fails_even_with_matching_hash(self):
        root, manifest = self.stage()
        for search in ('/old/runtime/lib:', '$ORIGIN:', '$ORIGIN/../../../outside'):
            data = inert(('libfake.so.1',), (search,), interpreter='/lib/ld-inert.so')
            (root/'bin/llama-cli').write_bytes(data)
            manifest['entries'][0].update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
            with self.subTest(search=search), self.assertRaisesRegex(ValueError, 'RUNPATH'):
                r.inventory(root, manifest)

    def test_modified_owned_content_never_deleted(self):
        result = self.prepare(apply=True)
        target = self.destination/'source/LICENSE'; target.write_text('new owner content')
        with self.assertRaisesRegex(ValueError, 'MODIFIED_PATH'):
            r.rollback(str(self.destination), result['receipt_sha256'], apply=True)
        self.assertEqual(target.read_text(), 'new owner content')

    def test_absolute_link_and_wrong_build_flags_fail(self):
        root, manifest = self.stage()
        manifest['entries'][-1]['link'] = '/etc/passwd'
        with self.assertRaises(ValueError): r.inventory(root, manifest)
        manifest['entries'][-1]['link'] = 'libfake.so.1.0'
        manifest['build_flags'] = dict(r.FLAGS, GGML_NATIVE='ON')
        with self.assertRaisesRegex(ValueError, 'FLAGS_MISMATCH'): r.inventory(root, manifest)

    def test_handoff_is_unqualified_and_035_refuses(self):
        root, manifest = self.stage()
        config = r.handoff(root, manifest, str(self.root/'never-admitted'), [str(self.source)])
        self.assertFalse(config['licenses_reviewed'])
        self.assertTrue(all(e['expectation'] == 'LOCAL_BUILD_ATTESTATION' for e in config['entries']))
        from research.qualification_035 import provision
        with self.assertRaises(ValueError): provision.inventory(config)

    def test_build_never_starts_process(self):
        with patch.object(r.subprocess, 'Popen', side_effect=AssertionError('must not execute')):
            self.assertEqual(r.main(['build']), 2)

    def test_035_trust_categories_not_weakened(self):
        from research.qualification_035 import provision, synthetic
        config = synthetic.bundle(self.root)
        config['entries'][0]['expectation'] = 'LOCAL_BUILD_ATTESTATION'
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT'): provision.inventory(config)


if __name__ == '__main__': unittest.main()
