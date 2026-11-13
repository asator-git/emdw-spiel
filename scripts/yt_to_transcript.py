#!/usr/bin/env python3
"""Stufe 1d: YouTube-Untertitel (json3) -> data/transcripts/<id>.json im gemeinsamen Format.
Automatische Untertitel kommen als kurze Zeilen; wir fassen sie zu Sätzen/Abschnitten (~15 s) zusammen."""
import json, glob, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
E = json.loads((ROOT / 'data/episodes.json').read_text())
n = 0
for e in E:
    if not e.get('youtube') or not e['in_game']: continue
    out = ROOT / f"data/transcripts/{e['id']}.json"
    if out.exists() and json.loads(out.read_text()).get('source') == 'whisper': continue  # Whisper hat Vorrang
    files = sorted(glob.glob(str(ROOT / f"data/raw/yt/{e['youtube']}.de*.json3")))
    if not files: continue
    ev = json.load(open(files[0]))['events']
    words = []
    for x in ev:
        txt = ''.join(s.get('utf8', '') for s in x.get('segs', [])).replace('\n', ' ').strip()
        if txt: words.append((x.get('tStartMs', 0) / 1000, (x.get('tStartMs', 0) + x.get('dDurationMs', 0)) / 1000, txt))
    segs, cur = [], None
    for s, en, t in words:
        if cur is None: cur = {'s': round(s, 1), 'e': en, 't': t}
        else: cur['t'] += ' ' + t; cur['e'] = en
        if (cur['e'] - cur['s'] > 15 and re.search(r'[.?!]$', t)) or cur['e'] - cur['s'] > 30:
            cur['e'] = round(cur['e'], 1); segs.append(cur); cur = None
    if cur: cur['e'] = round(cur['e'], 1); segs.append(cur)
    out.write_text(json.dumps({'id': e['id'], 'source': 'youtube', 'youtube': e['youtube'], 'segments': segs}, ensure_ascii=False, separators=(',', ':')))
    n += 1
print(n, 'YouTube-Transkripte geschrieben')
