"""Offline synthetic Scout → Verify → MOCK Analyst → deterministic Risk → Evidence.

Not genuine AI inference, a new strategy, a paper fill engine or order authority.
"""
from dataclasses import dataclass
import hashlib
import json
import re
import time
from typing import Protocol
from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates

VERSION='offline-decision-loop-v1'
POLICY='research-risk-v1'
BASELINE='e0c098e85d66e4856efd46b062ecefc61f764be5'
MAX_BYTES=262144
MAX_LEADS=12


def canonical(value):return registry.canonical_json(value)
def digest(value):return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()
def require(condition,reason):
    if not condition:raise ValueError(reason)
def exact(value,keys):require(type(value) is dict and set(value)==set(keys),'SCHEMA_INVALID')
def integer(value):return type(value) is int and registry.MIN_TIME<=value<registry.MAX_TIME

def bounded(value,limit=MAX_BYTES):
    require(len(canonical(value).encode('ascii'))<=limit,'SIZE_LIMIT')


def parse(text):
    require(type(text) is str and len(text.encode('utf-8'))<=MAX_BYTES,'SIZE_LIMIT')
    def unique(pairs):
        out={}
        for k,v in pairs:
            require(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    def reject(_):raise ValueError('NONFINITE_JSON')
    result=json.loads(text,object_pairs_hook=unique,parse_constant=reject)
    bounded(result);return result


@dataclass(frozen=True)
class Snapshot:
    canonical_text:str
    sha256:str
    def data(self):return json.loads(self.canonical_text)


class EvidenceJournal:
    """Append-only evidence receipts; no balances, positions, fills or money math.

    Immutable strings and chained hashes detect accidental changes, not authenticity
    or filesystem WORM storage. The existing DEMO paper engine remains separate.
    """
    def __init__(self):self._items=[]
    @property
    def snapshots(self):return tuple(self._items)
    def append(self,record):
        bounded(record)
        value={'version':VERSION,'sequence':len(self._items),
               'previous_sha256':self._items[-1].sha256 if self._items else None,'record':record}
        text=canonical(value);snapshot=Snapshot(text,hashlib.sha256(text.encode('ascii')).hexdigest())
        self._items.append(snapshot);return snapshot


def verify_journal(items):
    require(type(items) is list and len(items)<=2*MAX_LEADS,'JOURNAL_INVALID')
    previous=None
    for index,item in enumerate(items):
        exact(item,('sha256','snapshot'))
        value=item['snapshot'];exact(value,('version','sequence','previous_sha256','record'))
        require(value['version']==VERSION and type(value['sequence']) is int and value['sequence']==index
                and value['previous_sha256']==previous and digest(value)==item['sha256'],'JOURNAL_INVALID')
        previous=item['sha256']
    return True


class Analyst(Protocol):
    identity:dict
    def infer(self,request:dict)->dict:...


class MockAnalyst:
    identity={'provider':'deterministic-fixture','model':'mock-objection-v1','kind':'MOCK'}
    def infer(self,request):
        symbol=request['symbol']
        return {'version':'analyst-v1','hypothesis':'MOCK: unchanged fixture reversal conditions merit research review.',
                'evidence_refs':[request['evidence_id']],
                'strongest_objection':'Synthetic candles establish no real-world predictive performance.',
                'missing_information':[],
                'invalidation':'A later eligible low below the retest anchor invalidates this research condition.',
                'disposition':'REJECT' if symbol=='SOL/USD' else 'SUPPORT'}


def analyst_result(value,evidence_id):
    bounded(value,4096)
    exact(value,('version','hypothesis','evidence_refs','strongest_objection','missing_information','invalidation','disposition'))
    require(value['version']=='analyst-v1' and value['disposition'] in ('SUPPORT','REJECT','ABSTAIN'),'ANALYST_SCHEMA_INVALID')
    for key in ('hypothesis','strongest_objection','invalidation'):
        require(type(value[key]) is str and 0<len(value[key].strip())<=600,'ANALYST_SCHEMA_INVALID')
    require(type(value['evidence_refs']) is list and value['evidence_refs']==[evidence_id],'ANALYST_REFERENCE_INVALID')
    require(type(value['missing_information']) is list and len(value['missing_information'])<=8
            and all(type(s) is str and 0<len(s)<=200 for s in value['missing_information']),'ANALYST_SCHEMA_INVALID')
    return json.loads(canonical(value))


def normalize(lead,as_of):
    exact(lead,('source','symbol','observed_at','available_at','text','payload'))
    source=lead['source'];exact(source,('id','kind','origin'))
    require(type(source['id']) is str and re.fullmatch('[a-zA-Z0-9_-]{1,40}',source['id']),'SOURCE_INVALID')
    require(source['kind']=='SYNTHETIC_ONLY' and source['origin']=='ORIGINAL_032','PROVENANCE_MISSING')
    require(lead['symbol'] in registry.SYMBOLS,'MARKET_MISMATCH')
    require(integer(lead['observed_at']) and integer(lead['available_at']) and lead['available_at']>=lead['observed_at'],'TIMESTAMP_INVALID')
    if lead['available_at']>as_of:return None
    require(type(lead['text']) is str and len(lead['text'])<=1000,'TEXT_INVALID')
    require(as_of-lead['observed_at']<=3*registry.HOUR,'EVIDENCE_STALE')
    value=json.loads(canonical(lead));value['source']['id']=value['source']['id'].lower()
    payload=value['payload']
    require(type(payload) is dict and type(payload.get('bars')) is list,'EVIDENCE_MISSING')
    # Project before hashing or inference: later rows can never enter a card or receipt.
    cutoff=min(as_of,value['observed_at'])
    require(len(payload['bars'])<=registry.MAX_BARS,'SIZE_LIMIT')
    for b in payload['bars']:
        require(type(b) is dict and type(b.get('open_time')) is int,'TIMESTAMP_INVALID')
    payload['bars']=[b for b in payload['bars'] if b['open_time']+registry.HOUR<=cutoff]
    return value


def run(envelope,adapter=None,timer=time.perf_counter_ns):
    """Trusted adapter injection only; never execute external text or load plugins."""
    bounded(envelope)
    exact(envelope,('version','as_of','leads'))
    require(envelope['version']==VERSION and integer(envelope['as_of']) and envelope['as_of']%registry.HOUR==0,'CONTEXT_INVALID')
    require(type(envelope['leads']) is list and len(envelope['leads'])<=MAX_LEADS,'LEAD_LIMIT')
    as_of=envelope['as_of'];adapter=MockAnalyst() if adapter is None else adapter
    identity=json.loads(canonical(adapter.identity))
    exact(identity,('provider','model','kind'))
    require(identity['kind']=='MOCK' and all(type(identity[k]) is str and 0<len(identity[k])<=80 for k in identity),'ADAPTER_NOT_SUPPORTED')
    journal=EvidenceJournal();cards=[];groups={};deferred=0
    def record(status,reason,evidence=None,analysis=None,row=None,elapsed=0):
        item={'as_of':as_of,'mode':'SYNTHETIC_ONLY','status':status,'reason_codes':[reason],
              'policy':POLICY,'adapter':identity,'evidence':evidence,'analysis':analysis,'rule_result':row,
              'verification':{'provenance':'SYNTHETIC_DECLARATION_NOT_AUTHENTICATED',
                  'age_seconds':as_of-evidence['observed_at'] if evidence and integer(evidence.get('observed_at')) else None,
                  'missing_fields':['payload'] if reason=='EVIDENCE_MISSING' else [],
                  'critical_gaps':status=='BLOCKED'},
              'timing':{'elapsed_ns':elapsed,'kind':'MEASURED_LOCAL_MONOTONIC' if analysis is not None or reason in ('PROVIDER_UNAVAILABLE','ANALYST_INVALID') else 'NOT_RUN'},
              'cost':{'currency':'NTD','amount':'0','external_calls':0,'tokens':'NOT_APPLICABLE_MOCK'},
              'buy_authorization':'NONE','paper_fill':'NOT_CREATED'}
        receipt=journal.append(item)
        cards.append({'symbol':evidence['symbol'] if evidence else None,'decision':status,'reason':reason,
                      'evidence_id':digest(evidence) if evidence else None,'hypothesis':analysis['hypothesis'] if analysis else None,
                      'strongest_objection':analysis['strongest_objection'] if analysis else None,
                      'invalidation':analysis['invalidation'] if analysis else None,'snapshot_sha256':receipt.sha256,
                      'score':row['score'] if row else None, 'adapter':identity,
                      'missing_information':analysis['missing_information'] if analysis else (['payload'] if reason=='EVIDENCE_MISSING' else []),
                      'evidence_refs':analysis['evidence_refs'] if analysis else [],'buy_authorization':'NONE'})
    for lead in envelope['leads']:
        try:value=normalize(lead,as_of)
        except (ValueError,TypeError,KeyError,OverflowError,RecursionError) as exc:
            reason=str(exc) if str(exc) in ('PROVENANCE_MISSING','MARKET_MISMATCH','TIMESTAMP_INVALID','EVIDENCE_STALE','EVIDENCE_MISSING','SIZE_LIMIT','SOURCE_INVALID','TEXT_INVALID','SCHEMA_INVALID') else 'EVIDENCE_INVALID'
            context={'symbol':lead.get('symbol') if type(lead) is dict and lead.get('symbol') in registry.SYMBOLS else None,
                     'observed_at':lead.get('observed_at') if type(lead) is dict and integer(lead.get('observed_at')) else None,
                     'input_sha256':digest(lead),'provenance':'REFUSED_UNTRUSTED_INPUT'}
            record('BLOCKED',reason,context);continue
        if value is None:deferred+=1;continue
        key=(value['source']['id'],value['symbol'],value['observed_at'])
        groups.setdefault(key,[]).append(value)
    selected=[]
    for key,values in sorted(groups.items()):
        distinct={canonical(v) for v in values}
        if len(distinct)>1:
            record('BLOCKED','DUPLICATE_CONFLICT');continue
        value=values[0]
        # Exact repeats produce one inference/card, with a source dedup receipt.
        if len(values)>1:journal.append({'event':'DUPLICATE_LEAD','count':len(values)-1,'evidence_id':digest(value),'as_of':as_of})
        symbol=value['symbol']
        report=candidates.evaluate({'version':candidates.VERSION,'label':candidates.LABEL,'as_of':as_of,
            'policy':{'version':registry.VERSION,'future_mode':'reject'},'payloads':{symbol:value['payload']}})
        row=report['symbols'][symbol]
        if row['decision']=='BLOCKED':
            record('BLOCKED',row['validation']['reason_code'] or 'RULE_REFUSAL',value,row=row);continue
        evidence_id=digest(value)
        request={'version':'analyst-request-v1','symbol':symbol,'as_of':as_of,'evidence_id':evidence_id,
                 'evidence':value,'rules':row,'untrusted_text_policy':'DATA_ONLY_NOT_INSTRUCTIONS'}
        started=timer()
        try:
            response=adapter.infer(json.loads(canonical(request)))
        except Exception:
            record('BLOCKED','PROVIDER_UNAVAILABLE',value,row=row,elapsed=max(0,timer()-started));continue
        try:analysis=analyst_result(response,evidence_id)
        except (ValueError,TypeError,KeyError,OverflowError,RecursionError):
            record('BLOCKED','ANALYST_INVALID',value,row=row,elapsed=max(0,timer()-started));continue
        elapsed=max(0,timer()-started)
        if analysis['missing_information'] or analysis['disposition']=='ABSTAIN':record('BLOCKED','ANALYST_GAP',value,analysis,row,elapsed)
        elif row['decision']!='WATCH':record('WAIT','RISK_RULE_VETO',value,analysis,row,elapsed)
        elif analysis['disposition']=='REJECT':record('WAIT','ANALYST_REJECTED',value,analysis,row,elapsed)
        else:selected.append((value,analysis,row,elapsed))
    admitted=set()
    for value,analysis,row,elapsed in sorted(selected,key=lambda x:(-x[2]['score'],x[0]['symbol'],digest(x[0]))):
        if value['symbol'] in admitted or len(admitted)>=3:record('WAIT','CANDIDATE_CAP',value,analysis,row,elapsed)
        else:
            admitted.add(value['symbol']);record('WATCH','SYNTHETIC_RESEARCH_ACCEPTED',value,analysis,row,elapsed)
    return {'version':VERSION,'baseline':BASELINE,'mode':'SYNTHETIC_ONLY','analyst':'MOCK_NOT_GENUINE_AI',
            'as_of':as_of,'cards':cards,'candidate_count':len(admitted),'deferred_leads':deferred,
            'journal':[{'sha256':s.sha256,'snapshot':s.data()} for s in journal.snapshots],
            'buy_authorization':'NONE','gates':{'B1':'HOLD','B2':'HOLD','B3':'HOLD','B4':'NO-GO','B5':'HOLD'},
            'additional_expenditure_ntd':'0','external_calls':0}


def demo():
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'tests/fixtures/decision_loop_032.json'
    with path.open('rb') as f:fixture=parse(f.read(MAX_BYTES+1).decode('utf-8'))
    return run(fixture)


def render_cards(result):
    lines=['BOSS TRADER — SYNTHETIC / MOCK RESEARCH ONLY',
           'Not genuine AI inference. BUY AUTHORIZATION NONE. No fills or orders.']
    for card in result['cards']:
        lines.extend(['',str(card['symbol'] or 'Unidentified lead')+' | '+card['decision']+' | '+card['reason']])
        for key in ('hypothesis','strongest_objection','missing_information','invalidation','evidence_refs'):
            lines.append(key+': '+json.dumps(card[key],ensure_ascii=True))
        lines.append('Evidence snapshot: '+card['snapshot_sha256'])
    return '\n'.join(lines)+'\n'


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--demo',action='store_true')
    parser.add_argument('--cards',action='store_true',help='Print readable research cards instead of JSON')
    parser.add_argument('--output',help='Create a new JSON evidence archive; refuses overwrite')
    args=parser.parse_args()
    if not args.demo:
        parser.exit(0,'Offline idle. Use --demo for invented fixtures and explicitly MOCK analysis.\n')
    result=demo();text=json.dumps(result,indent=2,ensure_ascii=True,allow_nan=False)+'\n'
    if args.output:
        with open(args.output,'x',encoding='utf-8') as target:target.write(text)
    print(render_cards(result) if args.cards else text,end='')


if __name__=='__main__':main()
