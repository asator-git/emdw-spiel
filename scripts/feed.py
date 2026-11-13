#!/usr/bin/env python3
"""Stufe 0: RSS-Feed -> data/episodes.json (Metadaten aller Folgen)."""
import json, re, sys, html, urllib.request, pathlib, email.utils
ROOT = pathlib.Path(__file__).resolve().parent.parent
FEED = "https://feeds.simplecast.com/kzb4brMs"

def strip_html(s):
    s = re.sub(r'<br\s*/?>|</p>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s).replace('\xa0', ' ')
    return re.sub(r'\n\s*\n+', '\n\n', s).strip()

def tag(it, name):
    m = re.search(rf'<{name}[^>]*>(.*?)</{name}>', it, re.S)
    if not m: return ''
    v = m.group(1).strip()
    if v.startswith('<![CDATA['): v = v[9:-3]
    return v

NAME = r"(?:[A-ZÄÖÜ][\w\-äöüßéčćšžÿíáóúñ'.]+)(?:\s+(?:von|van|de|der|zu|vom)?\s*[A-ZÄÖÜ][\w\-äöüßéčćšžÿíáóúñ'.]+){0,3}"

def guests_from_title(t):
    """Gäste aus den verschiedenen Titelschemata: ', Name' | ' - Name' | 'mit Name' | 'Name über X' | 'erklärt von A und B'."""
    t = re.sub(r'\s*#spezial\s*$', '', t).strip()
    pats = [rf'^(.*?),\s*({NAME}(?:\s*(?:und|&)\s*{NAME})*)\s*\??$',          # Erklär mir X, Gast(?)
            rf'^(.*?)\s+[-–]\s+(?:mit\s+)?({NAME}(?:\s*(?:und|&)\s*{NAME})*)\s*$', # X - Gast
            rf'^(.*?)(?:\s+[-–])?\s+mit\s+({NAME}(?:\s*(?:und|&)\s*{NAME})*)(?:\s+vom\s.*)?\s*$',  # X mit Gast
            rf'^(?:deep dive\s*#?\d*:?\s*)({NAME})\s+über\s+(.*)$',
            rf'^(.*?),?\s+(?:erklärt|widerlegt) von\s+({NAME}(?:\s*(?:und|&)\s*{NAME})*)\s*$',
            rf'^(.*?)\s+[Mm]it\s+(?:\w+\s+alias\s+)?({NAME}?)(?:\s+(?:über|von)\s.*|:.*)?$']
    for k, p in enumerate(pats):
        m = re.match(p, t)
        if not m: continue
        topic, g = (m.group(2), m.group(1)) if k == 3 else (m.group(1), m.group(2))
        g = re.sub(r'\s+(?:von|über|vom)\s.*$', '', g)
        names = [x.strip() for x in re.split(r'\s+(?:und|&)\s+', g) if x.strip()]
        bad = {'Update', 'Gewinnspiel', 'Folge', 'Teil', 'Andreas Sator'}
        # Einzelwort-Namen nur bei persönlichen Folgen („Erklär mir dein …, Nina“) bzw. Bindestrich-Namen
        single_ok = bool(re.search(r'\b(dein|deine|deinen|deiner)\b', topic)) or '-' in g
        names = [n for n in names if n not in bad and not re.search(r'\d', n) and (len(n.split()) >= 2 or (k in (0, 1) and single_ok))]
        if names: return topic.strip(' -–:'), names
    return t, []

def parse(xml):
    out = []
    for it in xml.split('<item>')[1:]:
        title = html.unescape(tag(it, 'title')).replace('\xa0', ' ').strip()
        desc = strip_html(tag(it, 'description') or tag(it, 'content:encoded'))
        date = email.utils.parsedate_to_datetime(tag(it, 'pubDate')).date().isoformat()
        enc = re.search(r'<enclosure[^>]*url="([^"]+)"', it)
        audio = html.unescape(enc.group(1)) if enc else ''
        dur = tag(it, 'itunes:duration')
        if ':' in dur:
            p = [int(x) for x in dur.split(':')]; dur = sum(v * 60 ** i for i, v in enumerate(reversed(p)))
        dur = int(dur or 0)
        m = re.match(r'\s*#\s?(\d+)\s*(.*)', title)
        num = int(m.group(1)) if m else None
        rest = m.group(2) if m else title
        best_of = bool(re.search(r'best\s*of', title, re.I))
        topic, guests = guests_from_title(rest if m else title)
        link = tag(it, 'link')
        out.append(dict(guid=tag(it, 'guid'), num=num, title=title, topic=topic.strip(), guests=guests,
                        date=date, duration=dur, audio=audio, link=link, best_of=best_of,
                        description=desc[:4000]))
    out.sort(key=lambda e: e['date'])
    # IDs: Nummer, sonst Sonderfolge "s-<datum>"
    seen = set()
    for e in out:
        eid = str(e['num']) if e['num'] is not None else 's' + e['date'].replace('-', '')
        while eid in seen: eid += 'b'
        seen.add(eid); e['id'] = eid
        # Auswahl: Hauptfolgen + eigene Sonderfolgen; Best-ofs sind Wiederholungen
        e['in_game'] = (not e['best_of'] and e['duration'] > 600
                      and not re.search(r'replay|Wiederholung|Podcast-Empfehlung', e['title'], re.I))
    return out

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else None
    xml = open(src).read() if src else urllib.request.urlopen(FEED, timeout=60).read().decode()
    eps = parse(xml)
    path = ROOT / 'data/episodes.json'
    old = {e['id']: e for e in json.loads(path.read_text())} if path.exists() else {}
    for e in eps:  # bereits ermittelte Felder (YouTube-Zuordnung, Thema) behalten
        for k in ('youtube', 'yt_title', 'cluster', 'transcript_source'):
            if k in old.get(e['id'], {}): e[k] = old[e['id']][k]
    path.write_text(json.dumps(eps, ensure_ascii=False, indent=1))
    n = sum(e['in_game'] for e in eps)
    print(f"{len(eps)} Folgen im Feed, davon {n} fürs Spiel (ohne Best-ofs/Trailer)")
