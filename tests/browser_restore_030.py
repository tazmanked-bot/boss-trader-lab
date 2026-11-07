"""One opt-in native browser attempt. No fallback, installation or policy overrides."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parent.parent
HTML=ROOT/'docs/artifacts/boss-trader-demo-029.html'
OUT=ROOT/'docs/artifacts/restore-030-browser-evidence.json'
KEY='boss-trader-demo-paper-v1'


def run():
    from playwright.sync_api import sync_playwright
    result={'status':'BLOCKED','stage':'browser_launch','launch_attempts':1,
            'html_sha256':hashlib.sha256(HTML.read_bytes()).hexdigest(),
            'scope':'NATIVE_FILE_ORIGIN_NO_STORAGE_REPLACEMENT',
            'checks':[],'screenshots':'NOT_CAPTURED','native_persistence':'UNVERIFIED'}
    def check(name,value):
        assert value,name
        result['checks'].append(name)
    try:
        with tempfile.TemporaryDirectory(prefix='boss-restore-030-') as profile, sync_playwright() as p:
            context=p.chromium.launch_persistent_context(profile,executable_path='/usr/bin/chromium',
                chromium_sandbox=True,headless=True,timeout=8000,accept_downloads=True,
                viewport={'width':1440,'height':1000})
            context.route('**/*',lambda r:r.continue_() if r.request.url.startswith('file:') else r.abort())
            page=context.pages[0];page.set_default_timeout(5000)
            result['stage']='file_navigation'
            page.goto(HTML.as_uri(),wait_until='domcontentloaded',timeout=8000)
            result['stage']='export_preview_cancel_confirm'
            snapshot=lambda:page.evaluate(f'localStorage.getItem("{KEY}")')
            page.locator('[data-watch="BTC/USD"]').click()
            form=page.locator('#entry-form')
            for name,value in {'price':'100','size':'2','fee':'1','slip':'0.5','note':'<img src=x onerror=alert(1)>'}.items():
                form.locator(f'[name={name}]').fill(value)
            form.locator('[type=submit]').click()
            entry=json.loads(snapshot())['records'][0]
            page.locator('#exit-tab').click();form=page.locator('#exit-form')
            form.locator('[name=entryId]').select_option(entry['id'])
            for name,value in {'price':'110','qty':'1','fee':'0.5','slip':'0.25'}.items():form.locator(f'[name={name}]').fill(value)
            form.locator('[type=submit]').click()
            with page.expect_download() as export:page.locator('#export').click()
            backup=Path(export.value.path()).read_bytes()
            page.locator('#clear').click();page.locator('#confirm-clear').click()
            before=snapshot()
            def preview():
                with page.expect_file_chooser() as chooser:page.locator('#restore').click()
                chooser.value.set_files({'name':'invented-demo.json','mimeType':'application/json','buffer':backup})
                page.locator('#restore-dialog').wait_for(state='visible')
            preview()
            check('preview includes exact partial accounting','$8.50 USD' in page.locator('#restore-preview').inner_text())
            check('preview does not mutate saved journal',snapshot()==before)
            page.locator('#cancel-restore').click()
            check('cancel preserves exact storage bytes',snapshot()==before)
            preview();page.locator('#confirm-restore').click()
            check('restore equals exported journal',json.loads(snapshot())==json.loads(backup))
            check('malicious note is literal text',page.locator('#ledger img').count()==0 and '<img' in page.locator('#ledger').inner_text())
            check('partial accounting restored',page.locator('#gross').inner_text()=='$10.00 USD' and page.locator('#net').inner_text()=='$8.50 USD')
            page.locator('#exit-tab').click();form=page.locator('#exit-form')
            form.locator('[name=entryId]').select_option(entry['id'])
            for name,value in {'price':'110','qty':'1','fee':'0.5','slip':'0.25'}.items():form.locator(f'[name={name}]').fill(value)
            form.locator('[type=submit]').click()
            check('remaining close conserves entry costs',page.locator('#gross').inner_text()=='$20.00 USD' and page.locator('#net').inner_text()=='$17.00 USD' and page.locator('#open-count').inner_text()=='0')
            page.screenshot(path=str(ROOT/'docs/artifacts/restore-030-desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            check('phone no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'docs/artifacts/restore-030-phone.png'),full_page=True)
            result.update(status='PASS',stage='complete',screenshots='ACTUAL_NATIVE_BROWSER',native_persistence='RELOAD_AND_RESTART_NOT_TESTED')
            context.close()
    except Exception as exc:
        lines=str(exc).splitlines()
        result['blocker']={'type':type(exc).__name__,'message':lines[0][:500],
            'details':[l.strip()[:500] for l in lines if 'Operation not permitted' in l or 'ERR_BLOCKED_BY_ADMINISTRATOR' in l][:2]}
    OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    if not parser.parse_args().run:parser.exit(2,'Disabled; --run only where browser execution is already permitted.\n')
    raise SystemExit(run())
