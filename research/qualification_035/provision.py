"""Verified explicit-inventory provisioning. Dry-run default; no source writes."""
import ctypes
import errno
import hashlib
import json
import io
import os
from pathlib import Path
import secrets
import stat
import struct
import sys
import tempfile
from research.llama_analyst_033 import Refused
from research.decision_loop_032 import canonical,digest,exact

RECEIPT='.boss-provision-035.json'
CAP=2*1024**3
ELF_METADATA_LIMIT=64*1024
ELF_STRING_TABLE_LIMIT=1024*1024


def need(value,reason):
    if not value:raise Refused(reason)


def secure(path,*,allow_missing=False):
    """No symlink ancestors, untrusted owners, writeable ancestors or POSIX ACLs."""
    path=Path(path);need(path.is_absolute(),'ABSOLUTE_PATH_REQUIRED')
    for p in reversed((path,*path.parents)):
        if allow_missing and not p.exists() and not p.is_symlink():continue
        info=p.lstat();need(not stat.S_ISLNK(info.st_mode),'SYMLINK_ANCESTOR')
        need(info.st_uid in (os.stat('/').st_uid,os.getuid()) and not info.st_mode&0o022,'UNSAFE_OWNER_OR_PERMISSIONS')
        try:attrs=os.listxattr(p,follow_symlinks=False)
        except OSError:raise Refused('ACL_CHECK_UNAVAILABLE') from None
        need(not any(k in attrs for k in ('system.posix_acl_access','system.posix_acl_default')),'ACL_REVIEW_REQUIRED')
    return path


def hash_file(path):
    sha=hashlib.sha256();size=0
    flags=os.O_RDONLY|os.O_NOFOLLOW
    with os.fdopen(os.open(path,flags),'rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and 0<before.st_size<=CAP,'FILE_TYPE_OR_SIZE')
        while True:
            data=f.read(1024*1024)
            if not data:break
            size+=len(data);need(size<=CAP,'FILE_SIZE');sha.update(data)
        after=os.fstat(f.fileno())
        need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'SOURCE_CHANGED')
    return sha.hexdigest(),size


def elf(path,expected_sha256):
    """Small passive ELF64-LE dynamic dependency reader; never runs ldd/loader."""
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as source:
        data=source.read(128*1024**2+1)
    need(len(data)<=128*1024**2 and hashlib.sha256(data).hexdigest()==expected_sha256,'ELF_HASH_BINDING')
    with io.BytesIO(data) as f:
        file_size=len(data)
        head=f.read(64)
        need(len(head)==64 and head[:6]==b'\x7fELF\x02\x01','ELF64_LE_REQUIRED')
        fields=struct.unpack('<16sHHIQQQIHHHHHH',head)
        need(fields[2]==62 and fields[9]==56 and 0<fields[10]<=128,'ELF_X86_64_PROFILE')
        f.seek(fields[5]);headers=[]
        for _ in range(fields[10]):
            item=f.read(56);need(len(item)==56,'ELF_TRUNCATED');headers.append(struct.unpack('<IIQQQQQQ',item))
        def read(offset,size,*,limit=ELF_METADATA_LIMIT):
            need(0<=size<=limit,'ELF_METADATA_LIMIT')
            need(0<=offset<=file_size and size<=file_size-offset,'ELF_TRUNCATED')
            f.seek(offset);data=f.read(size);need(len(data)==size,'ELF_TRUNCATED');return data
        interpreter=None;dynamic=[]
        for h in headers:
            if h[0]==3:interpreter=read(h[2],h[5]).rstrip(b'\0').decode('ascii')
            if h[0]==2:
                data=read(h[2],h[5]);need(len(data)%16==0,'ELF_DYNAMIC_INVALID')
                for offset in range(0,len(data),16):
                    tag,value=struct.unpack_from('<qQ',data,offset)
                    if tag==0:break
                    dynamic.append((tag,value))
        if not dynamic:return {'needed':[],'interpreter':interpreter,'paths':[]}
        strings=next((v for k,v in dynamic if k==5),None);size=next((v for k,v in dynamic if k==10),0)
        need(strings is not None and 0<size<=ELF_STRING_TABLE_LIMIT,'ELF_STRING_TABLE')
        segment=next((h for h in headers if h[0]==1 and h[3]<=strings<h[3]+h[5]),None)
        need(segment is not None and segment[5]<=segment[6] and
             segment[2]<=file_size and segment[5]<=file_size-segment[2] and
             strings-segment[3]+size<=segment[5],'ELF_STRING_MAPPING')
        table=read(segment[2]+strings-segment[3],size,limit=ELF_STRING_TABLE_LIMIT)
        def string(at):
            need(at<len(table) and b'\0' in table[at:],'ELF_STRING_INVALID')
            return table[at:table.index(0,at)].decode('ascii')
        return {'needed':[string(v) for k,v in dynamic if k==1],
                'interpreter':interpreter,'paths':[string(v) for k,v in dynamic if k in (15,29)]}


def inventory(config):
    exact(config,('version','destination','protected_roots','entries','licenses_reviewed','build_evidence','dynamic_source_dirs'))
    need(config['version']=='private-bundle-v1','VERSION')
    need(config['licenses_reviewed'] is True and type(config['build_evidence']) is str and config['build_evidence'],'LICENSE_BUILD_REVIEW_REQUIRED')
    dest=Path(config['destination']);secure(dest.parent)
    need(not dest.exists() and not dest.is_symlink(),'DESTINATION_EXISTS')
    need(type(config['protected_roots']) is list and config['protected_roots'] and all(type(p) is str and Path(p).is_absolute() for p in config['protected_roots']),'PROTECTED_ROOTS_REQUIRED')
    protected=[Path(p).resolve() for p in config['protected_roots']]
    need(dest.is_absolute() and dest==dest.resolve(),'UNSAFE_DESTINATION')
    for p in protected:need(not dest.is_relative_to(p) and not p.is_relative_to(dest),'PROTECTED_DESTINATION')
    entries=config['entries'];need(type(entries) is list and 1<=len(entries)<=128,'INVENTORY_LIMIT')
    by_name={};by_source={};files={};links={};metadata={}
    for e in entries:
        exact(e,('source','bundle_path','role','sha256','expectation','evidence_ref'))
        name=e['bundle_path'];relative=Path(name)
        need(type(name) is str and name and not relative.is_absolute() and '..' not in relative.parts and name==relative.as_posix() and name!='.' and name not in by_name and name!=RECEIPT,'BUNDLE_PATH')
        need(e['role'] in ('runtime','library','loader','model'),'ROLE')
        need(e['expectation'] in ('UPSTREAM_PUBLISHED','REPRODUCIBLE_BUILD','SYNTHETIC_TEST') and type(e['evidence_ref']) is str and e['evidence_ref'],'INDEPENDENT_EXPECTATION_REQUIRED')
        source=Path(e['source']);secure(source.parent);need(source.is_absolute(),'SOURCE_PATH')
        need(not source.is_relative_to(dest) and not dest.is_relative_to(source),'SOURCE_DESTINATION_OVERLAP')
        if source.is_symlink():
            target=os.readlink(source);need(not Path(target).is_absolute(),'ABSOLUTE_LINK_REFUSED')
            target_name=os.path.normpath(str(relative.parent/target));need(not target_name.startswith('../') and target_name!='..','LINK_ESCAPE')
            links[name]=target
        else:
            secure(source);actual,size=hash_file(source)
            need(actual==e['sha256'],'HASH_MISMATCH')
            files[name]={'sha256':actual,'bytes':size,'role':e['role']}
            if e['role'] in ('runtime','library','loader'):metadata[name]=elf(source,actual)
        by_name[name]=e;by_source[str(source)]=name
    need(type(config['dynamic_source_dirs']) is list and len(config['dynamic_source_dirs'])<=8,'DYNAMIC_INVENTORY_REQUIRED')
    for directory in config['dynamic_source_dirs']:
        folder=secure(Path(directory));need(folder.is_dir(),'DYNAMIC_DIRECTORY')
        candidates=list(folder.glob('*.so*'));need(len(candidates)<=256,'DYNAMIC_INVENTORY_LIMIT')
        for candidate in candidates:need(str(candidate) in by_source,'DYNAMIC_LIBRARY_NOT_INVENTORIED')
    def final(name):
        visited=set()
        while name in links:
            need(name not in visited and len(visited)<32,'LINK_CYCLE');visited.add(name)
            name=os.path.normpath(str(Path(name).parent/links[name]))
        need(name in files,'UNRESOLVED_LINK_TARGET');return name
    for name in links:
        resolved=final(name);source=Path(by_name[name]['source'])
        need(source.resolve()==Path(by_name[resolved]['source']).resolve(),'LINK_MAPPING_MISMATCH')
        need(by_name[name]['sha256']==files[resolved]['sha256'],'LINK_DIGEST_MISMATCH')
    need(len({final(n) for n,e in by_name.items() if e['role']=='runtime'})==1 and len({final(n) for n,e in by_name.items() if e['role']=='model'})==1,'RUNTIME_AND_MODEL_REQUIRED')
    aliases={}
    for name in by_name:
        if by_name[name]['role'] in ('library','loader'):
            base=Path(name).name;need(base not in aliases or aliases[base]==final(name),'AMBIGUOUS_LIBRARY');aliases[base]=final(name)
    for name,meta in metadata.items():
        for required in meta['needed']:need(required in aliases,'DEPENDENCY_CLOSURE_UNRESOLVED:'+required)
        if meta['interpreter']:
            need(Path(meta['interpreter']).name in aliases and by_name[aliases[Path(meta['interpreter']).name]]['role']=='loader','INTERPRETER_UNRESOLVED')
        for search in meta['paths']:
            for part in search.split(':'):
                need((part=='$ORIGIN' or part.startswith('$ORIGIN/')) and not os.path.normpath(str(Path(name).parent/part.replace('$ORIGIN','.',1))).startswith('../'),'UNSAFE_RUNPATH')
    return {'config_sha256':digest(config),'files':files,'links':links,'elf_dependencies':metadata,
            'expectations':'SOURCE_RECORDS_NOT_CRYPTOGRAPHIC_ATTESTATION','state':'REAL_NOT_RUN'}


def _remove_owned(root,owned,identity):
    """Never enumerate new entries for deletion; changed/foreign paths stop cleanup."""
    need((root.stat().st_dev,root.stat().st_ino)==identity,'STAGING_IDENTITY_CHANGED')
    actual={str(p.relative_to(root)): (p.lstat().st_dev,p.lstat().st_ino) for p in root.rglob('*')}
    need(actual==owned,'STAGING_CHANGED_CLEANUP_REFUSED')
    for name in sorted(owned,key=lambda n:len(Path(n).parts),reverse=True):
        path=root/name;info=path.lstat()
        need((info.st_dev,info.st_ino)==owned[name],'OWN_FILE_REPLACED_CLEANUP_REFUSED')
        if stat.S_ISDIR(info.st_mode):path.rmdir()
        else:path.unlink()
    need((root.stat().st_dev,root.stat().st_ino)==identity,'STAGING_IDENTITY_CHANGED')
    root.rmdir()


def _rename_new(source,dest,parent_fd=None):
    libc=ctypes.CDLL(None,use_errno=True)
    need(hasattr(libc,'renameat2'),'ATOMIC_NOREPLACE_UNAVAILABLE')
    result=libc.renameat2(-100 if parent_fd is None else parent_fd,os.fsencode(source if parent_fd is None else source.name),-100 if parent_fd is None else parent_fd,os.fsencode(dest if parent_fd is None else dest.name),1)
    if result:raise Refused('ATOMIC_COMMIT_REFUSED:'+str(ctypes.get_errno()))


def provision(config,*,apply=False):
    plan=inventory(config);dest=Path(config['destination'])
    if not apply:return {**plan,'operation':'DRY_RUN','writes':0}
    need(sys.platform=='linux' and Path('/proc/self/fd').is_dir(),'LINUX_ATOMIC_PLATFORM_REQUIRED')
    import shutil
    need(shutil.disk_usage(dest.parent).free>sum(x['bytes'] for x in plan['files'].values())+64*1024**2,'DISK_HEADROOM')
    parent_fd=os.open(dest.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    need((os.fstat(parent_fd).st_dev,os.fstat(parent_fd).st_ino)==(dest.parent.stat().st_dev,dest.parent.stat().st_ino),'PARENT_CHANGED')
    stage_name='.boss-035-stage-'+secrets.token_hex(16);os.mkdir(stage_name,0o700,dir_fd=parent_fd)
    stage=Path('/proc/self/fd')/str(parent_fd)/stage_name;stage.chmod(0o700);identity=(stage.stat().st_dev,stage.stat().st_ino);committed=False;owned={}
    def track(path):owned[str(path.relative_to(stage))]=(path.lstat().st_dev,path.lstat().st_ino)
    def parents(path):
        for part in reversed(path.parents):
            if part==stage or not part.is_relative_to(stage):continue
            if not part.exists():part.mkdir(mode=0o700);track(part)
    try:
        for name,meta in plan['files'].items():
            source=Path(next(e['source'] for e in config['entries'] if e['bundle_path']==name))
            target=stage/name;parents(target)
            with os.fdopen(os.open(source,os.O_RDONLY|os.O_NOFOLLOW),'rb') as inp,target.open('xb') as out:
                track(target);sha=hashlib.sha256();count=0
                while True:
                    data=inp.read(1024*1024)
                    if not data:break
                    count+=len(data);need(count<=meta['bytes'],'SOURCE_CHANGED');sha.update(data);out.write(data)
                need(count==meta['bytes'] and sha.hexdigest()==meta['sha256'],'SOURCE_CHANGED')
                out.flush();os.fsync(out.fileno())
            target.chmod(0o500 if meta['role']=='runtime' else 0o400)
            need(hash_file(target)==(meta['sha256'],meta['bytes']),'POSTCOPY_MISMATCH')
        for name,target in plan['links'].items():
            path=stage/name;parents(path);path.symlink_to(target);track(path)
        for directory in stage.rglob('*'):
            if directory.is_dir() and not directory.is_symlink():directory.chmod(0o700)
        receipt={**plan,'operation':'APPLIED_PRIVATE_COPY','nonce':secrets.token_hex(16),
                 'destination_sha256':hashlib.sha256(str(dest).encode()).hexdigest(),
                 'root_inode':stage.stat().st_ino,'root_device':stage.stat().st_dev}
        with (stage/RECEIPT).open('x') as f:track(stage/RECEIPT);f.write(canonical(receipt));f.flush();os.fsync(f.fileno())
        (stage/RECEIPT).chmod(0o400)
        # Detect destination/parent races again; rename is exclusive, never replaces.
        secure(dest.parent);need(not dest.exists() and not dest.is_symlink(),'DESTINATION_RACE')
        _rename_new(stage,dest,parent_fd);committed=True
        return receipt
    finally:
        try:
            if not committed and stage.exists():_remove_owned(stage,owned,identity)
        finally:os.close(parent_fd)


def verify_bundle(config,receipt_sha256):
    dest=secure(Path(config['destination']));need(dest.is_dir(),'BUNDLE_MISSING')
    for p in config['protected_roots']:
        root=Path(p).resolve();need(not dest.is_relative_to(root) and not root.is_relative_to(dest),'PROTECTED_DESTINATION')
    receipt_path=dest/RECEIPT
    raw=receipt_path.read_text();need(hashlib.sha256(raw.encode()).hexdigest()==receipt_sha256,'RECEIPT_PIN_REQUIRED')
    receipt=json.loads(raw)
    need(receipt.get('operation')=='APPLIED_PRIVATE_COPY' and type(receipt.get('nonce')) is str and len(receipt['nonce'])==32,'NOT_OWN_PROVISION_RECEIPT')
    need(receipt['config_sha256']==digest(config) and receipt['destination_sha256']==hashlib.sha256(str(dest).encode()).hexdigest(),'RECEIPT_BINDING')
    need((dest.stat().st_ino,dest.stat().st_dev)==(receipt['root_inode'],receipt['root_device']),'BUNDLE_IDENTITY')
    expected=set(receipt['files'])|set(receipt['links'])|{RECEIPT}
    actual={str(p.relative_to(dest)) for p in dest.rglob('*') if not p.is_dir() or p.is_symlink()}
    need(actual==expected,'FOREIGN_OR_MISSING_FILES_NO_ROLLBACK')
    for name,meta in receipt['files'].items():need(hash_file(dest/name)==(meta['sha256'],meta['bytes']),'MODIFIED_BUNDLE_NO_ROLLBACK')
    for name,target in receipt['links'].items():need((dest/name).is_symlink() and os.readlink(dest/name)==target,'MODIFIED_LINK')
    # Directory extras are foreign too, even if empty.
    required_dirs={str(Path(name).parent) for name in expected}
    allowed_dirs=set()
    for name in expected:
        allowed_dirs.update(str(p) for p in Path(name).parents if str(p)!='.')
    need({str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_dir() and not p.is_symlink()}==allowed_dirs,'FOREIGN_DIRECTORIES')
    return receipt


def rollback(config,receipt_sha256):
    verify_bundle(config,receipt_sha256)
    dest=Path(config['destination'])
    owned={str(p.relative_to(dest)):(p.lstat().st_dev,p.lstat().st_ino) for p in dest.rglob('*')}
    _remove_owned(dest,owned,(dest.stat().st_dev,dest.stat().st_ino))
    return {'operation':'ROLLED_BACK_OWN_BUNDLE','state':'REAL_NOT_RUN'}
