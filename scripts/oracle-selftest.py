#!/usr/bin/env python3
"""Mutation tests of the independent oracle using explicitly synthetic XML."""
from pathlib import Path
import importlib.util,tempfile,xml.etree.ElementTree as ET
from decimal import Decimal,localcontext
spec=importlib.util.spec_from_file_location('oracle',Path(__file__).with_name('verify-full.py'));o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
def model(mode,source=False,reloaded=False):
    q,us,sc,bbt,meters=o.profile(mode,source)
    root=ET.Element('Session',{'version':'7003','sample-rate':'48000'})
    tm=ET.SubElement(root,'TempoMap',{'superclocks-per-second':'282240000'})
    ts=ET.SubElement(tm,'Tempos');ms=ET.SubElement(tm,'Meters');music=ET.SubElement(tm,'MusicTimes')
    notes=[4,4,8,4,4,4];durations=[141120000,169344000,112896000,141120000,137678049,112896000]
    for i,(x,u,clock,bar) in enumerate(zip(q,us,sc,bbt)):
        duration=durations[i] if source else o.per_quarter(u)
        with localcontext() as context:
            context.prec=17;npm=str(Decimal(16934400000)/Decimal(duration))
        ET.SubElement(ts,'Tempo',{'npm':npm,'enpm':npm,'note-type':str(notes[i] if source else 4),'type':'Constant','locked-to-meter':'0','continuing':'0','active':'1','omega':'0','sclock':str(clock),'quarters':f'{x}:0','bbt':bar})
    coords=dict(zip(q,zip(sc,bbt)))
    for x,n,d in meters:
        clock,bar=coords[x];ET.SubElement(ms,'Meter',{'note-value':str(d),'divisions-per-bar':str(n),'sclock':str(clock),'quarters':f'{x}:0','bbt':bar})
    if not source:
        terminal_bbt='429496732|4|1919' if mode=='meter-fault' else '536870913|3|1919'
        node=ET.SubElement(music,'MusicTime',{'sclock':'4611686018427387903','quarters':'2147483647:0' if reloaded else '2147483646:1919','bbt':terminal_bbt,'name':'<import'})
        ET.SubElement(node,'Tempo',{'npm':'120','enpm':'120','note-type':'4','type':'Constant','locked-to-meter':'0','continuing':'0','active':'1'})
        ET.SubElement(node,'Meter',{'note-value':'4','divisions-per-bar':'4'})
    return root
def rejects(fn):
    try:fn()
    except AssertionError:return
    raise AssertionError('Oracle accepted a deliberate corruption')
count=0
with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'explicitly-synthetic.xml'
    for mode in ['positive','tempo-fault','meter-fault','position-fault']:
        for reloaded in [False,True]:
            path.write_bytes(ET.tostring(model(mode,reloaded=reloaded)))
            o.inspect_native(path,mode,reloaded=reloaded)
            rejects(lambda:o.inspect_native(path,mode,reloaded=not reloaded));count+=1
            rejects(lambda:o.inspect_native(path,source=True));count+=1
            if mode!='positive':rejects(lambda:o.inspect_native(path,reloaded=reloaded));count+=1
    for xpath,key,value in [('./TempoMap/Tempos/Tempo','sclock','1'),('./TempoMap/Tempos/Tempo','quarters','1:0'),('./TempoMap/Tempos/Tempo','note-type','8'),('./TempoMap/Meters/Meter','divisions-per-bar','5'),('./TempoMap/MusicTimes/MusicTime','name','unrelated'),('./TempoMap/MusicTimes/MusicTime','sclock','1'),('./TempoMap/MusicTimes/MusicTime/Tempo','npm','121')]:
        root=model('positive');root.find(xpath).set(key,value);path.write_bytes(ET.tostring(root));rejects(lambda:o.inspect_native(path));count+=1
    path.write_bytes(ET.tostring(model('positive',source=True)));o.inspect_native(path,source=True)
    for mode in ['positive','tempo-fault','meter-fault','position-fault']:
        lines=[f'NATIVE_TICK {t} TEMPO {float(v):.10f} METER {n}/{d}' for t,v,n,d in o.query_expectations(mode)]
        output='\n'.join(lines+['BEATCOURIER_FULL_NATIVE_SAVED','> OK'])
        o.inspect_queries(output,mode)
        rejects(lambda:o.inspect_queries(output.replace('NATIVE_TICK 1 ','NATIVE_TICK 2 '),mode));count+=1
        rejects(lambda:o.inspect_queries(output.replace('TEMPO 120.0000000000','TEMPO 121.0000000000',1),mode));count+=1
        if mode!='positive':rejects(lambda:o.inspect_queries(output,'positive'));count+=1
print(f'Independent XML oracle: {count} corruption/stage controls passed; these selftest files are synthetic, not native evidence')
