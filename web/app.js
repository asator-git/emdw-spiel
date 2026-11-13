// Fünf am Tag – das Erklär-mir-die-Welt-Spiel. Vanilla JS, kein Build-Schritt, kein Backend.
const $app = document.getElementById('app');
const TZ = 'Europe/Vienna';
const NF = new Intl.NumberFormat('de-AT');
const VER = 1;

// ---------- Speicher (localStorage, immer mit try/catch) ----------
const KEY = 'emdw-spiel-v1';
const blank = () => ({ days: {}, streak: { cur: 0, best: 0, last: '' }, seen: {}, calib: [], settings: { vibe: true, sound: false }, free: 0, logoTaps: 0 });
let S = blank();
try { S = Object.assign(blank(), JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { /* privat/gesperrt: dann eben ohne Gedächtnis */ }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { } };

// ---------- Helfer ----------
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const today = () => new Intl.DateTimeFormat('sv-SE', { timeZone: TZ }).format(new Date());
const fmtDate = (d, opt = { weekday: 'long', day: 'numeric', month: 'long' }) => new Date(d + 'T12:00:00').toLocaleDateString('de-AT', opt);
const year = d => d.slice(0, 4);
const mmss = t => { t = Math.max(0, Math.round(t)); const h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), s = t % 60; return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s).padStart(2, '0'); };
function rng(seed) { let h = 1779033703 ^ seed.length; for (let i = 0; i < seed.length; i++) { h = Math.imul(h ^ seed.charCodeAt(i), 3432918353); h = h << 13 | h >>> 19; }
  return () => { h = Math.imul(h ^ h >>> 16, 2246822507); h = Math.imul(h ^ h >>> 13, 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; }; }
const shuffle = (a, r) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const vibe = p => { if (S.settings.vibe && navigator.vibrate) try { navigator.vibrate(p); } catch (e) { } };
let actx;
function tone(kind) {
  if (!S.settings.sound) return;
  try { actx = actx || new (window.AudioContext || window.webkitAudioContext)();
    const seq = kind === 'good' ? [523, 784] : kind === 'tap' ? [440] : [330, 262];
    seq.forEach((f, i) => { const o = actx.createOscillator(), g = actx.createGain(); o.type = 'triangle'; o.frequency.value = f;
      g.gain.setValueAtTime(.0001, actx.currentTime + i * .09); g.gain.exponentialRampToValueAtTime(.12, actx.currentTime + i * .09 + .01);
      g.gain.exponentialRampToValueAtTime(.0001, actx.currentTime + i * .09 + .18); o.connect(g).connect(actx.destination); o.start(actx.currentTime + i * .09); o.stop(actx.currentTime + i * .09 + .2); });
  } catch (e) { }
}
function toast(msg) { document.querySelector('.toast')?.remove(); const t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); t.textContent = msg; document.body.append(t); setTimeout(() => t.remove(), 2600); }

// ---------- Scribbles aus der CI (inline, damit sie die Farbe annehmen) ----------
const SCR = {};
async function scribble(name) { if (!SCR[name]) SCR[name] = fetch(`img/scribbles/${name}.svg`).then(r => r.text()).catch(() => ''); return SCR[name]; }
const ARROW = '<svg class="arrow" viewBox="0 0 34 14" aria-hidden="true"><path d="M1 7.5c9-.8 19-1.2 30-.6M24 1.5c2.6 2 5 3.6 8.4 5.4-3 1.6-5.6 3.4-8 5.6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>';
const PLAY = '<svg viewBox="0 0 22 22" aria-hidden="true"><path d="M5 3.2c5.4 2.4 9.6 5 13.6 7.9-4.2 2.8-8.4 5.4-13.4 7.8-.6-5.2-.7-10.4-.2-15.7z" fill="currentColor"/></svg>';
async function markWith(el, name, cls) {
  const svg = await scribble(name); if (!svg) return;
  const w = document.createElement('span'); w.className = 'mark-wrap ' + cls; w.setAttribute('aria-hidden', 'true'); w.innerHTML = svg;
  el.append(w);
}

// ---------- Daten ----------
const cache = {};
const getJSON = u => cache[u] || (cache[u] = fetch(u).then(r => { if (!r.ok) throw new Error(u); return r.json(); }));
const meta = () => getJSON('data/meta.json');
const pool = () => getJSON('data/pool.json');
async function dayRound(d) {
  try { const m = await getJSON(`data/days/${d.slice(0, 7)}.json`); if (m[d]) return { ...m[d], date: d }; } catch (e) { }
  // Fallback, falls der Plan ausläuft: deterministisch aus dem Datum
  const [P, M] = await Promise.all([pool(), meta()]);
  return { ...makeRound(P, M, () => true, rng('emdw-' + d)), date: d };
}
const epMap = M => M._map || (M._map = Object.fromEntries(M.eps.map(e => [e.id, e])));

// Runde aus dem Pool bauen (freier Modus, Hardcore, Fallback) – gleiche Dramaturgie wie die Tagesrunde
function makeRound(P, M, filter, r, opt = {}) {
  const E = epMap(M), cand = shuffle(P.filter(filter), r), used = new Set(), eps = new Set(), qs = [];
  const take = (f, typ, extra = () => ({})) => { const q = cand.find(q => !used.has(q.id) && !eps.has(q.e) && f(q)); if (!q) return; used.add(q.id); eps.add(q.e); qs.push({ ...q, typ, ...extra(q) }); };
  const person = n => n.split(' ').length >= 2 && n !== 'Andreas Sator';
  const guestsOf = q => { const th = E[q.e].th; let g = [...new Set(M.eps.filter(x => x.th === th && x.id !== q.e).flatMap(x => x.g))].filter(n => person(n) && !E[q.e].g.includes(n));
    if (g.length < 3) g = [...new Set(M.eps.flatMap(x => x.g))].filter(n => person(n) && !E[q.e].g.includes(n)); return [q.sp, ...shuffle(g, r).slice(0, 3)]; };
  const sibs = q => [q.e, ...shuffle(M.eps.filter(x => x.th === E[q.e].th && x.id !== q.e && x.th >= 0).map(x => x.id), r).slice(0, 3)];
  const plan = opt.only === 'ep' ? ['est', 'mc', 'wer', 'mc', 'mc'] : ['est', 'mc', 'wer', 'folge', 'zeit'];
  for (const typ of plan) {
    if (typ === 'est') take(q => q.n, 'est');
    else if (typ === 'mc') take(q => true, 'mc');
    else if (typ === 'wer') take(q => q.wer, 'wer', q => ({ opts: guestsOf(q) }));
    else if (typ === 'folge') take(q => q.fo, 'folge', q => ({ opts: sibs(q) }));
    else if (typ === 'zeit') {
      const items = [], ys = new Set();
      for (const q of cand) { const y = +year(E[q.e].dt); if (used.has(q.id) || eps.has(q.e) || [...ys].some(x => Math.abs(x - y) < 2)) continue; items.push(q); ys.add(y); used.add(q.id); if (items.length === 3) break; }
      if (items.length === 3) { items.forEach(q => eps.add(q.e)); qs.push({ typ: 'zeit', id: 'z', items: items.map(q => ({ id: q.id, e: q.e, st: q.st, aha: q.aha, t: q.t })) }); }
    }
  }
  while (qs.length < 5) { const before = qs.length; take(q => true, 'mc'); if (qs.length === before) break; }
  const need = new Set(qs.flatMap(q => [q.e, ...(q.typ === 'folge' ? q.opts : []), ...(q.items || []).map(z => z.e)]).filter(Boolean));
  return { q: qs, eps: Object.fromEntries([...need].map(id => [id, E[id]])) };
}

// ---------- Punkte ----------
const CONF = [{ p: .4, b: 'Bauch­gefühl', s: 'eher geraten' }, { p: .7, b: 'Ziemlich', s: 'sicher' }, { p: .95, b: 'Bomben', s: 'sicher' }];
const calibPts = (ok, p) => Math.round(60 * ok + 40 * (1 - (ok - p) ** 2));
function estPts(g, n) { const [v, , lo, hi, lg] = n; const err = lg ? Math.abs(Math.log(g) - Math.log(v)) / (Math.log(hi) - Math.log(lo)) : Math.abs(g - v) / (hi - lo); return Math.round(100 * Math.max(0, 1 - err * 3.4)); }
const cell = p => p >= 85 ? 3 : p >= 55 ? 2 : p >= 25 ? 1 : 0;
const EMO = ['⬜', '🟦', '🟦', '🟨'];

// ---------- Zahlen am Schieberegler ----------
function sliderVal(n, pos) { const [, , lo, hi, lg] = n; const v = lg ? Math.exp(Math.log(lo) + pos * (Math.log(hi) - Math.log(lo))) : lo + pos * (hi - lo); return niceRound(v, n); }
function sliderPos(n, v) { const [, , lo, hi, lg] = n; return lg ? (Math.log(v) - Math.log(lo)) / (Math.log(hi) - Math.log(lo)) : (v - lo) / (hi - lo); }
function niceRound(v, n) {
  const [, unit, lo, hi, lg] = n;
  if (isYear(n)) return Math.round(v);
  if (lg) { const mag = Math.pow(10, Math.floor(Math.log10(Math.max(v, 1e-9))) - 1); return Math.round(v / mag) * mag; }
  const span = hi - lo, step = span <= 2 ? .01 : span <= 20 ? .1 : span <= 300 ? 1 : Math.pow(10, Math.floor(Math.log10(span)) - 2);
  return Math.round(v / step) * step;
}
const isYear = n => n[2] >= 1000 && n[3] <= 2200 && !n[4];
function fmtNum(v, unit, n) {
  if ((n && isYear(n)) || (/jahr/i.test(unit || '') && v > 1000 && v < 2200 && Number.isInteger(v))) return String(Math.round(v));
  const a = Math.abs(v);
  if (a >= 1e9) return NF.format(+(v / 1e9).toFixed(a >= 1e10 ? 0 : 1)) + ' Mrd.';
  if (a >= 1e6) return NF.format(+(v / 1e6).toFixed(a >= 1e7 ? 0 : 1)) + ' Mio.';
  return NF.format(+v.toPrecision(a >= 100 ? 4 : 3));
}

// ---------- Rahmen ----------
function frame(inner, { tl = 'Erklär', tr = 'mir', cls = '', back = true } = {}) {
  const left = back ? `<button type="button" data-go="#/" aria-label="Zur Startseite">← ${esc(tl)}</button>` : esc(tl);
  return `<main id="main" class="screen ${cls}" tabindex="-1"><p class="corner corner--tl">${left}</p><p class="corner corner--tr">${tr}</p>${inner}</main>`;
}
let firstMount = true;
function mount(html) {
  $app.innerHTML = html;
  if (firstMount) { $app.querySelector('main')?.classList.add('no-anim'); firstMount = false; }  // erster Bildschirm sofort, ohne Einblenden (LCP)
  const m = $app.querySelector('main'); m?.focus({ preventScroll: true }); window.scrollTo(0, 0);
  $app.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => { location.hash = b.dataset.go; }));
  return m;
}

// ---------- Router ----------
async function route() {
  const h = location.hash.replace(/^#\/?/, '');
  const [p, a, b] = h.split('/');
  try {
    if (p === 'spiel') return playDaily();
    if (p === 'frei') return freeMenu();
    if (p === 'himmel') return sky(a);
    if (p === 'profil') return profile();
    if (p === 'duell') { sessionStorage.setItem('emdw-duel', JSON.stringify({ d: a, s: +b || 0 })); location.replace('#/'); return; }
    return home();
  } catch (e) { console.error(e); mount(frame(`<h2>Da hat was <mark>nicht</mark> geklappt.</h2><p>Lad die Seite bitte neu. Wenn\'s wieder passiert: Funkloch oder ein Fehler von mir.</p><button class="btn" data-go="#/">Zur Startseite</button>`)); }
}
addEventListener('hashchange', route);

// ---------- Start ----------
function streakAlive() { const d = today(); const y = new Date(Date.parse(d + 'T12:00:00Z') - 864e5).toISOString().slice(0, 10); return S.streak.last === d || S.streak.last === y ? S.streak.cur : 0; }
function duelInfo() { try { return JSON.parse(sessionStorage.getItem('emdw-duel') || 'null'); } catch (e) { return null; } }

async function home() {
  const d = today(), st = S.days[d], done = st?.done;
  const seen = Object.keys(S.seen).length;
  const md = d.slice(5);
  const egg = md === '03-28' ? `<p class="egg">Heute vor ${+d.slice(0, 4) - 2018} Jahren ist die erste Folge erschienen. Alles Gute, EMDW!</p>` : '';
  const duel = duelInfo();
  const duelBox = duel && done && duel.d === d ? `<div class="duel"><b>${st.score > duel.s ? 'Du hast gewonnen' : st.score === duel.s ? 'Unentschieden' : 'Knapp verloren'}</b><span>Die Herausforderung: ${duel.s} Punkte. Du: ${st.score}.</span></div>` : duel && !done ? `<div class="duel"><b>Du wurdest herausgefordert</b><span>${duel.d === d ? `Jemand hat die heutige Runde mit <strong>${duel.s} Punkten</strong> gespielt. Geht da mehr?` : `Die Runde vom ${fmtDate(duel.d, { day: 'numeric', month: 'long' })} ist vorbei – aber die heutige wartet.`}</span></div>` : '';
  mount(frame(`
    <div class="home-top">
      <button type="button" class="logo-btn" aria-label="Erklär mir die Welt" style="background:none;border:0;padding:0;justify-self:start"><img class="home-logo" src="img/logo/logo3-creme.svg" alt="Erklär mir die Welt" width="190" height="104"></button>
      <p class="home-date">${esc(fmtDate(d))}</p>
    </div>
    <h1>Fünf<br>am <mark>Tag</mark></h1>
    ${egg}
    <p class="home-lead">${done ? `Heute schon erledigt: <strong>${st.score} von 500</strong>. Die nächste Runde kommt um Mitternacht.` : `Fünf Fragen aus über 400 Folgen. Schätzen, einordnen, dazulernen – und dann die Stelle in der Folge anhören.`}</p>
    ${duelBox}
    ${done ? `<div class="row"><button class="btn" id="share">Ergebnis teilen</button><button class="btn btn--ghost" data-go="#/spiel">Ansehen</button></div>`
           : `<button class="btn" data-go="#/spiel">${st?.answers?.length ? 'Weiterspielen' : 'Los geht\'s'} ${ARROW}</button>`}
    <div class="stats" role="group" aria-label="Deine Zahlen">
      <div><b>${streakAlive()}</b><span>Tage Serie</span></div>
      <div><b>${S.streak.best}</b><span>Rekord</span></div>
      <div><b>${seen}</b><span>Folgen entdeckt</span></div>
    </div>
    <nav class="menu" aria-label="Mehr spielen">
      <a href="#/frei">Freies Spiel<small>Nach Thema oder Jahrgang, so lang du willst</small>${ARROW}</a>
      <a href="#/himmel">Sternenhimmel<small>Alle Folgen als Sterne. Was du kennst, leuchtet.</small>${ARROW}</a>
      <a href="#/profil">Wie sicher bist du?<small>Deine Kalibrierung, Statistik, Einstellungen</small>${ARROW}</a>
    </nav>`, { back: false, tl: 'Erklär', tr: 'mir' }));
  document.getElementById('share')?.addEventListener('click', () => share(d));
  const lb = $app.querySelector('.logo-btn');
  lb.addEventListener('click', async () => {
    S.logoTaps = (S.logoTaps || 0) + 1; save(); vibe(8);
    if (S.logoTaps % 5 === 0) {
      const P = await pool().catch(() => []); const fr = P.filter(q => q.k === 'andreas_frage');
      const q = fr[Math.floor(Math.random() * fr.length)];
      toast(q ? `Andreas würde jetzt fragen: ${q.qt.length < 140 ? '„' + q.qt + '“' : 'Was ist dein Sinn des Lebens?'}` : 'Andreas würde jetzt fragen: Was ist dein Sinn des Lebens?');
    }
  });
  // Pool und Metadaten im Leerlauf vorladen (für Freies Spiel & Sternenhimmel)
  (window.requestIdleCallback || setTimeout)(() => { meta().catch(() => { }); });
}

// ---------- Tagesrunde ----------
async function playDaily() {
  const d = today();
  const R = await dayRound(d);
  S.days[d] = S.days[d] || { answers: [] };
  const st = S.days[d];
  if (st.done) return result(R, st, { mode: 'daily' });
  runRound(R, st, { mode: 'daily', onDone: () => finishDaily(R, st) });
}
function finishDaily(R, st) {
  const d = R.date;
  st.done = true; st.score = st.answers.reduce((a, x) => a + x.pts, 0);
  if (S.streak.last !== d) { S.streak.cur = streakAlive() + 1; S.streak.last = d; S.streak.best = Math.max(S.streak.best, S.streak.cur); }
  save(); result(R, st, { mode: 'daily' });
}

// Generischer Ablauf für 5 Fragen
function runRound(R, st, opt) {
  const i = st.answers.length;
  if (i >= R.q.length) return opt.onDone();
  const q = R.q[i];
  const r = rng((R.date || 'frei') + q.id);
  const ctx = { R, q, i, r, opt, st, n: R.q.length };
  ({ est: qEst, mc: qMc, wer: qWer, folge: qFolge, zeit: qZeit }[q.typ])(ctx);
}
function prog(i, n) { return `<div class="prog" aria-hidden="true">${Array.from({ length: n }, (_, k) => `<i class="${k < i ? 'done' : k === i ? 'now' : ''}"></i>`).join('')}</div>`; }
const TYPES = { est: ['Schätzfrage', 'Schätz mal'], mc: ['Aha-Frage', 'Wusstest du das?'], wer: ['Wer hat\'s gesagt?', 'Ein Zitat, vier Gäste'], folge: ['Welche Folge?', 'Detektivarbeit'], zeit: ['Zeitstrahl', 'Wann war das Thema?'] };
function head(ctx) {
  const [k, hnd] = TYPES[ctx.q.typ];
  const lab = ctx.opt.mode === 'daily' ? `Frage ${ctx.i + 1} von ${ctx.n}` : ctx.opt.label || 'Freies Spiel';
  return `${prog(ctx.i, ctx.n)}<div class="q-type"><p class="kicker">${k}</p><span class="hand" aria-hidden="true">${hnd}</span></div><p class="sr">${lab}</p>`;
}
function screenFor(ctx, inner) { return mount(frame(head(ctx) + inner, { tl: 'Erklär', tr: ctx.opt.mode === 'daily' ? `${ctx.i + 1}/${ctx.n}` : 'mir' })); }

function record(ctx, ans) {
  ctx.st.answers.push(ans);
  const eps = [ans.e, ...(ans.eps || [])].filter(Boolean);
  eps.forEach(e => { S.seen[e] = (S.seen[e] || 0) + 1; });
  if (ans.conf != null) S.calib.push([CONF[ans.conf].p, ans.ok ? 1 : 0]);
  if (S.calib.length > 600) S.calib = S.calib.slice(-600);
  save();
}

function verdictLine(pts, ok, conf) {
  if (ok != null) ok = !!ok;
  if (ok === false && conf === 2) return 'Bombensicher – und daneben. Passiert den Besten.';
  if (ok === false && conf === 0) return 'Nicht ganz. Aber ehrlich unsicher gewesen, das bringt Punkte.';
  if (ok === false) return 'Leider nein.';
  if (pts >= 98) return 'Genau. Respekt.';
  if (pts >= 85) return conf === 0 ? 'Richtig – und das aus dem Bauch heraus.' : 'Richtig.';
  if (pts >= 55) return 'Ziemlich nah dran.';
  if (pts >= 20) return 'Die Richtung stimmt.';
  return 'Da lagst du daneben – so geht\'s den meisten.';
}
const JUBILAEUM = { '1': 'Die allererste Folge.', '100': 'Folge 100 – die erste Jubiläumsfolge.', '200': 'Folge 200.', '300': 'Jubiläumsfolge 300, mit Herbert Prohaska.', '400': 'Folge 400.' };
function epLine(e, ep) { return `${ep.n ? '#' + ep.n + ' ' : ''}${esc(ep.ti)}${ep.g?.length ? ' – ' + esc(ep.g.join(', ')) : ''} (${year(ep.dt)})`; }
function listenHref(ep, t) { return ep.yt ? `https://www.youtube.com/watch?v=${ep.yt}&t=${Math.max(0, Math.round(t) - 3)}s` : ep.ln; }
function ahaPanel(ctx, { pts, ok, conf, verdict, body, e, t, quote, sp, stand }) {
  const ep = ctx.R.eps[e];
  const jub = ep && JUBILAEUM[ep.n] ? `<p class="hand" style="font-size:22px;margin:0;color:var(--rot)">${JUBILAEUM[ep.n]}</p>` : '';
  return `<section class="aha" aria-labelledby="aha-h">
    <div class="aha-head"><p class="aha-word" id="aha-h">${ok === 0 || ok === false ? 'Hm.' : 'Aha.'}</p><p class="aha-pts">+${pts}<small>Punkte</small></p></div>
    <p class="aha-verdict">${esc(verdict || verdictLine(pts, ok, conf))}</p>
    ${body}
    ${stand ? `<p><span class="stand">${esc(stand)}</span></p>` : ''}
    ${quote ? `<blockquote>${esc(quote)}<cite>${esc(sp)} in ${ep ? epLine(e, ep) : ''}</cite></blockquote>` : (ep ? `<p class="src">Aus ${epLine(e, ep)}</p>` : '')}
    ${jub}
    ${ep ? `<a class="listen" href="${esc(listenHref(ep, t || 0))}" target="_blank" rel="noopener">${PLAY}<span>Stelle anhören<small>${ep.yt ? 'Ab ' + mmss(t || 0) + ' auf YouTube' : 'Folge öffnen, Stelle bei ' + mmss(t || 0)}</small></span></a>` : ''}
    <button class="btn btn--ink" id="next">${ctx.i + 1 < ctx.n ? 'Nächste Frage' : 'Zum Ergebnis'} ${ARROW}</button>
  </section>`;
}
function showAha(ctx, html) {
  const main = $app.querySelector('main');
  main.querySelector('.after')?.remove();
  const w = document.createElement('div'); w.className = 'after'; w.innerHTML = html; main.append(w);
  const sec = w.querySelector('.aha'); sec.setAttribute('tabindex', '-1');
  setTimeout(() => { sec.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }); sec.focus({ preventScroll: true }); }, 380);
  w.querySelector('#next').addEventListener('click', () => { vibe(8); runRound(ctx.R, ctx.st, ctx.opt); });
}
function feedback(ok) { if (ok) { vibe([18, 50, 28]); tone('good'); } else { vibe(40); tone('bad'); } }

// ---- Typ 1: Schätzfrage ----
function qEst(ctx) {
  const q = ctx.q, n = q.n, unit = n[1];
  let pos = .5, val = sliderVal(n, pos);
  screenFor(ctx, `
    <h2 class="q-text">${esc(q.q)}</h2>
    <div class="est">
      <p class="est-val" aria-hidden="true"><span id="ev">${fmtNum(val, unit, n)}</span><small>${esc(unit)}</small></p>
      <label class="sr" for="rg">Deine Schätzung in ${esc(unit)}</label>
      <input class="est-range" id="rg" type="range" min="0" max="1000" step="1" value="500" aria-valuetext="${fmtNum(val, unit, n)} ${esc(unit)}">
      <div class="est-scale" aria-hidden="true"><span>${fmtNum(n[2], unit, n)}</span>${n[4] ? '<span class="hand" style="font-size:16px">logarithmisch</span>' : ''}<span>${fmtNum(n[3], unit, n)}</span></div>
      <div class="est-steps"><button type="button" id="dn" aria-label="Etwas weniger">−</button><button type="button" id="up" aria-label="Etwas mehr">+</button></div>
      <button class="btn" id="go">Schätzung abgeben</button>
    </div>`);
  const rg = document.getElementById('rg'), ev = document.getElementById('ev');
  const upd = () => { val = sliderVal(n, pos); ev.textContent = fmtNum(val, unit, n); rg.setAttribute('aria-valuetext', `${fmtNum(val, unit, n)} ${unit}`); };
  let lastBuzz = 0;
  rg.addEventListener('input', () => { pos = rg.value / 1000; upd(); const now = Date.now(); if (now - lastBuzz > 90) { vibe(3); lastBuzz = now; } });
  document.getElementById('dn').addEventListener('click', () => { pos = Math.max(0, pos - .01); rg.value = pos * 1000; upd(); vibe(5); });
  document.getElementById('up').addEventListener('click', () => { pos = Math.min(1, pos + .01); rg.value = pos * 1000; upd(); vibe(5); });
  document.getElementById('go').addEventListener('click', () => {
    const pts = estPts(val, n); rg.disabled = true; $app.querySelectorAll('.est-steps button, #go').forEach(b => b.remove());
    const tp = Math.min(98, Math.max(2, sliderPos(n, n[0]) * 100)), yp = Math.min(98, Math.max(2, pos * 100));
    const rv = document.createElement('div'); rv.className = 'est-reveal'; rv.setAttribute('aria-hidden', 'true');
    rv.innerHTML = `<div class="bar"></div><span class="pin pin--you" style="left:${yp}%">du</span><span class="pin pin--true" style="left:${yp}%">${fmtNum(n[0], unit, n)}</span>`;
    $app.querySelector('.est').append(rv); requestAnimationFrame(() => requestAnimationFrame(() => { rv.querySelector('.pin--true').style.left = tp + '%'; }));
    feedback(pts >= 55);
    record(ctx, { id: q.id, typ: 'est', e: q.e, pts, g: val });
    const vv = pts >= 96 ? 'Punktgenau.' : pts >= 80 ? 'Sehr nah dran.' : pts >= 55 ? 'Nicht weit weg.' : pts >= 25 ? 'Die Richtung stimmt.' : 'Da lagst du daneben – so geht\'s vielen.';
    showAha(ctx, ahaPanel(ctx, { pts, verdict: `${vv} Die Antwort: ${fmtNum(n[0], unit, n)}${isYear(n) ? '' : ' ' + unit}.`, body: `<p>${esc(q.aha)}</p>`, e: q.e, t: q.t, quote: q.qt, sp: q.sp, stand: q.stand }));
  });
}

// ---- Typ 2 + 3: Auswahl mit „Wie sicher bist du?“ ----
function choice(ctx, { title, options, rightIdx, labels, after }) {
  let pick = -1, conf = -1;
  const order = shuffle(options.map((_, k) => k), ctx.r);
  screenFor(ctx, `${title}
    <div class="opts" role="group" aria-label="Antworten">${order.map((k, j) => `<button type="button" class="opt" data-k="${k}" aria-pressed="false"><span class="k" aria-hidden="true">${'abcd'[j]}</span><span>${labels(k)}</span></button>`).join('')}</div>
    <fieldset class="conf" id="conf" hidden><legend>Wie sicher bist du?</legend>
      <div class="seg">${CONF.map((c, k) => `<button type="button" data-c="${k}" aria-pressed="false"><b>${c.b}</b>${c.s}</button>`).join('')}</div>
      ${S.calib.length < 12 ? `<p class="conf-hint">Ehrlich sein zahlt sich aus: Wer bombensicher danebenliegt, bekommt fast nichts. Wer zugibt, dass er rät, bekommt trotzdem Punkte.</p>` : ''}
    </fieldset>
    <button class="btn" id="go" disabled>Antwort einloggen</button>`);
  const opts = [...$app.querySelectorAll('.opt')], cbs = [...$app.querySelectorAll('[data-c]')], go = document.getElementById('go'), cf = document.getElementById('conf');
  const sync = () => { go.disabled = !(pick >= 0 && conf >= 0); };
  opts.forEach(b => b.addEventListener('click', () => { pick = +b.dataset.k; opts.forEach(o => o.setAttribute('aria-pressed', o === b)); vibe(6); tone('tap');
    if (cf.hidden) { cf.hidden = false; setTimeout(() => cf.scrollIntoView({ block: 'nearest', behavior: 'smooth' }), 50); } sync(); }));
  cbs.forEach(b => b.addEventListener('click', () => { conf = +b.dataset.c; cbs.forEach(o => o.setAttribute('aria-pressed', o === b)); vibe(6); sync(); }));
  go.addEventListener('click', () => {
    const ok = pick === rightIdx ? 1 : 0, pts = calibPts(ok, CONF[conf].p);
    opts.forEach(o => { o.disabled = true; const k = +o.dataset.k;
      if (k === rightIdx) { o.classList.add('is-right'); markWith(o, 's80', 'circle'); }
      else if (k === pick) { o.classList.add('is-wrong'); markWith(o, 's11', 'cross'); } else o.classList.add('is-dim'); });
    cbs.forEach(b => b.disabled = true); go.remove(); cf.querySelector('.conf-hint')?.remove();
    feedback(ok);
    after({ ok, pts, conf, pick });
  });
}
function qMc(ctx) {
  const q = ctx.q, options = [q.a, ...q.x];
  choice(ctx, { title: `<h2 class="q-text">${esc(q.q)}</h2>`, options, rightIdx: 0, labels: k => esc(options[k]),
    after: ({ ok, pts, conf }) => { record(ctx, { id: q.id, typ: 'mc', e: q.e, pts, ok, conf });
      showAha(ctx, ahaPanel(ctx, { pts, ok, conf, body: `${ok ? '' : `<p><strong>Richtig ist: ${esc(q.a)}.</strong></p>`}<p>${esc(q.aha)}</p>`, e: q.e, t: q.t, quote: q.qt, sp: q.sp, stand: q.stand })); } });
}
function qWer(ctx) {
  const q = ctx.q, options = q.opts;
  choice(ctx, { title: `<blockquote class="q-quote">${esc(q.qt)}</blockquote><p class="muted" style="margin:0">Wer hat das bei Andreas im Podcast gesagt?</p>`, options, rightIdx: 0, labels: k => esc(options[k]),
    after: ({ ok, pts, conf }) => { record(ctx, { id: q.id, typ: 'wer', e: q.e, pts, ok, conf });
      const ep = ctx.R.eps[q.e];
      showAha(ctx, ahaPanel(ctx, { pts, ok, conf, body: `<p><strong>${esc(q.sp)}</strong>${ep ? ` in der Folge „${esc(ep.ti)}“ (${year(ep.dt)}).` : '.'}</p><p>${esc(q.aha)}</p>`, e: q.e, t: q.t, stand: q.stand })); } });
}

// ---- Typ 4: Welche Folge? (mit Hinweis-Leiter) ----
function qFolge(ctx) {
  const q = ctx.q, opts = q.opts.filter(id => ctx.R.eps[id]), E = ctx.R.eps;
  let hints = 0;
  const order = shuffle(opts, ctx.r);
  screenFor(ctx, `<h2 class="q-text">${esc(q.st)}</h2><p class="muted" style="margin:0">In welcher Folge hast du das gehört?</p>
    <div class="hints" id="hints"></div>
    <div class="opts">${order.map((id, j) => `<button type="button" class="opt" data-id="${id}"><span class="k" aria-hidden="true">${'abcd'[j]}</span><span>${esc(E[id].ti)}<small>${E[id].n ? '#' + E[id].n : 'Sonderfolge'}</small></span></button>`).join('')}</div>
    <button class="btn btn--ghost" id="hint">Tipp holen (−25 Punkte)</button>`);
  const hb = document.getElementById('hint'), hl = document.getElementById('hints'), ep = E[q.e];
  hb.addEventListener('click', () => { hints++; vibe(6);
    hl.insertAdjacentHTML('beforeend', hints === 1 ? `<p class="hint"><b>Jahr:</b> ${year(ep.dt)}</p>` : `<p class="hint"><b>Gast:</b> ${esc(ep.g.join(', ') || 'Andreas allein')}</p>`);
    if (hints >= 2) hb.remove(); });
  $app.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => {
    const ok = b.dataset.id === q.e ? 1 : 0, pts = ok ? 100 - 25 * hints : 0;
    $app.querySelectorAll('.opt').forEach(o => { o.disabled = true; if (o.dataset.id === q.e) { o.classList.add('is-right'); markWith(o, 's80', 'circle'); } else if (o === b) { o.classList.add('is-wrong'); markWith(o, 's11', 'cross'); } else o.classList.add('is-dim'); });
    hb.remove?.(); feedback(ok);
    record(ctx, { id: q.id, typ: 'folge', e: q.e, pts, ok, hints });
    showAha(ctx, ahaPanel(ctx, { pts, ok, verdict: ok ? (hints ? 'Richtig – mit ein bisschen Hilfe.' : 'Richtig, ganz ohne Tipp.') : `Es war „${ep.ti}“.`, body: `<p>${esc(q.aha)}</p>`, e: q.e, t: q.t, quote: q.qt, sp: q.sp, stand: q.stand }));
  }));
}

// ---- Typ 5: Zeitstrahl ----
function qZeit(ctx) {
  const q = ctx.q, E = ctx.R.eps;
  let order = shuffle(q.items, ctx.r);
  const truth = q.items.slice().sort((a, b) => E[a.e].dt.localeCompare(E[b.e].dt)).map(z => z.id);
  if (order.map(z => z.id).join() === truth.join()) order = [order[1], order[2], order[0]];
  screenFor(ctx, `<h2 class="q-text">Wann hat EMDW darüber <mark>geredet?</mark></h2><p class="muted" style="margin:0">Sortier die drei Aussagen nach dem Datum der Folge: die älteste nach oben.</p>
    <div class="tl-axis" aria-hidden="true"><span>früher</span><span>↓</span></div><ol class="tl" id="tl" style="list-style:none;padding:0;margin:0"></ol>
    <div class="tl-axis" aria-hidden="true"><span>später</span><span></span></div>
    <button class="btn" id="go">So passt\'s</button>`);
  const tl = document.getElementById('tl');
  const draw = (fixed) => {
    tl.innerHTML = order.map((z, k) => `<li class="tl-item ${fixed && truth[k] === z.id ? 'ok' : ''}"><span>${esc(z.st)}${!fixed && E[z.e].g?.length ? `<small class="tl-hint">mit ${esc(E[z.e].g.join(', '))}</small>` : ''}</span>
      ${fixed ? '' : `<span class="ctrl"><button type="button" data-m="${k}" data-d="-1" aria-label="Nach oben" ${k === 0 ? 'disabled' : ''}>↑</button><button type="button" data-m="${k}" data-d="1" aria-label="Nach unten" ${k === order.length - 1 ? 'disabled' : ''}>↓</button></span>`}
      ${fixed ? `<span class="when">${fmtDate(E[z.e].dt, { month: 'long', year: 'numeric' })} · ${E[z.e].n ? '#' + E[z.e].n : ''} ${esc(E[z.e].ti)}</span>` : ''}</li>`).join('');
    tl.querySelectorAll('[data-m]').forEach(b => b.addEventListener('click', () => { const k = +b.dataset.m, j = k + +b.dataset.d; [order[k], order[j]] = [order[j], order[k]]; vibe(6); draw(); tl.querySelectorAll('[data-m]')[Math.min(j, 2) * 2 + (+b.dataset.d > 0 ? 1 : 0)]?.focus(); }));
  };
  draw();
  document.getElementById('go').addEventListener('click', () => {
    const right = order.filter((z, k) => truth[k] === z.id).length;
    const pts = right === 3 ? 100 : right === 1 ? 40 : 0;
    document.getElementById('go').remove(); draw(true); feedback(right === 3);
    record(ctx, { id: q.id, typ: 'zeit', pts, ok: right === 3 ? 1 : 0, eps: q.items.map(z => z.e) });
    const sorted = truth.map(id => q.items.find(z => z.id === id));
    const body = sorted.map(z => `<p><strong>${year(E[z.e].dt)}:</strong> ${esc(z.aha)} <a href="${esc(listenHref(E[z.e], z.t))}" target="_blank" rel="noopener">Stelle anhören</a></p>`).join('');
    const ctx2 = { ...ctx };
    showAha(ctx2, ahaPanel(ctx2, { pts, ok: right === 3 ? 1 : 0, verdict: right === 3 ? 'Alles in der richtigen Reihenfolge.' : right === 1 ? 'Eine sitzt. Die Zeit vergeht halt schnell.' : 'Durcheinander – aber jetzt weißt du\'s.', body }));
  });
}

// ---------- Ergebnis & Teilen ----------
function grid(st) { return st.answers.map(a => cell(a.pts)); }
function shareText(d, st) {
  const g = grid(st).map(c => EMO[c]).join('');
  const sure = st.answers.filter(a => a.conf === 2 && a.ok).length;
  const url = location.origin + location.pathname + `#/duell/${d}/${st.score}`;
  return `Fünf am Tag · ${fmtDate(d, { day: 'numeric', month: 'numeric', year: 'numeric' })}\n${g}  ${st.score}/500${sure ? `\nBombensicher und richtig: ${sure}×` : ''}\nSchaffst du mehr? ${url}`;
}
async function share(d) {
  const st = S.days[d]; if (!st?.done) return;
  const text = shareText(d, st);
  try { if (navigator.share) { await navigator.share({ text }); return; } } catch (e) { if (e.name === 'AbortError') return; }
  try { await navigator.clipboard.writeText(text); toast('Kopiert. Jetzt einfügen, wo du willst.'); }
  catch (e) { prompt('Zum Kopieren:', text); }
}
function resultLine(s) {
  if (s >= 480) return 'Das ist fast schon unheimlich.';
  if (s >= 400) return 'Stark. Du hörst offensichtlich gut zu.';
  if (s >= 300) return 'Solide. Ein paar Folgen warten noch auf dich.';
  if (s >= 200) return 'Da ist noch Luft nach oben – und genau dafür gibt\'s ja die Folgen.';
  return 'Ein Tag zum Dazulernen. Morgen gibt\'s fünf neue Fragen.';
}
function calibNote() {
  const c = S.calib, sure = c.filter(x => x[0] === .95);
  if (sure.length < 5) return '';
  const rate = Math.round(100 * sure.reduce((a, x) => a + x[1], 0) / sure.length);
  return `Wenn du „bombensicher“ sagst, liegst du in <strong>${rate} %</strong> der Fälle richtig. ${rate >= 88 ? 'Gut kalibriert.' : rate >= 70 ? 'Ein bisschen übermütig vielleicht.' : 'Da ist Selbstvertrauen im Spiel, das die Fakten nicht ganz hergeben.'}`;
}
function result(R, st, opt) {
  const d = R.date, score = st.answers.reduce((a, x) => a + x.pts, 0);
  const duel = opt.mode === 'daily' ? duelInfo() : null;
  const cmp = duel && duel.d === d ? `<div class="duel"><b>${score > duel.s ? 'Gewonnen' : score === duel.s ? 'Unentschieden' : 'Knapp verloren'}</b><span>Du: ${score} · Herausforderung: ${duel.s}</span></div>` : '';
  if (duel && duel.d === d) sessionStorage.removeItem('emdw-duel');
  const items = R.q.map((q, k) => { const a = st.answers[k] || { pts: 0 };
    const e = q.e || q.items?.[0]?.e, ep = R.eps[e]; const t = q.t ?? q.items?.[0]?.t;
    return `<a href="${ep ? esc(listenHref(ep, t || 0)) : '#'}" target="_blank" rel="noopener"><b>${k + 1}</b><span>${esc(TYPES[q.typ][0])}${ep ? ' · ' + esc(ep.ti) : ''}</span><em>${a.pts}</em></a>`; }).join('');
  mount(frame(`
    <p class="kicker">${opt.mode === 'daily' ? esc(fmtDate(d)) : esc(opt.label || 'Freies Spiel')}</p>
    <p class="score-big" aria-label="${score} von 500 Punkten">${score}<small>/500</small></p>
    <div class="grid5" aria-hidden="true">${grid(st).map((c, k) => `<i class="g${c}">${k + 1}</i>`).join('')}</div>
    <h2>${esc(resultLine(score))}</h2>
    ${cmp}
    ${calibNote() ? `<p>${calibNote()}</p>` : ''}
    ${opt.mode === 'daily' ? `<div class="row"><button class="btn" id="share">Ergebnis teilen</button></div>
       <p class="muted" style="margin:0">Nächste Runde in <span class="countdown" id="cd"></span>. Deine Serie: <strong>${streakAlive()} ${streakAlive() === 1 ? 'Tag' : 'Tage'}</strong>.${streakAlive() === 7 ? ' Eine Woche! Andreas wäre stolz. Wahrscheinlich.' : ''}</p>`
       : `<button class="btn" id="again">Noch eine Runde ${ARROW}</button>`}
    <h3 class="kicker" style="margin-top:8px">Zum Nachhören</h3>
    <div class="recap">${items}</div>
    <nav class="menu"><a href="#/frei">Weiterspielen im freien Modus${ARROW}</a><a href="#/himmel">Sternenhimmel ansehen${ARROW}</a></nav>`, { tr: opt.mode === 'daily' ? 'Ergebnis' : 'mir' }));
  document.getElementById('share')?.addEventListener('click', () => share(d));
  document.getElementById('again')?.addEventListener('click', () => opt.again());
  const cd = document.getElementById('cd');
  if (cd) { const tick = () => { if (!document.body.contains(cd)) return clearInterval(iv);
      const now = new Date(), vienna = new Date(now.toLocaleString('en-US', { timeZone: TZ })); const s = 86400 - (vienna.getHours() * 3600 + vienna.getMinutes() * 60 + vienna.getSeconds());
      cd.textContent = `${Math.floor(s / 3600)}:${String(Math.floor(s % 3600 / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`; };
    const iv = setInterval(tick, 1000); tick(); }
  if (score === 500 && opt.mode === 'daily') toast('500 von 500. Willst du nicht selbst einen Podcast machen?');
}

// ---------- Freies Spiel ----------
async function freeMenu() {
  mount(frame(`<h1>Freies<br><mark>Spiel</mark></h1><p class="muted" style="margin:0">Lädt …</p>`));
  const M = await meta();
  const years = [...new Set(M.eps.map(e => year(e.dt)))].sort();
  let th = new Set(), ys = new Set();
  mount(frame(`
    <h1>Freies<br><mark>Spiel</mark></h1>
    <p style="margin:0">Such dir aus, worüber du heute mehr wissen willst. Nichts ausgewählt heißt: alles.</p>
    <p class="kicker">Themen</p>
    <div class="chips" id="th">${M.themes.map((t, k) => `<button type="button" class="chip" data-v="${k}" aria-pressed="false">${esc(t)}</button>`).join('')}</div>
    <p class="kicker">Jahrgänge</p>
    <div class="chips" id="ys">${years.map(y => `<button type="button" class="chip" data-v="${y}" aria-pressed="false">${y}</button>`).join('')}</div>
    <button class="btn" id="go">Fünf Fragen ${ARROW}</button>
    <button type="button" class="hardcore" id="hc"><b>Erste Stunde</b><span>Nur Folgen aus 2018 und 2019, nur schwere Fragen. Für alle, die von Anfang an dabei sind.</span></button>`));
  const bind = (id, set) => $app.querySelectorAll(`#${id} .chip`).forEach(b => b.addEventListener('click', () => { const v = b.dataset.v; set.has(v) ? set.delete(v) : set.add(v); b.setAttribute('aria-pressed', set.has(v)); vibe(5); }));
  bind('th', th); bind('ys', ys);
  document.getElementById('go').addEventListener('click', () => {
    const label = [...[...th].map(k => M.themes[k]), ...ys].join(', ') || 'Alles durcheinander';
    freeRound(q => { const e = epMap(M)[q.e]; return (!th.size || th.has(String(e.th))) && (!ys.size || ys.has(year(e.dt))); }, label);
  });
  document.getElementById('hc').addEventListener('click', () => freeRound(q => { const e = epMap(M)[q.e]; return +year(e.dt) <= 2019 && q.d >= 2; }, 'Erste Stunde (2018–2019)', true));
}
async function freeRound(filter, label, hard, only) {
  const [P, M] = await Promise.all([pool(), meta()]);
  const avail = P.filter(filter);
  if (avail.length < 8) { toast('Dafür gibt\'s noch zu wenige Fragen. Nimm noch ein Thema oder Jahr dazu.'); return; }
  const seed = 'frei-' + Date.now();
  const R = { ...makeRound(P, M, filter, rng(seed), { only }), date: seed };
  if (hard) R.q.forEach(q => { if (q.typ === 'folge') q.hard = 1; });
  const st = { answers: [] };
  S.free = (S.free || 0) + 1; save();
  history.replaceState(null, '', '#/frei/runde');
  const opt = { mode: 'free', label, again: () => freeRound(filter, label, hard, only) };
  opt.onDone = () => result(R, st, opt);
  runRound(R, st, opt);
}

// ---------- Sternenhimmel ----------
async function sky(sel) {
  mount(frame(`<h1>Sternen<br><mark>himmel</mark></h1><p class="muted">Lädt …</p>`));
  const M = await meta();
  const W = 360, H = 640, cols = 2, rows = 5, cw = W / cols, ch = H / rows;
  const byTh = M.themes.map((_, k) => M.eps.filter(e => e.th === k).sort((a, b) => a.dt.localeCompare(b.dt)));
  let svg = '';
  byTh.forEach((list, k) => {
    const cx = (k % cols) * cw + cw / 2, cy = Math.floor(k / cols) * ch + ch / 2 + 8;
    const r = rng('sky' + k), pts = [];
    list.forEach((e, j) => { // goldener Winkel: gleichmäßige, natürlich wirkende Verteilung
      const a = j * 2.39996 + r() * .5, d = 9 + Math.sqrt(j / Math.max(1, list.length)) * (Math.min(cw, ch) / 2 - 18) + r() * 4;
      pts.push([cx + Math.cos(a) * d * 1.18, cy + Math.sin(a) * d * .82, e]); });
    // Sternbild-Linie: die fünf meistgespielten bzw. die ersten Folgen verbinden
    const lit = pts.filter(p => S.seen[p[2].id]);
    const chain = (lit.length >= 2 ? lit : pts.slice(0, 5)).slice(0, 7).sort((a, b) => a[0] - b[0]);
    if (chain.length > 1) svg += `<path class="cline" d="M${chain.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L')}"/>`;
    svg += pts.map(([x, y, e]) => { const on = !!S.seen[e.id]; const rr = 1.6 + (e.n && e.n % 100 === 0 ? 1.4 : 0) + (on ? .9 : 0);
      return `<g class="star${on ? ' lit' : ''}${sel === e.id ? ' sel' : ''}" data-id="${e.id}" tabindex="0" role="button" aria-label="${esc((e.n ? 'Folge ' + e.n + ': ' : '') + e.ti)}${on ? ', schon entdeckt' : ''}">
        ${on ? `<circle class="glow" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rr * 3}"/>` : ''}<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rr}"/><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9" fill="transparent"/></g>`; }).join('');
    svg += `<text class="label" x="${(k % cols) * cw + 10}" y="${Math.floor(k / cols) * ch + 18}">${esc(M.themes[k])}</text><text class="label-n" x="${(k % cols) * cw + 10}" y="${Math.floor(k / cols) * ch + 30}">${lit.length} / ${list.length}</text>`;
  });
  const seen = M.eps.filter(e => S.seen[e.id]).length;
  mount(frame(`
    <h1>Sternen<br><mark>himmel</mark></h1>
    <p style="margin:0">Jede Folge ist ein Stern, jedes Thema ein Sternbild. Sobald du eine Frage aus einer Folge gespielt hast, leuchtet sie auf. <strong>${seen} von ${M.eps.length}</strong> hast du schon entdeckt.</p>
    <div class="legend" aria-hidden="true"><span><i style="background:var(--gelb)"></i>entdeckt</span><span><i style="background:rgba(172,218,239,.5)"></i>noch dunkel</span></div>
    <div class="sky-wrap"><svg class="sky" viewBox="0 0 ${W} ${H}" role="group" aria-label="Sternenhimmel aller Folgen">${svg}</svg></div>
    <div id="card" aria-live="polite"></div>`, { tr: 'mir' }));
  const card = document.getElementById('card'), E = epMap(M);
  const open = id => { const e = E[id]; if (!e) return; $app.querySelectorAll('.star').forEach(s => s.classList.toggle('sel', s.dataset.id === id)); vibe(5);
    card.innerHTML = `<div class="sky-card"><p class="kicker" style="color:var(--blau)">${e.n ? 'Folge ' + e.n : 'Sonderfolge'} · ${fmtDate(e.dt, { month: 'long', year: 'numeric' })} · ${esc(M.themes[e.th] || '')}</p><h3>${esc(e.ti)}</h3>
      ${e.g.length ? `<p style="margin:0">mit ${esc(e.g.join(', '))}</p>` : ''}${e.su ? `<p style="margin:0">${esc(e.su)}</p>` : ''}
      <div class="row"><a class="listen" href="${esc(e.yt ? 'https://www.youtube.com/watch?v=' + e.yt : e.ln)}" target="_blank" rel="noopener">${PLAY}<span>Folge hören</span></a></div>
      <button class="btn btn--ink" id="epq">Fragen zu dieser Folge</button></div>`;
    document.getElementById('epq').addEventListener('click', () => freeRound(q => q.e === id, `Folge ${e.n || ''}: ${e.ti}`, false, 'ep'));
    card.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); };
  $app.querySelectorAll('.star').forEach(s => { s.addEventListener('click', () => open(s.dataset.id)); s.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(s.dataset.id); } }); });
  if (sel) open(sel);
}

// ---------- Profil ----------
function profile() {
  const c = S.calib, lv = CONF.map(x => { const a = c.filter(y => y[0] === x.p); return { n: a.length, r: a.length ? a.reduce((s, y) => s + y[1], 0) / a.length : null }; });
  const played = Object.values(S.days).filter(x => x.done), avg = played.length ? Math.round(played.reduce((a, x) => a + x.score, 0) / played.length) : 0;
  // Kalibrierungsdiagramm: angegebene Sicherheit (x) gegen tatsächliche Trefferquote (y)
  const X = p => 40 + p * 270, Y = r => 190 - r * 160;
  const dots = lv.map((l, k) => l.n ? `<circle cx="${X(CONF[k].p)}" cy="${Y(l.r)}" r="${Math.min(14, 5 + l.n / 3)}" fill="var(--gelb)"/><text x="${X(CONF[k].p)}" y="${Y(l.r) - 16}" text-anchor="middle">${Math.round(l.r * 100)} %</text>` : '').join('');
  mount(frame(`
    <h1>Wie sicher<br><mark>bist du?</mark></h1>
    <p style="margin:0">Bei jeder Auswahlfrage sagst du, wie sicher du dir bist. Gut kalibriert heißt: Wenn du dir zu 95 % sicher bist, liegst du auch in etwa 95 % der Fälle richtig. Das ist die wichtigste Fähigkeit beim Einordnen von Nachrichten – und die seltenste.</p>
    ${c.length ? `<svg class="calib" viewBox="0 0 330 220" role="img" aria-label="Kalibrierung: ${lv.map((l, k) => l.n ? `${CONF[k].b.replace('­', '')}: ${Math.round(l.r * 100)} Prozent richtig bei ${l.n} Antworten` : '').filter(Boolean).join('; ')}">
      <line x1="40" y1="190" x2="310" y2="190" stroke="var(--line)" stroke-width="2"/><line x1="40" y1="30" x2="40" y2="190" stroke="var(--line)" stroke-width="2"/>
      <line x1="${X(0)}" y1="${Y(0)}" x2="${X(1)}" y2="${Y(1)}" stroke="var(--hell)" stroke-dasharray="4 5" stroke-width="1.5"/>
      <text x="${X(.62)}" y="${Y(.62) + 26}" fill="var(--hell)">perfekt kalibriert</text>
      ${CONF.map(x => `<text x="${X(x.p)}" y="210" text-anchor="middle">${x.b.replace('­', '')}</text>`).join('')}
      <text x="34" y="${Y(1) + 4}" text-anchor="end">100</text><text x="34" y="${Y(.5) + 4}" text-anchor="end">50</text><text x="34" y="${Y(0) + 4}" text-anchor="end">0</text>${dots}</svg>
      <p style="margin:0">${calibNote() || 'Noch zu wenige Antworten für ein Urteil. Spiel ein paar Runden, dann wird das hier spannend.'}</p>` : '<p class="muted">Sobald du gespielt hast, siehst du hier deine Kalibrierungskurve.</p>'}
    <div class="stats"><div><b>${played.length}</b><span>Tagesrunden</span></div><div><b>${avg}</b><span>Schnitt</span></div><div><b>${S.free || 0}</b><span>freie Runden</span></div></div>
    <div>
      <div class="switch"><span>Vibration</span><button type="button" id="sv" aria-pressed="${S.settings.vibe}">${S.settings.vibe ? 'An' : 'Aus'}</button></div>
      <div class="switch"><span>Töne</span><button type="button" id="ss" aria-pressed="${S.settings.sound}">${S.settings.sound ? 'An' : 'Aus'}</button></div>
    </div>
    <section class="prose"><h2 style="font-size:22px;margin-bottom:10px">Über das Spiel</h2>
      <p>Alle Fragen kommen aus den Transkripten von „Erklär mir die Welt“. Jede steht mit Zeitstempel in einer Folge, und jede wurde ein zweites Mal gegen das Transkript geprüft. Zahlen, die heute anders aussehen würden, tragen den Hinweis „Stand“ mit dem Jahr der Folge.</p>
      <p>Trotzdem kann ein Fehler durchrutschen. Wenn dir einer auffällt: Schreib Andreas, er freut sich (wirklich).</p>
      <p class="muted">Dein Fortschritt bleibt nur auf diesem Gerät. Kein Login, kein Tracking.</p></section>
    <button class="link" id="reset">Fortschritt auf diesem Gerät löschen</button>`, { tr: 'mir' }));
  const tg = (id, k) => document.getElementById(id).addEventListener('click', e => { S.settings[k] = !S.settings[k]; save(); e.target.setAttribute('aria-pressed', S.settings[k]); e.target.textContent = S.settings[k] ? 'An' : 'Aus'; if (k === 'vibe') vibe(20); if (k === 'sound') tone('good'); });
  tg('sv', 'vibe'); tg('ss', 'sound');
  document.getElementById('reset').addEventListener('click', () => { if (confirm('Wirklich alles löschen – Serie, Sterne, Kalibrierung?')) { S = blank(); save(); location.hash = '#/'; } });
}

// ---------- Start ----------
if ('serviceWorker' in navigator && location.protocol === 'https:') addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => { }));
route();
