#!/usr/bin/env python3
"""Verify signed-distribution metadata and exact package bytes before running Ardour."""
from pathlib import Path
import hashlib, json, subprocess

ART=Path('artifacts/native'); ART.mkdir(parents=True,exist_ok=True)
ROOT=Path('/tmp/beatcourier-native'); ROOT.mkdir()
DEBS=ROOT/'packages'; DEBS.mkdir()
VERSION='1:8.12.0+ds-1'
PACKAGES=['ardour','ardour-data','ardour-lv2-plugins']
def run(args,**kwargs):
    return subprocess.run(args,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,**kwargs).stdout
records=[];verified_files=[]
for name in PACKAGES:
    raw=run(['apt-cache','show',f'{name}={VERSION}'])
    paragraphs=raw.strip().split('\n\n')
    metadata=[]
    for paragraph in paragraphs:
        d={line.split(': ',1)[0]:line.split(': ',1)[1] for line in paragraph.splitlines() if ': ' in line and not line.startswith(' ')}
        if d.get('Package')==name and d.get('Version')==VERSION:metadata.append(d)
    assert len(metadata)==1,f'Expected exactly one authenticated candidate for {name}'
    d=metadata[0]; assert d['Architecture'] in ['amd64','all']
    assert d['Filename'].startswith('pool/main/a/ardour/')
    assert len(d['SHA256'])==64 and int(d['Size'])>0
    (ART/f'{name}-authenticated-package.txt').write_text(raw)
    run(['apt-get','download',f'{name}={VERSION}'],cwd=DEBS)
    downloaded=[p for p in DEBS.glob('*.deb') if p.name.startswith(name+'_')]
    assert len(downloaded)==1
    p=downloaded[0]; actual=hashlib.sha256(p.read_bytes()).hexdigest()
    assert p.stat().st_size==int(d['Size']) and actual==d['SHA256']
    package_version=run(['dpkg-deb','-f',str(p),'Version']).strip()
    package_name=run(['dpkg-deb','-f',str(p),'Package']).strip()
    package_architecture=run(['dpkg-deb','-f',str(p),'Architecture']).strip()
    assert package_version==VERSION and package_name==name and package_architecture==d['Architecture']
    verified_files.append(str(p.resolve()))
    records.append({'name':name,'version':VERSION,'source':d.get('Source','ardour'),'architecture':d['Architecture'],'filename':d['Filename'],'size':p.stat().st_size,'sha256':actual,'identityVerifiedBeforeInstall':True})
(ART/'package-pin.json').write_text(json.dumps({'distribution':'Debian 13 trixie','trust':'Default authenticated Debian APT metadata; no authentication bypass or new trust keys','packages':records},indent=2)+'\n')
run(['apt-get','install','-y','--no-install-recommends',*verified_files])
installed=run(['dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\n'])
(ART/'installed-runtime-packages.tsv').write_text(installed)
for name in PACKAGES:assert f'{name}\t{VERSION}\t' in installed
