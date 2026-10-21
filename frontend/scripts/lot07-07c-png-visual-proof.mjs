/** LOT07/07-C — Decode basic Chromium PNG screenshots to reject blank AFTER.
 * This is an independent pixel-level observation of screenshot bytes.
 * No browser/CSS/CDP input can manufacture this assertion from DOM visibility.
 */
import assert from 'node:assert/strict';
import { inflateSync } from 'node:zlib';

export function inspectPngVisibleInk(buffer) {
  const signature = Buffer.from([137,80,78,71,13,10,26,10]);
  assert.ok(buffer.subarray(0,8).equals(signature), 'Screenshot must be PNG');
  let width=0, height=0, bitDepth=0, colorType=-1, off=8;
  const idat=[];
  while(off+12<=buffer.length) {
    const size=buffer.readUInt32BE(off);const kind=buffer.toString('ascii',off+4,off+8);
    const content=buffer.subarray(off+8,off+8+size);
    assert.ok(off+size+12<=buffer.length,'PNG chunk truncated');
    if(kind==='IHDR') {
      width=content.readUInt32BE(0);height=content.readUInt32BE(4);
      bitDepth=content[8];colorType=content[9];
      assert.equal(content[10],0,'unexpected PNG compression');
      assert.equal(content[11],0,'unexpected PNG filter method');
      assert.equal(content[12],0,'interlaced PNG unsupported');
    }
    if(kind==='IDAT')idat.push(content);
    off+=size+12;
    if(kind==='IEND')break;
  }
  assert.ok(width>0&&height>0&&width*height<20000000,'invalid PNG dimensions');
  assert.equal(bitDepth,8,'unexpected PNG bit depth');
  assert.ok(colorType===2||colorType===6,'only RGB/RGBA PNG supported');
  const bytesPerPixel=colorType===6?4:3;
  const stride=width*bytesPerPixel;
  const data=inflateSync(Buffer.concat(idat));
  assert.equal(data.length,(stride+1)*height,'unexpected PNG scanline size');
  let last=Buffer.alloc(stride);
  let offset=0;
  let inkPixels=0;
  let minRgb=255;
  for(let y=0;y<height;y++) {
    const filter=data[offset++];
    const row=Buffer.allocUnsafe(stride);
    for(let i=0;i<stride;i++) {
      const raw=data[offset++];
      const left=i>=bytesPerPixel?row[i-bytesPerPixel]:0;
      const up=last[i];
      const upperLeft=i>=bytesPerPixel?last[i-bytesPerPixel]:0;
      let pred=0;
      if(filter===1)pred=left;
      else if(filter===2)pred=up;
      else if(filter===3)pred=Math.floor((left+up)/2);
      else if(filter===4) {
        const p=left+up-upperLeft;
        const da=Math.abs(p-left),db=Math.abs(p-up),dc=Math.abs(p-upperLeft);
        pred=da<=db&&da<=dc?left:db<=dc?up:upperLeft;
      } else assert.equal(filter,0,'Unsupported PNG filter');
      row[i]=(raw+pred)&255;
    }
    for(let i=0;i<stride;i+=bytesPerPixel) {
      const r=row[i],g=row[i+1],b=row[i+2];
      minRgb=Math.min(minRgb,r,g,b);
      if(r<205&&g<205&&b<205)inkPixels++;
    }
    last=row;
  }
  return {width,height,inkPixels,minRgb};
}
