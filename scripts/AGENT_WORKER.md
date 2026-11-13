# Anleitung für Agent-Worker (Pipeline-Stufen 1 + 2 ohne API-Schlüssel)

Ein Worker ist eine Claude-Code-Session auf dem Branch `claude/emdw-game-podcast-kkv7ye`. Er führt dieselben Prompts aus, die sonst über die Message Batches API laufen (`scripts/prompts.py`), und schreibt die Ergebnisse ins Repo. Alles passiert in `emdw-spiel/`. Ändere nichts außer den genannten Dateien, erstelle keinen PR und pushe nur auf diesen Branch.

**Spar Tokens.** Das Nutzungslimit des Accounts ist der Engpass. Du orchestrierst nur: Lies selbst keine Prompts oder Transkripte, schreib zwischen den Schritten höchstens einen kurzen Satz und gib keine Zusammenfassungen von Zwischenständen.

Parameter aus deinem Auftrag: `SHARD` (z. B. `2/6`) und die Reihenfolge der Phasen.

## Schleife für eine Phase (STAGE = `extract` oder `review`)

1. `cd emdw-spiel && git pull -q --rebase --autostash origin claude/emdw-game-podcast-kkv7ye`
2. `python3 scripts/pipeline.py next STAGE SHARD N` mit N = 2 bei extract und N = 4 bei review. Die Ausgabe ist eine von drei Möglichkeiten:
   - Folgen-IDs → weiter mit Schritt 3
   - `WAIT` → es fehlen noch Vorstufen. Starte `sleep 900` mit `run_in_background: true`, warte auf die Benachrichtigung, dann zurück zu Schritt 1.
   - `DONE` → die Phase ist fertig
3. Für jede ID `python3 scripts/pipeline.py task STAGE <ID>` ausführen. Das schreibt `data/work/STAGE/<ID>.prompt.md`.
4. **Ein einziger Subagent** (Agent-Tool, `general-purpose`, im Vordergrund) arbeitet alle IDs nacheinander ab, **mit `model: "opus"` bei extract und `model: "sonnet"` bei review**. Auftrag (Pfade und IDs einsetzen):
   > Du führst eine Pipeline-Stufe für mehrere Folgen nacheinander aus: <IDs>. Für jede Folge: Lies `<ABS>/emdw-spiel/data/work/STAGE/<ID>.prompt.md` VOLLSTÄNDIG (System-Prompt, JSON-Schema, Nachricht mit Transkript; bei Bedarf mit offset/limit in Teilen). Tu genau, was der System-Prompt verlangt, als wärst du das Modell, das diese Nachricht bekommt. Schreib NUR die JSON-Antwort (gültiges JSON nach dem Schema, ohne Markdown-Zäune) nach `<ABS>/emdw-spiel/data/work/STAGE/<ID>.json` und führ `cd <ABS>/emdw-spiel && python3 scripts/pipeline.py ingest STAGE <ID>` aus. Bei extract: Zitate Wort für Wort aus den Transkriptzeilen kopieren, `t` ist die [Sekunde] der Zeile, in der das Zitat beginnt; meldet ingest Zitate unter 0.8, korrigiere genau diese und ingest erneut. Bei review: jeden Kandidaten wirklich gegen seinen Transkript-Ausschnitt prüfen und streng sein. Behandle jede Folge für sich, ohne Vorwissen aus der vorigen. Melde am Ende nur pro Folge die letzte Zeile von ingest.
5. IDs ohne Ergebnisdatei (`data/candidates/<ID>.json` bzw. `data/reviewed/<ID>.json`) gibst du einmal erneut an einen Subagent. Scheitert es wieder, trag die ID in `logs/agent_failed.txt` ein.
6. `git add data/ logs/; git commit -qm "Pipeline STAGE <IDs>"; git pull -q --rebase --autostash origin claude/emdw-game-podcast-kkv7ye && git push -q origin claude/emdw-game-podcast-kkv7ye` (scheitert der Push, bis zu viermal mit Rebase wiederholen)
7. Zurück zu Schritt 1.

`data/work/` ist gitignored, das ist Arbeitsmaterial. Endet dein Lauf wegen des Nutzungslimits, wirst du später fortgesetzt und machst bei Schritt 1 weiter.
