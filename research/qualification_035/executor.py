"""Disabled real executor architecture; ONLY the pinned synthetic worker can run."""
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
from . import containment,process
from .provision import need
from research import target_validation_034 as target,llama_analyst_033 as adapter,decision_loop_032 as loop


def plan(manifest,request,bundle_receipt=None):
    prepared=adapter.prepare(manifest,request);profile=target.first_inference_plan(manifest,request)
    binding={'artifact_manifest_sha256':prepared.manifest_sha256,'artifact_pins_sha256':loop.digest(json.loads(prepared.provenance_json)),
             'prompt_sha256':prepared.prompt_sha256,'schema_sha256':hashlib.sha256(prepared.schema_json.encode()).hexdigest(),
             'target_scope_sha256':profile['scope_sha256'],'worker_sha256':containment.WORKER_SHA,'evidence_id':request['evidence_id'],
             'bundle_receipt_sha256':loop.digest(bundle_receipt) if bundle_receipt else None,
             'bundle_inventory_sha256':loop.digest({'files':bundle_receipt['files'],'links':bundle_receipt['links'],'elf':bundle_receipt['elf_dependencies']}) if bundle_receipt else None}
    return {'version':'disabled-executor-v1','state':'REAL_NOT_RUN','binding':binding,'profile':profile,
            'real_launch':'TECHNICALLY_DISABLED_REQUIRES_SUBSEQUENT_REVIEWED_CODE_CHANGE'}


def shortest_response(reference):
    value={'version':'analyst-v1','hypothesis':'x','evidence_refs':[reference],'strongest_objection':'x',
           'missing_information':[],'invalidation':'x','disposition':'REJECT'}
    loop.analyst_result(value,reference)
    raw=loop.canonical(value).encode('ascii')
    typical={**value,'hypothesis':'Synthetic conditions merit research review.',
             'strongest_objection':'No real predictive evidence or model quality is established.',
             'invalidation':'A subsequent eligible low breaches the observed retest anchor.'}
    return {'minimum_schema_valid_bytes':len(raw),'minimum_byte_div_four_estimate':math.ceil(len(raw)/4),
            'typical_synthetic_bytes':len(loop.canonical(typical)),'typical_byte_div_four_estimate':math.ceil(len(loop.canonical(typical))/4),
            'actual_tokenizer_count':None,'estimate_is_token_measurement':False,'max_generated_tokens':64,
            'likely_truncation_risk':True,'minimum_response_reasoning_quality':'SEMANTICALLY_USELESS_NOT_AI_EVIDENCE',
            'policy':'STRICT_REJECT_TRUNCATION_NO_CAP_INCREASE_NO_REMOVED_FIELDS'}


class DisabledExecutor:
    def __init__(self,prepared_plan,qualification):
        self.plan=json.loads(loop.canonical(prepared_plan));self.qualification=json.loads(loop.canonical(qualification))
    def infer(self,*args,**kwargs):
        raise adapter.Refused('REAL_NOT_RUN_NO_ACTIVATION_PATH')
    def stub(self,reference,scenario='normal',*,timeout=30):
        receipt=dict(self.qualification);pin=receipt.pop('receipt_sha256',None)
        need(pin==loop.digest(receipt),'QUALIFICATION_RECEIPT_CORRUPT')
        need(receipt.get('request_binding')==self.plan['binding'],'QUALIFICATION_BINDING_MISMATCH')
        mode=receipt.get('mode')
        need(mode=='SYNTHETIC_TEST_INJECTED_NOT_TARGET_QUALIFIED' or mode=='ACTUAL_LOCAL_SYNTHETIC_PROFILE_ONLY' and receipt.get('qualified') is True,'QUALIFICATION_HOLD')
        need(self.plan['state']=='REAL_NOT_RUN' and self.plan['binding']['worker_sha256']==containment.WORKER_SHA,'EXECUTOR_PLAN_INVALID')
        need(scenario in ('normal','hang','tree','nonzero','overflow','badref','extra'),'STUB_SCENARIO')
        need(reference==self.plan['binding']['evidence_id'],'EVIDENCE_BINDING_MISMATCH')
        if mode=='ACTUAL_LOCAL_SYNTHETIC_PROFILE_ONLY':
            # Return only the analysis ALREADY measured inside the qualified child.
            # Never dispatch a later unenclosed process based on a receipt.
            value=loop.analyst_result(receipt['analysis'],reference)
            return {'mode':'QUALIFIED_SYNTHETIC_CHILD_NOT_AI','state':'REAL_NOT_RUN','analysis':value,
                    'process':receipt['process'],'binding':self.plan['binding'],'real_inference_count':0,
                    'model_tokens':None,'buy_authorization':'NONE'}
        worker=containment.pinned_worker()
        with tempfile.TemporaryDirectory(prefix='boss-035-stub-') as tmp:
            raw,metadata=process.run([sys.executable,'-I','-S','-B',worker,scenario,reference],env=containment.environment(tmp),cwd=tmp,timeout=timeout)
        value=target.validate_first_output(raw,reference)
        return {'mode':'PINNED_SYNTHETIC_STUB_NOT_AI','state':'REAL_NOT_RUN','analysis':value,'process':metadata,
                'binding':self.plan['binding'],'qualification_mode':mode,'real_inference_count':0,
                'model_tokens':None,'token_ceiling_exercised_by_model':False,'buy_authorization':'NONE'}


def synthetic_receipt(binding):
    value={'mode':'SYNTHETIC_TEST_INJECTED_NOT_TARGET_QUALIFIED','qualified':False,'request_binding':binding,'state':'REAL_NOT_RUN'}
    return {**value,'receipt_sha256':loop.digest(value)}
