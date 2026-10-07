// Test-only fixed synthetic paths. The product core has no filesystem access.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {convertSession} from '../src/session.mjs';
const root='/tmp/beatcourier-native',out=new URL('../artifacts/native/',import.meta.url);
const source=fs.readFileSync(`${root}/source/Source.ardour`);
const sha=b=>createHash('sha256').update(b).digest('hex');
const before=sha(source),result=convertSession(source);
const bytes=Buffer.from(result.bytes);
fs.writeFileSync(`${root}/conductor.mid`,bytes);
fs.writeFileSync(new URL('conductor.mid',out),bytes);
const receipt={sourceSha256:before,outputSha256:sha(bytes),format:result.format,ppqn:result.ppqn,endTick:result.endTick,noteEvents:result.noteEvents,review:result.review};
fs.writeFileSync(new URL('conversion-receipt.json',out),JSON.stringify(receipt,null,2)+'\n');
assert.equal(sha(source),before);assert.equal(sha(fs.readFileSync(`${root}/source/Source.ardour`)),before);
const rejected=[];
function reject(name,input,code){
 assert.throws(()=>convertSession(input),e=>{assert.equal(e.code,code);return true;});
 rejected.push({name,code,sha256:sha(input),outputCreated:false});
}
reject('native-authored fractional quarter15.5',fs.readFileSync(`${root}/fractional/Fractional.ardour`),'FRACTIONAL_POSITION');
// Clearly labelled byte mutations of the synthetic input, never loaded into Ardour.
const text=source.toString('utf8');
function mutate(from,to){assert.ok(text.includes(from));return Buffer.from(text.replace(from,to));}
reject('nonconstant endpoint',mutate('enpm="100"','enpm="110"'),'RAMP');
reject('nonzero omega',mutate('omega="0"','omega="0.01"'),'RAMP');
reject('BBT-reset container',mutate('<MusicTimes/>','<MusicTimes><MusicTime name="test-reset"/></MusicTimes>'),'MAP_STRUCTURE');
reject('corrupted musical BBT',mutate('bbt="3|1|0"','bbt="3|2|0"'),'MAP_BBT');
reject('unrepresentable tempo',mutate('npm="100" enpm="100"','npm="1" enpm="1"'),'TEMPO_RANGE');
fs.writeFileSync(new URL('rejection-report.json',out),JSON.stringify(rejected,null,2)+'\n');
console.log('Production converter wrote fixed synthetic conductor; input bytes unchanged');
