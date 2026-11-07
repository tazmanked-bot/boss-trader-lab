"""Single permitted Chromium attempt; local HTTP E2E with invented provider fixtures."""
import hashlib
import json
from pathlib import Path
import tempfile
import threading
from http.server import ThreadingHTTPServer

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/artifacts/market-031-browser-evidence.json'


def run():
    from playwright.sync_api import sync_playwright
    from research.dashboard_029 import generate
    from research.market_observation_031 import handler,Service,parse
    from tests.test_market_observation_031 import raw,NOW
    result={'status':'BLOCKED','stage':'browser_launch','launch_attempts':1,
            'data':'INVENTED_BINANCE_SHAPED_FIXTURES_NOT_AUTHENTIC_MARKET_DATA',
            'checks':[],'screenshots':[],'live_fetch':'UNVERIFIED','native_persistence':'UNVERIFIED'}
    server=None
    def check(name,value):
        assert value,name
        result['checks'].append(name)
    try:
        with tempfile.TemporaryDirectory(prefix='boss-market-031-') as profile,sync_playwright() as p:
            context=p.chromium.launch_persistent_context(profile,executable_path='/usr/bin/chromium',
                chromium_sandbox=True,headless=True,timeout=8000,viewport={'width':1440,'height':1000})
            result['stage']='local_fixture_server'
            release=threading.Event();calls=[];clock=[100];failure=[False]
            def fetch():
                calls.append(1)
                if failure[0]:raise ValueError('Fixture provider HTTP 429; no retry')
                if not release.wait(5):raise ValueError('Fixture release timed out')
                return parse(raw(),NOW)
            html=generate().replace('<body>','<body><p style="padding:10px;background:#fff2d9">BROWSER TEST: INVENTED PROVIDER FIXTURES — NOT AUTHENTIC MARKET DATA</p>')
            result['html_sha256']=hashlib.sha256(html.encode()).hexdigest()
            server=ThreadingHTTPServer(('127.0.0.1',0),handler(html,Service(fetch,lambda:clock[0])))
            threading.Thread(target=server.serve_forever,daemon=True).start()
            page=context.pages[0];page.set_default_timeout(6000)
            page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:'+str(server.server_port)+'/') else r.abort())
            result['stage']='manual_refresh_e2e'
            page.goto('http://127.0.0.1:'+str(server.server_port)+'/',timeout=8000)
            check('page load no provider call',not calls)
            page.locator('#show-market').click();check('view switch no provider call',not calls)
            def capture(name):
                target='market-031-'+name+'.png';page.screenshot(path=str(ROOT/'docs/artifacts'/target),full_page=True);result['screenshots'].append(target)
            page.locator('#market-refresh').click()
            page.wait_for_function("document.getElementById('market-refresh').disabled")
            capture('desktop-loading');release.set()
            page.wait_for_function("document.getElementById('market-status').textContent.startsWith('OBSERVE_ONLY')")
            check('manual refresh one fixture call',len(calls)==1)
            check('exact USDT identity','BTC/USDT spot · quote USDT' in page.locator('#market-values').inner_text())
            check('demo hidden and market no paper entry',not page.locator('#entry-form').is_visible())
            capture('desktop-valid');page.set_viewport_size({'width':390,'height':844})
            check('390px no overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            capture('phone-valid')
            clock[0]=131;failure[0]=True;page.locator('#market-refresh').click()
            page.wait_for_function("document.getElementById('market-error').textContent.startsWith('STALE')")
            check('refusal preserves last success','101 USDT' in page.locator('#market-values').inner_text())
            capture('phone-refusal-stale');page.set_viewport_size({'width':1440,'height':1000});capture('desktop-refusal-stale')
            page.locator('#show-demo').click();check('demo restoration remains present',page.locator('#restore').is_visible())
            check('no extra provider calls',len(calls)==2)
            result.update(status='PASS',stage='complete')
            context.close()
    except Exception as exc:
        lines=str(exc).splitlines();result['blocker']={'type':type(exc).__name__,'message':lines[0][:500],
            'details':[s.strip()[:500] for s in lines if 'Operation not permitted' in s or 'ERR_BLOCKED_BY_ADMINISTRATOR' in s][:2]}
    finally:
        if server is not None:server.shutdown();server.server_close()
    OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    if not parser.parse_args().run:parser.exit(2,'Disabled; --run only in an already permitted browser environment.\n')
    raise SystemExit(run())
