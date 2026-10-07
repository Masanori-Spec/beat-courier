#!/usr/bin/env python3
"""Actual packaged Ardour GUI/Lua API, fixed synthetic files only. No product UI."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, shutil, subprocess, time, traceback
from fractions import Fraction
import pyatspi

PROJECT=Path(__file__).resolve().parents[1]; ART=PROJECT/'artifacts/native'; ROOT=Path('/tmp/beatcourier-native')
assert (ART/'package-pin.json').is_file()
for name in ['config','cache','data','empty-plugins']:(ROOT/name).mkdir()
env=os.environ.copy()
env.update(XDG_CONFIG_HOME=str(ROOT/'config'),XDG_CACHE_HOME=str(ROOT/'cache'),XDG_DATA_HOME=str(ROOT/'data'),GTK_MODULES='gail:atk-bridge',LANG='C.UTF-8',LANGUAGE='en')
for key in ['LADSPA_PATH','LV2_PATH','VST_PATH','VST3_PATH','LXVST_PATH']:env[key]=str(ROOT/'empty-plugins')
spec=importlib.util.spec_from_file_location('oracle',PROJECT/'scripts/verify-probe.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
def command(*args):return subprocess.run(args,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,env=env).stdout
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def walk(node,budget,depth=0):
    if depth>30 or budget[0]<=0:return
    budget[0]-=1;yield node,depth
    try:count=min(node.childCount,budget[0])
    except Exception:return
    for i in range(count):
        if budget[0]<=0:break
        try:child=node[i]
        except Exception:continue
        if child is not None:yield from walk(child,budget,depth+1)
def nodes(scope=None):return list(walk(scope or pyatspi.Registry.getDesktop(0),[10000]))
def rect(n):
    try:r=n.queryComponent().getExtents(pyatspi.DESKTOP_COORDS);return [r.x,r.y,r.width,r.height]
    except Exception:return None
def visible(n):
    try:return n.getState().contains(pyatspi.STATE_SHOWING)
    except Exception:return False
def snapshot(label):
    rows=[]
    for n,depth in nodes():
        try:
            row={'depth':depth,'role':n.getRoleName(),'name':n.name,'description':n.description,'rect':rect(n),'showing':visible(n),'states':[str(s) for s in n.getState().getStates()]}
            try:
                t=n.queryText();row['text']=t.getText(0,min(t.characterCount,12000))
            except Exception:pass
            rows.append(row)
        except Exception:pass
    (ART/f'{label}-tree.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    command('scrot',str(ART/f'{label}.png'));return rows
def matching(name,roles=None,scope=None):
    found=[];seen=set()
    for n,_ in nodes(scope):
        try:
            if visible(n) and n.name==name and (roles is None or n.getRoleName() in roles):
                key=(n.getRoleName(),n.name,tuple(rect(n) or []))
                if key not in seen:found.append(n);seen.add(key)
        except Exception:pass
    return found
def one(name,roles=None,scope=None,seconds=15):
    end=time.monotonic()+seconds;found=[]
    while time.monotonic()<end:
        found=matching(name,roles,scope)
        if len(found)==1:return found[0]
        time.sleep(.25)
    raise AssertionError(f'Expected one native control {name!r}, found {len(found)}')
def click(n):
    r=rect(n);assert r and r[2]>0 and r[3]>0
    x,y=r[0]+r[2]//2,r[1]+r[3]//2;assert 0<=x<1600 and 0<=y<1000
    command('xdotool','mousemove',str(x),str(y));command('xdotool','click','1');time.sleep(.5)
def paste(text):
    subprocess.run(['xclip','-selection','clipboard'],input=text,text=True,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,env=env)
    command('xdotool','key','--clearmodifiers','ctrl+a');command('xdotool','key','--clearmodifiers','ctrl+v');time.sleep(.3)
def frames():
    result=[]
    for n,_ in nodes():
        try:
            if visible(n) and n.getRoleName() in ['frame','dialog']:result.append(n)
        except Exception:pass
    return result
def initialize_profile():
    # The unmodified first-run wizard forces new-session setup, even when a
    # session was passed on the command line. Complete its defaults, quit that
    # dialog normally, then use the existing native-authored target on launch.
    log=(ART/'first-run.log').open('w')
    proc=subprocess.Popen(['/usr/bin/ardour','-a','-d','-n','-P'],env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        for step in range(40):
            assert proc.poll() is None,'First-run native process exited unexpectedly'
            time.sleep(1);rows=snapshot(f'first-run-{step:02d}')
            text='\n'.join(r['name']+'\n'+r.get('text','') for r in rows if r['showing'])
            dialogs=[n for n in frames() if n.name=='Session Setup']
            if len(dialogs)==1:
                click(one('Quit',['push button'],scope=dialogs[0]))
                assert proc.wait(timeout=20)==0,'First-run normal quit failed'
                return
            if 'Ardour is ready for use' in text:
                click(one('Apply',['push button']));continue
            if 'is a digital audio workstation' in text or 'Where would you like new' in text:
                click(one('Forward',['push button']));continue
        raise AssertionError('Unexpected first-run page; no unknown dialog accepted')
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
        log.close()
def prepare_gui(proc,label):
    end=time.monotonic()+70
    for step in range(30):
        assert proc.poll() is None,'Official native process exited during startup'
        time.sleep(1)
        snapshot(f'{label}-startup-{step:02d}')
        if matching('Audio System:',['label']):
            combos=[]
            for n,_ in nodes():
                try:
                    if visible(n) and n.getRoleName()=='combo box':combos.append(n)
                except Exception:pass
            # Native label geometry identifies its adjacent combo, not a guessed
            # screen coordinate or a hardware backend chosen by default.
            label_rect=rect(one('Audio System:',['label']))
            candidates=[n for n in combos if rect(n) and abs(rect(n)[1]-label_rect[1])<30 and rect(n)[0]>label_rect[0]]
            assert len(candidates)==1,'Audio backend control ambiguous'
            click(candidates[0]);click(one('None (Dummy)'))
            snapshot(f'{label}-dummy-selected')
            click(one('Start'));continue
        if matching('Window',['menu'] ) or matching('Window',['menu item']):return
        if time.monotonic()>end:break
    raise AssertionError('Native editor did not reach the source-confirmed menu state; inspect startup evidence')
def lua_window():
    click(one('Window',['menu','menu item']));click(one('Scripting',['menu item']))
    end=time.monotonic()+15
    while time.monotonic()<end:
        candidates=[n for n in frames() if 'Lua' in n.name]
        if len(candidates)==1:return candidates[0]
        time.sleep(.25)
    raise AssertionError('Native Lua window not exposed')
def run_lua(script,label):
    frame=lua_window();snapshot(f'{label}-lua-before')
    editable=[]
    for n,_ in nodes(frame):
        try:
            if visible(n) and n.getState().contains(pyatspi.STATE_EDITABLE) and n.getRoleName() in ['text','entry']:editable.append(n)
        except Exception:pass
    assert len(editable)==1,f'Expected one actual Lua editor, found {len(editable)}'
    click(editable[0]);paste(script);click(one('Run',scope=frame));time.sleep(2)
    snapshot(f'{label}-lua-result')
    outputs=set()
    for n,_ in nodes(frame):
        try:
            if visible(n) and not n.getState().contains(pyatspi.STATE_EDITABLE):
                t=n.queryText();value=t.getText(0,min(t.characterCount,12000))
                if re.search(r'^NATIVE_Q ',value,re.M):outputs.add(value)
        except Exception:pass
    assert len(outputs)==1,'Expected one distinct native read-only Lua output buffer'
    output=outputs.pop();(ART/f'{label}-lua-output.txt').write_text(output)
    lines=output.splitlines(); observed=[]
    for line in lines:
        if line.startswith('NATIVE_Q '):
            match=re.fullmatch(r'NATIVE_Q ([0-9]+) TEMPO ([0-9]+(?:\.[0-9]+)?) METER ([0-9]+)/4',line)
            assert match,'Malformed actual native query output'
            observed.append((int(match[1]),Fraction(match[2]),int(match[3])))
    expected=[(0,Fraction(120),4),(7,Fraction(120),4),(8,Fraction(100),4),(15,Fraction(100),4),(16,Fraction(150),3),(24,Fraction(150),3)]
    assert observed==expected,'Actual in-process native query lines differ from literal expectations'
    assert lines.count('BEATCOURIER_NATIVE_MAP_OK')==1 and lines.count('> OK')==1,'Standalone native completion required'
    command('xdotool','key','--clearmodifiers','Alt+F4');time.sleep(.5)
    return [{'quarter':q,'quarterNotesPerMinute':str(tempo),'meter':[meter,4]} for q,tempo,meter in observed]
def query_script(import_file):
    prefix=''
    if import_file:
        prefix="""local files=C.StringVector()
files:push_back('/tmp/beatcourier-native/conductor.mid')
Editor:do_import(files, Editing.ImportDistinctFiles, Editing.ImportAsTrack, ARDOUR.SrcQuality.SrcBest, ARDOUR.MidiTrackNameSource.SMFFileAndTrackName, ARDOUR.MidiTempoMapDisposition.SMFTempoUse, Temporal.timepos_t(0), ARDOUR.PluginInfo(), ARDOUR.Track(), false)
"""
    return prefix+"""local map=Temporal.TempoMap.read()
local positions={0,7,8,15,16,24}
local tempos={120,120,100,100,150,150}
local meters={4,4,4,4,3,3}
for i,q in ipairs(positions) do
 local p=Temporal.timepos_t.from_ticks(q*1920)
 assert(math.abs(map:quarters_per_minute_at(p)-tempos[i])<0.000001)
 assert(map:meter_at(p):divisions_per_bar()==meters[i])
 assert(map:meter_at(p):note_value()==4)
 print('NATIVE_Q '..q..' TEMPO '..map:quarters_per_minute_at(p)..' METER '..meters[i]..'/4')
end
assert(Session:save_state('',false,false,false,false,false)==0)
print('BEATCOURIER_NATIVE_MAP_OK')
"""
def normal_exit(proc,label):
    command('xdotool','key','--clearmodifiers','ctrl+q');time.sleep(1)
    snapshot(f'{label}-exit')
    # Saved synthetic session should need no discard confirmation. Unknown
    # warnings remain a failed diagnostic instead of a generic affirmative click.
    code=proc.wait(timeout=25);assert code==0,f'Native exit code {code}'
    return code
def launch(label,import_file):
    log_path=ART/f'{label}.log';log=log_path.open('w')
    args=['/usr/bin/ardour','-a','-d','-n','-P',str(ROOT/'target/Target.ardour')]
    proc=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        prepare_gui(proc,label);native_queries=run_lua(query_script(import_file),label)
        values=oracle.inspect(ROOT/'target/Target.ardour')
        shutil.copyfile(ROOT/'target/Target.ardour',ART/f'{label}.ardour')
        exit_code=normal_exit(proc,label);log.flush()
        text=log_path.read_text();assert not any(x in text for x in ['Segmentation fault','Aborted (core dumped)','Assertion failed'])
        return {'label':label,'normalExit':exit_code,'actualNativeMap':values,'actualNativeQueries':native_queries,'arguments':args}
    except Exception:
        snapshot(f'{label}-failure');raise
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
        log.close()
try:
    version=command('/usr/bin/ardour8-lua','-V');(ART/'native-version.txt').write_text(version)
    assert '8.12' in version,'Actual installed native version differs'
    with (ART/'native-author.log').open('w') as log:
        subprocess.run(['/usr/bin/ardour8-lua',str(PROJECT/'scripts/author.lua')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
    source=ROOT/'source/Source.ardour';target=ROOT/'target/Target.ardour'
    shutil.copyfile(source,ART/'native-authored-source.ardour');shutil.copyfile(target,ART/'native-target-before.ardour')
    original_hash=sha(source);source_values=oracle.inspect(source);oracle.inspect(target,True)
    subprocess.run(['python3',str(PROJECT/'scripts/make-probe.py')],env=env,check=True,timeout=20)
    initialize_profile()
    imported=launch('native-import',True);reloaded=launch('native-reloaded',False)
    assert sha(source)==original_hash,'Native source fixture changed'
    (ART/'probe-report.json').write_text(json.dumps({'status':'METADATA_ONLY_NATIVE_IMPORT_ACCEPTED','productConverter':'NOT_IMPLEMENTED','productUI':'NOT_IMPLEMENTED','consumer':'Authenticated Debian Ardour 8.12.0+ds-1','fixtureAuthoring':'Official native Lua TempoMap API','fileImport':'Unchanged GUI PublicEditor::do_import via official Lua binding, SMFTempoUse, empty instrument pointer','sourceSha256':original_hash,'source':source_values,'import':imported,'freshProcessReload':reloaded},indent=2)+'\n')
except Exception:
    # Preserve only the two fixed synthetic session files, even if a new native
    # schema makes the oracle fail before normal copies have been recorded.
    for name,path in [('failed-source',ROOT/'source/Source.ardour'),('failed-target',ROOT/'target/Target.ardour')]:
        if path.is_file() and path.stat().st_size<4*1024*1024:shutil.copyfile(path,ART/f'{name}.ardour')
    (ART/'failure.txt').write_text(traceback.format_exc());raise
