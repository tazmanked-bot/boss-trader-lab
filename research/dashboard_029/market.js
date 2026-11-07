/* Manual observation only. No journal access, timers, storage or automatic fetch. */
(function(root){
'use strict';
function controller(request,render){
 let busy=false,last=null;
 function refresh(){
  if(busy)return Promise.resolve(false);
  busy=true;render({loading:true,last,error:null,stale:!!last});
  return Promise.resolve().then(request).then(data=>{
   if(!data||data.source!=='BINANCE_PUBLIC_SPOT'||data.pair!=='BTC/USDT'||data.quote!=='USDT'||data.status!=='OBSERVE_ONLY'||data.interval!=='1h'||data.trading_authority!=='NONE'||data.reversal_classification!=='UNAVAILABLE_SOURCE_ADMISSION_HOLD'||data.paper_recording!=='UNAVAILABLE_OBSERVATION_SOURCE'||data.endpoint!=='https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=30'||data.current_executable_quote!==null||data.clock!=='LOCAL_SYSTEM_UTC_UNVERIFIED_B4_NO_GO'||data.freshness!=='RECENT_RELATIVE_TO_UNVERIFIED_LOCAL_CLOCK'||typeof data.latest_completed_close!=='string'||!/^\d+(?:\.\d+)?$/.test(data.latest_completed_close)||!Number.isFinite(Number(data.latest_completed_close))||Number(data.latest_completed_close)<=0||!Number.isFinite(Date.parse(data.capture_time))||!Number.isFinite(Date.parse(data.latest_completed_close_time)))throw Error('Observation source/schema refused');
   last=data;render({loading:false,last,error:null,stale:false});return true;
  }).catch(error=>{render({loading:false,last,error:String(error.message||error).slice(0,300),stale:!!last});return false;}).finally(()=>{busy=false;});
 }
 return Object.freeze({refresh});
}
if(typeof module!=='undefined'&&module.exports){module.exports={controller};return;}
root.Market031=Object.freeze({controller});
const $=id=>document.getElementById(id);
const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
function render(view){
 $('market-refresh').disabled=view.loading;
 $('market-status').textContent=view.loading?'Loading one manual public observation…':view.error?'Observation refused: '+view.error:view.last?'OBSERVE_ONLY — no reversal classification':'Not fetched — press Refresh explicitly.';
 $('market-error').textContent=view.stale?'STALE / NOT CURRENT: last successful observation retained. '+(view.error||'Refresh in progress.') : '';
 const card=$('market-values');card.replaceChildren();if(!view.last)return;
 const d=view.last;
 for(const [label,value] of [
  ['Source',d.source+' · BTC/USDT spot · quote USDT (not USD)'],
  ['Latest completed 1h close',d.latest_completed_close+' USDT'],
  ['Completed candle close time',d.latest_completed_close_time],['Capture time',d.capture_time],
  ['Freshness at capture',view.stale?'STALE — latest refresh unavailable':d.freshness+'; static snapshot, Refresh to reassess'],
  ['Clock',d.clock+'; completion/freshness conditional on local clock'],
  ['Current executable quote','Unavailable — no quote endpoint used'],
  ['Rule-based explanation','Unavailable: observation only. Reversal source admission HOLD; no LLM integrated.'],
  ['Observation-linked paper recording','Unavailable. Demo journal remains separate.'],
  ['Endpoint',d.endpoint]]){const line=node('p','');line.append(node('strong',label+': '),node('span',String(value)));card.append(line);}
}
const c=controller(async()=>{
 if(location.protocol!=='http:'||location.hostname!=='127.0.0.1')throw Error('Run the documented local same-origin server; file-origin fetch is disabled.');
 const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),18000);
 try{
  const response=await fetch('/api/market-read',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',credentials:'omit',cache:'no-store',redirect:'error',signal:abort.signal});
  const text=await response.text();if(text.length>8192)throw Error('Local response too large');
  const data=JSON.parse(text);if(!response.ok)throw Error(data.error||'Local route HTTP '+response.status);return data;
 }finally{clearTimeout(timer);}
},render);
$('market-refresh').addEventListener('click',()=>c.refresh());
$('show-market').addEventListener('click',()=>{document.querySelector('header .mode').textContent='MARKET · OBSERVE ONLY';$('demo-view').hidden=true;$('market-view').hidden=false;$('show-market').setAttribute('aria-pressed','true');$('show-demo').setAttribute('aria-pressed','false');});
$('show-demo').addEventListener('click',()=>{document.querySelector('header .mode').textContent='DEMO / SYNTHETIC DATA';$('market-view').hidden=true;$('demo-view').hidden=false;$('show-market').setAttribute('aria-pressed','false');$('show-demo').setAttribute('aria-pressed','true');});
render({loading:false,last:null,error:null,stale:false});
})(globalThis);
