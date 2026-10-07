#!/usr/bin/env python3
"""Handwritten native XML oracle, independent of MIDI fixture construction."""
from pathlib import Path
import json, sys, xml.etree.ElementTree as ET
from fractions import Fraction

EXPECTED_TEMPOS=[('0:0',Fraction(120),4),('8:0',Fraction(100),4),('16:0',Fraction(150),4)]
EXPECTED_METERS=[('0:0',Fraction(4),4),('16:0',Fraction(3),4)]
EXPECTED_CLOCKS={'0:0':0,'8:0':1128960000,'16:0':2483712000}
EXPECTED_BBT={'0:0':'1|1|0','8:0':'3|1|0','16:0':'5|1|0'}
def native_terminal(music):
    # Output-only normalization observed from the pinned native import/paste.
    # Source fixtures and product inputs still require empty MusicTimes.
    assert len(music)==1 and music[0].tag=='MusicTime'
    marker=music[0]
    expected={'sclock':'4611686018427387903','quarters':'2147483646:1919','bbt':'715827881|3|1919','name':'<import'}
    assert marker.attrib==expected,'Unexpected native terminal marker attributes'
    assert [n.tag for n in marker]==['Tempo','Meter']
    assert marker[0].attrib=={'npm':'120','enpm':'120','note-type':'4','type':'Constant','locked-to-meter':'0','continuing':'0','active':'1'}
    assert marker[1].attrib=={'note-value':'4','divisions-per-bar':'4'}
    assert all(len(n)==0 for n in marker)
    assert all(not (n.text or '').strip() and not (n.tail or '').strip() for n in music.iter())
    return {'kind':'Exact native MAX-time import boundary','attributes':expected,'restoredTempo':120,'restoredMeter':[4,4]}
def inspect(path,initial=False,imported=False):
    assert not (initial and imported)
    raw=Path(path).read_bytes();assert len(raw)<4*1024*1024
    assert b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw
    root=ET.fromstring(raw);assert root.tag=='Session' and root.attrib['sample-rate']=='48000'
    maps=root.findall('TempoMap');assert len(maps)==1
    tm=maps[0];assert tm.attrib['superclocks-per-second']=='282240000'
    assert len(tm.findall('MusicTimes'))==1
    music=tm.find('MusicTimes');assert not music.attrib
    normalization=native_terminal(music) if imported else None
    if not imported:assert len(music)==0,'Source MusicTimes must remain empty'
    for point in [*tm.find('Tempos'),*tm.find('Meters')]:
        q=point.attrib['quarters'];assert q in EXPECTED_CLOCKS
        assert int(point.attrib['sclock'])==EXPECTED_CLOCKS[q],f'Native time coordinate differs at {q}'
        assert point.attrib['bbt']==EXPECTED_BBT[q],f'Native bar coordinate differs at {q}'
    tempos=[]
    for point in tm.find('Tempos'):
        assert point.tag=='Tempo'
        assert Fraction(point.attrib['npm'])==Fraction(point.attrib['enpm'])
        assert Fraction(point.attrib.get('omega','0'))==0
        tempos.append((point.attrib['quarters'],Fraction(point.attrib['npm']),int(point.attrib['note-type'])))
    meters=[]
    for point in tm.find('Meters'):
        assert point.tag=='Meter'
        meters.append((point.attrib['quarters'],Fraction(point.attrib['divisions-per-bar']),int(point.attrib['note-value'])))
    assert tempos==(EXPECTED_TEMPOS[:1] if initial else EXPECTED_TEMPOS),f'Actual native tempos differ: {tempos}'
    assert meters==(EXPECTED_METERS[:1] if initial else EXPECTED_METERS),f'Actual native meters differ: {meters}'
    # Imported metadata may cause an empty MIDI source/track depending on the native
    # importer. No audio source or external plugin is allowed by this probe.
    for processor in root.iter('Processor'):
        assert processor.attrib.get('type') not in ['lv2','ladspa','vst','lxvst','vst3','au'],processor.attrib
    for source in root.iter('Source'):assert source.attrib.get('type')!='audio',source.attrib
    return {'sampleRate':48000,'superclocksPerSecond':282240000,'pointSuperclocks':{q:EXPECTED_CLOCKS[q] for q,_,_ in tempos},'tempos':[[q,str(v),n] for q,v,n in tempos],'meters':[[q,str(v),n] for q,v,n in meters],'nativeOutputNormalization':normalization}
if __name__=='__main__':
    result=inspect(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='initial')
    print(json.dumps(result,indent=2))
