#!/usr/bin/env python3
"""Production MIDI into the unchanged native GUI importer, synthetic files only."""
from pathlib import Path
import importlib.util,json,shutil,subprocess,traceback,xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ui=module('native_ui',HERE/'gui-probe.py')
oracle=module('full_oracle',HERE/'verify-full.py')
ART,ROOT,PROJECT=ui.ART,ui.ROOT,ui.PROJECT

def query_script(mode,import_file):
    prefix=''
    if import_file:
        path=ROOT/('conductor.mid' if mode=='positive' else f'{mode}.mid')
        assert path.is_file()
        prefix=f"""local files=C.StringVector()
files:push_back('{path}')
Editor:do_import(files, Editing.ImportDistinctFiles, Editing.ImportAsTrack, ARDOUR.SrcQuality.SrcBest, ARDOUR.MidiTrackNameSource.SMFFileAndTrackName, ARDOUR.MidiTempoMapDisposition.SMFTempoUse, Temporal.timepos_t(0), ARDOUR.PluginInfo(), ARDOUR.Track(), false)
"""
    # Fixed coordinates are independent of the converter's returned model.
    return prefix+"""local map=Temporal.TempoMap.read()
local ticks={0,1,15360,15361,26880,26881,30720,30721,32640,32641,38400,38401,53760,53761,61440}
for _,tick in ipairs(ticks) do
 local p=Temporal.timepos_t.from_ticks(tick)
 print('NATIVE_TICK '..tick..' TEMPO '..map:quarters_per_minute_at(p)..' METER '..map:meter_at(p):divisions_per_bar()..'/'..map:meter_at(p):note_value())
end
assert(Session:save_state('',false,false,false,false,false)==0)
print('BEATCOURIER_FULL_NATIVE_SAVED')
"""
def launch(mode,reloaded=False):
    label=mode+('-reloaded' if reloaded else '-import')
    log_path=ART/f'{label}.log';log=log_path.open('w')
    args=['/usr/bin/ardour','-a','-d','-n','-P',str(ROOT/'target/Target.ardour')]
    proc=subprocess.Popen(args,env=ui.env,stdout=log,stderr=subprocess.STDOUT)
    try:
        ui.prepare_gui(proc,label)
        queries=ui.run_lua(query_script(mode,not reloaded),label,lambda out:oracle.inspect_queries(out,mode))
        current=ROOT/'target/Target.ardour';shutil.copyfile(current,ART/f'{label}.ardour')
        values=oracle.inspect_native(current,mode,reloaded=reloaded)
        rejected=False
        if mode!='positive':
            try:oracle.inspect_native(current,reloaded=reloaded)
            except AssertionError:rejected=True
            assert rejected,'Deliberate native fault did not reject the positive expectation'
        code=ui.normal_exit(proc,label);log.flush()
        text=log_path.read_text();assert not any(s in text for s in ['Segmentation fault','Aborted (core dumped)','Assertion failed'])
        diagnostics=[line for line in text.splitlines() if 'CRITICAL' in line or 'WARNING' in line]
        return {'label':label,'normalExit':code,'nativeMap':values,'nativeQueries':queries,'positiveOracleRejected':rejected,'nonfatalDiagnosticLines':diagnostics,'arguments':args}
    except Exception:
        ui.snapshot(f'{label}-failure');raise
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
        log.close()
def main():
    version=ui.command('/usr/bin/ardour8-lua','-V');(ART/'native-version.txt').write_text(version);assert '8.12' in version
    with (ART/'full-native-author.log').open('w') as log:
        subprocess.run(['/usr/bin/ardour8-lua',str(HERE/'author-full.lua')],env=ui.env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
    source=ROOT/'source/Source.ardour';fractional=ROOT/'fractional/Fractional.ardour';target=ROOT/'target/Target.ardour'
    for name,path in [('native-authored-source',source),('native-authored-fractional',fractional),('native-target-before',target)]:shutil.copyfile(path,ART/f'{name}.ardour')
    hashes={str(p):ui.sha(p) for p in [source,fractional]}
    original=oracle.inspect_native(source,source=True);oracle.inspect_native(target,initial=True)
    # The rejection input really contains a native-produced half-quarter point.
    fractional_map=ET.parse(fractional).getroot().find('TempoMap')
    assert [n.attrib['quarters'] for n in fractional_map.find('Tempos')].count('15:960')==1
    assert len(fractional_map.find('MusicTimes'))==0
    subprocess.run(['node',str(HERE/'convert-fixture.mjs')],env=ui.env,check=True,timeout=30)
    midi=oracle.prepare_controls(ROOT,ART)
    receipt=json.loads((ART/'conversion-receipt.json').read_text())
    accounting=oracle.inspect_receipt(receipt,source,ROOT/'conductor.mid')
    shutil.copytree(ROOT/'target',ROOT/'target-pristine')
    ui.initialize_profile();ui.expose_disposable_dummy_backend()
    results=[]
    for mode in ['positive','tempo-fault','meter-fault','position-fault']:
        if mode!='positive':
            assert (ROOT/'target').resolve()==ROOT/'target' and not (ROOT/'target').is_symlink()
            shutil.rmtree(ROOT/'target');shutil.copytree(ROOT/'target-pristine',ROOT/'target')
            assert ui.sha(ROOT/'target/Target.ardour')==ui.sha(ART/'native-target-before.ardour')
        results.append(launch(mode));results.append(launch(mode,True))
    assert all(ui.sha(Path(path))==h for path,h in hashes.items()),'Original native source bytes changed'
    (ART/'full-native-report.json').write_text(json.dumps({'status':'PRODUCTION_CONVERTER_NATIVE_ACCEPTED','productUI':'NOT_IMPLEMENTED','consumer':'Authenticated Debian Ardour8.12.0+ds-1','fixtureAuthoring':'Official native Lua TempoMap API','inputSourceSha256':ui.sha(source),'fractionalSourceSha256':ui.sha(fractional),'source':original,'midi':midi,'receiptAccounting':accounting,'cases':results,'precision':'Exact whole-quarter/tick positions; tempo microseconds rounded with explicit receipt. Q28 wall-clock drift is272 native superclocks for the positive fixture.','logCaveat':'Normal exits are required. Nonfatal GTK/GObject diagnostics are retained; no error-free-log claim.'},indent=2)+'\n')
try:main()
except Exception:
    for name,path in [('failed-source',ROOT/'source/Source.ardour'),('failed-target',ROOT/'target/Target.ardour')]:
        if path.is_file() and path.stat().st_size<4*1024*1024:shutil.copyfile(path,ART/f'{name}.ardour')
    (ART/'full-failure.txt').write_text(traceback.format_exc());raise
