import {build} from 'esbuild';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {decodeBytes,decodeUTF8} from '../web/embedded.mjs';
const worker=await build({entryPoints:['web/worker.mjs'],bundle:true,write:false,format:'iife',target:'es2022',minify:true,legalComments:'inline'});
const sample=await readFile('test/fixtures/expanded-native.ardour');
const worker64=Buffer.from(worker.outputFiles[0].contents).toString('base64'),sample64=sample.toString('base64');
if(!Buffer.from(decodeBytes(sample64)).equals(sample)||!Buffer.from(decodeUTF8(worker64),'utf8').equals(Buffer.from(worker.outputFiles[0].contents)))throw Error('Embedded worker/sample byte identity failed');
// HTML tokenization precedes JavaScript parsing. Nested parser comment strings
// plus the native XML's <Script> element can swallow the real closing script.
// Base64 keeps both embedded payloads out of HTML script-tokenizer states.
const app=await build({entryPoints:['web/app.mjs'],bundle:true,write:false,format:'iife',target:'es2022',minify:true,legalComments:'inline',define:{WORKER_BASE64:JSON.stringify(worker64),SAMPLE_BASE64:JSON.stringify(sample64)}});
const js=app.outputFiles[0].text.replace(/<\/script/gi,'<\\/script');
if(/<!--|<\/?script/i.test(js))throw Error('Unsafe HTML script-tokenizer sequence in the inline app');
const css=await readFile('web/styles.css','utf8'),notices=await readFile('THIRD_PARTY_NOTICES.txt','utf8');
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const html=(await readFile('web/index.html','utf8')).replace('/* APP_CSS */',()=>css).replace('/* THIRD_PARTY */',()=>escape(notices)).replace('/* APP_JS */',()=>js);
if(/\/\* (APP_CSS|THIRD_PARTY|APP_JS) \*\//.test(html))throw Error('Unfilled standalone template');
await mkdir('dist',{recursive:true});await writeFile('dist/beat-courier.html',html);console.log('Standalone HTML',Buffer.byteLength(html),'bytes');
