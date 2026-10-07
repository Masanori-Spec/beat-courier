#!/usr/bin/env python3
"""Independent, literal MIDI fixture for import feasibility; not the future product converter."""
from pathlib import Path
import hashlib, json, struct

ROOT=Path('/tmp/beatcourier-native'); ART=Path('artifacts/native')
def vlq(n):
    assert 0<=n<=0x0fffffff
    out=[n&127];n>>=7
    while n:out.insert(0,(n&127)|128);n>>=7
    return bytes(out)
# Literal PPQN=1920, three FF51 tempos and two FF58 signatures.
# Every event is metadata. No instrument, notes, tracks of musical content or audio.
events=[(0,b'\xff\x51\x03\x07\xa1\x20'),(0,b'\xff\x58\x04\x04\x02\x18\x08'),
        (15360,b'\xff\x51\x03\x09\x27\xc0'),(30720,b'\xff\x51\x03\x06\x1a\x80'),
        (30720,b'\xff\x58\x04\x03\x02\x18\x08'),(61440,b'\xff\x2f\x00')]
track=b'';previous=0
for absolute,event in events:track+=vlq(absolute-previous)+event;previous=absolute
data=b'MThd'+struct.pack('>IHHH',6,0,1,1920)+b'MTrk'+struct.pack('>I',len(track))+track
(ROOT/'conductor.mid').write_bytes(data);(ART/'conductor.mid').write_bytes(data)
# Independent maintained mido parser checks actual bytes, with literal expectations.
import mido
parsed=mido.MidiFile(ROOT/'conductor.mid'); assert parsed.type==0 and parsed.ticks_per_beat==1920 and len(parsed.tracks)==1
observed=[];tick=0
for msg in parsed.tracks[0]:
    tick+=msg.time; assert msg.is_meta
    if msg.type=='set_tempo':observed.append([tick,'tempo',msg.tempo])
    elif msg.type=='time_signature':observed.append([tick,'meter',msg.numerator,msg.denominator,msg.clocks_per_click,msg.notated_32nd_notes_per_beat])
    else:assert msg.type=='end_of_track' and tick==61440
assert observed==[[0,'tempo',500000],[0,'meter',4,4,24,8],[15360,'tempo',600000],[30720,'tempo',400000],[30720,'meter',3,4,24,8]]
(ART/'midi-fixture.json').write_text(json.dumps({'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'parser':'python3-mido from authenticated Debian','events':observed,'endTick':61440,'noteEvents':0},indent=2)+'\n')
