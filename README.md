# Fünf am Tag – das Erklär-mir-die-Welt-Spiel

Jeden Tag fünf Fragen aus über 400 Folgen „Erklär mir die Welt“. Man schätzt, ordnet ein, sagt, wie sicher man sich ist, und lernt dabei etwas. Nach jeder Antwort führt „Stelle anhören“ direkt zur Minute in der Folge.

- **Spiel:** statische PWA in `web/` (Vanilla JS, kein Build, kein Backend, kein Login, Fortschritt in `localStorage`)
- **Daten:** aus den Transkripten aller Folgen, über eine dreistufige Claude-Pipeline gezogen, geprüft und kuratiert
- **Live:** https://asator-git.github.io/emdw-spiel/ (vorerst `noindex`, bis Andreas freigibt)

## Aufbau

```
emdw-spiel/
├── update.sh                 # ein Befehl: neue Folgen -> Transkript -> Fragen -> Deploy
├── scripts/
│   ├── feed.py               # RSS -> data/episodes.json
│   ├── youtube_fetch.sh      # Kanal-Videos: Metadaten + deutsche Untertitel (nur Text)
│   ├── match_youtube.py      # YouTube-Video <-> RSS-Folge (Datum, Dauer, Nummer, Gäste, Titelwörter)
│   ├── yt_to_transcript.py   # json3-Untertitel -> data/transcripts/<id>.json
│   ├── transcribe.py         # faster-whisper für alle Folgen ohne Untertitel (shardbar, pusht selbst)
│   ├── prompts.py            # Prompts + JSON-Schemas der Stufen 1 und 2
│   ├── pipeline.py           # Stufe 1+2: Batches-API oder Agent-Modus, maschinelle Zitatprüfung
│   ├── curate.py             # Stufe 3: Pool, Balance, Tagesrunden für 400 Tage im Voraus
│   ├── coverage.py           # COVERAGE.md
│   └── AGENT_WORKER.md       # Anleitung für Claude-Code-Sessions als Pipeline-Worker
├── data/
│   ├── episodes.json         # alle Folgen mit Metadaten, YouTube-ID, Spiel-Flag
│   ├── transcripts/<id>.json # {source, segments:[{s,e,t}]}
│   ├── candidates/<id>.json  # Stufe 1: 15–25 Kandidaten pro Folge, mit Zitat + Zeitstempel
│   ├── reviewed/<id>.json    # Stufe 2: Urteil, Korrekturen, „Stand <Jahr>“, Qualität
│   └── pool_report.md        # Verteilung nach Themen, Jahrgängen, Schwierigkeit
├── web/                      # das Spiel (wird 1:1 deployt)
│   ├── index.html, app.js, style.css, sw.js, manifest.webmanifest
│   ├── fonts/ img/           # CI: UT Glasgow Grotesk, Gedankenstrich, Logos, Scribbles
│   └── data/meta.json, pool.json, days/YYYY-MM.json
├── brand/                    # Original-CI aus dem Drive (Logos, Farben, Schriften, Scribbles)
├── tests/e2e.js              # Playwright: alle Modi auf iPhone + Pixel, Screenshots
├── COVERAGE.md               # Abdeckungsprotokoll der Transkripte
└── DECISIONS.md              # Konzept, Design, Entscheidungen, offene Punkte, Version 2
```

> **Hinweis zum öffentlichen Repo:** Die vollständigen Transkripte (`data/transcripts/`, ~37 MB) und die Original-CI-Dateien (`brand/`) liegen nicht hier, sondern im Repo `asator-git/oesterreich-digest`, Branch `claude/emdw-game-podcast-kkv7ye`, Ordner `emdw-spiel/`. Für Updates braucht man sie nicht: `update.sh` transkribiert nur neue Folgen (ohne Kandidaten), alles Bestehende bleibt, wie es ist.

## Die Pipeline

1. **Transkripte.** Der RSS-Feed liefert die Folgenliste. Wo es ein YouTube-Video mit deutschen Untertiteln gibt, kommen die Untertitel von dort. Alles andere transkribiert faster-whisper lokal (`large-v3-turbo`, Deutsch, VAD). Ergebnis: ein Format für beide Quellen, mit Zeitstempeln pro Abschnitt.
2. **Stufe 1, Extraktion** (`pipeline.py batch extract`): Claude liest jedes Transkript ganz und liefert 15–25 Kandidaten. Jeder hat Art, Fundstelle, wörtliches Zitat, geglättetes Zitat, Frage, Antwort, drei Distraktoren, Schätzregler-Bereich, Aha-Text, Schwierigkeit und Weltwissen-vs.-Folgendetail. Danach sucht `verify_quote` **jedes Zitat maschinell** im Transkript (±5 min) und setzt den Zeitstempel auf das erste Zitatwort.
3. **Stufe 2, Prüfung** (`pipeline.py batch review`): ein zweiter, unabhängiger Durchgang mit eigenem Prompt pro Kandidat. Er prüft Beleg, Transkriptionsfehler (Zahlen, Namen), Kontext, Aktualität („Stand <Jahr>“ oder raus), Fairness gegenüber dem Gast, Spielbarkeit und Ton. Urteil `keep`/`fix`/`drop` plus Qualität 1–5.
4. **Stufe 3, Kuratierung** (`curate.py`): nur `keep`/`fix` mit Qualität ≥ 3 und gefundenem Zitat. Höchstens 12 Einträge pro Folge, bevorzugt Weltwissen. Dazu kommen „Welche Folge?“ nur, wenn der Satz den Titel nicht verrät, „Wer hat's gesagt?“ nur für Gastzitate ohne Namensnennung, Tagesrunden mit fester Dramaturgie und 30 Tagen Abstand pro Folge. **Veröffentlichte Tage werden nie mehr verändert.**

Zitate von Gästen werden nur sprachlich geglättet (Füllwörter, Wiederholungen). Der Sinn bleibt gleich, das Original bleibt in `quote` erhalten.

### Zwei Wege, die Pipeline laufen zu lassen

- **Standard: Message Batches API.** `ANTHROPIC_API_KEY` setzen, dann `./update.sh`. Batches kosten 50 % weniger als Einzelanfragen. Der System-Prompt wird gecacht.
- **Agent-Modus (ohne Schlüssel).** `pipeline.py task|ingest` erzeugt denselben Prompt als Datei. Eine Claude-Code-Session führt ihn aus und speichert das JSON, danach laufen dieselben Prüfungen. So ist der erste Lauf entstanden, weil in der Bau-Session kein API-Schlüssel verfügbar war (siehe DECISIONS.md).

## Update-Ablauf nach einer neuen Folge

```bash
pip install yt-dlp faster-whisper anthropic   # einmalig; dazu ffmpeg
export ANTHROPIC_API_KEY=...
./update.sh            # Feed -> YouTube -> Whisper -> Batches (Extraktion, Prüfung) -> Kuratierung -> Deploy
```

Eine neue Folge kostet rund 10 Minuten Whisper auf einem Laptop (falls kein YouTube-Untertitel da ist) und ein paar Cent API. Neue Fragen fließen in Tagesrunden ab morgen ein. Heutige und vergangene Runden bleiben gleich, damit alle dieselben fünf Fragen haben.

Optionen: `SKIP_YOUTUBE=1`, `SKIP_DEPLOY=1`, `WHISPER_MODEL=large-v3` (genauer, ca. 2,5× langsamer), `DEPLOY_REMOTE=...`.

## Kosten der API-Läufe

Grundlage: Claude Opus 5.5 ($4 Input / $20 Output pro Mio. Tokens, **Batches −50 %** → $2 / $10), gemessene Längen aus diesem Lauf.

| Stufe | pro Folge | 443 Folgen (Erstbefüllung) | neue Folge |
|---|---|---|---|
| Extraktion: ~20k Tokens Transkript + 2k Prompt rein, ~9k raus (inkl. Denken) | ≈ $0,13 | ≈ $58 | ≈ $0,13 |
| Prüfung: ~20k Transkript + ~8k Kandidaten rein, ~8k raus | ≈ $0,14 | ≈ $62 | ≈ $0,14 |
| **Summe** | **≈ $0,27** | **≈ $120** | **≈ $0,27** |

Prompt-Caching spart beim System-Prompt noch ein paar Prozent.

**Tatsächlich gelaufen (Erstbefüllung, Agent-Modus statt Batches, weil kein API-Schlüssel da war):** Ein Agent-Lauf kostet pro Folge deutlich mehr als ein Batch-Aufruf. Dazu kommen der Tool-Overhead, das Lesen in Teilen und die Orchestrierung. Gemessen an den Listenpreisen kostete die Extraktion mit Opus etwa 1 $ pro Folge, die Prüfung mit Sonnet etwa 0,30 $ pro Folge, zusammen also rund 550 $ für alles. Über die Batches API wären es die oben genannten rund 120 $. Für laufende Updates deshalb unbedingt `update.sh` mit API-Schlüssel verwenden. Mit Claude Sonnet 5.5 (`EMDW_MODEL=claude-sonnet-5-5`) halbieren sich die Kosten, die Prüfung würde ich trotzdem auf Opus lassen. Whisper läuft lokal und kostet nichts außer Rechenzeit.

## Lokal starten und testen

```bash
cd web && python3 -m http.server 8765        # http://localhost:8765
node tests/e2e.js http://localhost:8765/ tests/shots   # spielt alle Modi auf iPhone + Pixel durch
```

## Deployment

**Live-Vorschau jetzt:** https://claude.ai/artifact/EXT4UuoSDSrKd7BJToMtko (privat; Andreas kann sie über „Share“ freigeben). Service Worker (Offline) und Duell-Links laufen dort wegen der Sandbox nicht, alles andere schon.

**GitHub Pages (live seit 13. 11. 2026):** https://asator-git.github.io/emdw-spiel/ – so wurde es eingerichtet: Neues Repo `asator-git/emdw-spiel` anlegen, den Inhalt von `emdw-spiel/` als Wurzel hineinpushen (`git subtree split --prefix emdw-spiel -b emdw && git push git@github.com:asator-git/emdw-spiel.git emdw:main`), dann unter Settings → Pages die Quelle „GitHub Actions“ wählen. Der Workflow `.github/workflows/pages.yml` deployt `web/` bei jedem Push. URL danach: https://asator-git.github.io/emdw-spiel/

GitHub Pages, Repo `asator-git/emdw-spiel`, Branch `gh-pages` (Inhalt von `web/`). `update.sh` macht das am Ende automatisch. Beim ersten Mal muss das Repo existieren und Pages auf `gh-pages` / Root stehen. Wie es zum ersten Deploy kam und was noch offen ist, steht in DECISIONS.md. Bis Andreas freigibt, steht `<meta name="robots" content="noindex">` in `index.html`.
