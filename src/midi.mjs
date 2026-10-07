import {midiTempo} from './rational.mjs';
export const PPQN=1920;
const VLQ_MAX=0x0fffffffn;
export function vlq(value){
  if(typeof value!=='bigint'||value<0n||value>VLQ_MAX)throw new Error('MIDI delta outside28-bit range');
  const out=[Number(value&127n)];value>>=7n;
  while(value){out.unshift(Number(value&127n)|128);value>>=7n;}return out;
}
function quarter(value){
  if(typeof value!=='bigint'||value<0n||value>1000000n)throw new Error('Quarter position outside supported range');
  return value*BigInt(PPQN);
}
function ordered(points){
  if(!Array.isArray(points)||points.length<1||points.length>2048||points[0].quarter!==0n)throw new Error('Bounded complete map from quarter0 required');
  for(let i=1;i<points.length;i++)if(points[i].quarter<=points[i-1].quarter)throw new Error('Map positions must strictly increase');
}
export function encodeConductor(map){
  ordered(map.tempos);ordered(map.meters);
  const events=[],review=[];
  for(const point of map.tempos){
    const tick=quarter(point.quarter),tempo=midiTempo(point.npm,point.noteType),us=tempo.microseconds;
    events.push({tick,kind:0,data:[255,81,3,us>>>16,(us>>>8)&255,us&255]});
    review.push({kind:'tempo',quarter:String(point.quarter),tick:String(tick),...tempo});
  }
  for(const point of map.meters){
    const tick=quarter(point.quarter),{numerator,denominator}=point;
    if(!Number.isInteger(numerator)||numerator<1||numerator>127||![1,2,4,8,16,32,64].includes(denominator))throw new Error('Unsupported MIDI meter');
    events.push({tick,kind:1,data:[255,88,4,numerator,Math.log2(denominator),24,8]});
    review.push({kind:'meter',quarter:String(point.quarter),tick:String(tick),numerator,denominator,clocksPerClick:24,notated32nds:8});
  }
  events.sort((a,b)=>a.tick<b.tick?-1:a.tick>b.tick?1:a.kind-b.kind);
  const end=events.at(-1).tick+BigInt(PPQN);let previous=0n;const track=[];
  for(const event of events){track.push(...vlq(event.tick-previous),...event.data);previous=event.tick;}
  track.push(...vlq(end-previous),255,47,0);
  const len=track.length;
  const bytes=Uint8Array.from([77,84,104,100,0,0,0,6,0,0,0,1,7,128,77,84,114,107,(len>>>24)&255,(len>>>16)&255,(len>>>8)&255,len&255,...track]);
  review.sort((a,b)=>Number(a.quarter)-Number(b.quarter)||(a.kind==='tempo'?-1:1));
  return {bytes,review,format:0,ppqn:PPQN,endTick:String(end),noteEvents:0};
}
