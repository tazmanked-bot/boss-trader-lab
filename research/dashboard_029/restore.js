/* Temporary preview transaction; accounting and schema belong to Paper029. */
(function(root){
'use strict';
function create(P,model,current,commit,at){
 let pending=null;
 const summary=s=>{const t=P.totals(s);return {sessions:s.sessions.length,watches:s.watch.length,entries:s.records.filter(r=>r.kind==='ENTRY').length,exits:s.records.filter(r=>r.kind==='EXIT').length,gross:P.money(t.gross),net:P.money(t.net)};};
 return Object.freeze({
  preview(raw){
   pending=null;
   const before=current(),candidate=P.restore(raw,model,at());
   pending={raw:JSON.stringify(candidate),before:JSON.stringify(before)};
   return {backup:summary(P.validate(JSON.parse(raw))),replacement:summary(candidate),current:summary(before)};
  },
  cancel(){pending=null;},
  confirm(){
   const saved=pending;pending=null;
   if(!saved)throw new Error('Preview a valid backup before confirming.');
   if(JSON.stringify(current())!==saved.before)throw new Error('Current journal changed. Preview the backup again.');
   const candidate=P.restore(saved.raw,model,at());
   commit(candidate);return summary(candidate);
  }
 });
}
if(typeof module!=='undefined'&&module.exports)module.exports={create};else root.Restore030=Object.freeze({create});
})(globalThis);
