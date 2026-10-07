import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeConductor} from '../src/midi.mjs';
import {midiTempo} from '../src/rational.mjs';
import {inspectSession} from '../src/session.mjs';
test('Ardour signed-byte native meter limits are narrower than SMF',()=>{
 const map={tempos:[{quarter:0n,npm:'120',noteType:4}],meters:[{quarter:0n,numerator:127,denominator:64}]};
 assert.ok(encodeConductor(map).bytes.length>0);
 for(const numerator of [128,255])assert.throws(()=>encodeConductor({...map,meters:[{quarter:0n,numerator,denominator:4}]}));
 assert.throws(()=>encodeConductor({...map,meters:[{quarter:0n,numerator:4,denominator:128}]}));
 assert.throws(()=>midiTempo('120',128));
});
test('native XML rejects signed-byte overflow before conversion',()=>{
 const xml=(note,num,den)=>new TextEncoder().encode(`<Session version="7003" sample-rate="48000"><TempoMap superclocks-per-second="282240000"><Tempos><Tempo npm="120" enpm="120" note-type="${note}" type="Constant" locked-to-meter="0" continuing="0" active="1" omega="0" sclock="0" quarters="0:0" bbt="1|1|0"/></Tempos><Meters><Meter note-value="${den}" divisions-per-bar="${num}" sclock="0" quarters="0:0" bbt="1|1|0"/></Meters><MusicTimes/></TempoMap></Session>`);
 assert.equal(inspectSession(xml(64,127,64)).meters[0].numerator,127);
 for(const args of [[128,4,4],[4,128,4],[4,255,4],[4,4,128]])assert.throws(()=>inspectSession(xml(...args)),e=>e.code==='MAP_NUMBER');
});
