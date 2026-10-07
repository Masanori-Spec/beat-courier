#!/usr/bin/env python3
"""Route original browser downloads only; never regenerate the positive MIDI."""
from pathlib import Path
import hashlib,importlib.util,json,shutil
project=Path(__file__).resolve().parents[1];base=project/'downloaded-browser/artifacts/browser';art=project/'artifacts/native';root=Path('/tmp/beatcourier-native')
sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads((base/'browser-report.json').read_text());assert report['status']=='PASS'
for key in ['pageErrors','consoleErrors','networkRequests']:assert report[key]==[]
commands=report['chromiumMainProcessCommands'];assert commands and all('--no-sandbox' not in c and '--disable-setuid-sandbox' not in c for c in commands)
shipped=(project/'dist/beat-courier.html').read_bytes();assert shipped==(project/'downloaded-browser/dist/beat-courier.html').read_bytes() and sha(shipped)==report['shippedHTMLSHA256']
source=(root/'source/Source.ardour').read_bytes();fractional=(root/'fractional/Fractional.ardour').read_bytes()
assert source==(project/'test/fixtures/expanded-native.ardour').read_bytes()==(base/'source-input.ardour').read_bytes()
assert fractional==(project/'test/fixtures/fractional-native.ardour').read_bytes()==(base/'fractional-input.ardour').read_bytes()
midi=(base/'conductor.mid').read_bytes();receipt_bytes=(base/'receipt.json').read_bytes();receipt=json.loads(receipt_bytes)
assert receipt['tool']=='BeatCourier' and receipt['version']=='0.1.0' and receipt['exportOrigin']=='browser UI download'
assert receipt['nativeProfile']=='Ardour8.12 whole-quarter stepped map'
assert receipt['sourceFile']=={'name':'private-session.ardour','bytes':len(source)} and receipt['outputBytes']==len(midi)
assert report['downloads']['primary']=={'sha256':sha(midi),'bytes':len(midi),'receiptSHA256':sha(receipt_bytes)}
assert (base/'repeated-conductor.mid').read_bytes()==midi and (base/'repeated-receipt.json').read_bytes()==receipt_bytes
assert (base/'sample-conductor.mid').read_bytes()==midi
spec=importlib.util.spec_from_file_location('oracle',project/'scripts/verify-full.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
o.inspect_midi(base/'conductor.mid');o.inspect_receipt(receipt,root/'source/Source.ardour',base/'conductor.mid')
rejected=report['rejections'];assert any(r['name']=='native fractional15.5' and r['code']=='FRACTIONAL_POSITION' and r['sha256']==sha(fractional) for r in rejected)
for code in ['RAMP','MAP_STRUCTURE','MAP_BBT','TEMPO_RANGE','XML_DOCTYPE','INPUT_LIMIT']:assert any(r['code']==code for r in rejected)
(root/'conductor.mid').write_bytes(midi);(art/'conductor.mid').write_bytes(midi);(art/'conversion-receipt.json').write_bytes(receipt_bytes)
(art/'rejection-report.json').write_text(json.dumps(rejected,indent=2)+'\n')
(art/'browser-input-provenance.json').write_text(json.dumps({'origin':'Actual sandboxed offline browser MIDI and receipt, passed unchanged into the accepted eight-case native gate','testedHTMLSHA256':sha(shipped),'sourceSHA256':sha(source),'fractionalSHA256':sha(fractional),'browserMIDISHA256':sha(midi),'browserReceiptSHA256':sha(receipt_bytes),'bytes':len(midi)},indent=2)+'\n')
print('Actual browser MIDI and receipt copied unchanged; no positive regeneration')
