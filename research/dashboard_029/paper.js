/* Exact 8-decimal paper arithmetic. No market calculations or network code. */
(function(root){
'use strict';
const SCALE=100000000n, LIMIT=128*1024, SYMBOLS=['BTC/USD','XRP/USD','SOL/USD'];
const fail=(s)=>{throw new Error(s);};
const assert=(v,s)=>{if(!v)fail(s);};
const exact=(v,keys)=>assert(v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join('|')===keys.slice().sort().join('|'),'Invalid saved structure');
const text=(v,n)=>assert(typeof v==='string'&&v.length<=n,'Invalid saved text');
const hash=(v,n)=>assert(typeof v==='string'&&new RegExp('^[a-f0-9]{'+n+'}$').test(v),'Invalid source reference');
function amount(value,zero=false){
 assert(typeof value==='string'&&/^\d{1,12}(?:\.\d{1,8})?$/.test(value),'Use a finite positive decimal, up to 8 decimal places');
 const [a,b='']=value.split('.'), result=BigInt(a)*SCALE+BigInt(b.padEnd(8,'0'));
 assert(zero?result>=0n:result>0n,zero?'Cost cannot be negative':'Price and quantity must be positive');return result;
}
function decimal(v){const sign=v<0n?'-':'';v=v<0n?-v:v;return sign+(v/SCALE).toString()+((v%SCALE)?'.'+(v%SCALE).toString().padStart(8,'0').replace(/0+$/,''):'');}
function money(v){const sign=v<0n?'-':'';v=v<0n?-v:v;const cents=(v+500000n)/1000000n;return sign+'$'+(cents/100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,',')+'.'+(cents%100n).toString().padStart(2,'0')+' USD';}
const product=(p,q)=>(p*q+SCALE/2n)/SCALE;
const part=(total,q,original)=>(total*q+original/2n)/original;
function session(model){
 assert(model.mode==='DEMO_ONLY','Only demo sessions are supported');hash(model.id,64);hash(model.source_revision,40);
 text(model.as_of_text,64);return {id:model.id,revision:model.source_revision,asOf:model.as_of_text,source:'DEMO_ONLY'};
}
function stamp(value){assert(typeof value==='string'&&/^\d{4}-\d\d-\d\dT[0-9:.+-]+Z$/.test(value)&&Number.isFinite(Date.parse(value)),'Invalid local record time');return value;}
function totals(state){
 const lots=new Map(), exits=[];let gross=0n,net=0n;
 for(const r of state.records){
  const price=amount(r.price),qty=amount(r.qty),fee=amount(r.fee,true),slip=amount(r.slip,true);
  if(r.kind==='ENTRY'){
   lots.set(r.id,{record:r,qty,remaining:qty,sold:0n,basis:product(price,qty),fee,slip,allocatedBasis:0n,allocatedFee:0n,allocatedSlip:0n});
  }else{
   const l=lots.get(r.entryId);assert(l,'Exit must reference an earlier paper entry');
   assert(r.symbol===l.record.symbol&&r.session===l.record.session,'Exit source or symbol mismatch');
   assert(qty<=l.remaining,'Exit quantity exceeds available paper quantity');
   const sold=l.sold+qty,basis=part(l.basis,sold,l.qty),entryFee=part(l.fee,sold,l.qty),entrySlip=part(l.slip,sold,l.qty);
   const g=product(price,qty)-(basis-l.allocatedBasis),n=g-(entryFee-l.allocatedFee)-(entrySlip-l.allocatedSlip)-fee-slip;
   gross+=g;net+=n;exits.push({record:r,gross:g,net:n});
   Object.assign(l,{sold,remaining:l.remaining-qty,allocatedBasis:basis,allocatedFee:entryFee,allocatedSlip:entrySlip});
  }
 }
 return {gross,net,exits,lots:[...lots.values()],open:[...lots.values()].filter(l=>l.remaining>0n)};
}
function validate(state){
 exact(state,['version','mode','sessions','watch','records','activity']);
 assert(state.version===1&&state.mode==='DEMO_ONLY','Unsupported journal version or source');
 assert(Array.isArray(state.sessions)&&state.sessions.length<=20,'Session limit reached');
 const sessions=new Set();for(const s of state.sessions){exact(s,['id','revision','asOf','source']);hash(s.id,64);hash(s.revision,40);text(s.asOf,64);assert(s.source==='DEMO_ONLY'&&!sessions.has(s.id),'Invalid or duplicate source session');sessions.add(s.id);}
 assert(Array.isArray(state.watch)&&state.watch.length<=12,'Watch list limit reached');
 const watches=new Set();for(const w of state.watch){
  exact(w,['session','symbol','why','invalidation','features']);assert(sessions.has(w.session)&&SYMBOLS.includes(w.symbol),'Invalid watch source');
  const key=w.session+w.symbol;assert(!watches.has(key),'Duplicate watch');watches.add(key);text(w.why,500);text(w.invalidation,500);
  exact(w.features,['slowing_downside','low_retest_hold','fresh_recovery','volume_consistent']);
  for(const f of Object.values(w.features)){exact(f,['passed','strength_bps']);assert(typeof f.passed==='boolean'&&Number.isInteger(f.strength_bps)&&f.strength_bps>=0&&f.strength_bps<=10000,'Invalid watch condition');}
 }
 assert(Array.isArray(state.records)&&state.records.length<=200,'Paper record limit reached; export before reset');
 const ids=new Set();for(const r of state.records){
  exact(r,['id','kind','session','symbol','quote','price','qty','fee','slip','note','at','entryId']);hash(r.id,32);
  assert(!ids.has(r.id),'Duplicate submission');ids.add(r.id);assert(['ENTRY','EXIT'].includes(r.kind),'Invalid paper record');
  assert(sessions.has(r.session)&&SYMBOLS.includes(r.symbol)&&r.quote==='USD','Quote/source mismatch; USD demo only');
  amount(r.price);amount(r.qty);amount(r.fee,true);amount(r.slip,true);text(r.note,280);stamp(r.at);
  assert(r.kind==='ENTRY'?r.entryId===null:typeof r.entryId==='string','Invalid paper entry reference');
 }
 totals(state);assert(Array.isArray(state.activity)&&state.activity.length<=80,'Invalid activity log');
 for(const a of state.activity){exact(a,['text','at']);text(a.text,300);stamp(a.at);}
 assert(JSON.stringify(state).length<=LIMIT,'Journal storage limit reached');return state;
}
function log(s,message,at){s.activity.unshift({text:message,at:stamp(at)});s.activity=s.activity.slice(0,80);}
function load(raw,model,at){
 let state;if(raw===null)state={version:1,mode:'DEMO_ONLY',sessions:[],watch:[],records:[],activity:[]};
 else{assert(typeof raw==='string'&&raw.length<=LIMIT,'Saved journal too large');state=validate(JSON.parse(raw));}
 const current=session(model);
 if(!state.sessions.some(s=>s.id===current.id)){assert(state.sessions.length<20,'Session limit reached; export before reset');state.sessions.push(current);log(state,'Recorded static demo session '+current.id.slice(0,8),at);}
 return validate(state);
}
const clone=s=>JSON.parse(JSON.stringify(validate(s)));
function watch(s,model,symbol,at){
 s=clone(s);assert(s.sessions.some(x=>x.id===model.id),'Unknown session');
 const row=model.rows[symbol];assert(SYMBOLS.includes(symbol)&&row&&row.decision==='WATCH'&&row.features,'Only a demo WATCH can be added');
 assert(!s.watch.some(w=>w.session===model.id&&w.symbol===symbol),'Already watching this demo setup');
 s.watch.push({session:model.id,symbol,why:row.why_early||'Not defined',invalidation:row.invalidation_observation||'Not defined',features:row.features});
 log(s,'Added '+symbol+' to demo watch',at);return validate(s);
}
function unwatch(s,sessionId,symbol,at){s=clone(s);s.watch=s.watch.filter(w=>!(w.session===sessionId&&w.symbol===symbol));log(s,'Removed '+symbol+' from demo watch',at);return validate(s);}
function entry(s,model,input){
 s=clone(s);assert(model.rows[input.symbol]&&model.rows[input.symbol].decision==='WATCH','No qualifying demo setup for this paper entry');
 assert(input.quote==='USD'&&SYMBOLS.includes(input.symbol),'Quote mismatch; use the exact USD pair');
 const price=amount(input.price),size=amount(input.size);assert(['quantity','notional'].includes(input.sizing),'Invalid paper sizing');
 const qty=input.sizing==='quantity'?size:size*SCALE/price;assert(qty>0n,'Notional is too small at 8-decimal precision');
 const r={id:input.id,kind:'ENTRY',session:model.id,symbol:input.symbol,quote:input.quote,price:decimal(price),qty:decimal(qty),
          fee:decimal(amount(input.fee,true)),slip:decimal(amount(input.slip,true)),note:input.note,at:input.at,entryId:null};
 s.records.push(r);log(s,'Recorded hypothetical paper entry • '+input.symbol,input.at);return validate(s);
}
function exit(s,input){
 s=clone(s);const lot=totals(s).open.find(l=>l.record.id===input.entryId);assert(lot,'Select an open paper entry');
 assert(input.quote==='USD','Quote mismatch; exit costs and prices must be USD');
 const r={id:input.id,kind:'EXIT',session:lot.record.session,symbol:lot.record.symbol,quote:input.quote,
          price:decimal(amount(input.price)),qty:decimal(amount(input.qty)),fee:decimal(amount(input.fee,true)),
          slip:decimal(amount(input.slip,true)),note:input.note,at:input.at,entryId:input.entryId};
 s.records.push(r);log(s,'Recorded hypothetical paper exit • '+r.symbol,input.at);return validate(s);
}
const api={amount,decimal,money,product,totals,validate,load,watch,unwatch,entry,exit,LIMIT};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Paper029=Object.freeze(api);
})(typeof globalThis==='undefined'?this:globalThis);
