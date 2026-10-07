import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeConductor,vlq} from '../src/midi.mjs';
const fixture=()=>({tempos:[{quarter:0n,npm:'120',noteType:4},{quarter:8n,npm:'100',noteType:4},{quarter:16n,npm:'150',noteType:4}],meters:[{quarter:0n,numerator:4,denominator:4},{quarter:16n,numerator:3,denominator:4}]});
test('literal conductor bytes with EOT one quarter after final change',()=>{
  const result=encodeConductor(fixture());
  const expected='4d546864000000060000000107804d54726b0000002c00ff510307a12000ff580404021808f800ff51030927c0f800ff5103061a8000ff5804030218088f00ff2f00';
  assert.equal(Buffer.from(result.bytes).toString('hex'),expected);
  assert.equal(result.endTick,'32640');assert.equal(result.review.length,5);assert.equal(result.noteEvents,0);
});
test('VLQ boundary literals and overflow rejection',()=>{
  assert.deepEqual(vlq(127n),[127]);assert.deepEqual(vlq(128n),[129,0]);assert.deepEqual(vlq(268435455n),[255,255,255,127]);assert.throws(()=>vlq(268435456n));
});
test('missing initial, duplicate positions and fractional quarters reject',()=>{
  const a=fixture();a.tempos[0].quarter=1n;assert.throws(()=>encodeConductor(a));
  const b=fixture();b.tempos[1].quarter=0n;assert.throws(()=>encodeConductor(b));
  const c=fixture();c.tempos[1].quarter=15.5;assert.throws(()=>encodeConductor(c));
});
test('unrepresentable event gap and meter reject',()=>{
  const a=fixture();a.tempos[2].quarter=1000000n;assert.throws(()=>encodeConductor(a));
  const b=fixture();b.meters[1].denominator=3;assert.throws(()=>encodeConductor(b));
});
