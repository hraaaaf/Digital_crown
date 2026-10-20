// LOT07/07-C. Read only the publicly available Orthalis Connect tutorial
// markup. Log media public host/path only. Do not follow unknown domains,
// download videos, scrape authentication flows, or retain identifying data.
import crypto from "node:crypto";
const sources=[
  "https://demo.orthalis.com/",
  "https://www.orthalis.com/en/orthalis-connect/"
];
const allowedMediaHost=(h)=>h==="demo.orthalis.com"||h==="www.orthalis.com"||h==="orthalis.com"||h==="youtube.com"||h==="www.youtube.com"||h==="youtu.be"||h==="player.vimeo.com"||h==="vimeo.com";
const lessonLabels=["Intro","La fiche de synthèse","Le planning","Poser un rendez-vous","Connexion à Dentapoche","L'IA","Module 1er contact"];
const report=[];
for(const source of sources) {
 const ctrl=new AbortController();
 const timeout=setTimeout(()=>ctrl.abort(),13000);
 try{
   const response=await fetch(source,{signal:ctrl.signal,headers:{"User-Agent":"DigitalCrown-LOT07-07C-orthalis-public-tutorial-research","Accept":"text/html"}});
   const raw=await response.text();
   const html=raw.slice(0,850_000);
   const refs=[];
   const attr=/\b(?:href|src|data-src|data-url|data-video|poster)\s*=\s*["']([^"']{1,1024})["']/gi;
   for(const match of html.matchAll(attr)){
     try {
       const url=new URL(match[1],source);
       if(!["http:","https:"].includes(url.protocol)||!allowedMediaHost(url.hostname))continue;
       if(!/\.(?:mp4|webm|m3u8)(?:$|\?)/i.test(url.pathname)||/^(?:data|javascript)/.test(match[1]))continue;
       const safe={host:url.hostname,path:url.pathname,kind:url.pathname.split(".").at(-1).toLowerCase()};
       if(!refs.some(r=>r.host===safe.host&&r.path===safe.path))refs.push(safe);
     } catch{}
   }
   const embeds=[];
   const vids=/<(?:iframe|video|source)\b[^>]*>/gi;
   for(const match of html.matchAll(vids)) {
     const str=match[0];
     const href=[...str.matchAll(/\b(?:src|data-src)\s*=\s*["']([^"']+)["']/g)].map(m=>m[1]);
     for(const item of href){
       try{const u=new URL(item,source);if(allowedMediaHost(u.hostname)&&["http:","https:"].includes(u.protocol)){
         const v={host:u.hostname,path:u.pathname};if(!embeds.some(x=>x.host===v.host&&x.path===v.path))embeds.push(v);
       }}catch{}
     }
   }
   report.push({source_host:new URL(source).hostname,source_path:new URL(source).pathname,http:response.status,
     html_bytes:Buffer.byteLength(raw),html_sha256:crypto.createHash("sha256").update(raw).digest("hex"),
     explicit_lesson_labels_present:lessonLabels.filter(x=>html.toLowerCase().includes(x.toLowerCase())),
     video_element_count:(html.match(/<video\b/gi)||[]).length,
     iframe_count:(html.match(/<iframe\b/gi)||[]).length,
     public_media_links:refs.slice(0,15),
     public_video_embeds:embeds.slice(0,15),
     scope:"PUBLIC_HTML_ONLY_NOT_A_DEMO_WORKFLOW"});
 }catch(e){report.push({source_host:new URL(source).hostname,status:"unavailable",reason:String(e.name||"fetch_error")});}
 finally{clearTimeout(timeout);}
}
console.log("ORTHALIS_PUBLIC_TUTORIAL_INVENTORY="+JSON.stringify(report));
