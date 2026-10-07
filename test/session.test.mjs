import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {inspectSession,convertSession} from '../src/session.mjs';
const original=fs.readFileSync(new URL('./fixtures/native-authored.ardour',import.meta.url));
const hash=b=>createHash('sha256').update(b).digest('hex');
const input=s=>new TextEncoder().encode(s);
const changed=(from,to)=>input(original.toString('utf8').replace(from,to));
test('actual native-authored7003 fixture maps every literal point without touching input',()=>{
  const before=hash(original),result=convertSession(original);
  assert.equal(hash(original),before);
  assert.deepEqual(result.review.map(r=>[r.kind,r.quarter,r.tick]),[['tempo','0','0'],['meter','0','0'],['tempo','8','15360'],['tempo','16','30720'],['meter','16','30720']]);
  assert.equal(Buffer.from(result.bytes).toString('hex'),'4d546864000000060000000107804d54726b0000002c00ff510307a12000ff580404021808f800ff51030927c0f800ff5103061a8000ff5804030218088f00ff2f00');
});
test('fractional15.5 rejects, never rounds',()=>{
  assert.throws(()=>inspectSession(changed('quarters="16:0"','quarters="15:960"')),e=>e.code==='FRACTIONAL_POSITION');
});
test('ramp metadata and MusicTimes reject',()=>{
  for(const [from,to] of [['enpm="100"','enpm="110"'],['omega="0"','omega="0.1"'],['type="Constant"','type="Ramped"'],['continuing="0"','continuing="1"'],['<MusicTimes/>','<MusicTimes><MusicTime/></MusicTimes>']]){
    assert.ok(original.includes(from),from);assert.throws(()=>inspectSession(changed(from,to)));
  }
});
test('malformed or unsupported XML never reaches external resources',()=>{
  for(const s of ['<!DOCTYPE Session SYSTEM "https://example.invalid/x"><Session/>','<?xml-stylesheet href="https://example.invalid/x"?><Session/>','<Session>&#0;</Session>','<Session>\u0000</Session>','<Session><x></Session>'])assert.throws(()=>inspectSession(input(s)));
  assert.throws(()=>inspectSession(new Uint8Array([0xff,0xfe,0,0])));
  assert.throws(()=>inspectSession(changed('version="1.0"','version="1.1"')));
});
test('wrong session version, duplicate map and unsupported clock reject',()=>{
  assert.throws(()=>inspectSession(changed('version="7003"','version="7002"')));
  assert.throws(()=>inspectSession(changed('</Session>','<TempoMap/></Session>')));
  assert.throws(()=>inspectSession(changed('282240000','282240001')));
  assert.throws(()=>inspectSession(changed('1128960000','1128960001')),e=>e.code==='MAP_CLOCK');
  assert.throws(()=>inspectSession(changed('bbt="3|1|0"','bbt="3|2|0"')),e=>e.code==='MAP_BBT');
});
test('XML scan rejects malformed full-size input in bounded time',()=>{
  const start=performance.now();assert.throws(()=>inspectSession(input('<'.repeat(4*1024*1024))));
  assert.ok(performance.now()-start<2000,'Deterministic scan must reject within2seconds');
  assert.throws(()=>inspectSession(new Uint8Array(4*1024*1024+1)));
});
