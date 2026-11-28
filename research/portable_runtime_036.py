"""Passive portable-runtime preparation. No compiler, loader, model or network execution.

Actual compilation stays HOLD. A plan is not an execution/containment approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import time
from research.qualification_035 import provision as p
from research.llama_analyst_033 import Refused

COMMIT = '0978a6e9022fb9bd6874b86154ee304e81929b9f'
TREE = '5e472b707005dec79feedd0942c3814fb88b9a6d'
BASE = '66b4f17c560a1b4220daf17a9ccdb99b75e72c3d'
RECEIPT = '.portable-036.json'
GATES = {'real': 'REAL_NOT_RUN', 'desktop_build': 'HOLD', 'full_containment': 'HOLD',
         'inference': 'HOLD', 'AEP_Gate_B': 'HOLD', 'buy_authorization': 'NONE'}
LIMITS = {'jobs': 1, 'nice': 10, 'cpu_quota_percent': 100, 'memory_max_bytes': 3*1024**3,
          'swap_max_bytes': 0, 'pids_max': 64, 'wall_seconds': 900, 'cpu_seconds': 600,
          'output_max_bytes': 1024**2, 'disk_free_min_bytes': 8*1024**3,
          'available_ram_min_bytes': 4*1024**3}
FLAGS = {
    'CMAKE_BUILD_TYPE': 'Release', 'BUILD_SHARED_LIBS': 'ON',
    'CMAKE_BUILD_WITH_INSTALL_RPATH': 'ON', 'CMAKE_BUILD_RPATH_USE_ORIGIN': 'ON',
    'CMAKE_INSTALL_RPATH': '$ORIGIN;$ORIGIN/../lib',
    'CMAKE_INSTALL_RPATH_USE_LINK_PATH': 'OFF', 'CMAKE_SKIP_RPATH': 'OFF',
    'CMAKE_INSTALL_REMOVE_ENVIRONMENT_RPATH': 'ON',
    'FETCHCONTENT_FULLY_DISCONNECTED': 'ON', 'FETCHCONTENT_UPDATES_DISCONNECTED': 'ON',
    'LLAMA_BUILD_COMMON': 'ON', 'LLAMA_BUILD_TOOLS': 'ON', 'LLAMA_BUILD_SERVER': 'ON',
    'LLAMA_BUILD_TESTS': 'OFF', 'LLAMA_BUILD_EXAMPLES': 'OFF', 'LLAMA_BUILD_APP': 'OFF',
    'LLAMA_BUILD_UI': 'OFF', 'LLAMA_USE_PREBUILT_UI': 'OFF', 'LLAMA_CONNECT': 'OFF',
    'LLAMA_OPENSSL': 'OFF', 'LLAMA_SUBPROCESS': 'OFF', 'LLAMA_LLGUIDANCE': 'OFF',
    'LLAMA_BUILD_BORINGSSL': 'OFF', 'LLAMA_BUILD_LIBRESSL': 'OFF',
    'LLAMA_USE_SYSTEM_GGML': 'OFF', 'LLAMA_TOOLS_INSTALL': 'OFF', 'LLAMA_TESTS_INSTALL': 'OFF',
    'GGML_NATIVE': 'OFF', 'GGML_CPU': 'ON', 'GGML_AVX': 'ON', 'GGML_AVX2': 'ON',
    'GGML_FMA': 'ON', 'GGML_SSE42': 'OFF', 'GGML_F16C': 'OFF', 'GGML_BMI2': 'OFF',
    'GGML_AVX512': 'OFF', 'GGML_AVX512_VBMI': 'OFF', 'GGML_AVX512_VNNI': 'OFF',
    'GGML_AVX512_BF16': 'OFF', 'GGML_AVX_VNNI': 'OFF', 'GGML_AMX_TILE': 'OFF',
    'GGML_AMX_INT8': 'OFF', 'GGML_AMX_BF16': 'OFF',
    'GGML_CUDA': 'OFF', 'GGML_VULKAN': 'OFF', 'GGML_METAL': 'OFF', 'GGML_HIP': 'OFF',
    'GGML_SYCL': 'OFF', 'GGML_RPC': 'OFF',
    'GGML_MUSA': 'OFF', 'GGML_OPENVINO': 'OFF', 'GGML_HEXAGON': 'OFF',
    'GGML_ZDNN': 'OFF', 'GGML_ZENDNN': 'OFF', 'GGML_VIRTGPU': 'OFF',
    'GGML_VIRTGPU_BACKEND': 'OFF', 'GGML_ET': 'OFF', 'GGML_ET_SYSEMU': 'OFF',
    'GGML_ACCELERATE': 'OFF', 'GGML_STATIC': 'OFF', 'GGML_LTO': 'OFF',
    'GGML_BUILD_TESTS': 'OFF', 'GGML_BUILD_EXAMPLES': 'OFF', 'GGML_OPENCL': 'OFF', 'GGML_WEBGPU': 'OFF',
    'GGML_BLAS': 'OFF', 'GGML_OPENMP': 'OFF', 'GGML_OPENMP_FETCH': 'OFF',
    'GGML_CCACHE': 'OFF', 'GGML_BACKEND_DL': 'OFF', 'GGML_CPU_ALL_VARIANTS': 'OFF',
    'GGML_LLAMAFILE': 'OFF', 'GGML_CPU_KLEIDIAI': 'OFF',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def relative(name):
    p.need(type(name) is str and name and '\\' not in name and '\x00' not in name, 'PATH')
    path = PurePosixPath(name)
    p.need(not path.is_absolute() and all(x not in ('', '.', '..') for x in name.split('/')), 'PATH')
    return path


def git(source, *args):
    """Only fixed read-only plumbing calls; no checkout, filters, hooks or fetch."""
    argv = ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
            '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-C', str(source), *args]
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent', 'LC_ALL': 'C',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0',
           'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_LAZY_FETCH': '1'}
    proc = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True, close_fds=True)
    data = bytearray(); errors = bytearray(); started = time.monotonic()
    try:
        with selectors.DefaultSelector() as sel:
            sel.register(proc.stdout, selectors.EVENT_READ, data)
            sel.register(proc.stderr, selectors.EVENT_READ, errors)
            while sel.get_map():
                p.need(time.monotonic()-started < 15, 'GIT_TIMEOUT')
                for key, _ in sel.select(.05):
                    chunk = os.read(key.fd, 65536)
                    if not chunk: sel.unregister(key.fileobj)
                    else: key.data.extend(chunk)
                    p.need(len(data)+len(errors) <= 4*1024**2, 'GIT_OUTPUT_LIMIT')
        p.need(proc.wait(timeout=1) == 0, 'PINNED_LOCAL_SOURCE_UNAVAILABLE')
        return bytes(data)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL); proc.wait(timeout=2)
        proc.stdout.close(); proc.stderr.close()


def source_manifest(source):
    source = p.secure(Path(source))
    p.need(source.is_dir() and (source/'.git').exists(), 'LOCAL_CHECKOUT_REQUIRED')
    p.need(git(source, 'rev-parse', 'HEAD').decode().strip() == COMMIT, 'WRONG_SOURCE_COMMIT')
    p.need(git(source, 'rev-parse', 'HEAD^{tree}').decode().strip() == TREE, 'WRONG_SOURCE_TREE')
    entries = []; total = 0
    for record in git(source, 'ls-tree', '-rz', '--full-tree', COMMIT).split(b'\0'):
        if not record: continue
        header, name = record.split(b'\t', 1); mode, kind, oid = header.decode().split()
        name = name.decode('utf-8'); relative(name)
        p.need(kind == 'blob' and mode in ('100644', '100755'), 'SOURCE_LINK_OR_SUBMODULE_REVIEW_REQUIRED')
        path = p.secure(source/name); info = path.stat(); size = info.st_size
        p.need(stat.S_ISREG(info.st_mode) and size <= 64*1024**2, 'SOURCE_FILE_TYPE')
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        p.need(size <= 64*1024**2, 'SOURCE_SIZE_LIMIT')
        with path.open('rb') as f: data = f.read(64*1024**2+1)
        p.need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == oid,
               'DIRTY_TRACKED_SOURCE')
        p.need(bool(path.stat().st_mode & 0o111) == (mode == '100755'), 'DIRTY_SOURCE_MODE')
        total += size; p.need(total <= 1024**3 and len(entries) < 20000, 'SOURCE_SIZE_LIMIT')
        entries.append({'path': name, 'mode': mode, 'git_blob': oid, 'sha256': sha, 'size': size})
    p.need(entries and any(e['path'] == 'LICENSE' for e in entries), 'SOURCE_INCOMPLETE')
    # Untracked content is never exported. Detect concurrent HEAD/tree/file changes again during copy.
    return {'commit': COMMIT, 'tree': TREE, 'entries': entries, 'bytes': total,
            'untracked': 'EXCLUDED', 'git_sha256': p.hash_file(Path('/usr/bin/git'))[0]}


def resources(build_cgroup=None):
    from research.memory_headroom_037 import snapshot
    return snapshot(build_cgroup)['available_bytes']


def compatibility():
    p.need(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'LINUX_X86_64_REQUIRED')
    processors = []
    for line in Path('/proc/cpuinfo').read_text().splitlines():
        if line.startswith('flags') and ':' in line: processors.append(set(line.split(':', 1)[1].split()))
    p.need(processors and all({'avx', 'avx2', 'fma'} <= flags for flags in processors), 'AVX2_FMA_COMPATIBILITY_HOLD')
    return {'architecture': 'x86_64', 'kernel_flags_all_visible_cpus': ['avx', 'avx2', 'fma'],
            'real_instruction_execution': 'NOT_TESTED'}


def recipe(root):
    root = Path(root)
    return [['/usr/bin/cmake', '-S', str(root/'source'), '-B', str(root/'build'),
             '-DCMAKE_INSTALL_PREFIX='+str(root/'stage'),
             *['-D'+k+'='+v for k, v in sorted(FLAGS.items())]],
            ['/usr/bin/cmake', '--build', str(root/'build'), '--target', 'llama-cli', '--parallel', '1']]


def prepare(source, destination, protected, *, apply=False):
    source = Path(source); root = Path(destination)
    p.need(root.is_absolute() and root == root.resolve() and not root.exists() and not root.is_symlink(), 'NEW_DESTINATION_REQUIRED')
    p.secure(root.parent)
    p.need(type(protected) is list and protected, 'PROTECTED_ROOTS_REQUIRED')
    for value in [str(source), *protected]:
        other = Path(value); p.need(other.is_absolute(), 'ABSOLUTE_PROTECTED_ROOT')
        other = other.resolve()
        p.need(not root.is_relative_to(other) and not other.is_relative_to(root), 'PROTECTED_DESTINATION')
    manifest = source_manifest(source)
    cpu = compatibility()
    available = resources(); disk = shutil.disk_usage(root.parent).free
    p.need(available >= LIMITS['available_ram_min_bytes'], 'RAM_HEADROOM_HOLD')
    p.need(disk >= LIMITS['disk_free_min_bytes']+manifest['bytes'], 'DISK_HEADROOM_HOLD')
    plan = {'version': 'portable-preparation-036-v1', 'source': str(source), 'destination': str(root),
            'protected_roots': protected, 'source_manifest': manifest, 'commands': recipe(root), 'compatibility': cpu,
            'limits': LIMITS, 'observed_ram_bytes': available, 'observed_disk_free_bytes': disk,
            'environment': {'LC_ALL': 'C', 'TZ': 'UTC', 'SOURCE_DATE_EPOCH': '1793705189',
                            'GIT_CEILING_DIRECTORIES': str(root), 'HOME': str(root/'home'),
                            'PATH': '/usr/bin:/bin'},
            'gates': GATES, 'writes': 0, 'execution_enforcement': 'NOT_ACTIVE_BUILD_DISABLED', 'flags_status': 'SOURCE_REVIEWED_BUILD_UNTESTED',
            'provenance': 'LOCAL_PREPARATION_ONLY_NOT_UPSTREAM_OR_REPRODUCIBLE'}
    if not apply: return plan
    # Ownership ledger is returned and externally pinned. Never recursively delete on exception.
    owned = {}; hashes = {}; old = os.umask(0o077)
    def track(path):
        s = path.lstat(); key = str(path.relative_to(root)); owned[key] = [s.st_dev, s.st_ino, stat.S_IFMT(s.st_mode)]
        if path.is_file(): hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        root.mkdir(mode=0o700); track(root)
        for name in ('source', 'build', 'stage', 'home'):
            (root/name).mkdir(mode=0o700); track(root/name)
        for e in manifest['entries']:
            target = root/'source'/e['path']
            missing = []; parent = target.parent
            while not parent.exists(): missing.append(parent); parent = parent.parent
            for parent in reversed(missing): parent.mkdir(mode=0o700); track(parent)
            original = p.secure(source/e['path'])
            p.need(hashlib.sha256(original.read_bytes()).hexdigest() == e['sha256'] and original.stat().st_size == e['size'], 'SOURCE_CHANGED')
            with os.fdopen(os.open(original, os.O_RDONLY|os.O_NOFOLLOW), 'rb') as src:
                with target.open('xb') as dest: shutil.copyfileobj(src, dest, 1024**2)
            target.chmod(0o700 if e['mode'] == '100755' else 0o600); track(target)
            p.need(hashlib.sha256(target.read_bytes()).hexdigest() == e['sha256'] and target.stat().st_size == e['size'], 'COPY_HASH')
        p.need(source_manifest(source) == manifest, 'SOURCE_CHANGED')
        plan['writes'] = len(owned)+1; plan['owned'] = owned; plan['owned_hashes'] = hashes
        # Receipt itself cannot contain its own inode; outer digest pins full receipt bytes.
        with (root/RECEIPT).open('x') as f: f.write(canonical(plan)+'\n')
        return {'operation': 'PREPARED_ONLY', 'receipt_sha256': p.hash_file(root/RECEIPT)[0],
                'destination': str(root), 'gates': GATES}
    finally:
        os.umask(old)


def rollback(destination, receipt_sha256, *, apply=False):
    root = p.secure(Path(destination)); receipt = p.secure(root/RECEIPT)
    p.need(p.hash_file(receipt)[0] == receipt_sha256, 'RECEIPT_HASH')
    data = json.loads(receipt.read_text()); p.need(data['destination'] == str(root), 'RECEIPT_ROOT')
    expected = data['owned']; actual = [root, *root.rglob('*')]
    p.need(set(expected) | {RECEIPT} == {str(x.relative_to(root)) for x in actual}, 'FOREIGN_PATH_REFUSE')
    for path in actual:
        key = str(path.relative_to(root))
        p.need(not path.is_symlink(), 'ROLLBACK_SYMLINK')
        if key == RECEIPT: continue
        s = path.lstat(); p.need(expected[key] == [s.st_dev, s.st_ino, stat.S_IFMT(s.st_mode)], 'REPLACED_PATH_REFUSE')
        if path.is_file(): p.need(hashlib.sha256(path.read_bytes()).hexdigest() == data['owned_hashes'][key], 'MODIFIED_PATH_REFUSE')
    if not apply: return {'operation': 'ROLLBACK_DRY_RUN', 'paths': len(actual), 'gates': GATES}
    # Concurrency during rollback is not authorized: owner must stop writers first.
    for path in sorted(actual, key=lambda x: len(x.parts), reverse=True):
        if path.is_dir(): path.rmdir()
        else: path.unlink()
    return {'operation': 'ROLLED_BACK_OWN_PREPARATION', 'gates': GATES}


def check_search(root, artifact, entries):
    root = Path(root).resolve(); artifact = Path(artifact)
    for value in entries:
        for entry in value.split(':'):
            p.need(entry == '$ORIGIN' or entry.startswith('$ORIGIN/'), 'UNSAFE_RUNPATH')
            tail = entry[len('$ORIGIN'):]
            p.need('$' not in tail and '\\' not in tail, 'UNSAFE_RUNPATH')
            resolved = (artifact.parent/tail.lstrip('/')).resolve()
            p.need(resolved.is_relative_to(root), 'ESCAPING_RUNPATH')


def soname(path):
    """DT_SONAME supplement to the unchanged CODEX035 passive parser."""
    with path.open('rb') as source: data = source.read(128*1024**2+1)
    p.need(len(data) <= 128*1024**2, 'ELF_METADATA_LIMIT')
    fields = struct.unpack_from('<16sHHIQQQIHHHHHH', data)
    headers = [struct.unpack_from('<IIQQQQQQ', data, fields[5]+i*56) for i in range(fields[10])]
    tags = []
    for h in headers:
        if h[0] == 2:
            for at in range(h[2], h[2]+h[5], 16):
                tag, value = struct.unpack_from('<qQ', data, at)
                if not tag: break
                tags.append((tag, value))
    names = [v for k, v in tags if k == 14]
    p.need(len(names) <= 1, 'AMBIGUOUS_SONAME')
    if not names: return None
    strings = next(v for k, v in tags if k == 5); size = next(v for k, v in tags if k == 10)
    h = next(h for h in headers if h[0] == 1 and h[3] <= strings < h[3]+h[5])
    start = h[2]+strings-h[3]; table = data[start:start+size]
    p.need(names[0] < len(table) and b'\0' in table[names[0]:], 'SONAME_INVALID')
    return table[names[0]:table.index(0, names[0])].decode('ascii')


def inventory(root, manifest):
    """Exact staged inventory, no ldd/default loader fallback or host searching.

    Caller supplies independently reviewed metadata. This does not authenticate it.
    All ELF dependencies (including interpreter) must be in the explicit stage.
    """
    root = p.secure(Path(root)); p.need(root.is_dir(), 'STAGE_REQUIRED')
    p.need(manifest.get('version') == 'portable-artifacts-036-v1', 'MANIFEST_VERSION')
    p.need(manifest.get('source_commit') == COMMIT and manifest.get('source_tree') == TREE, 'SOURCE_PROVENANCE')
    for key in ('compiler', 'cmake', 'build_flags', 'environment', 'commands', 'dependencies', 'license_evidence', 'build_record'):
        p.need(manifest.get(key), 'PROVENANCE_FIELD_REQUIRED:'+key)
    p.need(manifest['build_flags'] == FLAGS, 'BUILD_FLAGS_MISMATCH')
    entries = manifest.get('entries', []); p.need(1 <= len(entries) <= 128, 'ARTIFACT_COUNT')
    names = {}; result = {}; aliases = {}; listing = set()
    for e in entries:
        name = str(relative(e['path'])); p.need(name not in listing, 'DUPLICATE_ARTIFACT'); listing.add(name)
        path = root/name
        if 'link' in e:
            relative(e['link']); p.secure(path.parent)
            p.need(path.is_symlink() and os.readlink(path) == e['link'], 'LINK_MISMATCH')
            resolved = path.resolve(strict=True); p.need(resolved.is_relative_to(root), 'LINK_ESCAPE')
            aliases[name] = str(resolved.relative_to(root)); continue
        p.secure(path); sha, size = p.hash_file(path)
        p.need((sha, size) == (e['sha256'], e['size']), 'ARTIFACT_HASH_SIZE')
        meta = p.elf(path, sha); check_search(root, path, meta['paths']); meta['soname'] = soname(path)
        p.need(p.hash_file(path) == (sha, size), 'ARTIFACT_CHANGED')
        p.need(not meta['needed'] or meta['paths'], 'EXPLICIT_DEPENDENCY_PATH_REQUIRED')
        for name_value in meta['needed']+[meta['soname']] if meta['soname'] else meta['needed']:
            p.need(name_value and '/' not in name_value and name_value not in ('.', '..'), 'DEPENDENCY_NAME')
        result[name] = dict(meta, sha256=sha, size=size)
    actual = {str(f.relative_to(root)) for f in root.rglob('*') if not f.is_dir() or f.is_symlink()}
    p.need(actual == listing, 'UNLISTED_DYNAMIC_OR_FOREIGN_FILE')
    for name, target in aliases.items(): p.need(target in result, 'UNLISTED_LINK_TARGET')
    for name, meta in result.items():
        if meta['soname']:
            p.need(meta['soname'] not in names, 'DUPLICATE_SONAME'); names[meta['soname']] = name
        for dependency in meta['needed']:
            matches = []
            for entry in meta['paths']:
                for search in entry.split(':'):
                    directory = (root/name).parent/search[len('$ORIGIN'):].lstrip('/')
                    candidate = directory/dependency
                    if candidate.exists():
                        key = str(candidate.resolve().relative_to(root))
                        p.need(key in result, 'UNINVENTORIED_DEPENDENCY'); matches.append(key)
            p.need(matches and len(set(matches)) == 1, 'MISSING_OR_AMBIGUOUS_DEPENDENCY')
            p.need(result[matches[0]]['soname'] == dependency, 'DEPENDENCY_SONAME_MISMATCH')
        if meta['interpreter']:
            interpreter = meta['interpreter']; p.need(interpreter.startswith('/'), 'INTERPRETER_PATH')
            p.need(interpreter.lstrip('/') in listing, 'INTERPRETER_NOT_INVENTORIED')
    p.need('bin/llama-cli' in result and result['bin/llama-cli']['interpreter'], 'DYNAMIC_CLI_INTERPRETER_REQUIRED')
    return {'operation': 'PASSIVE_ARTIFACT_CHECK', 'artifacts': result, 'symlink_chains': aliases,
            'attestation': 'LOCAL_BUILD_ATTESTATION_NOT_INDEPENDENT', 'manifest_sha256': digest(manifest),
            'build_inputs_sha256': digest({k: v for k, v in manifest.items() if k != 'entries'}),
            'provisioner_035': 'HOLD_INDEPENDENT_EXPECTATIONS_AND_MODEL_REQUIRED', 'gates': GATES}


def repeat(first, second):
    for report in (first, second):
        p.need(report.get('operation') == 'PASSIVE_ARTIFACT_CHECK' and report.get('artifacts'), 'VERIFIED_REPORT_REQUIRED')
    same = first['artifacts'] == second['artifacts'] and first['symlink_chains'] == second['symlink_chains']
    return {'byte_comparison': 'IDENTICAL_LOCAL_REPORTS' if same else 'NONDETERMINISM_OR_INPUT_DIFFERENCE',
            'recorded_inputs': 'IDENTICAL' if first.get('build_inputs_sha256') == second.get('build_inputs_sha256') else 'DIFFERENT',
            'independent_reproducibility': 'UNVERIFIED', 'upstream_authenticity': 'UNVERIFIED', 'gates': GATES}


def handoff(root, manifest, destination, protected):
    """Produce deliberately unqualified CODEX035 inventory; never upgrades trust."""
    report = inventory(root, manifest)
    entries = []
    for e in manifest['entries']:
        name = e['path']; target = report['symlink_chains'].get(name, name)
        meta = report['artifacts'][target]
        entries.append({'source': str(Path(root)/name), 'bundle_path': name,
                        'role': 'runtime' if name == 'bin/llama-cli' else 'library',
                        'sha256': meta['sha256'], 'expectation': 'LOCAL_BUILD_ATTESTATION',
                        'evidence_ref': 'LOCAL_NOT_INDEPENDENT:'+report['manifest_sha256']})
    return {'version': 'private-bundle-v1', 'destination': destination,
            'protected_roots': protected, 'entries': entries,
            'licenses_reviewed': False, 'build_evidence': 'LOCAL_BUILD_ATTESTATION_ONLY',
            'dynamic_source_dirs': [str(Path(root)/'lib')]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--source', required=True); prep.add_argument('--destination', required=True)
    prep.add_argument('--protected', action='append', required=True); prep.add_argument('--apply', action='store_true')
    rb = sub.add_parser('rollback'); rb.add_argument('--destination', required=True); rb.add_argument('--receipt-sha256', required=True); rb.add_argument('--apply', action='store_true')
    verify = sub.add_parser('verify'); verify.add_argument('--stage', required=True); verify.add_argument('--manifest', required=True)
    comp = sub.add_parser('compare'); comp.add_argument('first'); comp.add_argument('second')
    ho = sub.add_parser('handoff'); ho.add_argument('--stage', required=True); ho.add_argument('--manifest', required=True)
    ho.add_argument('--destination', required=True); ho.add_argument('--protected', action='append', required=True)
    sub.add_parser('build'); sub.add_parser('status')
    args = parser.parse_args(argv)
    try:
        if args.action == 'prepare': result = prepare(args.source, args.destination, args.protected, apply=args.apply)
        elif args.action == 'rollback': result = rollback(args.destination, args.receipt_sha256, apply=args.apply)
        elif args.action == 'verify': result = inventory(args.stage, json.loads(Path(args.manifest).read_text()))
        elif args.action == 'handoff': result = handoff(args.stage, json.loads(Path(args.manifest).read_text()), args.destination, args.protected)
        elif args.action == 'compare': result = repeat(json.loads(Path(args.first).read_text()), json.loads(Path(args.second).read_text()))
        elif args.action == 'build': raise Refused('SEPARATE_OWNER_APPROVAL_AND_CONTAINMENT_REQUIRED_BUILD_HOLD')
        else: result = {'gates': GATES, 'source_commit': COMMIT, 'source_tree': TREE, 'base': BASE,
                        'limits': LIMITS, 'host': platform.system(), 'actual_build_executor': 'DISABLED'}
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    except (Refused, OSError, ValueError, KeyError, StopIteration, struct.error) as exc:
        print(json.dumps({'operation': 'REFUSED', 'reason': str(exc), 'gates': GATES}, sort_keys=True)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
