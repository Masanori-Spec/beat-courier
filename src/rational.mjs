// Exact bounded rational accounting; no floating-point event positions.
const gcd=(a,b)=>{a=a<0n?-a:a;while(b){const t=a%b;a=b;b=t;}return a;};
export function rational(n,d=1n){
  if(d===0n)throw new Error('Zero denominator');
  if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return {n:n/g,d:d/g};
}
export function decimal(value){
  if(typeof value!=='string'||value.length>32||! /^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,20})?$/.test(value))throw new Error('Unsupported bounded decimal');
  const [whole,part='']=value.split('.');return rational(BigInt(whole+part),10n**BigInt(part.length));
}
export const text=x=>x.d===1n?String(x.n):`${x.n}/${x.d}`;
export function midiTempo(npmText,noteType){
  if(![1,2,4,8,16,32,64].includes(noteType))throw new Error('Unsupported tempo note value');
  const bpm=decimal(npmText);if(bpm.n<=0n)throw new Error('Tempo must be positive');
  const exact=rational(15000000n*BigInt(noteType)*bpm.d,bpm.n);
  if(exact.n<exact.d||exact.n>16777215n*exact.d)throw new Error('Tempo outside MIDI24-bit range');
  const rounded=(exact.n*2n+exact.d)/(exact.d*2n);
  return {microseconds:Number(rounded),exactMicroseconds:text(exact),errorMicroseconds:text(rational(rounded*exact.d-exact.n,exact.d)),sourceQuarterNotesPerMinute:text(rational(bpm.n*4n,bpm.d*BigInt(noteType))),midiQuarterNotesPerMinute:text(rational(60000000n,rounded)),rounded:exact.d!==1n};
}
