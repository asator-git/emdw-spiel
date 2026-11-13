#!/usr/bin/env python3
"""Stufe 3: Kuratierung. Geprüfte Kandidaten -> Fragen-Pool + Tagesrunden fürs Spiel.

Regeln:
- nur Kandidaten mit Review-Urteil keep/fix, Qualität >= 3 und maschinell gefundenem Zitat (>= 0.8)
- Korrekturen aus dem Review werden übernommen, „Stand <Jahr>“-Hinweise ebenso
- pro Folge höchstens MAX_PER_EP Einträge (Balance über Folgen/Jahrgänge), bevorzugt Weltwissen und hohe Qualität
- Tagesrunden: feste Dramaturgie (Schätzen, Wie sicher?, Wer hat's gesagt?, Welche Folge?, Zeitstrahl),
  5 verschiedene Folgen, keine Folge zweimal innerhalb von 30 Tagen, kein Eintrag doppelt.
  Bereits veröffentlichte Tage (<= heute) werden nie verändert – nur die Zukunft wird nachgefüllt.
Ausgabe: web/data/meta.json, web/data/pool.json, web/data/days/YYYY-MM.json, data/pool_report.md
"""
import json, re, random, hashlib, datetime, pathlib, collections, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from prompts import THEMEN

ROOT = pathlib.Path(__file__).resolve().parent.parent
D, W = ROOT / 'data', ROOT / 'web/data'
(W / 'days').mkdir(parents=True, exist_ok=True)
MAX_PER_EP = 12
DAYS_AHEAD = 400
TODAY = datetime.date.fromisoformat(os.environ.get('EMDW_TODAY', datetime.date.today().isoformat()))

def ep_link(e, t=None):
    if e.get('youtube'):
        return f"https://www.youtube.com/watch?v={e['youtube']}" + (f"&t={int(t)}s" if t else '')
    return e['link']

def short_title(e):
    t = re.sub(r'^(Jubiläum!\s*)?deep dive\s*#?\d*:?\s*', '', e.get('topic') or '').strip(' -–:')
    if len(t) < 8:  # „deep dive mit X“ -> ganzer Titel ohne Nummer
        t = re.sub(r'^#?\d+\s*', '', e['title'])
    return re.sub(r'\s+', ' ', t).strip()

def load():
    E = {e['id']: e for e in json.loads((D / 'episodes.json').read_text()) if e['in_game']}
    items, themes, summaries = [], {}, {}
    stats = collections.Counter()
    for eid, e in E.items():
        cf, rf = D / f'candidates/{eid}.json', D / f'reviewed/{eid}.json'
        if not cf.exists(): continue
        cd = json.loads(cf.read_text())
        themes[eid], summaries[eid] = cd['theme'], cd['summary']
        if rf.exists():
            rv = {r['i']: r for r in json.loads(rf.read_text())['reviews']}
        elif os.environ.get('EMDW_DEV_UNREVIEWED'):  # nur für lokale UI-Tests, nie fürs Deployment
            rv = {i: {'verdict': 'keep', 'quality': 3} for i in range(len(cd['candidates']))}
        else:
            stats['ohne_review'] += len(cd['candidates']); continue
        for i, c in enumerate(cd['candidates']):
            stats['kandidaten'] += 1
            r = rv.get(i)
            if not r: stats['nicht_ausgewaehlt'] += 1; continue
            if r['verdict'] == 'drop': stats['review_drop'] += 1; continue
            if r['quality'] < 3: stats['qualitaet<3'] += 1; continue
            if c.get('quote_match', 0) < 0.8: stats['zitat_nicht_gefunden'] += 1; continue
            if r['verdict'] == 'fix':
                for k in ('statement', 'question', 'answer', 'distractors', 'aha', 'quote_clean'):
                    if r.get(k): c[k] = r[k]
            if len(c['distractors']) != 3 or c['answer'] in c['distractors']: stats['distraktoren_kaputt'] += 1; continue
            c.update(eid=eid, i=i, quality=r['quality'], stand=r.get('stand_note', ''), verdict=r['verdict'])
            items.append(c)
    return E, items, themes, summaries, stats

EXCLUDED = json.loads((D / 'audit/excluded.json').read_text()) if (D / 'audit/excluded.json').exists() else {}

def choose(E, items):
    items = [c for c in items if f"{c['eid']}-{c['i']}" not in EXCLUDED]
    by_ep = collections.defaultdict(list)
    for c in items: by_ep[c['eid']].append(c)
    keep = []
    for eid, cs in by_ep.items():
        cs.sort(key=lambda c: (-(c['quality'] + (0.6 if c.get('scope') == 'welt' else 0) + (0.3 if c['kind'] == 'zahl' else 0)), c['i']))
        picked, kinds = [], collections.Counter()
        for c in cs:  # Vielfalt der Arten pro Folge
            if kinds[c['kind']] >= 4: continue
            picked.append(c); kinds[c['kind']] += 1
            if len(picked) >= MAX_PER_EP: break
        keep += picked
    return keep

def num_ok(c):
    v, lo, hi = c['number_value'], c['slider_min'], c['slider_max']
    if not (c['kind'] == 'zahl' and isinstance(v, (int, float)) and lo < v < hi): return False
    if c['log_scale'] and lo <= 0: return False
    return True

def entry(c, E):
    e = E[c['eid']]
    q = {'id': f"{c['eid']}-{c['i']}", 'e': c['eid'], 'k': c['kind'], 's': c.get('scope', 'welt'), 'd': c['difficulty'], 'qu': c['quality'],
         'q': c['question'], 'a': c['answer'], 'x': c['distractors'], 'aha': c['aha'], 'st': c['statement'],
         'qt': c['quote_clean'], 'sp': c['speaker'], 't': c['t'], 'tag': c.get('tags', [])[:3]}
    if c['stand']: q['stand'] = c['stand']
    elif c.get('time_sensitive'): q['stand'] = f"Stand {e['date'][:4]}"
    if num_ok(c):
        q['n'] = [c['number_value'], c['number_unit'], c['slider_min'], c['slider_max'], 1 if c['log_scale'] else 0]
    # „Welche Folge?“ nur, wenn der Satz den Folgentitel nicht schon verrät (keine gemeinsamen Wortstämme)
    stems = lambda txt: {w[:5].lower() for w in re.findall(r'[A-Za-zÄÖÜäöüß]{5,}', txt)} - {'erklä', 'welche', 'warum'}
    if c['kind'] in ('aha', 'erklaerung') and not (stems(c['statement']) & stems(short_title(e) + ' ' + ' '.join(e['guests']))):
        q['fo'] = 1
    guest = c['speaker'] not in ('Andreas Sator', 'Andreas') and any(c['speaker'].split()[-1] in g for g in e['guests'])
    if c['kind'] in ('zitat', 'erklaerung') and guest and len(c['speaker'].split()) >= 2 and len(c['quote_clean'].split()) <= 45 and not c['quote_clean'].rstrip().endswith('?'):
        if not any(n.lower() in c['quote_clean'].lower() for n in c['speaker'].split() if len(n) > 3):
            q['wer'] = 1
    return q

def build_meta(E, themes, summaries):
    eps = []
    for eid, e in sorted(E.items(), key=lambda x: x[1]['date']):
        eps.append({'id': eid, 'n': e['num'], 'ti': short_title(e), 'g': e['guests'], 'dt': e['date'],
                    'th': THEMEN.index(themes[eid]) if eid in themes else -1, 'yt': e.get('youtube', ''),
                    'ln': e['link'], 'su': summaries.get(eid, '')})
    return {'themes': THEMEN, 'eps': eps, 'built': TODAY.isoformat()}

# ---------- Tagesrunden ----------
def rng_for(day): return random.Random(int(hashlib.sha256(f'emdw-{day}'.encode()).hexdigest()[:12], 16))

def build_days(pool, meta, E):
    epinfo = {x['id']: x for x in meta['eps']}
    old = {}
    for f in (W / 'days').glob('*.json'):
        old.update(json.loads(f.read_text()))
    used = set()
    days = {d: v for d, v in old.items() if d <= TODAY.isoformat()}  # Vergangenheit + heute: unverändert
    for d, v in days.items():
        for q in v['q']:
            used.add(q.get('id'))
            for z in q.get('items', []): used.add(z['id'])
    recent = collections.deque(maxlen=150)  # ~30 Tage × 5 Folgen
    by = lambda f: [q for q in pool if f(q) and q['id'] not in used]
    day = TODAY + datetime.timedelta(days=0 if TODAY.isoformat() not in days else 1)
    end = TODAY + datetime.timedelta(days=DAYS_AHEAD)
    while day <= end:
        ds = day.isoformat(); R = rng_for(ds)
        def pick(cands, avoid_eps):
            # Ausweichstufen: erst ohne kürzlich gespielte Folgen, sonst nur ohne heutige
            c1 = [q for q in cands if q['e'] not in avoid_eps and q['e'] not in recent]
            cands = c1 or [q for q in cands if q['e'] not in avoid_eps]
            if not cands: return None
            cands.sort(key=lambda q: q['id']); R.shuffle(cands)
            # bevorzugt Themen, die heute noch nicht dran waren
            # Tagesrunde: bevorzugt Qualität 4–5 (aus dem Review), dann Themen, die heute noch fehlen
            cands.sort(key=lambda q: (q.get('qu', 3) < 4, epinfo[q['e']]['th'] in themes_today))
            return cands[0]
        themes_today, eps_today, qs = set(), set(), []
        def take(q, typ, **extra):
            used.add(q['id']); eps_today.add(q['e']); themes_today.add(epinfo[q['e']]['th'])
            qs.append({**q, 'typ': typ, **extra})
        est = pick(by(lambda q: 'n' in q and q['s'] == 'welt' and q['d'] <= 2), eps_today) or pick(by(lambda q: 'n' in q), eps_today)
        if est: take(est, 'est')
        mc = pick(by(lambda q: q['k'] in ('aha', 'erklaerung', 'zahl') and q['s'] == 'welt'), eps_today)
        if mc: take(mc, 'mc')
        wer = pick(by(lambda q: q.get('wer')), eps_today)
        if wer:
            person = lambda g: len(g.split()) >= 2 and g != 'Andreas Sator'
            others = sorted({g for x in meta['eps'] if x['id'] != wer['e'] for g in x['g'] if x['th'] == epinfo[wer['e']]['th'] and person(g)} - set(epinfo[wer['e']]['g']))
            if len(others) < 3: others = sorted({g for x in meta['eps'] if x['id'] != wer['e'] for g in x['g'] if person(g)} - set(epinfo[wer['e']]['g']))
            R.shuffle(others)
            take(wer, 'wer', opts=[wer['sp']] + others[:3])
        fo = pick(by(lambda q: q.get('fo') and q['d'] >= 2), eps_today) or pick(by(lambda q: q.get('fo')), eps_today)
        if fo:
            th = epinfo[fo['e']]['th']
            sib = [x['id'] for x in meta['eps'] if x['th'] == th and x['id'] != fo['e'] and x['id'] in E]
            sib.sort(); R.shuffle(sib)
            take(fo, 'folge', opts=[fo['e']] + sib[:3])
        # Zeitstrahl: drei Aussagen, deren Jahre mind. 2 Jahre auseinanderliegen; zeitgebundene Aussagen
        # (Pandemie, Krieg, „Stand“-Fakten) zuerst, damit man nachdenken kann statt zu raten
        tl, years = [], []
        pool_tl = by(lambda q: q['s'] == 'welt' and q['k'] in ('aha', 'zahl', 'erklaerung'))
        pool_tl.sort(key=lambda q: (not q.get('stand'), q.get('qu', 3) < 4, R.random()))
        for q in pool_tl:
            y = int(epinfo[q['e']]['dt'][:4])
            if any(abs(y - x) < 2 for x in years) or q['e'] in eps_today: continue
            tl.append(q); years.append(y); used.add(q['id'])
            if len(tl) == 3: break
        if len(tl) == 3:
            qs.append({'typ': 'zeit', 'id': 'z-' + ds, 'items': [{'id': q['id'], 'e': q['e'], 'st': q['st'], 'aha': q['aha'], 't': q['t']} for q in tl]})
            eps_today.update(q['e'] for q in tl)
        if len(qs) < 5: print('WARNUNG: Pool reicht nicht mehr für', ds); break
        recent.extend(eps_today)
        days[ds] = {'q': qs}
        day += datetime.timedelta(days=1)
    # pro Monat eine Datei; Folgen-Infos, die die Runde braucht, kommen mit (keine Abhängigkeit von meta.json)
    months = collections.defaultdict(dict)
    for ds, v in days.items():
        need = {q['e'] for q in v['q'] if 'e' in q} | {o for q in v['q'] for o in q.get('opts', []) if o in epinfo} \
               | {z['e'] for q in v['q'] for z in q.get('items', [])}
        v['eps'] = {i: {k: epinfo[i][k] for k in ('n', 'ti', 'g', 'dt', 'yt', 'ln', 'th')} for i in sorted(need)}
        months[ds[:7]][ds] = v
    for m, v in months.items():
        (W / f'days/{m}.json').write_text(json.dumps(v, ensure_ascii=False, separators=(',', ':')))
    return days

def report(E, items, keep, pool, stats, meta, days):
    th = collections.Counter(meta['themes'][next(x['th'] for x in meta['eps'] if x['id'] == q['e'])] for q in pool)
    yr = collections.Counter(next(x['dt'][:4] for x in meta['eps'] if x['id'] == q['e']) for q in pool)
    lines = ['# Fragen-Pool – Bericht', '', f'Stand: {TODAY}', '',
             f"- Kandidaten aus geprüften Folgen: {stats['kandidaten']}",
             f"- nicht zur Prüfung ausgewählt (pro Folge werden die 14 aussichtsreichsten geprüft): {stats['nicht_ausgewaehlt']}",
             f"- im Review verworfen: {stats['review_drop']}",
             f"- Qualität < 3 verworfen: {stats['qualitaet<3']}",
             f"- Zitat nicht im Transkript gefunden: {stats['zitat_nicht_gefunden']}",
             f"- Distraktoren unbrauchbar: {stats['distraktoren_kaputt']}",
             f"- noch ohne Review (nicht im Pool): {stats['ohne_review']}",
             f"- geprüft und spieltauglich: {len(items)}",
             f"- **im Pool (max. {MAX_PER_EP} pro Folge): {len(pool)}** aus {len({q['e'] for q in pool})} Folgen",
             f"- davon Schätzfragen: {sum('n' in q for q in pool)}, „Wer hat's gesagt?“-tauglich: {sum('wer' in q for q in pool)}, Weltwissen: {sum(q['s']=='welt' for q in pool)}",
             f"- Tagesrunden geplant: {len(days)} (bis {max(days) if days else '–'})", '',
             '## Themen', *[f'- {k}: {v}' for k, v in th.most_common()], '',
             '## Jahrgänge', *[f'- {k}: {v}' for k, v in sorted(yr.items())], '',
             '## Schwierigkeit', *[f'- {k}: {v}' for k, v in sorted(collections.Counter(q["d"] for q in pool).items())], '',
             '## Arten', *[f'- {k}: {v}' for k, v in collections.Counter(q["k"] for q in pool).most_common()]]
    (D / 'pool_report.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[4:16]))

if __name__ == '__main__':
    E, items, themes, summaries, stats = load()
    keep = choose(E, items)
    pool = [entry(c, E) for c in keep]
    pool.sort(key=lambda q: (E[q['e']]['date'], q['id']))
    meta = build_meta(E, themes, summaries)
    (W / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    (W / 'pool.json').write_text(json.dumps(pool, ensure_ascii=False, separators=(',', ':')))
    days = build_days(pool, meta, E)
    report(E, items, keep, pool, stats, meta, days)
