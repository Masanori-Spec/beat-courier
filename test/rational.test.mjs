import test from 'node:test';
import assert from 'node:assert/strict';
import {decimal,text,midiTempo} from '../src/rational.mjs';
test('literal integer tempo encodings',()=>{
  assert.equal(midiTempo('120',4).microseconds,500000);
  assert.equal(midiTempo('100',4).microseconds,600000);
  assert.equal(midiTempo('150',4).microseconds,400000);
  assert.equal(midiTempo('120',8).microseconds,1000000);
});
test('handwritten rational rounding receipts',()=>{
  assert.deepEqual(midiTempo('123',4),{microseconds:487805,exactMicroseconds:'20000000/41',errorMicroseconds:'5/41',sourceQuarterNotesPerMinute:'123',midiQuarterNotesPerMinute:'12000000/97561',rounded:true});
  assert.equal(midiTempo('90',4).microseconds,666667);
  assert.equal(midiTempo('90',4).errorMicroseconds,'1/3');
});
test('decimal math and eighth-note units remain exact',()=>{
  assert.equal(text(decimal('122.500')),'245/2');
  assert.equal(midiTempo('122.5',8).sourceQuarterNotesPerMinute,'245/4');
  assert.equal(midiTempo('122.5',8).exactMicroseconds,'48000000/49');
});
test('invalid and unrepresentable values reject before rounding',()=>{
  for(const value of ['0','-1','NaN','Infinity','1e2','01','0.000000000001','60000001'])assert.throws(()=>midiTempo(value,4));
  for(const note of [0,3,256,Infinity])assert.throws(()=>midiTempo('120',note));
  assert.throws(()=>decimal('1.'.padEnd(1000000,'0')));
});
