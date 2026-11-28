"""Read-only cgroup-v2 capacity evidence for the supervisor and future build parent.

No cgroup creation, controller enablement, limit changes or inference authority.
"""
import os
from pathlib import Path, PurePosixPath
import re
from research.llama_analyst_033 import Refused


def need(value, reason):
    if not value:raise Refused(reason)


def read_text(path):
    with os.fdopen(os.open(path, os.O_RDONLY|os.O_NOFOLLOW), 'rb') as source:
        data=source.read(1024**2+1)
    need(len(data)<=1024**2,'MEMORY_METADATA_SIZE')
    return data.decode('ascii')


def absolute(value):
    need(type(value) is str and value.startswith('/') and '\x00' not in value,'CGROUP_PATH')
    path=PurePosixPath(value)
    need('..' not in path.parts and str(path)==value and not value.startswith('//'),'CGROUP_PATH')
    return path


def unescape(value):
    values={'040':' ','011':'\t','012':'\n','134':'\\'}
    def replace(match):
        need(match[1] in values,'MOUNT_ESCAPE');return values[match[1]]
    decoded=re.sub(r'\\([0-9]{3})',replace,value)
    # A decoded backslash is a legal Linux filename character.
    need(not re.search(r'\\(?![0-9]{3})',value),'MOUNT_ESCAPE')
    return decoded


def number(value):
    need(bool(re.fullmatch('[0-9]+',value)) and len(value)<=20,'MEMORY_VALUE')
    result=int(value);need(result<2**64,'MEMORY_VALUE');return result


def snapshot(build_cgroup=None, *, reader=read_text):
    """Conservative min(MemAvailable, max/high minus current at both ancestor chains).

    Only the real hierarchy root may lack memory interfaces unconditionally.
    Nonroot absent interfaces require readable proof the parent has not enabled
    memory; its own applicable ancestors are still checked. Partial/unreadable or
    hidden metadata fails closed. The future child 3-GiB ceiling is NOT host
    headroom and must not be subtracted as if it were an ancestor constraint.
    """
    result={'version':'memory-headroom-037-v1','status':'HOLD','available_bytes':0,
            'limits':[],'scope':'VISIBLE_PROCESS_AND_CONFIGURED_BUILD_ANCESTORS',
            'observation':'POINT_IN_TIME_NOT_RESERVED_MEMORY'}
    try:
        mem=reader('/proc/meminfo')
        matches=re.findall(r'^MemAvailable:\s+([0-9]+)\s+kB\s*$',mem,re.MULTILINE)
        need(len(matches)==1,'MEM_AVAILABLE_REQUIRED')
        available=number(matches[0])*1024;result['kernel_available_bytes']=available
        membership=reader('/proc/self/cgroup');mountinfo=reader('/proc/self/mountinfo')
        unified=[line[3:] for line in membership.splitlines() if line.startswith('0::')]
        need(len(unified)==1,'CGROUP_V2_MEMBERSHIP_REQUIRED');logical=absolute(unified[0])
        build=None
        if build_cgroup is not None:
            raw=os.fspath(build_cgroup)
            need(type(raw) is str and raw.startswith('/'),'CGROUP_PATH')
            # Preserve benign legacy config spelling (trailing slash / dot / repeated slash).
            build=absolute(str(PurePosixPath('/'+raw.lstrip('/'))))
        mounts=[]
        for line in mountinfo.splitlines():
            if ' - ' not in line:continue
            left,right=line.split(' - ',1)
            right_fields=right.split();need(bool(right_fields),'CGROUP_MOUNT_METADATA')
            if right_fields[0]!='cgroup2':continue
            fields=left.split();need(len(fields)>=6,'CGROUP_MOUNT_METADATA')
            root=absolute(unescape(fields[3]));point=absolute(unescape(fields[4]))
            if logical.is_relative_to(root) and (build is None or build.is_relative_to(point)):
                mounts.append((root,point))
        need(mounts,'CGROUP_MOUNT_NOT_MAPPED')
        # Prefer the widest visible ancestor chain; ambiguous aliases fail closed.
        mounts.sort(key=lambda item:len(item[0].parts));root,point=mounts[0]
        need(sum(len(item[0].parts)==len(root.parts) for item in mounts)==1,'AMBIGUOUS_CGROUP_MOUNT')
        need(root==PurePosixPath('/'),'CGROUP_ANCESTORS_NOT_VISIBLE')
        need('memory' in reader(str(point/'cgroup.controllers')).split(),'MEMORY_CONTROLLER_UNAVAILABLE')
        process=point/logical.relative_to(root)
        result.update(process_cgroup=str(process),configured_build_cgroup=str(build) if build else None,
                      mountpoint=str(point),hierarchy_root=str(root))
        nodes=set()
        for leaf in (process,build):
            if leaf is None:continue
            need(leaf.is_relative_to(point),'BUILD_CGROUP_OUTSIDE_MOUNT')
            depth=0
            while True:
                nodes.add(leaf);depth+=1;need(depth<=128,'CGROUP_DEPTH')
                if leaf==point:break
                leaf=leaf.parent
        def optional(path):
            try:return reader(str(path)).strip()
            except FileNotFoundError:return None
        for node in sorted(nodes,key=lambda item:(len(item.parts),str(item)),reverse=True):
            kind=reader(str(node/'cgroup.type')).strip()
            need(kind in ('domain','threaded','domain threaded'),'CGROUP_TYPE')
            high=optional(node/'memory.high');maximum=optional(node/'memory.max')
            current=optional(node/'memory.current')
            if high is None and maximum is None and current is None:
                if node==point:
                    result['limits'].append({'path':str(node),'state':'HIERARCHY_ROOT_NO_MEMORY_INTERFACES'})
                    continue
                controllers=reader(str(node.parent/'cgroup.subtree_control')).split()
                need('memory' not in controllers,'MISSING_ENABLED_MEMORY_INTERFACE')
                result['limits'].append({'path':str(node),'state':'PARENT_MEMORY_CONTROLLER_NOT_ENABLED'})
                continue
            need(node!=point,'CGROUP_NAMESPACE_ROOT_REVIEW_REQUIRED')
            need(None not in (high,maximum,current),'PARTIAL_MEMORY_INTERFACE')
            used=number(current);entry={'path':str(node),'current_bytes':used,'max':maximum,'high':high}
            for name,value in (('max',maximum),('high',high)):
                if value=='max':continue
                remaining=max(0,number(value)-used);available=min(available,remaining)
                entry[name+'_remaining_bytes']=remaining
            need(reader(str(node/'memory.max')).strip()==maximum and reader(str(node/'memory.high')).strip()==high,
                 'MEMORY_LIMIT_CHANGED')
            result['limits'].append(entry)
        need(reader('/proc/self/cgroup')==membership and reader('/proc/self/mountinfo')==mountinfo,'CGROUP_SCOPE_CHANGED')
        result.update(status='PASS',available_bytes=available)
    except (OSError,ValueError,TypeError,Refused) as exc:
        result.update(status='HOLD',available_bytes=0,reason=str(exc))
    return result
