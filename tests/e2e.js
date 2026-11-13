// Spielt alle Modi auf iPhone- und Android-Viewport durch und macht Screenshots jedes Screens.
// Aufruf: node tests/e2e.js [baseURL] [outDir]
const { chromium, devices } = require('playwright');
const base = process.argv[2] || 'http://localhost:8765/';
const out = process.argv[3] || 'tests/shots';
require('fs').mkdirSync(out, { recursive: true });
const errors = [];
async function playQuestion(p, shot) {
  const typ = await p.evaluate(() => document.querySelector('.kicker')?.textContent || '');
  if (await p.$('#rg')) { await p.locator('#rg').fill('620'); await shot('q-schaetzen'); await p.click('#go'); }
  else if (await p.$('#tl')) { await shot('q-zeitstrahl'); await p.click('[data-m="0"][data-d="1"]'); await p.click('#go'); }
  else if (await p.$('#hint')) { await p.click('#hint'); await shot('q-folge'); await p.locator('.opt').nth(1).click(); }
  else { await p.locator('.opt').nth(0).click(); await p.locator('[data-c="1"]').click(); await shot(typ.includes('Wer') ? 'q-wer' : 'q-mc'); await p.click('#go'); }
  await p.waitForSelector('.aha'); await p.waitForTimeout(700); await shot('aha-' + typ.replace(/\W+/g, '').slice(0, 10));
  await p.click('#next');
}
(async () => {
  const b = await chromium.launch();
  for (const [name, dev] of [['iphone', devices['iPhone 13']], ['android', devices['Pixel 7']]]) {
    const ctx = await b.newContext({ ...dev, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    p.on('pageerror', e => errors.push(`${name}: ${e.message}`));
    p.on('console', m => { if (m.type() === 'error') errors.push(`${name} console: ${m.text()}`); });
    let n = 0; const shot = async s => { await p.waitForTimeout(250); await p.screenshot({ path: `${out}/${name}-${String(++n).padStart(2, '0')}-${s}.png`, fullPage: true }); };
    await p.goto(base); await p.waitForSelector('.home-top'); await p.waitForTimeout(500); await shot('home');
    await p.click('text=Los geht'); 
    for (let i = 0; i < 5; i++) { await p.waitForSelector('.q-text, .q-quote'); await playQuestion(p, shot); }
    await p.waitForSelector('.score-big'); await shot('ergebnis');
    await p.goto(base + '#/'); await p.waitForSelector('.home-top'); await shot('home-fertig');
    await p.goto(base + '#/frei'); await p.waitForSelector('#go'); await p.locator('#th .chip').first().click(); await shot('frei');
    await p.locator('#th .chip').first().click(); await p.click('#go');
    for (let i = 0; i < 5; i++) { await p.waitForSelector('.q-text, .q-quote'); await playQuestion(p, async s => { if (i < 1) await shot('frei-' + s); }); }
    await p.waitForSelector('.score-big'); await shot('frei-ergebnis');
    await p.goto(base + '#/'); await p.waitForSelector('.home-top'); await p.goto(base + '#/frei'); await p.waitForSelector('#hc'); await p.click('#hc'); await p.waitForTimeout(800); await shot('erste-stunde');
    await p.goto(base + '#/himmel'); await p.waitForSelector('.sky'); await shot('himmel');
    await p.locator('.star.lit').first().click().catch(() => p.locator('.star').first().click()); await p.waitForTimeout(400); await shot('himmel-karte');
    await p.goto(base + '#/profil'); await p.waitForSelector('.switch'); await shot('profil');
    await p.goto(base + '#/duell/2026-11-11/300'); await p.waitForTimeout(600); await shot('duell');
    await ctx.close();
  }
  await b.close();
  console.log(errors.length ? 'FEHLER:\n' + errors.join('\n') : 'keine JS-Fehler');
})();
