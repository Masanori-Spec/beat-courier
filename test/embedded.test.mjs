import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeBytes,decodeUTF8} from '../web/embedded.mjs';
test('embedded UTF-8 payloads preserve non-Latin text and HTML tokenizer sentinels',()=>{
 const text="const text='日本語 π 𝄞'; /* <!-- <Script> </script> */",bytes=Buffer.from(text,'utf8'),encoded=bytes.toString('base64');
 assert.deepEqual(Buffer.from(decodeBytes(encoded)),bytes);assert.equal(decodeUTF8(encoded),text);assert.deepEqual(Buffer.from(decodeUTF8(encoded),'utf8'),bytes);
});
test('sample bytes preserve BOM and line endings; malformed worker UTF-8 rejects',()=>{
 const bytes=Buffer.from([239,187,191,60,83,101,115,115,105,111,110,47,62,13,10]);assert.deepEqual(Buffer.from(decodeBytes(bytes.toString('base64'))),bytes);
 assert.throws(()=>decodeUTF8(Buffer.from([255,254]).toString('base64')));
});
