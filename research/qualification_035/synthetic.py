"""Original inert ELF-shaped bytes for provisioning tests; NEVER executable code."""
import hashlib
import struct
from pathlib import Path


def elf_bytes(needed=()):
    strings=b'\0';offsets=[]
    for name in needed:offsets.append(len(strings));strings+=name.encode()+b'\0'
    tags=[(1,n) for n in offsets]+[(5,0x400000+512),(10,len(strings)),(0,0)]
    data=bytearray(768)
    data[:64]=struct.pack('<16sHHIQQQIHHHHHH',b'\x7fELF\x02\x01'+b'\0'*10,3,62,1,0,64,0,0,64,56,2,0,0,0)
    data[64:120]=struct.pack('<IIQQQQQQ',1,5,0,0x400000,0,768,768,4096)
    data[120:176]=struct.pack('<IIQQQQQQ',2,4,256,0x400100,0,len(tags)*16,len(tags)*16,8)
    for index,pair in enumerate(tags):struct.pack_into('<qQ',data,256+index*16,*pair)
    data[512:512+len(strings)]=strings
    return bytes(data)


def bundle(root):
    source=Path(root)/'synthetic-original';source.mkdir(mode=0o700)
    for name in ('bin','lib','models'):(source/name).mkdir(mode=0o700)
    (source/'bin/runtime').write_bytes(elf_bytes(('libfake.so.1',)));(source/'bin/runtime').chmod(0o500)
    (source/'lib/libfake.so.1.0').write_bytes(elf_bytes());(source/'lib/libfake.so.1.0').chmod(0o400)
    (source/'lib/libfake.so.1').symlink_to('libfake.so.1.0');(source/'lib/libfake.so').symlink_to('libfake.so.1')
    (source/'models/model.gguf').write_bytes(b'GGUF ORIGINAL INERT TEST SENTINEL; NO MODEL');(source/'models/model.gguf').chmod(0o400)
    entries=[]
    for name,role in (('bin/runtime','runtime'),('lib/libfake.so.1.0','library'),('lib/libfake.so.1','library'),('lib/libfake.so','library'),('models/model.gguf','model')):
        entries.append({'source':str(source/name),'bundle_path':name,'role':role,'sha256':hashlib.sha256((source/name).read_bytes()).hexdigest(),
                        'expectation':'SYNTHETIC_TEST','evidence_ref':'ORIGINAL_035_INERT_TEST_BYTES_NOT_UPSTREAM_PROVENANCE'})
    return {'version':'private-bundle-v1','destination':str(Path(root)/'new-private'),
            'protected_roots':[str(source),str(Path(root)/'recorder-not-accessed')],'entries':entries,
            'dynamic_source_dirs':[str(source/'lib')],'licenses_reviewed':True,'build_evidence':'ORIGINAL_SYNTHETIC_TEST_ONLY_NOT_A_BUILD'}
