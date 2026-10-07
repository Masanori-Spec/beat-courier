import {xmlDocument,fail,LIMITS} from './xml.mjs';
import {decimal,midiTempo} from './rational.mjs';
import {encodeConductor} from './midi.mjs';
const elements=node=>Array.from(node.childNodes).filter(n=>n.nodeType===1);
function attrs(node,allowed){for(const a of Array.from(node.attributes))if(!allowed.includes(a.name))fail('MAP_STRUCTURE',`Unsupported ${node.tagName} attribute: ${a.name}`);}
function children(node,allowed){
  for(const n of Array.from(node.childNodes)){
    if(n.nodeType===1&&!allowed.includes(n.tagName))fail('MAP_STRUCTURE',`Unsupported ${node.tagName} child`);
    if(n.nodeType===3&&n.data.trim())fail('MAP_STRUCTURE',`Unexpected text in ${node.tagName}`);
    if(![1,3,8].includes(n.nodeType))fail('MAP_STRUCTURE','Unsupported map content');
  }
}
function one(parent,name){const found=elements(parent).filter(n=>n.tagName===name);if(found.length!==1)fail('MAP_STRUCTURE',`Exactly one ${name} required`);return found[0];}
function integer(value,min,max){
  if(typeof value!=='string'||value.length>20||! /^(?:0|[1-9][0-9]*)$/.test(value))fail('MAP_NUMBER','Canonical bounded integer required');
  const n=BigInt(value);if(n<min||n>max)fail('MAP_NUMBER','Integer outside supported range');return n;
}
function point(node){
  const q=node.getAttribute('quarters');if(!/^(?:0|[1-9][0-9]{0,6}):(?:0|[1-9][0-9]{0,3})$/.test(q))fail('MAP_POSITION','Canonical quarter:tick coordinate required');
  const [whole,ticks]=q.split(':').map(BigInt);
  if(whole>1000000n||ticks>1919n)fail('MAP_POSITION','Position outside supported native range');
  if(ticks!==0n)fail('FRACTIONAL_POSITION','Ardour8.12 profile requires whole-quarter change positions; fractional positions are not rounded');
  const clock=integer(node.getAttribute('sclock'),0n,9223372036854775807n);
  const bbt=node.getAttribute('bbt');if(!/^[1-9][0-9]{0,6}\|[1-9][0-9]{0,2}\|(?:0|[1-9][0-9]{0,3})$/.test(bbt))fail('MAP_POSITION','Canonical bounded BBT coordinate required');
  if(whole===0n&&(clock!==0n||bbt!=='1|1|0'))fail('MAP_ORIGIN','Map must begin at quarter0, clock0 and bar1');
  return {quarter:whole,sourceQuarters:q,sourceClock:String(clock),sourceBBT:bbt};
}
function sequence(points){
  if(!points.length||points.length>LIMITS.pointsPerKind||points[0].quarter!==0n)fail('MAP_POINTS','A bounded complete map beginning at quarter0 is required');
  for(let i=1;i<points.length;i++)if(points[i].quarter<=points[i-1].quarter||BigInt(points[i].sourceClock)<=BigInt(points[i-1].sourceClock))fail('MAP_POSITION','Point positions must strictly increase');
}
function validateClocks(tempos,meters){
  // Native8.12 stores a rounded integer duration per tempo note, then uses
  // integer division for duration per quarter. This validates the source's
  // own redundant coordinates; output tempo microseconds have a separate receipt.
  const perQuarter=tempo=>{
    const n=decimal(tempo.npm),numerator=16934400000n*n.d;
    const perNote=(2n*numerator+n.n)/(2n*n.n);
    return perNote*BigInt(tempo.noteType)/4n;
  };
  for(let i=1;i<tempos.length;i++){
    const previous=tempos[i-1],point=tempos[i];
    if(BigInt(point.sourceClock)!==BigInt(previous.sourceClock)+(point.quarter-previous.quarter)*perQuarter(previous))fail('MAP_CLOCK','Native tempo clock and quarter coordinates disagree');
  }
  for(const point of meters){
    let active=tempos[0];for(const tempo of tempos){if(tempo.quarter>point.quarter)break;active=tempo;}
    if(BigInt(point.sourceClock)!==BigInt(active.sourceClock)+(point.quarter-active.quarter)*perQuarter(active))fail('MAP_CLOCK','Native meter clock and quarter coordinates disagree');
  }
}
function validateBars(tempos,meters){
  const starts=[];
  for(let i=0;i<meters.length;i++){
    const meter=meters[i];let bar=1n;
    if(i){
      const previous=starts[i-1],barTicks=BigInt(previous.numerator)*7680n/BigInt(previous.denominator);
      const delta=(meter.quarter-previous.quarter)*1920n;
      if(delta%barTicks!==0n)fail('METER_BOUNDARY','Supported meter changes must begin a native bar');
      bar=previous.bar+delta/barTicks;
    }
    if(meter.sourceBBT!==`${bar}|1|0`)fail('MAP_BBT','Native meter BBT and quarter coordinates disagree');
    starts.push({...meter,bar});
  }
  for(const tempo of tempos){
    let meter=starts[0];for(const candidate of starts){if(candidate.quarter>tempo.quarter)break;meter=candidate;}
    const grid=7680n/BigInt(meter.denominator),delta=(tempo.quarter-meter.quarter)*1920n;
    if(delta%grid!==0n)fail('TEMPO_BOUNDARY','Ardour8.12 imports tempo changes on meter beats; off-beat points are unsupported');
    const beatOffset=delta/grid,num=BigInt(meter.numerator);
    const expected=`${meter.bar+beatOffset/num}|${beatOffset%num+1n}|0`;
    if(tempo.sourceBBT!==expected)fail('MAP_BBT','Native tempo BBT and quarter coordinates disagree');
  }
}
export function inspectSession(bytes){
  const {document}=xmlDocument(bytes),root=document.documentElement;
  if(root.getAttribute('version')!=='7003')fail('SESSION_VERSION','This profile supports the native Session7003 format verified with Ardour8.12');
  const sampleRate=integer(root.getAttribute('sample-rate'),8000n,384000n);
  const map=one(root,'TempoMap');if(document.getElementsByTagName('TempoMap').length!==1)fail('MAP_STRUCTURE','Ambiguous nested tempo map');
  attrs(map,['superclocks-per-second']);children(map,['Tempos','Meters','MusicTimes']);
  if(map.getAttribute('superclocks-per-second')!=='282240000')fail('MAP_CLOCK','Unsupported native clock rate');
  const music=one(map,'MusicTimes');attrs(music,[]);children(music,[]);
  if(elements(music).length)fail('MUSIC_TIME','BBT resets are unsupported');
  const tempoNode=one(map,'Tempos'),meterNode=one(map,'Meters');attrs(tempoNode,[]);attrs(meterNode,[]);children(tempoNode,['Tempo']);children(meterNode,['Meter']);
  const tempos=elements(tempoNode).map(node=>{
    attrs(node,['npm','enpm','note-type','type','locked-to-meter','continuing','active','sclock','quarters','bbt','omega']);children(node,[]);
    let npm,enpm,omega;try{npm=decimal(node.getAttribute('npm'));enpm=decimal(node.getAttribute('enpm'));omega=decimal(node.getAttribute('omega'));}catch{fail('TEMPO_NUMBER','Unsupported native tempo number');}
    if(npm.n!==0n&&npm.n*enpm.d===enpm.n*npm.d&&omega.n===0n&&node.getAttribute('type')==='Constant'&&node.getAttribute('continuing')==='0'){}else fail('RAMP','Only explicit constant, noncontinuing tempos are supported');
    if(!['0','1'].includes(node.getAttribute('locked-to-meter'))||node.getAttribute('active')!=='1')fail('TEMPO_FLAGS','Unsupported native tempo flags');
    const noteType=Number(integer(node.getAttribute('note-type'),1n,64n));
    try{midiTempo(node.getAttribute('npm'),noteType);}catch{fail('TEMPO_RANGE','Tempo cannot be represented by this MIDI profile');}
    return {...point(node),npm:node.getAttribute('npm'),noteType};
  });
  const meters=elements(meterNode).map(node=>{
    attrs(node,['note-value','divisions-per-bar','sclock','quarters','bbt']);children(node,[]);
    const numerator=Number(integer(node.getAttribute('divisions-per-bar'),1n,127n));
    const denominator=Number(integer(node.getAttribute('note-value'),1n,64n));
    if(![1,2,4,8,16,32,64].includes(denominator))fail('METER_RANGE','Power-of-two meter denominator required');
    return {...point(node),numerator,denominator};
  });
  sequence(tempos);sequence(meters);
  validateClocks(tempos,meters);
  validateBars(tempos,meters);
  return {version:'7003',nativeProfile:'Ardour8.12',sampleRate:Number(sampleRate),superclocksPerSecond:282240000,tempos,meters};
}
export function convertSession(bytes){const model=inspectSession(bytes);return {model,...encodeConductor(model)};}
