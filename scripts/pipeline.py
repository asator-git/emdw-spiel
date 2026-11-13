#!/usr/bin/env python3
"""Claude-Pipeline: Transkripte -> Kandidaten (Stufe 1) -> geprüfte Kandidaten (Stufe 2). Stufe 3 = curate.py.

Zwei gleichwertige Ausführungswege mit identischen Prompts/Schemas (scripts/prompts.py):
  A) Message Batches API (Standard, 50 % günstiger):   ANTHROPIC_API_KEY setzen, dann
       pipeline.py batch extract [IDs]   -> schickt einen Batch ab, merkt sich die ID in data/batches.json
       pipeline.py batch review  [IDs]
       pipeline.py collect               -> holt fertige Batches ab und speichert die Ergebnisse
  B) Agent-Modus (ohne API-Schlüssel, z. B. in einer Claude-Code-Session):
       pipeline.py task extract <ID>     -> schreibt den kompletten Prompt nach data/work/extract/<ID>.prompt.md
       (Claude liest den Prompt und schreibt die JSON-Antwort nach data/work/extract/<ID>.json)
       pipeline.py ingest extract <ID>   -> validiert Schema + prüft jedes Zitat maschinell gegen das Transkript
Beide Wege landen in data/candidates/<ID>.json bzw. data/reviewed/<ID>.json.
  pipeline.py status                    -> Fortschritt
"""
import json, sys, os, re, pathlib, difflib, time, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from prompts import (EXTRACT_SYSTEM, EXTRACT_SCHEMA, REVIEW_SYSTEM, REVIEW_SCHEMA, THEMEN, extract_user, review_user)

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / 'data'
MODEL = os.environ.get('EMDW_MODEL', 'claude-opus-5-5')
for sub in ('candidates', 'reviewed', 'work/extract', 'work/review'):
    (D / sub).mkdir(parents=True, exist_ok=True)

def episodes():
    return {e['id']: e for e in json.loads((D / 'episodes.json').read_text())}

def transcript(eid):
    tr = json.loads((D / f'transcripts/{eid}.json').read_text())
    lines = [tr['source']] + [f"[{int(s['s'])}] {s['t']}" for s in tr['segments']]
    return tr, lines

def system(stage, ep):
    if stage == 'extract':
        return EXTRACT_SYSTEM.replace('{themen}', ', '.join(THEMEN))
    return REVIEW_SYSTEM.replace('{date}', ep['date']).replace('{year}', ep['date'][:4])

def user(stage, ep, lines):
    if stage == 'extract':
        return extract_user(ep, lines)
    return review_user(ep, lines, json.loads((D / f"candidates/{ep['id']}.json").read_text())['candidates'])

SCHEMA = {'extract': EXTRACT_SCHEMA, 'review': REVIEW_SCHEMA}
OUTDIR = {'extract': 'candidates', 'review': 'reviewed'}

# ---------- Maschinelle Zitatprüfung ----------
def _norm_words(s):
    s = unicodedata.normalize('NFKC', s.lower())
    s = re.sub(r'\b(äh|ähm|öh|hm|mhm)\b', ' ', s)
    return re.findall(r'[\wäöüß%]+', s)

def verify_quote(quote, tr, t):
    """Sucht das Zitat im Transkript (± 5 min um t). Liefert (Trefferquote 0..1, Sekunde der Zeile,
    in der das erste gefundene Zitatwort steht)."""
    q = _norm_words(quote)
    if len(q) < 4: return 0.0, t
    segs = tr['segments']
    idx = [i for i, s in enumerate(segs) if abs(s['s'] - t) <= 300] or list(range(len(segs)))
    words, owner = [], []
    for i in range(max(0, idx[0] - 1), min(len(segs), idx[-1] + 2)):
        w = _norm_words(segs[i]['t']); words += w; owner += [i] * len(w)
    if not words: return 0.0, t
    n = len(q)
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(q)
    best, best_first = 0.0, None
    for start in range(0, max(1, len(words) - n + 1)):
        sm.set_seq1(words[start:start + n + 2])
        blocks = [b for b in sm.get_matching_blocks() if b.size]
        r = sum(b.size for b in blocks) / n
        if r > best + 1e-9:
            best, best_first = r, start + blocks[0].a if blocks else start
    if best_first is None: return round(best, 3), t
    # Sekunde innerhalb des Abschnitts anteilig schätzen (Abschnitte sind bis zu 30 s lang)
    i = owner[best_first]; first = owner.index(i); cnt = owner.count(i)
    seg = segs[i]; frac = (best_first - first) / max(1, cnt)
    t_fix = seg['s'] + frac * (seg.get('e', seg['s']) - seg['s'])
    return round(min(best, 1.0), 3), int(t_fix)

def retime():
    """Zeitstempel aller gespeicherten Kandidaten mit der aktuellen Zitatprüfung neu berechnen."""
    for f in sorted((D / 'candidates').glob('*.json')):
        d = json.loads(f.read_text())
        if not (D / f"transcripts/{d['id']}.json").exists(): continue  # Transkript nicht im Repo: Zeitstempel bleiben
        tr, _ = transcript(d['id']); ch = 0
        for c in d['candidates']:
            m, t = verify_quote(c['quote'], tr, c['t'])
            if (m, t) != (c.get('quote_match'), c['t']): ch += 1
            c['quote_match'], c['t'] = m, t
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1)); print(d['id'], ch, 'geändert')

# ---------- Validierung & Speichern ----------
def validate(stage, data, ep):
    errs = []
    if stage == 'extract':
        if data.get('theme') not in THEMEN: errs.append('theme')
        for i, c in enumerate(data.get('candidates', [])):
            miss = [k for k in EXTRACT_SCHEMA['properties']['candidates']['items']['required'] if k not in c]
            if miss: errs.append(f'cand {i}: fehlt {miss}')
            if len(c.get('distractors', [])) != 3: errs.append(f'cand {i}: distractors != 3')
    else:
        for r in data.get('reviews', []):
            if r.get('verdict') not in ('keep', 'fix', 'drop'): errs.append(f"review {r.get('i')}: verdict")
    return errs

def save(stage, eid, data, ep, how):
    errs = validate(stage, data, ep)
    if errs: raise ValueError(f'{eid}: Schemafehler {errs[:5]}')
    if stage == 'extract':
        tr, _ = transcript(eid)
        for c in data['candidates']:
            c['quote_match'], c['t'] = verify_quote(c['quote'], tr, c['t'])
        data['transcript_source'] = tr['source']
    else:
        cands = json.loads((D / f'candidates/{eid}.json').read_text())['candidates']
        from prompts import review_selection
        need = set(review_selection(cands))
        if not need <= {r['i'] for r in data['reviews']}:
            raise ValueError(f'{eid}: Review deckt nicht alle {len(need)} ausgewählten Kandidaten ab')
    data.update(id=eid, model=MODEL, via=how, at=time.strftime('%Y-%m-%d'))
    (D / OUTDIR[stage] / f'{eid}.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
    return data

# ---------- Weg A: Batches API ----------
def todo(stage, ids):
    E = episodes()
    have_tr = {p.stem for p in (D / 'transcripts').glob('*.json')}
    out = []
    for eid, e in E.items():
        if ids and eid not in ids: continue
        if not e['in_game'] or eid not in have_tr: continue
        if (D / OUTDIR[stage] / f'{eid}.json').exists(): continue
        if stage == 'review' and not (D / f'candidates/{eid}.json').exists(): continue
        out.append(e)
    return out

def batch(stage, ids):
    import anthropic
    client = anthropic.Anthropic()
    reqs = []
    for e in todo(stage, ids):
        _, lines = transcript(e['id'])
        reqs.append({'custom_id': f"{stage}-{e['id']}", 'params': {
            'model': MODEL, 'max_tokens': 32000,
            'output_config': {'effort': 'high', 'format': {'type': 'json_schema', 'schema': SCHEMA[stage]}},
            'system': [{'type': 'text', 'text': system(stage, e), 'cache_control': {'type': 'ephemeral'}}],
            'messages': [{'role': 'user', 'content': user(stage, e, lines)}]}})
    if not reqs: print('nichts zu tun'); return
    b = client.messages.batches.create(requests=reqs)
    log = json.loads((D / 'batches.json').read_text()) if (D / 'batches.json').exists() else []
    log.append({'id': b.id, 'stage': stage, 'n': len(reqs), 'created': time.strftime('%Y-%m-%d %H:%M'), 'collected': False})
    (D / 'batches.json').write_text(json.dumps(log, indent=1))
    print(f'Batch {b.id}: {len(reqs)} Anfragen ({stage})')

def collect():
    import anthropic
    client = anthropic.Anthropic()
    log = json.loads((D / 'batches.json').read_text())
    E = episodes()
    usage = {'in': 0, 'out': 0, 'cache_read': 0}
    for entry in log:
        if entry['collected']: continue
        b = client.messages.batches.retrieve(entry['id'])
        if b.processing_status != 'ended': print(entry['id'], b.processing_status); continue
        for r in client.messages.batches.results(entry['id']):
            stage, eid = r.custom_id.split('-', 1)
            if r.result.type != 'succeeded': print('FEHLER', r.custom_id, r.result.type); continue
            msg = r.result.message
            usage['in'] += msg.usage.input_tokens; usage['out'] += msg.usage.output_tokens
            usage['cache_read'] += msg.usage.cache_read_input_tokens or 0
            if msg.stop_reason != 'end_turn': print('WARNUNG', r.custom_id, msg.stop_reason); continue
            text = next(bl.text for bl in msg.content if bl.type == 'text')
            try: save(stage, eid, json.loads(text), E[eid], 'batch')
            except ValueError as ex: print(ex)
        entry['collected'] = True; entry['usage'] = usage
    (D / 'batches.json').write_text(json.dumps(log, indent=1))
    print('Tokens:', usage)

# ---------- Weg B: Agent-Modus ----------
def task(stage, eid):
    ep = episodes()[eid]
    _, lines = transcript(eid)
    p = D / f'work/{stage}/{eid}.prompt.md'
    p.write_text(f"# SYSTEM\n\n{system(stage, ep)}\n\n# JSON-SCHEMA DER ANTWORT\n\n```json\n{json.dumps(SCHEMA[stage], ensure_ascii=False)}\n```\n\n# NACHRICHT\n\n{user(stage, ep, lines)}\n")
    print(p)

def ingest(stage, eid):
    f = D / f'work/{stage}/{eid}.json'
    txt = f.read_text().strip()
    txt = re.sub(r'^```(?:json)?\s*|\s*```$', '', txt)
    d = save(stage, eid, json.loads(txt), episodes()[eid], 'agent')
    if stage == 'extract':
        bad = [c for c in d['candidates'] if c['quote_match'] < 0.8]
        print(f"{eid}: {len(d['candidates'])} Kandidaten, {len(bad)} mit unsicherem Zitat (<0.8)")
        for c in bad: print(f"   {c['quote_match']:.2f}  {c['quote'][:80]}")
    else:
        v = [r['verdict'] for r in d['reviews']]
        print(f"{eid}: keep {v.count('keep')}, fix {v.count('fix')}, drop {v.count('drop')}")

def nxt(stage, shard, count=1):
    """Nächste offene Folge(n) für diesen Shard (für Agent-Worker, die in einer Schleife arbeiten)."""
    k, n = map(int, shard.split('/'))
    E = sorted((e for e in episodes().values() if e['in_game']), key=lambda e: e['date'])
    out = []
    for i, e in enumerate(E):
        if i % n != k: continue
        if not (D / f"transcripts/{e['id']}.json").exists(): continue
        if (D / OUTDIR[stage] / f"{e['id']}.json").exists(): continue
        if stage == 'review' and not (D / f"candidates/{e['id']}.json").exists(): continue
        out.append(e['id'])
        if len(out) >= count: break
    if out: print(' '.join(out)); return
    left = sum(1 for i, e in enumerate(E) if i % n == k and not (D / OUTDIR[stage] / f"{e['id']}.json").exists())
    print('WAIT' if left else 'DONE')

def status():
    E = [e for e in episodes().values() if e['in_game']]
    n = lambda sub: sum((D / f"{sub}/{e['id']}.json").exists() for e in E)
    print(f"Folgen {len(E)} | Transkripte {n('transcripts')} | extrahiert {n('candidates')} | geprüft {n('reviewed')}")

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    cmd = a[0]
    if cmd == 'batch': batch(a[1], set(a[2:]))
    elif cmd == 'collect': collect()
    elif cmd == 'task': [task(a[1], x) for x in a[2:]]
    elif cmd == 'ingest': [ingest(a[1], x) for x in a[2:]]
    elif cmd == 'status': status()
    elif cmd == 'next': nxt(a[1], a[2], int(a[3]) if len(a) > 3 else 1)
    elif cmd == 'retime': retime()
    elif cmd == 'wait':  # Batches abwarten und abholen
        while True:
            collect()
            log = json.loads((D / 'batches.json').read_text())
            if all(x['collected'] for x in log): break
            time.sleep(120)
    else: print(__doc__)
