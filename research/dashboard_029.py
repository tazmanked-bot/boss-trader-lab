"""Generate one self-contained offline demo dashboard using unchanged 024 output."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from research import manual_kraken_reversal_024 as manual

SOURCE_REVISION='457531a92df4112957d3c3744c081a15f16858ed'
ASSETS=Path(__file__).with_suffix('')


def view_model(report,*,generated_at):
    """Presentation boundary, not a data admission or scanner implementation."""
    source=manual.operator_report(report)
    if source['source']!=manual.SOURCE or source['requests']!=0:
        raise ValueError('Only the existing static synthetic report is supported')
    rows={}
    for symbol,row in source['pairs'].items():
        price=row['fixture_only_closed_price_usd']
        if type(price) not in (int,float) or not math.isfinite(price) or price<=0:price=None
        rows[symbol]={**row,'fixture_only_closed_price_usd':price}
    as_of=source['capture']['as_of'] if source['capture'] else None
    seed={'revision':SOURCE_REVISION,'fixture':manual.DEMO_SHA256,
          'evidence':report.get('decision_evidence_ref'),'rows':rows,'as_of':as_of}
    session=hashlib.sha256(json.dumps(seed,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return {'version':1,'mode':'DEMO_ONLY','id':session,'source':source['source'],
            'source_revision':SOURCE_REVISION,'fixture_sha256':manual.DEMO_SHA256,
            'as_of':as_of,'as_of_text':datetime.fromtimestamp(as_of,timezone.utc).isoformat() if as_of else 'Unavailable',
            'generated_at':generated_at,'rows':rows,'candidates':source['candidates'],
            'reason':source['reason'],'live_source_admission':'HOLD','B4':'NO-GO','policy':'NO ORDERS'}


def render(model):
    # Escape JSON script boundaries, including hostile strings in presentation tests.
    payload=json.dumps(model,sort_keys=True,ensure_ascii=True,allow_nan=False)
    payload=payload.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    template=(ASSETS/'screen.html').read_text(encoding='utf-8')
    for token,value in (('__MODEL__',payload),('__ENGINE__',(ASSETS/'paper.js').read_text()),
                        ('__APP__',(ASSETS/'app.js').read_text())):
        if template.count(token)!=1:raise ValueError('Invalid dashboard template')
        template=template.replace(token,value)
    if len(template.encode())>512*1024:raise ValueError('Dashboard too large')
    return template


def generate(*,generated_at=None):
    # System clock labels file-generation time only; never trusted UTC evidence.
    generated_at=generated_at or datetime.now(timezone.utc).isoformat()
    return render(view_model(manual.offline_demo(),generated_at=generated_at))


def main():
    parser=argparse.ArgumentParser(description='Generate a local synthetic BOSS Trader dashboard; no network')
    parser.add_argument('--output',default='boss-trader-demo.html')
    args=parser.parse_args()
    target=Path(args.output)
    target.write_text(generate(),encoding='utf-8')
    print(f'Wrote {target} — DEMO / SYNTHETIC DATA; open locally; NO REAL ORDERS')


if __name__=='__main__':main()
