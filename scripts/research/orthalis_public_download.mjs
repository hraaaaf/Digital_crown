// LOT07 / 07-C research-only. Download publicly linked web assets from official
// Orthalis domains; no sessions, credentials, guessed endpoints, patient data,
// Windows binaries, application installer execution, or hidden downloads.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
const folder=process.argv[2];
if(!folder) throw new Error("output directory is required");
fs.mkdirSync(folder,{recursive:true});
const allow=new Set(["www.orthalis.com","orthalis.com","demo.orthalis.com"]);
const roots=[
 "https://www.orthalis.com/orthalis/",
 "https://www.orthalis.com/en/orthalis-connect/",
 "https://demo.orthalis.com/",
 "https://demo.orthalis.com/guacamole/"
];
const FILE_LIMIT=1_800_000,ASSET_MAX=12;
const re=/(?:src|href)\s*=\s*["']([^"']{1,1600})["']/gi;
const pages=[], assets=[], installers=[], failed=[];
const asURL=(rel,base)=>{try{const url=new URL(rel,base);if(url.protocol!=="https:"||!allow.has(url.hostname)||url.username||url.password)return null;url.hash="";return url;}catch{return null;}};
function getLinks(html,base){
 const links=[]; for(const m of html.matchAll(re)){const u=asURL(m[1],base);if(u) links.push(u);}
 return Array.from(new Set(links.map(x=>x.href)));
}
const digest=x=>crypto.createHash("sha256").update(x).digest("hex");
function metadata(u){const x=new URL(u);return {host:x.hostname,path:x.pathname};}
async function read(url,limit){
 const c=new AbortController(),t=setTimeout(()=>c.abort(),22000);
 try{
   const res=await fetch(url,{redirect:"follow",headers:{"User-Agent":"DigitalCrown-LOT07-07C-REA-research/1.0","Accept":"text/html,application/javascript,text/javascript,*/*;q=0.5"},signal:c.signal});
   const final=asURL(res.url,url);
   if(!final) throw new Error("redirected outside official domains");
   const len=Number(res.headers.get("content-length")||0);
   if(len>limit) throw new Error("size limit");
   const chunks=[];let total=0;
   for await(const chunk of res.body){
      total+=chunk.length;if(total>limit) throw new Error("size limit");
      chunks.push(chunk);
   }
   if(!res.ok) throw new Error("HTTP "+res.status);
   return {bytes:Buffer.concat(chunks),contentType:res.headers.get("content-type")||"",final:final.href,status:res.status};
 }finally{clearTimeout(t);}
}
for(const url of roots){
 try{
   const data=await read(url,FILE_LIMIT);
   const html=data.bytes.toString("utf8");
   const links=getLinks(html,data.final);
   pages.push({...metadata(url),final:metadata(data.final),http:data.status,bytes:data.bytes.length,sha256:digest(data.bytes),link_count:links.length,content_type:data.contentType.split(";")[0]});
   const publicFileLinks=links.filter(u=>/\.(exe|msi|deb|appimage|dmg|rpm|msix|apk|zip)(?:\?|$)/i.test(u));
   for(const found of publicFileLinks) installers.push(metadata(found));
   for(const candidate of links){
      const info=metadata(candidate);
      if(!/\.m?js$/i.test(info.path))continue;
      if(assets.some(a=>a.url===candidate))continue;
      if(assets.length>=ASSET_MAX)break;
      try {
        const script=await read(candidate,FILE_LIMIT);
        if(!/(javascript|text\/plain|octet-stream)/i.test(script.contentType) && !/\.m?js(?:\?|$)/i.test(script.final))continue;
        const dest=path.join(folder,"orthalis-public-web-"+String(assets.length+1).padStart(2,"0")+".js");
        fs.writeFileSync(dest,script.bytes,{mode:0o600});
        assets.push({url:candidate,source:info,stored_as:path.basename(dest),size:script.bytes.length,sha256:digest(script.bytes),content_type:script.contentType.split(";")[0]});
      }catch(err){failed.push({kind:"script",source:info,reason:String(err.message).slice(0,100)});}
   }
 }catch(err){failed.push({kind:"page",source:metadata(url),reason:String(err.message).slice(0,100)});}
}
const summary={
 protocol:"LOT07-07C_ORTHALIS_UBUNTU_OFFICIAL_DOWNLOAD_ATTEMPT",
 gate:"public_pages_and_web_assets_ONLY",
 pages,public_installer_links:[...new Map(installers.map(a=>[a.host+a.path,a])).values()],
 collected_web_js:assets.map(({url,...rest})=>rest),
 failures:failed,
 native_orthalis_installer_downloaded:false,
 native_orthalis_installer_executed:false,
 notes:"Script artifacts are public web shell / Guacamole client, not the proprietary Orthalis desktop executable. No authorized login or patient information captured."
};
fs.writeFileSync(path.join(folder,"download-summary.json"),JSON.stringify(summary,null,2)+"\n",{mode:0o600});
console.log("OFFICIAL_ORTHALIS_ASSET_PROBE="+JSON.stringify(summary));
if(pages.length===0) process.exitCode=2;
