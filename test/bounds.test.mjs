import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {inspectSession,convertSession} from '../src/session.mjs';
const original=fs.readFileSync(new URL('./fixtures/native-authored.ardour',import.meta.url),'utf8');
const bytes=s=>new TextEncoder().encode(s);
const mutation=(a,b)=>{assert.ok(original.includes(a));return bytes(original.replace(a,b));};
test('selected map schema rejects duplicate containers, unexpected attributes and child content',()=>{
 for(const [a,b] of [['<Tempos>','<Tempos extra="1">'],['<MusicTimes/>','<MusicTimes/><MusicTimes/>'],['omega="0"','omega="0" unsupported="x"'],['<MusicTimes/>','<MusicTimes>meaningful</MusicTimes>'],['<MusicTimes/>','<MusicTimes><![CDATA[x]]></MusicTimes>']])assert.throws(()=>inspectSession(mutation(a,b)));
});
test('native positions reject missing origin, duplicate points and unordered clocks',()=>{
 for(const [a,b] of [['quarters="0:0"','quarters="1:0"'],['quarters="8:0"','quarters="0:0"'],['quarters="8:0"','quarters="1000001:0"'],['quarters="8:0"','quarters="8:1920"'],['sclock="1128960000"','sclock="0"']])assert.throws(()=>inspectSession(mutation(a,b)));
});
test('XML depth, element count, attributes and namespace forms are bounded',()=>{
 for(const s of ['<Session>'+ '<x>'.repeat(64)+'</x>'.repeat(64)+'</Session>','<Session>'+'<x/>'.repeat(30000)+'</Session>','<Session '+Array.from({length:65},(_,i)=>`a${i}="x"`).join(' ')+'/>','<Session xmlns="urn:x"/>','<x:Session/>','<Session version="7003" version="7003"/>'])assert.throws(()=>inspectSession(bytes(s)));
});
test('adversarial comment/CDATA/reference scans finish within the file bound',()=>{
 const start=performance.now();
 for(const s of ['<Session><!--'+'<?xml '.repeat(500000)+'--></Session>','<Session><![CDATA['+'<'.repeat(3000000)+'</Session>','<Session a="'+'x'.repeat(3000000),'<Session>&#x110000;</Session>','<Session>&#xD800;</Session>','<Session>&#xFFFE;</Session>'])assert.throws(()=>inspectSession(bytes(s)));
 assert.ok(performance.now()-start<4000);
});
test('legal XML character references remain inert and source bytes are unchanged',()=>{
 const input=bytes(original.replace('<MusicTimes/>','<!--&external; is only comment text--><MusicTimes/>').replace('npm="120"','npm="&#49;20"'));
 const before=input.slice();assert.equal(convertSession(input).review[0].microseconds,500000);assert.deepEqual(input,before);
});
test('whole-quarter scope does not silently accept off-bar meter changes',()=>{
 const input=mutation('<Meter note-value="4" divisions-per-bar="3" sclock="2483712000" quarters="16:0" bbt="5|1|0"/>','<Meter note-value="4" divisions-per-bar="3" sclock="2314368000" quarters="15:0" bbt="4|4|0"/>');
 // Exact source clock at q15 is4s+7*0.6s; ensure the geometry guard is reached.
 assert.throws(()=>inspectSession(input),e=>e.code==='METER_BOUNDARY');
});
