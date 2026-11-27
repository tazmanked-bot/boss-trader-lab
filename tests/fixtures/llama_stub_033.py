"""CONTROLLED TEST PROGRAM. No GGUF/model loading, network, tools or AI inference."""
import json
import os
import sys
import time
scenario,reference=sys.argv[1:]
sys.stdin.buffer.read(1409)
if scenario=='timeout':time.sleep(5)
if scenario=='nonzero':sys.exit(7)
if scenario=='overflow':sys.stdout.write('x'*10000);sys.exit(0)
if scenario=='stderr-overflow':sys.stderr.write('x'*10000);sys.exit(0)
if scenario=='environment':
    import resource
    limits={k:resource.getrlimit(getattr(resource,k))[0] for k in ('RLIMIT_AS','RLIMIT_CPU','RLIMIT_FSIZE','RLIMIT_NOFILE','RLIMIT_CORE')}
    print(json.dumps({'keys':sorted(os.environ),'secret_present':bool(os.environ.get('OWNER_TEST_SECRET')),'cwd_is_home':os.getcwd()==os.environ['HOME'],'limits':limits}));sys.exit(0)
if scenario=='invalid':print('not JSON');sys.exit(0)
value={'version':'analyst-v1','hypothesis':'SIMULATED STUB: existing features merit research review.',
       'evidence_refs':[reference],'strongest_objection':'This program is not a model and tests no reasoning quality.',
       'missing_information':[],'invalidation':'A later eligible low below the retest anchor invalidates the condition.',
       'disposition':'SUPPORT'}
if scenario=='extra':value['order']='BUY'
if scenario=='badref':value['evidence_refs']=['unknown']
if scenario=='no-objection':value['strongest_objection']=''
if scenario=='duplicate':
    print('{"version":"analyst-v1",'+json.dumps(value)[1:]);sys.exit(0)
print(json.dumps(value))
