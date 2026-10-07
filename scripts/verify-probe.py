#!/usr/bin/env python3
"""Handwritten native XML oracle, independent of MIDI fixture construction."""
from pathlib import Path
import json, sys, xml.etree.ElementTree as ET
from fractions import Fraction

EXPECTED_TEMPOS=[('0:0',Fraction(120),4),('8:0',Fraction(100),4),('16:0',Fraction(150),4)]
EXPECTED_METERS=[('0:0',Fraction(4),4),('16:0',Fraction(3),4)]
EXPECTED_CLOCKS={'0:0':0,'8:0':1128960000,'16:0':2483712000}
EXPECTED_BBT={'0:0':'1|1|0','8:0':'3|1|0','16:0':'5|1|0'}
def inspect(path,initial=False):
    raw=Path(path).read_bytes();assert len(raw)<4*1024*1024
    assert b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw
    root=ET.fromstring(raw);assert root.tag=='Session' and root.attrib['sample-rate']=='48000'
    maps=root.findall('TempoMap');assert len(maps)==1
    tm=maps[0];assert tm.attrib['superclocks-per-second']=='282240000'
    assert len(tm.findall('MusicTimes'))==1 and len(tm.find('MusicTimes'))==0
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
    return {'sampleRate':48000,'superclocksPerSecond':282240000,'pointSuperclocks':{q:EXPECTED_CLOCKS[q] for q,_,_ in tempos},'tempos':[[q,str(v),n] for q,v,n in tempos],'meters':[[q,str(v),n] for q,v,n in meters]}
if __name__=='__main__':
    result=inspect(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='initial')
    print(json.dumps(result,indent=2))
