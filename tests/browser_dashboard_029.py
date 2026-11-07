"""Optional Playwright review with installed Chromium; no downloads or server.

The exact generated document is rendered in about:blank because managed
Chromium blocks file/loopback navigation. Persistence uses an explicit storage
test double; native file-origin persistence remains unverified.
Runtime dashboard still opens as one local HTML file in ordinary browsers.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/'docs/artifacts/boss-trader-demo-029.html').read_text()
URL='http://127.0.0.1:8765/demo'
KEY='boss-trader-demo-paper-v1'
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
    print('PASS '+name,flush=True)


def main():
    errors=[];external=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,timeout=15000,
            args=['--disable-background-networking','--disable-crashpad-for-testing','--host-resolver-rules=MAP * ~NOTFOUND'])
        context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        def route(request):
            if request.request.url==URL:request.fulfill(status=200,content_type='text/html',body=HTML)
            else:external.append(request.request.url);request.abort()
        context.route('**/*',route)
        def render_page(saved=None):
            page=context.new_page();page.set_default_timeout(8000)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.evaluate('''saved=>{window.__storageFixture=saved;Object.defineProperty(window,'localStorage',{value:{getItem(k){return Object.hasOwn(window.__storageFixture,k)?window.__storageFixture[k]:null},setItem(k,v){window.__storageFixture[k]=String(v)}}})}''',saved or {})
            page.set_content(HTML,wait_until='domcontentloaded',timeout=12000)
            return page
        def rehydrate(page):
            saved=page.evaluate('window.__storageFixture');page.close();return render_page(saved)
        page=render_page()
        check('three actual fixture WATCH cards',page.locator('#cards .card').count()==3 and page.locator('#candidate-count').inner_text()=='3')
        check('desktop no horizontal scroll',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('source and fixture labels visible',page.get_by_text('DEMO / SYNTHETIC DATA',exact=True).is_visible() and '2030-' in page.locator('#asof').inner_text())
        page.locator('[data-watch="BTC/USD"]').click()
        check('watch stores conditions and session',page.locator('#watch-list .watch-item').count()==1 and 'Demo source session' in page.locator('#watch-list').inner_text())
        form=page.locator('#entry-form')
        for name,value in {'price':'100','size':'2','fee':'1','slip':'0.5','note':'Synthetic walkthrough • hypothetical entry'}.items():form.locator(f'[name={name}]').fill(value)
        form.locator('[type=submit]').dblclick()
        check('double submission creates one entry',page.locator('#record-count').inner_text()=='1')
        check('open position has no invented mark',page.locator('#open-count').inner_text()=='1' and 'Unrealized P&L: unavailable' in page.locator('#open-positions').inner_text())
        page.locator('#exit-tab').click();exit_form=page.locator('#exit-form')
        entry_id=page.evaluate(f'JSON.parse(localStorage.getItem("{KEY}")).records[0].id')
        exit_form.locator('[name=entryId]').select_option(entry_id)
        for name,value in {'price':'110','qty':'3','fee':'1','slip':'0.5'}.items():exit_form.locator(f'[name={name}]').fill(value)
        exit_form.locator('[type=submit]').click()
        check('oversell blocked visibly',page.locator('#record-count').inner_text()=='1' and 'exceeds available' in page.locator('#feedback').inner_text())
        exit_form.locator('[name=qty]').fill('2');exit_form.locator('[name=note]').fill('Synthetic walkthrough • hypothetical close')
        exit_form.locator('[type=submit]').click()
        check('correct gross and net P&L',page.locator('#gross').inner_text()=='$20.00 USD' and page.locator('#net').inner_text()=='$17.00 USD')
        check('exit closes selected paper lot',page.locator('#open-count').inner_text()=='0' and page.locator('#record-count').inner_text()=='2')
        page=rehydrate(page);page.locator('#load-demo').click()
        check('controlled storage rehydration preserves records without duplicate session',page.locator('#record-count').inner_text()=='2' and page.locator('#watch-list .watch-item').count()==1 and page.evaluate(f'JSON.parse(localStorage.getItem("{KEY}")).sessions.length')==1)
        page.screenshot(path=str(ROOT/'docs/artifacts/dashboard-029-desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)')
        check('390px no horizontal scroll',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('touch buttons at least 44px',page.locator('button:visible').evaluate_all('(els)=>els.every(e=>e.getBoundingClientRect().height>=44)'))
        page.screenshot(path=str(ROOT/'docs/artifacts/dashboard-029-phone.png'),full_page=True)
        page.locator('#view-mode').select_option('empty')
        check('honest WAIT and zero-candidate view',page.locator('#candidate-count').inner_text()=='0' and page.locator('#empty-scan').inner_text()=='No qualifying setup.' and page.locator('#cards .tag.WAIT').count()==3)
        check('presentation state labeled and entry paused',page.locator('#test-notice').is_visible() and page.locator('#entry-form [type=submit]').is_disabled())
        page.screenshot(path=str(ROOT/'docs/artifacts/dashboard-029-empty.png'),full_page=True)
        page.locator('#view-mode').select_option('blocked')
        check('honest BLOCKED view without price',page.locator('#cards .tag.BLOCKED').count()==3 and page.locator('#cards .ref').first.inner_text()=='Unavailable')
        page.screenshot(path=str(ROOT/'docs/artifacts/dashboard-029-blocked.png'),full_page=True)
        page.locator('#view-mode').select_option('actual')
        page.locator('#clear').click();page.locator('#cancel-clear').click()
        check('cancel clear preserves records',page.locator('#record-count').inner_text()=='2')
        with page.expect_download() as download:page.locator('#export').click()
        raw=Path(download.value.path()).read_text();exported=json.loads(raw)
        check('export contains actual local demo records',len(exported['records'])==2 and exported['mode']=='DEMO_ONLY')
        page.locator('#clear').click();page.locator('#confirm-clear').click()
        check('confirmed clear removes demo records and watch',page.locator('#record-count').inner_text()=='0' and page.locator('#watch-list .watch-item').count()==0)
        page.locator('#entry-tab').click();form=page.locator('#entry-form')
        for name,value in {'price':'100','size':'1','fee':'0','slip':'0','note':'<img src=x onerror="window.injected=true">'}.items():form.locator(f'[name={name}]').fill(value)
        form.locator('[name=quote]').evaluate('(e)=>e.value="USDT"');form.locator('[type=submit]').click()
        check('mismatched quote refused in UI',page.locator('#record-count').inner_text()=='0' and 'Quote mismatch' in page.locator('#feedback').inner_text())
        form.locator('[name=quote]').evaluate('(e)=>e.value="USD"');form.locator('[type=submit]').click()
        check('journal text rendered without HTML execution',page.locator('#ledger img').count()==0 and page.evaluate('window.injected===undefined') and '<img' in page.locator('#ledger').inner_text())
        page.evaluate(f'localStorage.setItem("{KEY}","not valid JSON")');page=rehydrate(page)
        check('corrupt storage preserved and changes paused',page.locator('#storage-error').is_visible() and page.locator('[data-watch="BTC/USD"]').is_disabled() and page.evaluate(f'localStorage.getItem("{KEY}")')=='not valid JSON')
        page.locator('#clear').click();page.locator('#confirm-clear').click()
        check('confirmed reset recovers corrupt storage',page.locator('[data-watch="BTC/USD"]').is_enabled())
        other=browser.new_context(viewport={'width':390,'height':844});other.route('**/*',route)
        tab=other.new_page();tab.set_content(HTML,wait_until='domcontentloaded');tab.locator('[data-watch="BTC/USD"]').click()
        check('disabled storage stays usable in memory',tab.locator('#watch-list .watch-item').count()==1 and 'this tab only' in tab.locator('#storage-status').inner_text())
        other.close()
        check('no JavaScript errors',not errors);check('no external document requests',not external)
        browser.close()
    report={'checks':len(checks),'passed':checks,'external_requests':external,'page_errors':errors,
            'browser_delivery':'Exact standalone HTML rendered via set_content at about:blank; no navigation/server/external request',
            'file_url_test':'UNVERIFIED: managed Chromium policy blocks file navigation',
            'persistence_scope':'Explicit storage test double plus pure journal engine round-trip; native file storage/reload unverified'}
    (ROOT/'docs/artifacts/dashboard-029-browser-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Browser: {len(checks)} checks passed',flush=True)


if __name__=='__main__':main()
