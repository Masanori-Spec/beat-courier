"""Read real hosted native pixels; never synthesize labels or expected-value images."""
from pathlib import Path
from PIL import Image, ImageOps
import csv, io, json, math, subprocess

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
    # Tesseract TSV text is unquoted. A recognized quote glyph must remain a
    # glyph rather than swallowing later rows as a CSV multiline field.
    for row in csv.DictReader(io.StringIO(result.stdout),delimiter='\t',quoting=csv.QUOTE_NONE):
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

def toolbar_labels(raw_path,words,window_rect):
    def inside(r):return r[0]>=window_rect[0] and r[1]>=window_rect[1] and r[0]+r[2]<=window_rect[0]+window_rect[2] and r[1]+r[3]<=window_rect[1]+window_rect[3]
    run=unique_phrase(words,'Run')
    assert inside(run['rect'])
    if phrase_matches(words,'Clear Output'):
        clear=unique_phrase(words,'Clear Output');assert inside(clear['rect']);return run,clear
    clear=unique_phrase(words,'Clear')
    assert inside(clear['rect'])
    # A low-confidence exact Output token is a crop hint only. No action or
    # acceptance uses it until the actual cropped pixels pass the same60% rule.
    tails=[w for w in words if w['text']=='Output' and abs(w['rect'][1]-clear['rect'][1])<15 and 0<w['rect'][0]-(clear['rect'][0]+clear['rect'][2])<80]
    assert len(tails)==1 and abs(run['rect'][1]-clear['rect'][1])<15 and 0<clear['rect'][0]-run['rect'][0]<140
    boxes=[run['rect'],clear['rect'],tails[0]['rect']]
    assert all(inside(r) for r in boxes)
    left=math.floor(min(r[0] for r in boxes)-8);top=math.floor(min(r[1] for r in boxes)-5)
    right=math.ceil(max(r[0]+r[2] for r in boxes)+6);bottom=math.ceil(max(r[1]+r[3] for r in boxes)+4)
    assert 0<=left<right<=1600 and 0<=top<bottom<=1000 and right-left<240 and bottom-top<40
    assert inside([left,top,right-left,bottom-top]),'Toolbar crop must remain inside the actual native Lua window'
    raw_path=Path(raw_path);gray=ImageOps.grayscale(Image.open(raw_path));assert gray.size==(1600,1000)
    cropped=gray.crop((left,top,right,bottom)).point(lambda v:0 if v>140 else 255)
    processed=cropped.resize((cropped.width*5,cropped.height*5))
    image_path=raw_path.with_name(raw_path.stem+'-toolbar-ocr.png');processed.save(image_path)
    result=subprocess.run(['tesseract',str(image_path),'stdout','--psm','7','tsv'],check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
    raw_path.with_name(raw_path.stem+'-toolbar.tsv').write_text(result.stdout)
    refined=[]
    for row in csv.DictReader(io.StringIO(result.stdout),delimiter='\t',quoting=csv.QUOTE_NONE):
        if row['level']!='5' or not row['text'].strip():continue
        refined.append({'text':row['text'],'confidence':float(row['conf']),'line':[row['block_num'],row['par_num'],row['line_num']],'rect':[left+int(row['left'])/5,top+int(row['top'])/5,int(row['width'])/5,int(row['height'])/5]})
    raw_path.with_name(raw_path.stem+'-toolbar-geometry.json').write_text(json.dumps({'crop':[left,top,right,bottom],'scale':5,'sourceHints':boxes,'refinedWords':refined},indent=2)+'\n')
    checked_run=unique_phrase(refined,'Run');checked_clear=unique_phrase(refined,'Clear Output')
    assert abs(checked_run['rect'][0]-run['rect'][0])<4 and abs(checked_run['rect'][1]-run['rect'][1])<4
    return checked_run,checked_clear
