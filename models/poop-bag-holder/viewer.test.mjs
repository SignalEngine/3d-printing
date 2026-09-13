// Headless check of viewer.html: renders, model framed, touch drag rotates, pinch zooms,
// stale pointer recovers, view buttons move the camera, survives a 0x0 iframe start.
// usage: node viewer.test.mjs   (exit 0 = all pass)
import { createRequire } from "module";
import { readFileSync } from "fs";
import path from "path";
const require = createRequire("/root/intentos/package.json");
const { chromium } = require("playwright");
const { PNG } = (() => { try { return require("pngjs"); } catch { return {}; } })();

import { spawn } from "child_process";
import { writeFileSync } from "fs";
// serve over http: Chrome refuses a file:// iframe inside a setContent (about:blank) host page
const PORT = 8000 + Math.floor(Math.random() * 900);
writeFileSync("iframe-host.html", `<body style="margin:0"><iframe id="f" src="viewer.html" style="width:0;height:0;border:0"></iframe>
<script>setTimeout(()=>{const f=document.getElementById('f');f.style.width='412px';f.style.height='900px'},500)</script></body>`);
const server = spawn("python3", ["-m", "http.server", String(PORT), "--bind", "127.0.0.1"], { stdio: "ignore" });
process.on("exit", () => server.kill());
await new Promise((r) => setTimeout(r, 800));
const file = `http://127.0.0.1:${PORT}/viewer.html`;
const results = [];
const check = (name, ok, detail) => { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${name}: ${detail}`); };

function coverage(buf) {
  if (!PNG) return null;
  const img = PNG.sync.read(buf); const { width, height, data } = img;
  const bg = [data[0], data[1], data[2]]; let n = 0, sx = 0, sy = 0;
  for (let y = 0; y < height; y += 2) for (let x = 0; x < width; x += 2) {
    const i = (y * width + x) * 4;
    if (Math.abs(data[i] - bg[0]) + Math.abs(data[i + 1] - bg[1]) + Math.abs(data[i + 2] - bg[2]) > 40) { n++; sx += x; sy += y; }
  }
  const total = Math.ceil(width / 2) * Math.ceil(height / 2);
  return { frac: n / total, cx: n ? sx / n / width : 0, cy: n ? sy / n / height : 0 };
}

const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
try {
  for (const [label, vp] of [["portrait", { width: 412, height: 915 }], ["landscape", { width: 915, height: 412 }]]) {
    const ctx = await browser.newContext({ viewport: vp, hasTouch: true, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    const errors = []; page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(file);
    await page.waitForFunction(() => window.__state && window.__state().ready, null, { timeout: 60000 });
    await page.waitForTimeout(1500);
    check(`${label}: no page errors`, errors.length === 0, errors.join(" | ") || "none");

    const stage = page.locator("#stage");
    const shot = await stage.screenshot();
    const cov = coverage(shot);
    if (cov) check(`${label}: model visible and centred`, cov.frac > 0.08 && Math.abs(cov.cx - 0.5) < 0.2 && Math.abs(cov.cy - 0.5) < 0.2,
      `coverage ${(cov.frac * 100).toFixed(1)}% centroid (${cov.cx.toFixed(2)}, ${cov.cy.toFixed(2)})`);

    const box = await stage.boundingBox();
    const cdp = await ctx.newCDPSession(page);
    const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
    const touch = (type, pts) => cdp.send("Input.dispatchTouchEvent", { type, touchPoints: pts.map(([x, y], id) => ({ x, y, id })) });

    let s0 = await page.evaluate(() => window.__state());
    await touch("touchStart", [[cx - 60, cy]]);
    for (let i = 1; i <= 8; i++) await touch("touchMove", [[cx - 60 + i * 15, cy]]);
    await touch("touchEnd", []);
    await page.waitForTimeout(600);
    let s1 = await page.evaluate(() => window.__state());
    check(`${label}: one-finger drag rotates`, Math.abs(s1.az - s0.az) > 0.1, `azimuth ${s0.az.toFixed(2)} -> ${s1.az.toFixed(2)}`);

    const during = [];
    await touch("touchStart", [[cx - 30, cy], [cx + 30, cy]]);
    for (let i = 1; i <= 8; i++) {
      await touch("touchMove", [[cx - 30 - i * 10, cy], [cx + 30 + i * 10, cy]]);
      await page.waitForTimeout(60);
      during.push((await page.evaluate(() => window.__state().dist)).toFixed(1));
    }
    await touch("touchEnd", []);
    await page.waitForTimeout(1500);
    const s2 = await page.evaluate(() => window.__state());
    check(`${label}: pinch zooms and stays zoomed`, Math.abs(s2.dist - s1.dist) > 1, `distance ${s1.dist.toFixed(1)} -> during [${during.join(", ")}] -> after ${s2.dist.toFixed(1)}`);
    await page.setViewportSize({ width: vp.width, height: vp.height - 60 });   // phone URL bar collapsing
    await page.waitForTimeout(800);
    const s2b = await page.evaluate(() => window.__state());
    check(`${label}: zoom survives a resize`, Math.abs(s2b.dist - s2.dist) < 1, `distance ${s2.dist.toFixed(1)} -> ${s2b.dist.toFixed(1)}`);

    await touch("touchStart", [[cx, cy]]); await touch("touchCancel", []);
    const s3 = await page.evaluate(() => window.__state());
    await touch("touchStart", [[cx - 60, cy]]);
    for (let i = 1; i <= 8; i++) await touch("touchMove", [[cx - 60 + i * 15, cy + 2]]);
    await touch("touchEnd", []);
    await page.waitForTimeout(600);
    const s4 = await page.evaluate(() => window.__state());
    check(`${label}: drag still rotates after a cancelled touch`, Math.abs(s4.az - s3.az) > 0.1, `azimuth ${s3.az.toFixed(2)} -> ${s4.az.toFixed(2)}`);

    const before = await page.evaluate(() => window.__state());
    await page.click("#v-top");
    await page.waitForTimeout(600);
    const top = await page.evaluate(() => window.__state());
    check(`${label}: Top button looks down`, top.polar < 0.35 && top.view === "top", `polar ${before.polar.toFixed(2)} -> ${top.polar.toFixed(2)}`);
    await page.click("#v-clip");
    await page.waitForTimeout(600);
    const clip = await page.evaluate(() => window.__state());
    check(`${label}: Leash clip button swings round`, Math.abs(clip.az - top.az) > 0.5 || Math.abs(clip.polar - top.polar) > 0.5, `az ${top.az.toFixed(2)} -> ${clip.az.toFixed(2)}`);
    await ctx.close();
  }

  // artifact iframe: starts 0x0, sized after 500 ms; scene must still frame itself
  const ctx = await browser.newContext({ viewport: { width: 412, height: 915 } });
  const page = await ctx.newPage();
  await page.goto(`http://127.0.0.1:${PORT}/iframe-host.html`);
  const frame = await (await page.waitForSelector("#f")).contentFrame();
  try {
    await frame.waitForFunction(() => window.__state && window.__state().ready && window.__state().w > 100, null, { timeout: 45000 });
  } catch {
    const st = await frame.evaluate(() => (window.__state ? window.__state() : "no __state")).catch((e) => e.message);
    check("iframe 0x0 start: viewer framed itself after resize", false, `url ${frame.url()} state ${JSON.stringify(st)}`);
    await browser.close(); process.exit(1);
  }
  await page.waitForTimeout(1500);
  const shot = await (await frame.$("#stage")).screenshot();
  const cov = coverage(shot);
  if (cov) check("iframe 0x0 start: model visible after resize", cov.frac > 0.08, `coverage ${(cov.frac * 100).toFixed(1)}%`);
  else check("iframe 0x0 start: viewer ready after resize", true, "pngjs missing, readiness only");
  await ctx.close();
} finally {
  await browser.close();
}
if (!PNG) console.log("NOTE: pngjs not found, pixel checks skipped");
process.exit(results.every(Boolean) && results.length ? 0 : 1);
