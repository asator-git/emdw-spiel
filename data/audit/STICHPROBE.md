# Stichprobe: 100 zufällige Pool-Fragen gegen das Transkript

Zufallsauswahl (Seed 2026) aus dem kuratierten Pool, geprüft von einem unabhängigen Prüfer (Claude Opus 5.5 ohne Kenntnis der Pipeline) gegen den Transkript-Ausschnitt ±60 s.

**Ergebnis: 2 Fehler bei 100 Fragen = 2 %** (Grenze laut Auftrag: über 2 % → Pipeline nachbessern).

## Fehler

- 39-2 (a): Die Aha-Aussage schreibt Harald Fidler die Vermutung zu, Gustav Davis habe schlicht Geld verdienen wollen; das kommt im Transkriptausschnitt nicht vor (dort geht es nur um Kleinformat, Preis und Illustrationen).
- 195-18 (e): Die Aha-Aussage gibt Badelts Satz als Tatsache wieder, dass es bei einer 60-Prozent-Median-Schwelle Armut gibt, solange keine völlige Gleichverteilung herrscht. Das ist mathematisch falsch: Auch bei Ungleichheit kann niemand unter 60 Prozent des Medians liegen.

## Konsequenz

- Beide Einträge sind über `data/audit/excluded.json` aus dem Pool entfernt.
- Beide Fehler steckten im Aha-Text, nicht in Frage oder Antwort. Der Review-Prompt verlangt deshalb jetzt ausdrücklich, dass jede Tatsachenbehauptung im Aha belegt ist und sachlich falsche Gastaussagen nicht als Fakt übernommen werden.
- Grenzfälle, die nicht als Fehler zählen (Paraphrase, „um 1868“ statt 1869, Fakten mit „Stand“-Hinweis), stehen mit Begründung in `sample100_verdicts.json`.
