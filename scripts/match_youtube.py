#!/usr/bin/env python3
"""Stufe 1b: YouTube-Videos den RSS-Folgen zuordnen (Datum, Dauer, Titel/Beschreibung, Gäste).
Schreibt youtube-ID in data/episodes.json und nicht zuordenbare Videos nach logs/youtube_unmatched.log."""
import json, glob, re, pathlib, datetime, difflib, unicodedata
ROOT = pathlib.Path(__file__).resolve().parent.parent
E = json.loads((ROOT / 'data/episodes.json').read_text())

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return re.sub(r'[^a-z0-9 ]+', ' ', ''.join(c for c in s if not unicodedata.combining(c)))

def words(s): return {w for w in norm(s).split() if len(w) > 3}

vids = []
for p in glob.glob(str(ROOT / 'data/raw/yt/*.info.json')):
    v = json.load(open(p))
    if not v.get('upload_date') or (v.get('duration') or 0) < 600: continue  # Shorts/Trailer raus
    v['date'] = datetime.date(int(v['upload_date'][:4]), int(v['upload_date'][4:6]), int(v['upload_date'][6:]))
    v['words'] = words(v['title'] + ' ' + (v.get('description') or '')[:1500])
    v['num'] = None
    m = re.search(r'(?:#|Folge\s*)(\d{1,3})\b', v['title'] + ' ' + (v.get('description') or '')[:300])
    if m: v['num'] = int(m.group(1))
    vids.append(v)

# Videos ohne geladene Metadaten (YouTube-Bot-Check): flache Kanalliste mit Titel + Dauer
seen = {v['id'] for v in vids}
flat = ROOT / 'data/raw/yt_flat.tsv'
if flat.exists():
    for line in flat.read_text().splitlines():
        vid, title, dur = (line.split('\t') + ['', ''])[:3]
        if vid in seen or not dur.isdigit() or int(dur) < 600: continue
        v = {'id': vid, 'title': title, 'duration': int(dur), 'date': None, 'description': '', 'words': words(title)}
        m = re.search(r'(?:#|Folge\s*)(\d{1,3})\b', title)
        v['num'] = int(m.group(1)) if m else None
        vids.append(v)

def score(e, v):
    s = 0.0
    if v['date'] is not None:
        d = abs((datetime.date.fromisoformat(e['date']) - v['date']).days)
        if d > 400: return -1
        s += max(0, 3 - d / 4)                   # Datum: gleicher Tag = 3 Punkte
    elif v['num'] is None or v['num'] != e['num']:
        if abs(e['duration'] - v['duration']) > 120: return -1
    dd = abs(e['duration'] - v['duration'])
    s += max(0, 3 - dd / 60)                     # Dauer: Differenz in Minuten
    g = [n for gst in e['guests'] for n in norm(gst).split() if len(n) > 3]
    s += 2.5 * sum(1 for n in g if n in v['words']) / max(1, len(g))
    ew = words(e['topic'] + ' ' + e['description'][:1500])
    s += 4 * len(ew & v['words']) / max(1, min(len(ew), len(v['words'])))
    if v['num'] is not None and e['num'] == v['num']: s += 4
    return s

pairs = sorted(((score(e, v), i, j) for i, e in enumerate(E) if e['in_game'] for j, v in enumerate(vids)), reverse=True)
used_e, used_v, match = set(), set(), {}
for s, i, j in pairs:
    if s < 4.5: break
    if i in used_e or j in used_v: continue
    used_e.add(i); used_v.add(j); match[i] = (j, s)
for i, e in enumerate(E):
    if i in match:
        v = vids[match[i][0]]
        e['youtube'] = v['id']; e['yt_title'] = v['title']; e['yt_score'] = round(match[i][1], 2)
    else:
        e.pop('youtube', None); e.pop('yt_title', None); e.pop('yt_score', None)
(ROOT / 'data/episodes.json').write_text(json.dumps(E, ensure_ascii=False, indent=1))
with open(ROOT / 'logs/youtube_unmatched.log', 'w') as f:
    f.write('# YouTube-Videos ohne zuordenbare RSS-Folge\n')
    for j, v in enumerate(vids):
        if j not in used_v: f.write(f"{v['id']}\t{v['date']}\t{v['duration']}s\t{v['title']}\n")
    f.write('\n# Spiel-Folgen ohne YouTube-Video (-> Whisper)\n')
    for i, e in enumerate(E):
        if e['in_game'] and i not in match: f.write(f"{e['id']}\t{e['date']}\t{e['title']}\n")
n = sum(1 for e in E if e['in_game'])
print(f"{len(vids)} Videos, {len(match)}/{n} Spiel-Folgen zugeordnet; schwächste Treffer:")
for i, (j, s) in sorted(match.items(), key=lambda x: x[1][1])[:12]:
    print(f"  {s:.1f}  {E[i]['title'][:60]}  <->  {vids[j]['title'][:60]}")
