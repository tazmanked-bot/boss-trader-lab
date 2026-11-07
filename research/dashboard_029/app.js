(function(){
'use strict';
const model=JSON.parse(document.getElementById('demo-data').textContent),P=Paper029,KEY='boss-trader-demo-paper-v1';
const $=id=>document.getElementById(id),now=()=>new Date().toISOString();
const labels={slowing_downside:'Downside slowing',low_retest_hold:'Low retest held',fresh_recovery:'Fresh recovery',volume_consistent:'Volume consistent'};
const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const uid=()=>Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
let state,lastRaw=null,storageAvailable=true,locked=false,view='actual',entryToken=uid(),exitToken=uid();
function feedback(message,error=false){$('feedback').textContent=message;$('feedback').className='feedback'+(error?' error':'');}
function storageMessage(message,error=false){$(error?'storage-error':'storage-status').textContent=message;if(error)$('storage-error').hidden=false;}
try{lastRaw=localStorage.getItem(KEY);}catch(_){storageAvailable=false;}
try{state=P.load(lastRaw,model,now());}catch(_){locked=true;state=P.load(null,model,now());storageMessage('Saved demo data is unreadable or unsupported. Changes are paused. Existing data has not been overwritten; clear only after confirmation.',true);}
function write(next,reset=false){
 if(locked&&!reset)throw new Error('Changes paused. Reload or explicitly clear unsupported saved data.');
 const raw=JSON.stringify(P.validate(next));
 if(storageAvailable){
  let current;try{current=localStorage.getItem(KEY);}catch(_){storageAvailable=false;}
  if(storageAvailable&&current!==lastRaw&&!reset){locked=true;throw new Error('Demo journal changed in another tab. Reload before recording.');}
  if(storageAvailable){try{localStorage.setItem(KEY,raw);lastRaw=raw;}catch(_){storageAvailable=false;}}
 }
 state=next;
 storageMessage(storageAvailable?'Saved locally in this browser • demo records only':'Browser storage unavailable • changes kept in this tab only; export before leaving');
 render();
}
if(!locked)write(state);
else render();
window.addEventListener('storage',e=>{if(e.key===KEY){locked=true;storageMessage('Demo data changed in another tab. Reload before making changes.',true);render();}});
function rows(){
 if(view==='actual')return model.rows;
 const out={};for(const [symbol,r] of Object.entries(model.rows))out[symbol]={...r,decision:view==='empty'?'WAIT':'BLOCKED',features:null,score:null,why_early:null,invalidation_observation:null,fixture_only_closed_price_usd:null,refusal:view==='blocked'?'Presentation test: source unavailable':null};return out;
}
function render(){
 $('asof').textContent=model.as_of_text+' · fixture coordinate, not current time';$('revision').textContent=model.source_revision.slice(0,12);
 $('full-revision').textContent=model.source_revision;$('fixture-hash').textContent=model.fixture_sha256;$('session-ref').textContent=model.id;
 $('generated').textContent=model.generated_at+' · local system clock; not source time';
 const shown=rows(),values=Object.values(shown),watch=values.filter(r=>r.decision==='WATCH').length;
 $('observed-count').textContent=values.length;$('candidate-count').textContent=view==='actual'?model.candidates.length:0;
 $('watch-count').textContent=watch;$('other-count').textContent=values.filter(r=>r.decision==='WAIT').length+' / '+values.filter(r=>r.decision==='BLOCKED').length;
 $('record-count').textContent=state.records.length;$('test-notice').hidden=view==='actual';
 $('empty-scan').hidden=watch>0;$('empty-scan').textContent=values.every(r=>r.decision==='BLOCKED')?'Source unavailable. No candidate can be admitted.':'No qualifying setup.';
 const cards=$('cards');cards.replaceChildren();
 const ordered=[...model.candidates,...Object.keys(shown).filter(s=>!model.candidates.includes(s))];
 for(const symbol of ordered){
  const r=shown[symbol],card=node('article',undefined,'card');card.dataset.symbol=symbol;
  const top=node('div',undefined,'card-top'),symbolLabel=node('div',undefined,'symbol');
  symbolLabel.append(node('span',symbol.split('/')[0].slice(0,1),'coin'),node('span',symbol));top.append(symbolLabel,node('span',r.decision,'tag '+r.decision));card.append(top);
  const price=r.fixture_only_closed_price_usd;card.append(node('div',price===null?'Unavailable':P.money(P.amount(String(price))),'ref'),node('div','Reference price • fixture only','hint'));
  const checks=node('ul',undefined,'checks');for(const [key,label] of Object.entries(labels)){const line=node('li');line.append(node('span',label),node('span',r.features?(r.features[key].passed?'✓ Pass':'Wait'):'Unavailable','check'));checks.append(line);}card.append(checks);
  card.append(node('p',r.score===null?'Rule score unavailable':'Rule score '+r.score.toLocaleString()+' / 40,000 · ranking, not confidence','hint'));
  const why=node('div',undefined,'why');why.append(node('b','Rule-based explanation'),node('span',r.why_early||(r.decision==='WAIT'?'No qualifying demo setup.':'Source unavailable; research preview blocked.')));card.append(why);
  const detail=node('details');detail.append(node('summary','Invalidation & availability'),node('p',r.invalidation_observation||'Invalidation observation: Not defined'),node('p','Entry price: Not defined · Numeric invalidation: Not defined'),node('p','Catalyst: UNVERIFIED · no real BUY authorization'));
  if(r.refusal)detail.append(node('p',r.refusal));card.append(detail);
  const button=node('button',state.watch.some(w=>w.session===model.id&&w.symbol===symbol)?'Added to demo watch':'Add to demo watch');button.type='button';button.dataset.watch=symbol;
  button.disabled=locked||r.decision!=='WATCH'||state.watch.some(w=>w.session===model.id&&w.symbol===symbol);
  button.addEventListener('click',()=>{try{write(P.watch(state,model,symbol,now()));feedback('Saved '+symbol+' to the demo watch list.');}catch(e){feedback(e.message,true);}});card.append(button);cards.append(card);
 }
 const watchList=$('watch-list');watchList.replaceChildren();$('watch-total').textContent=state.watch.length+' saved';
 if(!state.watch.length)watchList.append(node('div','Add a demo WATCH above to keep its recorded conditions here.','empty'));
 for(const w of state.watch){
  const item=node('div',undefined,'watch-item'),head=node('div',undefined,'watch-actions');head.append(node('strong',w.symbol+' • monitoring only'));
  const remove=node('button','Remove');remove.type='button';remove.disabled=locked;remove.addEventListener('click',()=>{try{write(P.unwatch(state,w.session,w.symbol,now()));}catch(e){feedback(e.message,true);}});head.append(remove);item.append(head);
  item.append(node('p',w.why),node('p',Object.entries(w.features).map(([k,f])=>labels[k]+': '+(f.passed?'pass':'wait')).join(' · ')),node('p',w.invalidation),node('small','Demo source session '+w.session.slice(0,12)));watchList.append(item);
 }
 const entryForm=$('entry-form'),selected=entryForm.elements.symbol.value;entryForm.elements.symbol.replaceChildren();
 for(const [symbol,r] of Object.entries(model.rows))if(r.decision==='WATCH'){const o=node('option',symbol);o.value=symbol;entryForm.elements.symbol.append(o);}
 if(selected)entryForm.elements.symbol.value=selected;
 entryForm.querySelector('button[type=submit]').disabled=locked||view!=='actual'||!entryForm.elements.symbol.options.length;
 const summary=P.totals(state);$('gross').textContent=P.money(summary.gross);$('net').textContent=P.money(summary.net);$('open-count').textContent=summary.open.length;
 const exitForm=$('exit-form'),chosen=exitForm.elements.entryId.value;exitForm.elements.entryId.replaceChildren();
 const blank=node('option',summary.open.length?'Choose an open paper entry':'No open paper entries');blank.value='';exitForm.elements.entryId.append(blank);
 for(const lot of summary.open){const o=node('option',lot.record.symbol+' · '+P.decimal(lot.remaining)+' available · '+lot.record.id.slice(0,8));o.value=lot.record.id;exitForm.elements.entryId.append(o);}
 if(summary.open.some(l=>l.record.id===chosen))exitForm.elements.entryId.value=chosen;
 exitForm.querySelector('button[type=submit]').disabled=locked||!summary.open.length;
 const positions=$('open-positions');positions.replaceChildren();if(!summary.open.length)positions.append(node('p','No open paper positions.','hint'));
 for(const lot of summary.open){const e=node('div',undefined,'open-position');e.append(node('strong',lot.record.symbol+' · '+P.decimal(lot.remaining)+' '+lot.record.symbol.split('/')[0]),node('p','Remaining entry notional '+P.money(lot.basis-lot.allocatedBasis)+' · unallocated entry costs '+P.money(lot.fee-lot.allocatedFee+lot.slip-lot.allocatedSlip)),node('p','Market mark: unavailable · Unrealized P&L: unavailable','hint'));positions.append(e);}
 const ledger=$('ledger');ledger.replaceChildren();if(!state.records.length)ledger.append(node('div','No paper records yet. Enter a hypothetical price and size to start.','empty'));
 for(const r of [...state.records].reverse()){
  const row=node('div',undefined,'record'),left=node('div');left.append(node('strong',r.kind==='ENTRY'?'Paper entry • '+r.symbol:'Paper exit • '+r.symbol),node('div',r.qty+' '+r.symbol.split('/')[0]+' at '+P.money(P.amount(r.price))+' • hypothetical'),node('small',r.at+' · demo '+r.session.slice(0,8)));
  const right=node('div',undefined,'right');right.append(node('div','Fee '+P.money(P.amount(r.fee,true))+' · slippage '+P.money(P.amount(r.slip,true))));
  const exitResult=summary.exits.find(e=>e.record.id===r.id);if(exitResult)right.append(node('strong','Net realized '+P.money(exitResult.net)));
  row.append(left,right);if(r.note)row.append(node('div',r.note,'record-note'));ledger.append(row);
 }
 $('activity').replaceChildren(...state.activity.map(a=>node('li',a.text+' · '+a.at)));
 $('export').disabled=locked;$('restore').disabled=locked;
}
$('load-demo').addEventListener('click',()=>{view='actual';$('view-mode').value='actual';render();feedback('Embedded demo loaded. Same source session; no network request.');});
$('view-mode').addEventListener('change',e=>{view=e.target.value;render();});
function tab(kind){const entry=kind==='entry';$('entry-form').hidden=!entry;$('exit-form').hidden=entry;for(const k of ['entry','exit']){$(k+'-tab').classList.toggle('active',k===kind);$(k+'-tab').setAttribute('aria-pressed',String(k===kind));}feedback('');}
$('entry-tab').addEventListener('click',()=>tab('entry'));$('exit-tab').addEventListener('click',()=>tab('exit'));
$('entry-form').addEventListener('submit',e=>{e.preventDefault();try{if(view!=='actual')throw new Error('Presentation-only view; paper entry is paused.');const f=e.target;const input=Object.fromEntries(new FormData(f));input.id=entryToken;input.at=now();input.slip=input.slip||'0';write(P.entry(state,model,input));entryToken=uid();f.reset();feedback('Paper entry recorded. Hypothetical only; no order sent.');}catch(err){feedback(err.message,true);}});
$('exit-form').addEventListener('submit',e=>{e.preventDefault();try{const f=e.target,input=Object.fromEntries(new FormData(f));input.id=exitToken;input.at=now();input.slip=input.slip||'0';write(P.exit(state,input));exitToken=uid();f.reset();feedback('Paper exit recorded. Hypothetical only; no order sent.');}catch(err){feedback(err.message,true);}});
$('clear').addEventListener('click',()=>$('clear-dialog').showModal());$('cancel-clear').addEventListener('click',()=>$('clear-dialog').close());
$('confirm-clear').addEventListener('click',()=>{try{locked=false;write(P.load(null,model,now()),true);$('storage-error').hidden=true;entryToken=uid();exitToken=uid();$('entry-form').reset();$('exit-form').reset();$('clear-dialog').close();feedback(storageAvailable?'Local demo data cleared.':'Demo data cleared in this tab only. Browser storage is unavailable; any previously saved data could not be changed.');}catch(e){feedback(e.message,true);}});

const recovery=Restore030.create(P,model,()=>state,next=>write(next),now);
let restoreRead=0;
function cancelRestore(){restoreRead++;recovery.cancel();$('restore-file').value='';$('restore-dialog').close();}
$('restore').addEventListener('click',()=>{restoreRead++;recovery.cancel();$('restore-file').value='';$('restore-file').click();});
$('restore-file').addEventListener('change',async e=>{
 const ticket=++restoreRead;recovery.cancel();
 try{
  if(locked)throw new Error('Changes paused. Reload before restoring.');
  const files=e.target.files;
  if(!files||files.length!==1)throw new Error('Choose exactly one local JSON journal file.');
  const file=files[0];
  if(!/\.json$/i.test(file.name))throw new Error('Choose a local .json journal backup.');
  if(file.size>P.LIMIT)throw new Error('Backup exceeds journal storage limit (128 KiB).');
  const raw=await file.text();if(ticket!==restoreRead)return;
  if(locked)throw new Error('Journal changed. Reload before restoring.');
  const preview=recovery.preview(raw);
  const describe=(label,s)=>label+': '+s.sessions+' sessions, '+s.watches+' watches, '+s.entries+' entries, '+s.exits+' exits; gross '+s.gross+'; net '+s.net;
  $('restore-preview').textContent=[describe('Backup',preview.backup),describe('Current journal (will be replaced)',preview.current),describe('After replacement (includes displayed fixture session)',preview.replacement)].join('\n');
  $('restore-storage').textContent=storageAvailable?'Replacement will be saved locally if browser storage remains available.':'MEMORY ONLY: browser storage unavailable. Replacement stays in this tab only; export before leaving.';
  $('restore-dialog').showModal();
 }catch(err){recovery.cancel();feedback('Restore refused: '+err.message,true);}
});
$('cancel-restore').addEventListener('click',cancelRestore);
$('restore-dialog').addEventListener('cancel',e=>{e.preventDefault();cancelRestore();});
$('confirm-restore').addEventListener('click',()=>{
 try{recovery.confirm();entryToken=uid();exitToken=uid();$('restore-dialog').close();$('restore-file').value='';feedback(storageAvailable?'Demo journal replaced and saved locally. User-supplied synthetic records only.':'Demo journal replaced IN THIS TAB ONLY. Storage unavailable; export before leaving.');}
 catch(err){$('restore-dialog').close();feedback('Restore refused: '+err.message,true);}
});
$('export').addEventListener('click',()=>{try{const raw=JSON.stringify(P.validate(state));if(new TextEncoder().encode(raw).length>P.LIMIT)throw new Error('Journal exceeds backup byte limit; no backup file created.');const url=URL.createObjectURL(new Blob([raw],{type:'application/json'})),a=node('a');a.href=url;a.download='boss-trader-demo-journal.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){feedback(e.message,true);}});
})();
