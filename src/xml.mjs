import { DOMParser } from '@xmldom/xmldom';
export const LIMITS=Object.freeze({fileBytes:4*1024*1024,elements:30000,depth:64,pointsPerKind:2048});
export class SessionError extends Error {constructor(code,message){super(message);this.name='SessionError';this.code=code;}}
export const fail=(code,message)=>{throw new SessionError(code,message);};
const xmlSpace=c=>c===' '||c==='\t'||c==='\r'||c==='\n';
const xmlChar=n=>n===9||n===10||n===13||(n>=32&&n<=0xd7ff)||(n>=0xe000&&n<=0xfffd)||(n>=0x10000&&n<=0x10ffff);
const nameStart=c=>c==='_'||(c>='A'&&c<='Z')||(c>='a'&&c<='z');
const namePart=c=>nameStart(c)||(c>='0'&&c<='9')||c==='.'||c==='-';
// One advancing cursor, bounded names/references/attributes, and no searching regex.
// Comments and CDATA are consumed once; their apparent markup is never rescanned.
function lexXML(text) {
  let i=text.charCodeAt(0)===0xfeff?1:0, tokens=0,totalAttributes=0,roots=0;
  const beginning=i,stack=[],spans=[];
  const name=()=>{
    const start=i;if(!nameStart(text[i]))fail('INVALID_XML','Expected an unprefixed XML name');
    while(i<text.length&&namePart(text[i])){if(i-start>=128)fail('XML_LIMIT','XML names are bounded');i++;}
    if(text[i]===':')fail('UNSUPPORTED_XML','XML namespaces are unsupported');
    return text.slice(start,i);
  };
  const reference=()=>{
    const start=i++;while(i<text.length&&text[i]!==';'&&i-start<=32)i++;
    if(text[i]!==';'||i-start>32)fail('INVALID_XML','Malformed or oversized XML reference');
    const ref=text.slice(start+1,i++);
    if(['amp','lt','gt','apos','quot'].includes(ref))return;
    if(!/^#(?:[0-9]+|x[0-9a-fA-F]+)$/.test(ref))fail('INVALID_XML','Unsupported XML entity reference');
    const n=ref[1]==='x'?parseInt(ref.slice(2),16):Number(ref.slice(1));
    if(!xmlChar(n))fail('INVALID_XML','Forbidden numeric XML character');
  };
  while(i<text.length){
    if(++tokens>80000)fail('XML_LIMIT','XML token limit exceeded');
    if(text[i]!=='<'){
      while(i<text.length&&text[i]!=='<'){
        if(!stack.length&&!xmlSpace(text[i]))fail('INVALID_XML','Text outside the root element');
        if(text.startsWith(']]>',i))fail('INVALID_XML','CDATA terminator in ordinary text');
        if(text[i]==='&')reference();else i++;
      }
      continue;
    }
    const start=i;
    if(text.startsWith('<!--',i)){
      const end=text.indexOf('--',i+4);
      if(end<0||text[end+2]!=='>')fail('INVALID_XML','Malformed or unterminated XML comment');
      i=end+3;continue;
    }
    if(text.startsWith('<![CDATA[',i)){
      if(!stack.length)fail('INVALID_XML','CDATA outside root');
      const end=text.indexOf(']]>',i+9);if(end<0)fail('INVALID_XML','Unterminated CDATA');
      i=end+3;continue;
    }
    if(text.startsWith('<?',i)){
      const end=text.indexOf('?>',i+2);
      if(end<0||end+2-start>256)fail('INVALID_XML','Unterminated or oversized processing instruction');
      const token=text.slice(start,end+2);
      if(!token.startsWith('<?xml ')&&!token.startsWith('<?xml\t')&&!token.startsWith('<?xml\r')&&!token.startsWith('<?xml\n'))fail('UNSUPPORTED_XML','Processing instructions are unsupported');
      if(start!==beginning)fail('INVALID_XML','XML declaration must occur once at the start');
      if(!/^<\?xml[ \t\r\n]+version[ \t\r\n]*=[ \t\r\n]*(?:"1\.0"|'1\.0')(?:[ \t\r\n]+encoding[ \t\r\n]*=[ \t\r\n]*(?:"[Uu][Tt][Ff]-8"|'[Uu][Tt][Ff]-8'))?(?:[ \t\r\n]+standalone[ \t\r\n]*=[ \t\r\n]*(?:"(?:yes|no)"|'(?:yes|no)'))?[ \t\r\n]*\?>$/.test(token))fail('XML_VERSION','Only XML1.0 with optional UTF-8 encoding declaration is supported');
      i=end+2;continue;
    }
    if(text.startsWith('<!',i))fail('XML_DOCTYPE','DTD and entity declarations are unsupported');
    i++;
    if(text[i]==='/'){
      i++;const tag=name();while(xmlSpace(text[i]))i++;
      if(text[i++]!=='>')fail('INVALID_XML','Malformed closing tag');
      const opened=stack.pop();if(!opened||opened.name!==tag)fail('INVALID_XML','Mismatched XML elements');
      opened.closeStart=start;opened.end=i;continue;
    }
    const tag=name(),attributes=new Map();let selfClosing=false;
    while(true){
      const attrStart=i;while(xmlSpace(text[i]))i++;
      if(text[i]==='>'){i++;break;}
      if(text[i]==='/'&&text[i+1]==='>'){i+=2;selfClosing=true;break;}
      if(i===attrStart)fail('INVALID_XML','Attributes require separating whitespace');
      const key=name();if(key==='xmlns')fail('UNSUPPORTED_XML','XML namespaces are unsupported');
      if(attributes.has(key))fail('INVALID_XML','Duplicate XML attribute');
      if(attributes.size>=64||++totalAttributes>120000)fail('XML_LIMIT','XML attribute limit exceeded');
      while(xmlSpace(text[i]))i++;
      if(text[i++]!=='=')fail('INVALID_XML','Expected attribute equals sign');
      while(xmlSpace(text[i]))i++;
      const quote=text[i++];if(quote!=='"'&&quote!=="'")fail('INVALID_XML','Attributes require quotes');
      while(i<text.length&&text[i]!==quote){
        if(text[i]==='<')fail('INVALID_XML','Raw markup in XML attribute');
        if(text[i]==='&')reference();else i++;
      }
      if(text[i++]!==quote)fail('INVALID_XML','Unterminated attribute');
      attributes.set(key,{start:attrStart,end:i});
    }
    if(!stack.length&&++roots!==1)fail('INVALID_XML','Exactly one root is required');
    const span={name:tag,start,openEnd:i,selfClosing,attributes};spans.push(span);
    if(stack.length+1>LIMITS.depth||spans.length>LIMITS.elements)fail('XML_LIMIT','XML depth/element limit exceeded');
    if(selfClosing){span.closeStart=start;span.end=i;}else stack.push(span);
  }
  if(stack.length||roots!==1)fail('INVALID_XML','Incomplete XML document');
  return spans;
}
export function xmlDocument(bytes) {
  if(!(bytes instanceof Uint8Array)||bytes.length>LIMITS.fileBytes)fail('INPUT_LIMIT','Session XML must be a byte array up to4 MiB');
  let text;try{text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);}catch{fail('XML_ENCODING','Session XML must be UTF-8');}
  for(const c of text)if(!xmlChar(c.codePointAt(0)))fail('INVALID_XML','Forbidden XML character');
  const spans=lexXML(text);let document;
  try{document=new DOMParser({onError:(level,message)=>{throw Error(`${level}: ${message}`);}}).parseFromString(text.replace(/^\uFEFF/,''),'application/xml');}
  catch(e){fail('INVALID_XML',e.message);}
  if(document.documentElement?.tagName!=='Session')fail('INVALID_XML','A complete Session document is required');
  const all=Array.from(document.getElementsByTagName('*'));
  if(all.length!==spans.length)fail('INVALID_XML','Ambiguous XML token structure');
  const ranges=new Map();all.forEach((node,index)=>{
    const span=spans[index];
    if(node.tagName!==span.name||node.attributes.length!==span.attributes.size||node.namespaceURI)fail('INVALID_XML','Ambiguous XML element/attribute structure');
    ranges.set(node,span);
  });
  return {document,text,ranges,elementCount:all.length};
}

