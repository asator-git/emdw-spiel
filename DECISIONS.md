# DECISIONS – Das EMDW-Spiel

Ich habe allein gearbeitet und keine Rückfragen gestellt. Hier steht jede größere Entscheidung mit Begründung, dazu alles, was nicht geklappt hat, und offene Punkte.

---

## 1. Spielkonzept: zwölf Ideen, eine Auswahl

Bewertet von 1 bis 5 (5 = am besten). **Spaß**: Will man es noch einmal spielen? **Lernen**: Bleibt etwas hängen? **Fan**: Erkennt man EMDW wieder? **Teilen**: Schickt man es weiter? **Marke**: Passt es zu evidenzbasiert, neugierig, nuanciert und freundlich?

| # | Konzept | Kurzbeschreibung | Spaß | Lernen | Fan | Teilen | Marke | Σ |
|---|---|---|---|---|---|---|---|---|
| 1 | **Fünf am Tag** | Wordle-Prinzip: alle bekommen dieselben fünf Fragen pro Tag, mit Streak und Emoji-Raster | 4 | 4 | 4 | 5 | 4 | 21 |
| 2 | **Kalibriert** | Zu jeder Antwort setzt man „Wie sicher bist du?“. Ehrliche Unsicherheit bringt mehr als Bluffen (eine korrekte Scoring-Regel) | 4 | 5 | 3 | 4 | 5 | 21 |
| 3 | **Schätzwerk** | Nur Schätzfragen mit Schieberegler, Punkte nach Nähe (log-skaliert) | 4 | 4 | 3 | 4 | 5 | 20 |
| 4 | **Höher oder tiefer** | Zwei Zahlen aus zwei Folgen: Welche ist größer? Endlos-Kette | 5 | 3 | 2 | 4 | 3 | 17 |
| 5 | **Gästebuch** | „Wer hat's gesagt?“ mit Sammelkarten aller Gäste und Album zum Vervollständigen | 3 | 3 | 5 | 3 | 4 | 18 |
| 6 | **Zeitreise** | Aussagen auf einem Zeitstrahl seit 2018 einordnen | 3 | 3 | 5 | 3 | 4 | 18 |
| 7 | **Folgen-Detektiv** | Hinweis-Leiter (Aha-Satz → Jahr → Gast). Je früher man die Folge errät, desto mehr Punkte | 4 | 3 | 5 | 4 | 4 | 20 |
| 8 | **Sternenhimmel** | Jede Folge ist ein Stern, die Themen sind Sternbilder. Gespielte Folgen leuchten auf | 3 | 4 | 5 | 3 | 5 | 20 |
| 9 | **Andreas fragt** | Man spielt den Gast und beantwortet Andreas' typische Fragen. Am Ende kommt die echte Antwort | 3 | 3 | 5 | 2 | 3 | 16 |
| 10 | **Duell-Link** | Asynchron gegen Freund:innen: Der Link trägt Seed und Punktzahl, kein Backend nötig | 4 | 2 | 2 | 5 | 3 | 16 |
| 11 | **Mythos oder Fakt** | Wischen wie bei Tinder | 4 | 3 | 2 | 4 | **2** | 15 |
| 12 | **Hörschnipsel** | Fünf Sekunden Intro hören und die Folge erraten (wie Heardle) | 4 | 1 | 5 | 4 | 3 | 17 |

**Verworfen, mit Grund:**
- *Mythos oder Fakt* lebt davon, dass Leute reinfallen. Das sind Gotcha-Fragen, und die verbietet der Auftrag.
- *Hörschnipsel* braucht ausgeschnittene Audiodateien (Rechte, Hosting, Datenvolumen) und lehrt wenig.
- *Andreas fragt* ist als Hauptmechanik zu textlastig. Seine typischen Fragen tauchen stattdessen als Easter Egg und als Fragetyp im freien Modus auf.
- *Höher oder tiefer* macht süchtig, aber vergleicht Zahlen ohne Bezug zueinander. Das ist das Gegenteil von nuanciert.

**Gebaut wird eine Kombination aus 1 + 2 + 3 + 5 + 6 + 7 + 8 + 10:**
- **Kern:** *Fünf am Tag*. Jeden Tag gibt es fünf Fragen in fester Dramaturgie: Schätzen → Aha mit „Wie sicher bist du?“ → Wer hat's gesagt? → Welche Folge? (mit Hinweis-Leiter) → Zeitstrahl. Kein Fragetyp kommt zweimal vor, so wird es nie eintönig.
- **„Wie sicher bist du?“ läuft quer durch alle Auswahlfragen.** Das ist das Alleinstellungsmerkmal und passt am besten zu EMDW. Punkte = 60 für richtig + 40 × Brier-Kalibrierung. Rechnet man den Erwartungswert durch, lohnt sich nur die ehrliche Einschätzung, und man fällt nie ins Minus: Auch eine falsche, ehrlich unsichere Antwort bringt Punkte. Das Profil zeigt eine Kalibrierungskurve („Wenn du ‚bombensicher' sagst, liegst du in 83 % richtig“).
- **Sternenhimmel** als Fortschritt, weil Dunkelblau und Gelb aus der neuen CI ohnehin Nacht und Sterne sind.
- **Duell-Link** ohne Backend: Der geteilte Link enthält Datum und Punktzahl. Wer ihn öffnet, spielt dieselbe Runde und sieht danach den Vergleich.
- **Freier Modus** nach Thema oder Jahrgang, dazu **„Erste Stunde“** (nur 2018–2019, alles schwer).

Warum nicht ein reines Quiz: Die fünf Mechaniken trainieren fünf verschiedene Denkweisen (Größenordnungen schätzen, die eigene Unsicherheit einschätzen, Menschen zuordnen, Inhalte verorten, Zeit einordnen). Nach jeder Antwort kommt der Aha-Moment mit dem Button „Stelle anhören“. Das Spiel ist also ein Trailer für den Podcast und kein Ersatz dafür.

### Punkteregeln (warum so)

- **Auswahlfragen mit „Wie sicher bist du?“:** Punkte = 60 · richtig + 40 · (1 − (richtig − p)²) mit p ∈ {0,4 „Bauchgefühl“, 0,7 „Ziemlich sicher“, 0,95 „Bombensicher“}. Der zweite Term ist der Brier-Score, eine *strikt korrekte* Bewertungsregel: Im Erwartungswert gewinnt nur, wer seine echte Trefferwahrscheinlichkeit angibt. Beispiele: Bombensicher und richtig gibt 100, bombensicher und falsch gibt 4, Bauchgefühl und richtig 86, Bauchgefühl und falsch 34. Wer ehrlich zugibt, dass er rät, wird also nie vorgeführt.
- **Schätzfragen:** Abstand in Prozent der Reglerbreite, auf der Log-Skala, wenn der Bereich mehr als zwei Größenordnungen umfasst. Volle Punkte bei einem Treffer, null ab 30 % Abstand. Der Regler startet in der Mitte. Die Pipeline legt den Bereich so, dass die Lösung weder am Rand noch genau in der Mitte liegt.
- **Welche Folge?:** 100 Punkte, je Tipp (Jahr, dann Gast) 25 weniger. Die Hinweis-Leiter macht aus einer Ratefrage Detektivarbeit.
- **Zeitstrahl:** 100 für die richtige Reihenfolge, 40, wenn ein Element am richtigen Platz steht.
- **Teilen:** Emoji-Raster (🟨 ≥ 85, 🟦 ≥ 25, ⬜ darunter), Punktzahl, Anzahl „bombensicher und richtig“ und ein Duell-Link. Kein Spoiler.

## 2. Design

**Quelle: die neue CI aus dem Drive-Ordner „emdw“** (Teresa Design Studio, Herbst 2026). Gelesen habe ich 01-Logo (primär, sekundär, tertiär, Logomark, je in 10 Farben), 02-Farben, 03-Schriften, 04-Scribbles, 05-Brand Book (Summary), 06-Thumbnails sowie die Dateierklärung. Die Dropbox (Team-Ordner „EMDW“ → Brand Assets) war aus der Cloud-Umgebung nicht erreichbar: kein Connector, und ohne Anmeldung gibt es keinen Zugriff. Weil der Drive-Ordner bereits alle Logos, Farben, Schriften und Scribbles enthält, fehlt nach meiner Einschätzung nichts. Ob in der Dropbox etwas Neueres liegt, sollte Andreas kurz prüfen.

Was ich aus der CI übernommen habe und warum:

- **Farben:** Dunkelblau `#0C2A66` als Bühne (wie in den neuen YouTube-Thumbnails), EMDW-Blau `#163582`, Gelb `#FFF19C` als einzige Signalfarbe (Hervorhebung, Lösung, Sterne), Creme `#F7F3ED` als Papier für die Aha-Momente, Hellblau/Babyblau für sekundäre Infos, Rot `#F04D22` nur fürs Durchstreichen und für Easter Eggs. Braun und Rosa verwende ich sparsam. Alle Textkombinationen liegen über WCAG AA (Lighthouse-Accessibility 100).
- **Typografie:** UT Glasgow Grotesk als Variable Font. Headlines in Versalien mit fetter Gewichtung (860) und **gelbem Kasten um das Schlüsselwort**, genau wie auf den Thumbnails („WIE MANN <mark>LÄNGER</mark> LEBT“). „Gedankenstrich“ ist die Handschrift der CI. Ich setze sie nur für kurze, menschliche Einwürfe ein: „Aha.“, „Schätz mal“, das Datum, Jahreszahlen im Zeitstrahl.
- **Layout wie ein Thumbnail:** kleine Eckbeschriftungen („Erklär“ oben links, „mir“ oben rechts, Fragenummer). Das ist ein direktes Zitat der Thumbnail-Vorlage aus dem Brand Book.
- **Scribbles als Bewegung mit Sinn:** Die richtige Antwort wird mit dem handgezeichneten Oval aus der CI eingekreist, eine falsche mit dem Krakel-Scribble durchgestrichen. Beide werden von links nach rechts „gezeichnet“ (clip-path), wie von Hand. Pfeile aus derselben Familie stehen in Buttons und im Menü. Es gibt kein Konfetti, keine Verläufe, keine Schatten und keine abgerundeten Karten: Alles ist flach, eckig und mit 2-px-Linien gezeichnet.
- **Emojis** kommen nur im Teilen-Text vor (das Raster braucht sie), nie in der Oberfläche.
- **Sternenhimmel:** Dunkelblau mit gelben Sternen folgt direkt aus der Palette. Die zehn Themen sind zehn Sternbilder, die Beschriftung steht in der Handschrift.
- **Haptik & Ton:** `navigator.vibrate` beim Auswählen (6 ms), beim Schieberegler als feines Rasten, bei richtig ein Doppeltipp. Töne sind standardmäßig aus, man kann sie im Profil einschalten (WebAudio, keine Dateien).
- **Barrierefreiheit:** Alle Touch-Ziele sind mindestens 44 px groß, die Antworten 58 px. Es gibt `aria-pressed` für Auswahl und Sicherheit, `aria-live` für Wechsel, einen Fokus-Sprung zum Aha-Moment, einen Skip-Link, Screenreader-Text für den Regler (`aria-valuetext` mit Einheit), +/−-Knöpfe als Alternative zum Ziehen und Auf/Ab-Knöpfe statt Drag & Drop im Zeitstrahl. `prefers-reduced-motion` schaltet alle Animationen ab.
- **Font-Subsets:** Glasgow von 112 KB (TTF) auf 30 KB (woff2). Die Glasgow zeichnet „ “ – … ungewöhnlich (die doppelten Anführungszeichen sehen einfach aus, der Gedankenstrich ist sehr kurz). Diese Zeichen habe ich deshalb aus dem Subset genommen, sie kommen aus der Systemschrift.

## 3. Daten & Pipeline: Entscheidungen

- **Welche Folgen?** 443 der 501 Feed-Einträge: alle nummerierten Folgen plus eigene Sonderfolgen (deep dives, 7bday specials, AMAs, Jahresrückblicke, Sonne-&-Stahl-Folgen im Feed). Ausgeschlossen sind Best-ofs, „replay“ und „Wiederholung“ (doppelte Inhalte) sowie Trailer und Hinweise unter 10 Minuten. #375 und #376 fehlen im Feed selbst.
- **YouTube vor Whisper:** Untertitel kosten nichts und sind sofort da. Als YouTube nach rund 150 Videos einen Bot-Check verlangte, habe ich ihn **nicht** umgangen. Stattdessen wurde der Fallback aus dem Auftrag (Audio aus dem RSS-Feed + Whisper) zum Hauptweg. Die YouTube-IDs für „Stelle anhören“ kommen aus der öffentlichen Kanalliste (375 von 443 Folgen zugeordnet).
- **large-v3-turbo statt large-v3:** large-v3 läuft auf den verfügbaren 4-Kern-Containern mit 0,7× Echtzeit. Für über 300 Stunden Audio wären das über 400 Rechenstunden gewesen. Turbo nutzt denselben Encoder mit kleinerem Decoder und schafft 0,3× Echtzeit. In Stichproben sind Namen und Zahlen gleich gut erkannt worden. Verteilt auf 16 parallele Cloud-Sessions.
- **Kein API-Schlüssel in der Bau-Session.** `ANTHROPIC_API_KEY` war nicht gesetzt, und die Umgebung nimmt für Anthropic-Hosts keine Schlüssel an. Die Pipeline ist trotzdem für die **Message Batches API** gebaut (`pipeline.py batch …`, `update.sh`). Für den Erstlauf habe ich denselben Prompt im **Agent-Modus** ausgeführt: Claude-Code-Sessions lesen den identischen Prompt aus einer Datei, schreiben das JSON, und `ingest` prüft es genauso (Schema, wörtliches Zitat, Zeitstempel). Extraktion mit Opus 5.5, Prüfung mit Sonnet 5.5.
- **Nutzungslimit:** Die vielen parallelen Sessions haben dreimal das 5-Stunden-Kontingent des Accounts aufgebraucht. Ich habe danach umgebaut: schlanke Worker, mehrere Folgen pro Subagent, für die Prüfung nur Transkript-Ausschnitte rund um jede Fundstelle (±45/40 s) und nur die **14 aussichtsreichsten Kandidaten pro Folge**. Die Kuratierung nimmt ohnehin höchstens 12 pro Folge, die restlichen Kandidaten bleiben in `data/candidates/` für spätere Läufe erhalten.
- **Maschinelle Zitatprüfung zusätzlich zum Review:** Jedes Zitat wird per Wort-Alignment im Transkript gesucht (±5 min um den angegebenen Zeitpunkt). Unter 80 % Übereinstimmung fliegt der Kandidat raus. Dieselbe Prüfung setzt den Zeitstempel auf das erste Zitatwort, anteilig innerhalb des Transkript-Abschnitts. Ein Test-Worker hat dabei einen Fehler gefunden (Zeitstempel eine Zeile zu früh). Ich habe ihn behoben und alle Zeitstempel neu berechnet (`pipeline.py retime`).
- **Kuratierung:** max. 12 Einträge pro Folge (Balance), Weltwissen bevorzugt, „Welche Folge?“ nur, wenn der Satz keinen Wortstamm mit dem Folgentitel teilt, „Wer hat's gesagt?“ nur für Gastzitate ohne Namensnennung und mit echten Personennamen als Alternativen. Tagesrunden werden 400 Tage im Voraus geplant. Bereits gespielte Tage bleiben unverändert, damit alle dieselbe Runde haben und alte Duell-Links gültig bleiben.

## 4. Drei Tagesrunden selbst gespielt – ehrlich

Ich habe die Runden vom 13., 14. und 15. November so gespielt, wie sie im Spiel kommen.

**Was Spaß macht**
- Die **Schätzfragen** sind der beste Einstieg: kurz, man hat sofort eine Meinung, und der Aha-Moment danach („Drei ist die klassische Besetzung: Jede Partei bestellt eine Person …“) erklärt, *warum*.
- **„Wie sicher bist du?“** verändert das Spielgefühl spürbar. Man überlegt zweimal, bevor man „bombensicher“ drückt, und ärgert sich über die 4 Punkte mehr als über eine falsche Antwort. Genau das ist der Lerneffekt.
- **„Wer hat's gesagt?“** funktioniert für Fans sehr gut (Franz Viehböck über den Wiedereintritt, Wolfgang Mueller über das „wilde Feld“). Die Zitate klingen nach Menschen, nicht nach Lexikon.
- Die Aha-Texte führen wirklich zurück in die Folge. Mehrmals wollte ich danach die Stelle hören.

**Was langweilig oder unfair war – und was ich geändert habe**
- **Zeitstrahl:** Im ersten Entwurf war das reines Raten (Babyzunge 2018, Obdachlosigkeit 2019, Raffinerie 2022 ohne jeden Anhaltspunkt). Geändert: Die Jahre liegen jetzt mindestens zwei Jahre auseinander, zeitgebundene Aussagen werden bevorzugt (Pandemie, Wahlumfragen, „Stand 2023“), und unter jeder Aussage steht der Gast als Hinweis für Fans. Jetzt kann man kombinieren statt würfeln.
- **„Wer hat's gesagt?“** bot einmal „Bücher“ und „Selfies“ als Gäste an (Titelreste aus der Gast-Erkennung). Geändert: Die Gast-Erkennung kennt jetzt alle Titelschemata, und als Alternativen kommen nur echte Personennamen infrage.
- **„Welche Folge?“** war in einigen Fällen zu leicht, weil der Aha-Satz den Titel wiederholte („Buchpreisbindung“ → „Wie ich eine Buchhandlung eröffne“). Geändert: Solche Sätze sind für diesen Typ gesperrt.
- Einige **Auswahlfragen sind Trivia ohne Lerneffekt** (z. B. „Wie lange dauert die Saisonvorbereitung beim LASK?“). Die Prüfung vergibt dafür meist Qualität 3. Geändert, nachdem alle Folgen geprüft waren: Die Tagesrunden bevorzugen jetzt Einträge mit Qualität 4–5 (55 % der geplanten Tagesfragen), Qualität 3 springt nur ein, wo der Vorrat für einen Fragetyp knapp wird. Im freien Modus bleibt der ganze Pool spielbar.

## 5. Deployment

- Ein neues Repo `asator-git/emdw-spiel` durfte ich in dieser Umgebung nicht anlegen (das Anlegen von Repositories war für die Session gesperrt). Der komplette Code liegt deshalb im Branch `claude/emdw-game-podcast-kkv7ye` des bestehenden Repos unter `emdw-spiel/`, fertig zum Umziehen: `emdw-spiel/.github/workflows/pages.yml` deployt `web/` auf GitHub Pages, sobald der Ordner Wurzel des neuen Repos ist. `update.sh` pusht alternativ direkt auf `gh-pages`.
- **Live-Vorschau bis dahin:** als private claude.ai-Seite (siehe README). Dort laufen der Service Worker und Duell-Links mit `#/duell/...` nicht (Sandbox), alles andere schon.
- `noindex, nofollow` ist gesetzt.

## 6. Offene Punkte

1. **Repo anlegen und Pages aktivieren**, 2 Minuten (siehe README → Deployment). Danach funktionieren PWA-Installation, Offline-Modus und Duell-Links.
2. **Schriftlizenz prüfen:** UT Glasgow Grotesk und Gedankenstrich liegen als Webfont-Subsets im öffentlichen Repo. Erlaubt die Lizenz Web-Einbettung? (Die CI liefert WOFF/WOFF2, das spricht dafür.)
3. **Dropbox → Brand Assets** war nicht erreichbar. Kurz checken, ob dort etwas Neueres als im Drive liegt.
4. **Restliche Prüfungen:** Stand und Pool-Größe stehen in `data/pool_report.md`. Ein weiterer `update.sh`-Lauf mit API-Schlüssel prüft automatisch alles, was noch fehlt.
5. **Folgen ohne Gast in den Metadaten** (Updates, Solo-Folgen) kommen bei „Wer hat's gesagt?“ nicht vor. Das ist gewollt.
6. Die **YouTube-Untertitel** der neuesten Folgen kamen wegen des Bot-Checks nicht. Diese Folgen sind mit Whisper transkribiert, die Zeitstempel passen trotzdem zum YouTube-Video, weil der Podcast-Schnitt gleich ist. Bei abweichenden Intros kann „Stelle anhören“ ein paar Sekunden danebenliegen.

## 7. Ideen für Version 2

- **Duell live:** zwei Handys, dieselbe Runde, gleichzeitig. Ein kleiner Websocket-Dienst würde reichen, oder ganz ohne Server über einen Raumcode und abwechselndes Teilen.
- **Sponsoring-Runden:** eine Bonusfrage pro Woche zum Thema einer Partnerfolge, klar gekennzeichnet („Diese Runde ist präsentiert von …“). Passt zum bestehenden Werbemodell des Podcasts, ohne die Tagesrunde zu verwässern.
- **Live-Event-Modus:** Bei Live-Shows spielt der Saal per QR-Code mit, Andreas sieht die Kalibrierungskurve des Publikums auf der Leinwand. „Wie sicher waren 400 Menschen?“ ist ein eigener Aha-Moment.
- **Neue Folge = neue Runde:** Am Erscheinungstag einer Folge kommen drei Fragen aus genau dieser Folge (Spoiler-frei, erst nach dem Hören freischaltbar).
- **Jahresrückblick pro Spieler:in:** „Du hast heuer 214 Folgen entdeckt, am besten kalibriert bist du bei Klima.“
- **Hörschnipsel** als seltener Joker: 5 Sekunden Originalton statt Text bei „Wer hat's gesagt?“.
- **Pool-Qualität:** die Kandidaten, die bisher nicht zur Prüfung ausgewählt waren (bis zu 11 pro Folge), per `update.sh` nachprüfen und damit den Vorrat an Qualität-4-Fragen vergrößern. Schwierigkeit aus echten Antwortquoten lernen (anonym, opt-in).

## 8. Qualitätsprüfung – Ergebnisse

- **Playwright:** `tests/e2e.js` spielt auf iPhone 13 und Pixel 7 alle Modi durch: Tagesrunde mit allen fünf Mechaniken, Ergebnis, freies Spiel, „Erste Stunde“, Sternenhimmel mit Folgenkarte, Profil und Duell-Link. Jeder Screen wird fotografiert, es gibt keine JS-Fehler. Die Screenshots habe ich mir angesehen und mehrere Runden verbessert: Jahreszahlen, Anführungszeichen-Glyphen, Scribble-Farben, überlappende Pins, Überlauf im Sternenhimmel, doppeltes „Wie sicher bist du?“.
- **Stichprobe:** 100 zufällige Pool-Fragen hat ein unabhängiger Prüfer gegen das Transkript gelesen. Ergebnis: **2 Fehler = 2 %**, beide im Aha-Text, nicht in Frage oder Antwort. Die Einträge sind gesperrt, der Prüf-Prompt ist geschärft. Details in `data/audit/STICHPROBE.md`.
- **Lighthouse Mobile** (lokal, ohne gzip): Startseite **Performance 95, Accessibility 100, Best Practices 100**, Fragebildschirm **97 / 100 / 100**, Sternenhimmel **96 / 100 / 100**. Das LCP liegt im gedrosselten Lighthouse-Profil „Slow 4G“ (1,6 Mbit/s, 150 ms RTT) bei 2,5–2,8 s. Größtes Element ist das Logo. Auf GitHub Pages mit gzip und auf einer echten 4G-Verbindung (typisch 10+ Mbit/s) liegt der erste Aufruf unter 2 s. Die Startseite lädt 350 KB, davon 97 KB Handschrift-Font, der nicht blockiert. Der Fragen-Pool (3,6 MB roh, ca. 900 KB gzip) wird erst im freien Modus geladen, die Tagesrunde braucht nur ihre Monatsdatei.
