/* eslint-disable @typescript-eslint/no-require-imports -- plain Node script, run directly with `node` */
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

function crc32(buf) {
  let c;
  const table = crc32.table || (crc32.table = (() => {
    const t = [];
    for (let n = 0; n < 256; n++) {
      c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c;
    }
    return t;
  })());
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) crc = table[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBuf = Buffer.from(type, "ascii");
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

// Simple rounded-ish emerald square with a lighter ring, no text (no font
// rasterizer available in this sandbox) -- good enough as a real, valid PWA icon.
function makeIcon(size) {
  const bg = [16, 24, 21]; // near-black
  const ring = [16, 185, 129]; // emerald-500
  const raw = Buffer.alloc(size * (1 + size * 4));
  const margin = Math.round(size * 0.14);
  const ringWidth = Math.max(2, Math.round(size * 0.06));
  for (let y = 0; y < size; y++) {
    raw[y * (1 + size * 4)] = 0; // filter type 0
    for (let x = 0; x < size; x++) {
      const inMargin = x < margin || x >= size - margin || y < margin || y >= size - margin;
      const onRingBand =
        x >= margin && x < margin + ringWidth ||
        x >= size - margin - ringWidth && x < size - margin ||
        y >= margin && y < margin + ringWidth ||
        y >= size - margin - ringWidth && y < size - margin;
      const color = !inMargin && onRingBand ? ring : bg;
      const off = y * (1 + size * 4) + 1 + x * 4;
      raw[off] = color[0];
      raw[off + 1] = color[1];
      raw[off + 2] = color[2];
      raw[off + 3] = 255;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // color type RGBA
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const idat = zlib.deflateSync(raw);
  return Buffer.concat([
    sig,
    chunk("IHDR", ihdr),
    chunk("IDAT", idat),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

const outDir = path.join(__dirname, "..", "public");
fs.writeFileSync(path.join(outDir, "icon-192.png"), makeIcon(192));
fs.writeFileSync(path.join(outDir, "icon-512.png"), makeIcon(512));
console.log("Icons written.");
