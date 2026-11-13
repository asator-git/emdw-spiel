#!/usr/bin/env python3
"""Abdeckungsprotokoll der Transkripte -> COVERAGE.md"""
import json, pathlib, collections, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
E = json.loads((ROOT / 'data/episodes.json').read_text())
T = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'data/transcripts').glob('*.json')}
game = [e for e in E if e['in_game']]
src = collections.Counter(T[e['id']]['source'] for e in game if e['id'] in T)
missing = [e for e in game if e['id'] not in T]
words = sum(len(s['t'].split()) for t in T.values() for s in t['segments'])
hours = sum(e['duration'] for e in game if e['id'] in T) / 3600
L = ['# Abdeckungsprotokoll der Transkripte', '', f'Stand: {datetime.date.today()}', '',
     f'Der RSS-Feed enthält **{len(E)} Einträge**. Davon sind **{len(game)} eigenständige Folgen**: alle nummerierten Folgen #1–#{max(e["num"] or 0 for e in E)} (ohne #375/#376, die im Feed fehlen) plus Sonderfolgen wie deep dives, Sommer-Specials, AMAs und Jahresrückblicke.',
     '', f'| | Folgen | Anteil |', '|---|---|---|',
     f'| transkribiert, gesamt | {len(game) - len(missing)} | {100 * (len(game) - len(missing)) / len(game):.1f} % |',
     f'| davon YouTube-Untertitel | {src["youtube"]} | |', f'| davon Whisper (lokal, large-v3-turbo) | {src["whisper"]} | |',
     f'| fehlt | {len(missing)} | |', '',
     f'Umfang: {hours:.0f} Stunden Audio, {words:,} Wörter.'.replace(',', '.'), '',
     f'YouTube-Link für „Stelle anhören“ (mit Zeitstempel): {sum(1 for e in game if e.get("youtube"))} Folgen. Die übrigen verlinken auf die Folgenseite bei Simplecast und nennen die Minute.', '',
     '## Fehlende Folgen', '']
L += [f'- {e["id"]} ({e["date"]}) {e["title"]} – Grund: noch nicht transkribiert (Whisper-Lauf ausstehend oder Audio-Download gescheitert)' for e in missing] or ['Keine. 100 % der Spiel-Folgen sind transkribiert.']
L += ['', '## Bewusst ausgeschlossene Feed-Einträge', '', 'Diese Einträge sind Wiederholungen oder keine eigenen Folgen. Sie würden Fragen doppeln:', '']
L += [f'- {e["date"]} {e["title"]} ({e["duration"] // 60} min) – {"Best-of/Wiederholung" if e["best_of"] or "replay" in e["title"].lower() or "Wiederholung" in e["title"] else "Trailer/Hinweis (unter 10 min) oder Podcast-Empfehlung"}' for e in E if not e['in_game']]
L += ['', '## Wege und Hindernisse', '',
      '- **Folgenliste:** RSS-Feed von Simplecast (Titel, Nummer, Datum, Beschreibung, Gäste aus dem Titelschema „#N Erklär mir X, Gast“, Audio-URL).',
      '- **YouTube:** Der Kanal hat 406 Videos (Folgen ab etwa #194, Dezember 2021). Für die ersten rund 150 Videos kamen Metadaten und deutsche Untertitel per yt-dlp. Danach hat YouTube für die Cloud-IP einen Bot-Check („Sign in to confirm you\'re not a bot“) verlangt. Den habe ich bewusst nicht umgangen. Die Zuordnung der restlichen Videos lief über die öffentliche Kanalliste (Titel mit Folgennummer, Dauer).',
      '- **Zuordnung YouTube ↔ RSS:** Punkte aus Datumsnähe, Dauer, Folgennummer im Titel, Gästenamen und Wortüberschneidung in Titel/Beschreibung, dann eine gierige Eins-zu-eins-Zuordnung. Nicht zuordenbare Videos stehen in `logs/youtube_unmatched.log` (meist Shorts, Clips, Videos, die vom Podcast-Schnitt abweichen).',
      '- **Whisper:** Alles ohne YouTube-Untertitel lief über faster-whisper. large-v3 schafft auf 4 CPU-Kernen 0,7× Echtzeit, das wären über 170 Rechenstunden gewesen. Deshalb habe ich **large-v3-turbo** genommen (gleicher Encoder, schnellerer Decoder, ca. 0,3× Echtzeit) und auf 16 parallele Cloud-Sessions verteilt. Sprache Deutsch, VAD-Filter, Gastname als Prompt (hilft bei der Schreibweise von Namen).',
      '- **Qualität:** Whisper-Transkripte haben Satzzeichen und sind meist besser als die automatischen YouTube-Untertitel. Zahlen und Namen prüft Stufe 2 der Pipeline extra.']
(ROOT / 'COVERAGE.md').write_text('\n'.join(L) + '\n')
print(f'{len(game) - len(missing)}/{len(game)} transkribiert, {len(missing)} fehlen')
