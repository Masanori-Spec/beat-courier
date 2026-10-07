export const decodeBytes=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
export const decodeUTF8=value=>new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(decodeBytes(value));
