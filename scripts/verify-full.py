#!/usr/bin/env python3
"""Independent handwritten native/MIDI oracle; never imports the JS converter."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,re,xml.etree.ElementTree as ET

QUARTERS=[0,8,14,16,20,28]
US=[500000,600000,800000,500000,487805,400000]
SOURCE_SC=[0,1128960000,2145024000,2596608000,3161088000,4262512392]
TARGET_SC=[0,1128960000,2145024000,2596608000,3161088000,4262512664]
BBT=['1|1|0','3|1|0','5|1|0','5|5|0','6|6|0','9|1|0']
METERS=[(0,4,4),(8,3,4),(14,7,8),(28,4,4)]
LITERAL_MIDI=bytes.fromhex('4d546864000000060000000107804d54726b0000005400ff510307a12000ff580404021808f800ff51030927c000ff580403021808da00ff51030c350000ff5804070318089e00ff510307a120bc00ff510307717df800ff5103061a8000ff5804040218088f00ff2f00')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rounded(n):return (2*n.numerator+n.denominator)//(2*n.denominator)
def per_quarter(us):return rounded(F(us)*F(282240000,1000000))
def profile(mode='positive',source=False):
    assert mode in ['positive','tempo-fault','meter-fault','position-fault']
    qs=QUARTERS.copy();us=US.copy();sc=(SOURCE_SC if source else TARGET_SC).copy();bbt=BBT.copy();meters=METERS.copy()
    if mode=='tempo-fault':us[-1]=600000
    if mode=='meter-fault':meters[-1]=(28,5,4)
    if mode=='position-fault':qs[3]=17;sc[3:]=[2822400000,3245760000,4347184664];bbt[3]='5|7|0'
    return qs,us,sc,bbt,meters
def inspect_midi(path,mode='positive'):
    import mido
    if mode=='positive':assert Path(path).read_bytes()==LITERAL_MIDI,'Actual production MIDI differs from handwritten wire bytes'
    midi=mido.MidiFile(path);assert midi.type==0 and midi.ticks_per_beat==1920 and len(midi.tracks)==1
    q,us,_,_,meters=profile(mode);events=[];tick=0;eot_count=0
    assert len(midi.tracks[0])==11,'Exactly ten map events and one end-of-track are required'
    for event in midi.tracks[0]:
        tick+=event.time;assert event.is_meta,'No note/channel events permitted'
        if event.type=='set_tempo':events.append((tick,'tempo',event.tempo))
        elif event.type=='time_signature':
            assert event.clocks_per_click==24 and event.notated_32nd_notes_per_beat==8
            events.append((tick,'meter',event.numerator,event.denominator))
        else:
            eot_count+=1
            assert event.type=='end_of_track' and event is midi.tracks[0][-1] and tick==55680
    expected=[(x*1920,'tempo',u) for x,u in zip(q,us)]+[(x*1920,'meter',n,d) for x,n,d in meters]
    expected.sort(key=lambda x:(x[0],0 if x[1]=='tempo' else 1));assert events==expected,(events,expected)
    assert midi.tracks[0][-1].type=='end_of_track' and eot_count==1
    return {'format':0,'ppqn':1920,'events':events,'endTick':55680,'channelEvents':0,'sha256':digest(path)}
def terminal(music,mode,reloaded):
    assert len(music)==1 and music[0].tag=='MusicTime' and not music.attrib
    node=music[0]
    # Hand-derived from the fixed final bar9 at q28 and native Beats::max.
    bbt='429496732|4|1919' if mode=='meter-fault' else '536870913|3|1919'
    expected={'sclock':'4611686018427387903','quarters':'2147483647:0' if reloaded else '2147483646:1919','bbt':bbt,'name':'<import'}
    assert node.attrib==expected,('terminal',node.attrib,expected)
    assert [n.tag for n in node]==['Tempo','Meter']
    assert node[0].attrib=={'npm':'120','enpm':'120','note-type':'4','type':'Constant','locked-to-meter':'0','continuing':'0','active':'1'}
    assert node[1].attrib=={'note-value':'4','divisions-per-bar':'4'}
    assert all(len(n)==0 for n in node)
    assert all(not(n.text or '').strip() and not(n.tail or '').strip() for n in music.iter())
    return expected
def inspect_native(path,mode='positive',source=False,reloaded=False,initial=False):
    raw=Path(path).read_bytes();assert len(raw)<4*1024*1024 and b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw
    root=ET.fromstring(raw);assert root.tag=='Session' and root.attrib['version']=='7003' and root.attrib['sample-rate']=='48000'
    maps=root.findall('TempoMap');assert len(maps)==1
    tm=maps[0];assert tm.attrib=={'superclocks-per-second':'282240000'}
    assert [n.tag for n in tm]==['Tempos','Meters','MusicTimes']
    q,us,sc,bbt,meters=profile(mode,source)
    if initial:q,us,sc,bbt,meters=q[:1],us[:1],sc[:1],bbt[:1],meters[:1]
    tempo_nodes=list(tm.find('Tempos'));meter_nodes=list(tm.find('Meters'))
    assert len(tempo_nodes)==len(q) and len(meter_nodes)==len(meters)
    observed=[]
    source_notes=[4,4,8,4,4,4];source_durations=[141120000,169344000,112896000,141120000,137678049,112896000]
    for i,(node,x,u,clock,bar) in enumerate(zip(tempo_nodes,q,us,sc,bbt)):
        a=node.attrib;assert node.tag=='Tempo' and len(node)==0
        assert set(a)=={'npm','enpm','note-type','type','locked-to-meter','continuing','active','sclock','quarters','bbt','omega'},a
        assert a['quarters']==f'{x}:0' and int(a['sclock'])==clock and a['bbt']==bar,(a,x,clock,bar)
        assert a['type']=='Constant' and a['continuing']=='0' and a['active']=='1' and a['locked-to-meter']=='0' and F(a['omega'])==0
        assert F(a['npm'])==F(a['enpm'])
        note=source_notes[i] if source else 4;duration=source_durations[i] if source else per_quarter(u)
        assert int(a['note-type'])==note
        assert rounded(F(16934400000)/F(a['npm']))==duration
        assert abs(F(a['npm'])-F(16934400000,duration))<F(1,10**10)
        observed.append({'quarter':x,'sclock':clock,'bbt':bar,'npm':a['npm'],'noteType':note,'superclocksPerTempoNote':duration})
    expected_by_q=dict(zip(q,zip(sc,bbt)))
    for node,(x,n,d) in zip(meter_nodes,meters):
        assert node.tag=='Meter' and len(node)==0
        clock,bar=expected_by_q[x]
        assert node.attrib=={'note-value':str(d),'divisions-per-bar':str(n),'sclock':str(clock),'quarters':f'{x}:0','bbt':bar},node.attrib
    music=tm.find('MusicTimes')
    normalization=None
    if source or initial:assert not music.attrib and len(music)==0
    else:normalization=terminal(music,mode,reloaded)
    assert not any(n.attrib.get('type') in ['lv2','ladspa','vst','lxvst','vst3','au'] for n in root.iter('Processor'))
    assert not any(n.attrib.get('type')=='audio' for n in root.iter('Source'))
    return {'tempos':observed,'meters':meters,'terminalNormalization':normalization,'sourceToTargetClockDeltaAtQ28':0 if source or initial else sc[-1]-SOURCE_SC[-1]}
def query_expectations(mode):
    qs,us,_,_,meters=profile(mode)
    # Each exact boundary and the next native tick, plus interior/end sentinels.
    ticks=[0,1,15360,15361,26880,26881,30720,30721,32640,32641,38400,38401,53760,53761,61440]
    expected=[]
    for tick in ticks:
        i=0
        for j,q in enumerate(qs):
            if q*1920<tick:i=j
        meter=meters[0]
        for candidate in meters:
            if candidate[0]*1920<tick:meter=candidate
        expected.append((tick,F(16934400000,per_quarter(us[i])),meter[1],meter[2]))
    return expected
def inspect_queries(output,mode):
    lines=output.splitlines();observed=[]
    for line in lines:
        if line.startswith('NATIVE_TICK '):
            m=re.fullmatch(r'NATIVE_TICK ([0-9]+) TEMPO ([0-9]+(?:\.[0-9]+)?) METER ([0-9]+(?:\.[0-9]+)?)/([0-9]+(?:\.[0-9]+)?)',line);assert m,line
            observed.append((int(m[1]),F(m[2]),F(m[3]),F(m[4])))
    expected=query_expectations(mode);assert len(observed)==len(expected)
    for actual,want in zip(observed,expected):
        assert actual[0]==want[0] and actual[2:]==want[2:] and abs(actual[1]-want[1])<F(1,10**7),(actual,want)
    assert lines.count('BEATCOURIER_FULL_NATIVE_SAVED')==1 and lines.count('> OK')==1
    return [{'tick':t,'quarterNotesPerMinute':str(v),'meter':[int(n),int(d)]} for t,v,n,d in observed]
def prepare_controls(root,art):
    import mido
    positive=Path(root)/'conductor.mid';baseline=inspect_midi(positive)
    for mode in ['tempo-fault','meter-fault','position-fault']:
        midi=mido.MidiFile(positive);events=[];tick=0
        for e in midi.tracks[0]:
            tick+=e.time;events.append([tick,e.copy()])
        if mode=='tempo-fault':
            match=[e for t,e in events if t==53760 and e.type=='set_tempo'];assert len(match)==1;match[0].tempo=600000
        if mode=='meter-fault':
            match=[e for t,e in events if t==53760 and e.type=='time_signature'];assert len(match)==1;match[0].numerator=5
        if mode=='position-fault':
            match=[row for row in events if row[0]==30720 and row[1].type=='set_tempo'];assert len(match)==1;match[0][0]=32640
        last=0
        for t,e in events:e.time=t-last;last=t
        midi.tracks[0]=mido.MidiTrack([e for _,e in events]);path=Path(root)/f'{mode}.mid';midi.save(path)
        (Path(art)/path.name).write_bytes(path.read_bytes());inspect_midi(path,mode)
        try:inspect_midi(path)
        except AssertionError:pass
        else:raise AssertionError('Fault did not fail positive MIDI expectation')
    # Mido's writer normalizes repeated EOTs, so append a literal extra EOT to
    # the actual fault file and update only its track length for this wire test.
    raw=(Path(root)/'tempo-fault.mid').read_bytes();assert raw[14:18]==b'MTrk'
    length=int.from_bytes(raw[18:22],'big');assert len(raw)==22+length
    malformed=raw[:18]+(length+4).to_bytes(4,'big')+raw[22:]+bytes.fromhex('00ff2f00')
    bad=Path(art)/'wire-rejected-extra-eot.mid';bad.write_bytes(malformed)
    try:inspect_midi(bad,'tempo-fault')
    except AssertionError:pass
    else:raise AssertionError('Repeated EOT was accepted')
    (Path(art)/'wire-rejection-report.json').write_text(json.dumps({'extraEndOfTrackRejected':True,'sha256':digest(bad),'nativeExecution':False},indent=2)+'\n')
    return baseline

def inspect_receipt(receipt,source_path,midi_path):
    assert receipt['sourceSha256']==digest(source_path) and receipt['outputSha256']==digest(midi_path)
    assert receipt['format']==0 and receipt['ppqn']==1920 and receipt['endTick']=='55680' and receipt['noteEvents']==0
    source=ET.parse(source_path).getroot().find('TempoMap')
    expected=[]
    for node,q,u in zip(source.find('Tempos'),QUARTERS,US):
        npm=F(node.attrib['npm']);note=int(node.attrib['note-type']);exact=F(15000000*note)/npm
        expected.append({'kind':'tempo','quarter':str(q),'tick':str(q*1920),'microseconds':u,'exactMicroseconds':str(exact),'errorMicroseconds':str(F(u)-exact),'sourceQuarterNotesPerMinute':str(npm*4/note),'midiQuarterNotesPerMinute':str(F(60000000,u)),'rounded':exact.denominator!=1})
    for q,n,d in METERS:expected.append({'kind':'meter','quarter':str(q),'tick':str(q*1920),'numerator':n,'denominator':d,'clocksPerClick':24,'notated32nds':8})
    expected.sort(key=lambda r:(int(r['quarter']),0 if r['kind']=='tempo' else 1))
    assert receipt['review']==expected,'Every receipt entry must match independent exact rational accounting'
    return {'checkedEntries':len(expected),'positionRounding':False,'positiveClockDriftSuperclocks':272,'positiveClockDriftSeconds':'17/17640000'}
