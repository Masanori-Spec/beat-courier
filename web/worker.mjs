import {convertSession} from '../src/session.mjs';
const hash=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(n=>n.toString(16).padStart(2,'0')).join('');
self.onmessage=async event=>{
 const {id,buffer}=event.data;
 try{
  const source=new Uint8Array(buffer),result=convertSession(source);
  const [sourceSha256,outputSha256]=await Promise.all([hash(source),hash(result.bytes)]);
  const model={...result.model,tempos:result.model.tempos.map(p=>({...p,quarter:String(p.quarter)})),meters:result.model.meters.map(p=>({...p,quarter:String(p.quarter)}))};
  const receipt={sourceSha256,outputSha256,format:result.format,ppqn:result.ppqn,endTick:result.endTick,noteEvents:result.noteEvents,review:result.review};
  self.postMessage({id,ok:true,model,receipt,buffer:result.bytes.buffer},[result.bytes.buffer]);
 }catch(error){self.postMessage({id,ok:false,error:{code:error.code||'CONVERSION',message:String(error.message)}});}
};
