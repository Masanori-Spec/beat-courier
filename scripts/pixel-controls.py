"""Read real hosted native pixels; never synthesize labels or expected-value images."""
from pathlib import Path
from PIL import Image, ImageOps
import csv, io, json, subprocess

def read_pixels(raw_path):
    raw_path=Path(raw_path)
    gray=ImageOps.grayscale(Image.open(raw_path));assert gray.size==(1600,1000)
    # Threshold140 and3x scaling were replayed against the retained R1 native
    # dark-theme wizard. Unrecognized/ambiguous controls fail closed.
    processed=gray.point(lambda v:0 if v>140 else 255).resize((4800,3000))
    processed_path=raw_path.with_name(raw_path.stem+'-ocr.png');processed.save(processed_path)
    result=subprocess.run(['tesseract',str(processed_path),'stdout','--psm','11','tsv'],check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
    raw_path.with_suffix('.tsv').write_text(result.stdout)
    words=[]
    for row in csv.DictReader(io.StringIO(result.stdout),delimiter='\t'):
        if row['level']!='5' or not row['text'].strip():continue
        words.append({'text':row['text'],'confidence':float(row['conf']),'line':[row['block_num'],row['par_num'],row['line_num']], 'rect':[int(row[k])/3 for k in ['left','top','width','height']]})
    assert len(words)<5000,'Unexpected OCR resource use'
    raw_path.with_name(raw_path.stem+'-words.json').write_text(json.dumps(words,indent=2)+'\n')
    return words

def phrase_matches(words,phrase):
    wanted=phrase.split();found=[]
    for i in range(len(words)-len(wanted)+1):
        run=words[i:i+len(wanted)]
        if [w['text'] for w in run]!=wanted or min(w['confidence'] for w in run)<60:continue
        if any(w['line']!=run[0]['line'] for w in run):continue
        left=min(w['rect'][0] for w in run);top=min(w['rect'][1] for w in run)
        right=max(w['rect'][0]+w['rect'][2] for w in run);bottom=max(w['rect'][1]+w['rect'][3] for w in run)
        found.append({'text':phrase,'rect':[left,top,right-left,bottom-top],'confidence':min(w['confidence'] for w in run)})
    return found

def unique_phrase(words,phrase):
    found=phrase_matches(words,phrase)
    assert len(found)==1,f'Expected one high-confidence native pixel label {phrase!r}, found {len(found)}'
    return found[0]
