#!/usr/bin/env python3
"""Actual packaged Ardour GUI/Lua API, fixed synthetic files only. No product UI."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, shutil, subprocess, time, traceback
import xml.etree.ElementTree as ET
from fractions import Fraction
import pyatspi

PROJECT=Path(__file__).resolve().parents[1]; ART=PROJECT/'artifacts/native'; ROOT=Path('/tmp/beatcourier-native')
assert (ART/'package-pin.json').is_file()
for name in ['config','cache','data','empty-plugins']:(ROOT/name).mkdir()
env=os.environ.copy()
env.update(XDG_CONFIG_HOME=str(ROOT/'config'),XDG_CACHE_HOME=str(ROOT/'cache'),XDG_DATA_HOME=str(ROOT/'data'),GTK_MODULES='gail:atk-bridge',LANG='C.UTF-8',LANGUAGE='en')
for key in ['LADSPA_PATH','LV2_PATH','VST_PATH','VST3_PATH','LXVST_PATH']:env[key]=str(ROOT/'empty-plugins')
spec=importlib.util.spec_from_file_location('oracle',PROJECT/'scripts/verify-probe.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
pspec=importlib.util.spec_from_file_location('pixels',PROJECT/'scripts/pixel-controls.py');pixels=importlib.util.module_from_spec(pspec);pspec.loader.exec_module(pixels)
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
def native_windows():
    result=subprocess.run(['xdotool','search','--onlyvisible','--name','Ardour|Session Setup|Lua'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env=env)
    assert result.returncode in [0,1]
    ids=result.stdout.splitlines();assert len(ids)<50
    return [{'id':w,'name':command('xdotool','getwindowname',w)} for w in ids]
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
    (ART/f'{label}-windows.json').write_text(json.dumps(native_windows(),indent=2)+'\n')
    command('scrot',str(ART/f'{label}.png'));return rows
def pixel_state(label):
    snapshot(label);return pixels.read_pixels(ART/f'{label}.png')
def click_box(r):
    x,y=round(r[0]+r[2]/2),round(r[1]+r[3]/2)
    assert r[2]>0 and r[3]>0 and 0<=x<1600 and 0<=y<1000
    command('xdotool','mousemove',str(x),str(y));command('xdotool','click','1');time.sleep(.5)
def click_label(words,phrase):click_box(pixels.unique_phrase(words,phrase)['rect'])
def has(words,phrase):return bool(pixels.phrase_matches(words,phrase))
def paste(text):
    subprocess.run(['xclip','-selection','clipboard'],input=text,text=True,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,env=env)
    command('xdotool','key','--clearmodifiers','ctrl+a');command('xdotool','key','--clearmodifiers','ctrl+v');time.sleep(.3)
def clipboard_sentinel(value):
    subprocess.run(['xclip','-selection','clipboard'],input=value,text=True,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,env=env)
def geometry(window):
    raw=command('xdotool','getwindowgeometry','--shell',window)
    data=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    return [int(data[k]) for k in ['X','Y','WIDTH','HEIGHT']]
def initialize_profile():
    # The unmodified first-run wizard forces new-session setup, even when a
    # session was passed on the command line. Complete its defaults, quit that
    # dialog normally, then use the existing native-authored target on launch.
    log=(ART/'first-run.log').open('w')
    proc=subprocess.Popen(['/usr/bin/ardour','-a','-d','-n','-P'],env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        for step in range(12):
            assert proc.poll() is None,'First-run native process exited unexpectedly'
            time.sleep(1);words=pixel_state(f'first-run-{step:02d}')
            setup=any(w['name'].strip()=='Session Setup' for w in native_windows())
            if setup or (has(words,'Session name:') and has(words,'Create session folder in:')):
                click_label(words,'Quit')
                assert proc.wait(timeout=20)==0,'First-run normal quit failed'
                return
            if has(words,'Ardour is ready for use'):
                # R2 pixels show Apply's dotted keyboard-focus ring contaminating
                # its OCR box. Move focus once, then require the same unique
                # high-confidence label before the physical click.
                command('xdotool','key','--clearmodifiers','Tab')
                words=pixel_state(f'first-run-{step:02d}-ready-refocused')
                assert has(words,'Ardour is ready for use')
                click_label(words,'Apply');continue
            if has(words,'Welcome to Ardour') or has(words,'Default folder for new sessions'):
                click_label(words,'Forward');continue
        raise AssertionError('Unexpected first-run page; no unknown dialog accepted')
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=10)
        log.close()
def prepare_gui(proc,label):
    for step in range(20):
        assert proc.poll() is None,'Official native process exited during startup'
        time.sleep(1);words=pixel_state(f'{label}-startup-{step:02d}')
        if has(words,'Audio System:'):
            label_rect=pixels.unique_phrase(words,'Audio System:')['rect']
            current=[]
            for name in ['None (Dummy)','ALSA','PulseAudio','JACK']:
                for match in pixels.phrase_matches(words,name):
                    r=match['rect']
                    if r[0]>label_rect[0]+label_rect[2] and abs(r[1]-label_rect[1])<20:current.append(match)
            assert len(current)==1,'Native audio-backend field is ambiguous'
            if current[0]['text']!='None (Dummy)':
                click_box(current[0]['rect']);words=pixel_state(f'{label}-backend-options');click_label(words,'None (Dummy)')
            words=pixel_state(f'{label}-dummy-selected')
            assert has(words,'None (Dummy)') and has(words,'Normal Speed') and has(words,'Silence'),'Hardware-free native backend defaults not observed'
            click_label(words,'Start');continue
        if has(words,'Window') and has(words,'Session'):return
    raise AssertionError('Native editor did not reach source-confirmed menu state')
def expose_disposable_dummy_backend():
    # Release builds hide this bundled hardware-free backend by default. This
    # single ordinary preference belongs only to the freshly created test XDG
    # profile. It does not change the consumer, importer, sandbox or OS settings.
    path=ROOT/'config/ardour8/config'
    assert path.is_file() and not path.is_symlink() and path.resolve()==path
    before=path.read_bytes();assert len(before)<1024*1024 and b'<!DOCTYPE' not in before and b'<!ENTITY' not in before
    (ART/'test-config-before.xml').write_bytes(before)
    root=ET.fromstring(before);assert root.tag=='Ardour'
    options=root.findall("./Config/Option[@name='hide-dummy-backend']")
    assert len(options)==1 and options[0].attrib.get('value') in ['1','true']
    pattern=rb'(<Option\s+name="hide-dummy-backend"\s+value=")(1|true)("\s*/>)'
    matches=list(re.finditer(pattern,before));assert len(matches)==1,'Native preference form differs'
    match=matches[0];start,end=match.span(2)
    after=before[:start]+b'0'+before[end:]
    assert after[:start]==before[:start] and after[start+1:]==before[end:]
    parsed=ET.fromstring(after);assert parsed.findall("./Config/Option[@name='hide-dummy-backend']")[0].attrib['value']=='0'
    path.write_bytes(after);assert path.read_bytes()==after
    (ART/'test-config-after.xml').write_bytes(after)
    (ART/'test-profile-preference.json').write_text(json.dumps({'path':str(path),'option':'hide-dummy-backend','before':options[0].attrib['value'],'after':'0','purpose':'Expose the already-bundled Dummy backend in the disposable GUI profile','changedByteRange':[start,end],'beforeSha256':hashlib.sha256(before).hexdigest(),'afterSha256':hashlib.sha256(after).hexdigest(),'allOtherBytesUnchanged':True},indent=2)+'\n')
def lua_window(label):
    words=pixel_state(f'{label}-editor-menu');click_label(words,'Window')
    words=pixel_state(f'{label}-window-menu');click_label(words,'Scripting')
    time.sleep(.5)
    windows=command('xdotool','search','--onlyvisible','--name','Lua').splitlines()
    assert len(windows)==1,'Expected exactly one visible native Lua X window'
    window=windows[0];command('xdotool','windowsize',window,'1100','850');command('xdotool','windowmove',window,'200','50')
    command('xdotool','windowactivate',window);time.sleep(.6)
    assert command('xdotool','getactivewindow').strip()==window
    r=geometry(window);assert r[2:]==[1100,850] and r[0]>=0 and r[1]>=0 and r[0]+r[2]<=1600 and r[1]+r[3]<=1000
    return window,r
def run_lua(script,label):
    window,frame=lua_window(label);words=pixel_state(f'{label}-lua-before')
    run=pixels.unique_phrase(words,'Run')['rect'];clear=pixels.unique_phrase(words,'Clear Output')['rect']
    assert abs(run[1]-clear[1])<15 and frame[1]+frame[3]*.5<run[1]<frame[1]+frame[3]*.9
    # The native source places the editable pane above Run/Clear and the
    # noneditable output below. Both actions use observed native geometry.
    click_box([frame[0]+100,frame[1]+40,100,max(20,run[1]-frame[1]-80)])
    paste(script);command('xdotool','key','--clearmodifiers','ctrl+a');command('xdotool','key','--clearmodifiers','ctrl+c')
    assert command('xclip','-selection','clipboard','-o').rstrip('\n')==script.rstrip('\n'),'Actual native editor paste differs'
    click_box(run);time.sleep(2);words=pixel_state(f'{label}-lua-result')
    run=pixels.unique_phrase(words,'Run')['rect'];clear=pixels.unique_phrase(words,'Clear Output')['rect']
    assert abs(run[1]-clear[1])<15
    output_top=run[1]+run[3]+15;output_bottom=frame[1]+frame[3]-20
    assert output_bottom-output_top>80,'Native output pane not fully usable'
    sentinel=f'BEATCOURIER_OUTPUT_PENDING_{label}'
    clipboard_sentinel(sentinel)
    click_box([frame[0]+100,output_top,300,output_bottom-output_top])
    command('xdotool','key','--clearmodifiers','ctrl+a');command('xdotool','key','--clearmodifiers','ctrl+c');time.sleep(.3)
    output=command('xclip','-selection','clipboard','-o')
    assert output!=sentinel and output!=script and 'Editor:do_import' not in output and 'print(' not in output,'Output copy is missing or echoes pasted editor code'
    (ART/f'{label}-lua-output.txt').write_text(output)
    lines=output.splitlines();observed=[]
    for line in lines:
        if line.startswith('NATIVE_Q '):
            match=re.fullmatch(r'NATIVE_Q ([0-9]+) TEMPO ([0-9]+(?:\.[0-9]+)?) METER ([0-9]+)/4',line)
            assert match,'Malformed actual native query output'
            observed.append((int(match[1]),Fraction(match[2]),int(match[3])))
    expected=[(0,Fraction(120),4),(7,Fraction(120),4),(8,Fraction(100),4),(15,Fraction(100),4),(16,Fraction(150),3),(24,Fraction(150),3)]
    assert observed==expected,'Actual in-process native query lines differ from literal expectations'
    assert lines.count('BEATCOURIER_NATIVE_MAP_OK')==1 and lines.count('> OK')==1,'Standalone native completion required'
    snapshot(f'{label}-output-copied')
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
    expose_disposable_dummy_backend()
    imported=launch('native-import',True);reloaded=launch('native-reloaded',False)
    assert sha(source)==original_hash,'Native source fixture changed'
    (ART/'probe-report.json').write_text(json.dumps({'status':'METADATA_ONLY_NATIVE_IMPORT_ACCEPTED','productConverter':'NOT_IMPLEMENTED','productUI':'NOT_IMPLEMENTED','consumer':'Authenticated Debian Ardour 8.12.0+ds-1','fixtureAuthoring':'Official native Lua TempoMap API','fileImport':'Unchanged GUI PublicEditor::do_import via official Lua binding, SMFTempoUse, empty instrument pointer','sourceSha256':original_hash,'source':source_values,'import':imported,'freshProcessReload':reloaded},indent=2)+'\n')
except Exception:
    # Preserve only the two fixed synthetic session files, even if a new native
    # schema makes the oracle fail before normal copies have been recorded.
    for name,path in [('failed-source',ROOT/'source/Source.ardour'),('failed-target',ROOT/'target/Target.ardour')]:
        if path.is_file() and path.stat().st_size<4*1024*1024:shutil.copyfile(path,ART/f'{name}.ardour')
    (ART/'failure.txt').write_text(traceback.format_exc());raise
