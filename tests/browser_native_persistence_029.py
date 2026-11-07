"""Opt-in native file-origin acceptance, using installed Playwright/Chromium.

One launch attempt, browser sandbox enabled, no policy overrides, escalation,
server, storage replacement or fallback. Failure is a recorded limitation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parent.parent
HTML=ROOT/'docs/artifacts/boss-trader-demo-029.html'
EVIDENCE=ROOT/'docs/artifacts/dashboard-029-native-persistence.json'
KEY='boss-trader-demo-paper-v1'


def run():
    from playwright.sync_api import sync_playwright
    evidence={'scope':'NATIVE_FILE_ORIGIN','storage':'NATIVE_LOCALSTORAGE_NO_REPLACEMENT',
              'html_sha256':hashlib.sha256(HTML.read_bytes()).hexdigest(),
              'launch_attempts':0,'reload':'NOT_TESTED','tab_reopen':'NOT_TESTED',
              'browser_restart':'NOT_TESTED','checks':[], 'external_document_requests':[],
              'screenshots':'NOT_CAPTURED','status':'BLOCKED','stage':'browser_launch'}
    def check(name,value):
        assert value,name
        evidence['checks'].append(name)
    def snapshot(page):return page.evaluate(f'JSON.parse(localStorage.getItem("{KEY}"))')
    context=None
    try:
        with tempfile.TemporaryDirectory(prefix='boss-029-native-') as profile, sync_playwright() as p:
            evidence['launch_attempts']=1
            context=p.chromium.launch_persistent_context(profile,executable_path='/usr/bin/chromium',
                headless=True,chromium_sandbox=True,timeout=8000,accept_downloads=True,
                viewport={'width':1440,'height':1000})
            def route(request):
                if request.request.url.startswith('file:'):request.continue_()
                else:evidence['external_document_requests'].append(request.request.url);request.abort()
            context.route('**/*',route)
            page=context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(5000)
            evidence['stage']='file_navigation'
            page.goto(HTML.as_uri(),wait_until='domcontentloaded',timeout=8000)
            evidence['stage']='native_journal_checks'
            check('native storage initially empty',len(snapshot(page)['records'])==0)
            page.locator('[data-watch="BTC/USD"]').click()
            form=page.locator('#entry-form')
            for name,value in {'price':'100','size':'2','fee':'1','slip':'0.5','note':'Invented native persistence review'}.items():
                form.locator(f'[name={name}]').fill(value)
            form.locator('[type=submit]').click()
            saved=snapshot(page);entry=saved['records'][0];session=entry['session']
            check('native entry saved with exact amounts',entry['price']=='100' and entry['qty']=='2' and entry['fee']=='1' and entry['slip']=='0.5')
            page.reload(wait_until='domcontentloaded',timeout=8000)
            check('native reload preserves complete state',snapshot(page)==saved)
            evidence['reload']='PASS'
            page.close();page=context.new_page();page.set_default_timeout(5000)
            page.goto(HTML.as_uri(),wait_until='domcontentloaded',timeout=8000)
            check('same profile/path tab reopen preserves state',snapshot(page)==saved)
            evidence['tab_reopen']='PASS'
            check('one watch/session/entry without duplication',len(saved['watch'])==len(saved['sessions'])==len(saved['records'])==1)
            page.locator('#exit-tab').click()
            for index in range(2):
                form=page.locator('#exit-form');form.locator('[name=entryId]').select_option(entry['id'])
                for name,value in {'price':'110','qty':'1','fee':'0.5','slip':'0.25','note':'Invented partial paper close'}.items():
                    form.locator(f'[name={name}]').fill(value)
                form.locator('[type=submit]').click()
                current=snapshot(page)
                check('exit source identity '+str(index+1),current['records'][-1]['session']==session)
                if index==0:
                    check('partial close conserves entry costs',page.locator('#gross').inner_text()=='$10.00 USD' and page.locator('#net').inner_text()=='$8.50 USD' and page.locator('#open-count').inner_text()=='1')
                    page.reload(wait_until='domcontentloaded',timeout=8000)
                    check('partial exit survives native reload',snapshot(page)==current)
                    page.locator('#exit-tab').click()
            check('final gross/net and closed quantity',page.locator('#gross').inner_text()=='$20.00 USD' and page.locator('#net').inner_text()=='$17.00 USD' and page.locator('#open-count').inner_text()=='0')
            with page.expect_download(timeout=5000) as download:page.locator('#export').click()
            exported=json.loads(Path(download.value.path()).read_text())
            check('export matches native saved records',exported==snapshot(page) and len(exported['records'])==3)
            evidence['stage']='fresh_screenshots'
            page.screenshot(path=str(ROOT/'docs/artifacts/dashboard-029-followup-desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            check('390px no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'docs/artifacts/dashboard-029-followup-phone.png'),full_page=True)
            evidence['screenshots']='FRESH_NATIVE_RUN'
            check('no external document requests',not evidence['external_document_requests'])
            evidence.update(status='PASS',stage='complete')
            context.close();context=None
    except Exception as exc:
        lines=str(exc).splitlines()
        relevant=[line.strip() for line in lines if any(token in line for token in (
            'Operation not permitted','ERR_BLOCKED_BY_ADMINISTRATOR','Timeout','No usable sandbox','Failed to move to new namespace'))]
        evidence['blocker']={'type':type(exc).__name__,'message':lines[0][:500] if lines else 'Unknown browser failure',
                             'details':[line[:500] for line in relevant[:3]]}
    finally:
        if context is not None:
            try:context.close()
            except Exception:pass
    EVIDENCE.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['status']=='PASS' else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true',help='One native browser attempt in the existing permitted environment')
    if not parser.parse_args().run:
        print('Disabled. Use --run only where native browser testing is already permitted.');return 2
    return run()


if __name__=='__main__':raise SystemExit(main())
