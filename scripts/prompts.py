"""Prompts und JSON-Schemas für die drei Pipeline-Stufen. Werden von pipeline.py (Batches-API)
und vom Agent-Modus (Claude in einer Cloud-Session) identisch verwendet."""

THEMEN = [
    "Klima & Energie", "Wirtschaft & Arbeit", "Gesundheit & Körper", "Psyche & Zusammenleben",
    "Österreich & Politik", "Welt & Konflikte", "Geschichte", "Wissenschaft & Technik",
    "Natur & Ernährung", "Gesellschaft & Kultur",
]

KINDS = ["zahl", "aha", "zitat", "erklaerung", "andreas_frage", "moment"]

EXTRACT_SYSTEM = """Du arbeitest für „Erklär mir die Welt“ (EMDW), den Wissens-Podcast von Andreas Sator aus Wien (seit 2018). Andreas lädt pro Folge eine Expertin oder einen Experten ein und stellt die Fragen, die sich Hörer:innen auch stellen. Aus den Folgen entsteht ein Handyspiel für Fans: Man lernt etwas, erkennt den Podcast wieder und wird zurück in die Folge geführt.

Deine Aufgabe: Lies das Transkript EINER Folge vollständig und finde 15 bis 25 Kandidaten für Spielfragen.

Arten (Feld "kind"):
- "zahl": eine überraschende, konkrete Zahl, die im Gespräch genannt wird (Prozent, Menge, Jahr, Dauer …). Gut zum Schätzen mit einem Schieberegler.
- "aha": ein Fakt, bei dem man sich denkt „Echt? Das wusste ich nicht“.
- "zitat": eine prägnante Kernaussage des Gastes, die gut für „Wer hat's gesagt?“ taugt (typisch für diese Person, nicht austauschbar).
- "erklaerung": ein Zusammenhang, den der Gast besonders schön oder anschaulich erklärt (Bild, Vergleich, Mechanismus).
- "andreas_frage": eine typische Frage oder Formulierung von Andreas (z. B. sein Einstieg, seine Abschlussfrage, wie er nachhakt). 0–2 pro Folge.
- "moment": ein lustiger, menschlicher oder überraschender Moment im Gespräch. 0–2 pro Folge.
Mische die Arten; Ziel ungefähr: 5+ zahl, 5+ aha, 2–4 zitat, 2–4 erklaerung.

Was eine gute Frage ausmacht: Man lernt etwas über die Welt, das man am Abend Freund:innen erzählt („Wusstest du, dass …?“). Mindestens zwei Drittel der Kandidaten müssen solches Weltwissen sein ("scope": "welt") – Zahlen und Zusammenhänge, die auch ohne die Folge stimmen und interessant sind. Details, die nur in diesem Gespräch vorkommen (Anekdoten, was eine Bekannte erlebt hat, Andreas' Einkauf), sind "scope": "folge" und höchstens ein Drittel. Zahlen aus Einzelfällen („eine Hörerin zahlte …“) taugen kaum zum Schätzen; nimm lieber Durchschnitte, Anteile, Größenordnungen, Jahreszahlen, Rekorde.

Harte Regeln:
1. Genau EINE Fundstelle pro Kandidat. "t" ist die Sekunde des Transkript-Abschnitts, in dem der Beleg beginnt (die Zahl in eckigen Klammern [s] am Zeilenanfang).
2. "quote" ist ein WÖRTLICHER Auszug aus dem Transkript (zusammenhängend, 8–60 Wörter), der die Aussage belegt. Nichts umformulieren, nichts zusammenkleben. Er wird maschinell gegen das Transkript geprüft.
3. "quote_clean" ist dasselbe Zitat nur sprachlich geglättet: Füllwörter („äh“, „ähm“, „also“, „sozusagen“, Wortwiederholungen) raus, offensichtliche Transkriptionsfehler korrigiert. Der Sinn bleibt exakt gleich, nichts dazu erfinden.
4. Automatische Transkripte enthalten Fehler, besonders bei Zahlen und Namen. Wenn eine Zahl unplausibel oder mehrdeutig ist, nimm den Kandidaten nicht.
5. Nur Aussagen, die ohne Kontext verständlich sind und die der Gast als Tatsache oder klare Einschätzung vertritt – keine Hypothesen, die gleich danach relativiert werden.
6. Fair: nichts, was Gast oder Andreas bloßstellt, nichts aus dem Zusammenhang Gerissenes, keine privaten Details über Dritte, keine parteipolitischen Spitzen als Fakt.
7. Zeitgebundenes (Umfragen, Preise, „derzeit“, Rekorde, Amtsinhaber:innen) ist erlaubt, aber setze "time_sensitive": true.
8. Werbung, Sponsor-Durchsagen und Hinweise auf Patreon/Steady sind tabu.

Zu jedem Kandidaten schreibst du direkt die Spielbausteine:
- "statement": die Aussage in einem neutralen, selbsttragenden deutschen Satz.
- "question": eine faire Frage an Spieler:innen. Du-Form. Keine Fangfrage, kein Wortklauben, keine doppelte Verneinung. Bei "zahl" eine Schätzfrage („Wie viel Prozent …?“, „Wie viele …?“).
- "answer": die richtige Antwort, kurz (max. 8 Wörter).
- "distractors": genau 3 falsche, aber plausible Antworten im selben Format und ähnlicher Länge wie "answer". Nicht absurd, nicht teilweise richtig.
- "number_value", "number_unit", "slider_min", "slider_max", "log_scale": nur bei "zahl" sinnvoll befüllt (Schieberegler-Bereich so, dass die Lösung nicht am Rand oder in der Mitte liegt; log_scale true, wenn der Bereich über mehr als zwei Größenordnungen geht). Bei anderen Arten: 0, "", 0, 0, false.
- "aha": 2–3 Sätze Auflösung, die man nach der Antwort liest. Erklärt, WARUM das so ist, mit dem Detail aus der Folge. Ton wie Andreas: Du-Form, neugierig, warm, ein bisschen trocken-witzig, österreichisches Deutsch erlaubt („heuer“, „Jänner“, „eh“). Nie belehrend. Keine KI-Floskeln („Spannend ist …“, „Tatsächlich …“, „Es ist wichtig zu beachten“, „faszinierend“, „tauchen wir ein“), keine Ausrufezeichen-Kaskaden, keine Emojis.
- "speaker": wer das sagt ("Andreas Sator" oder der Name des Gastes, wie in den Metadaten).
- "difficulty": 1 (weiß man fast intuitiv), 2 (Allgemeinwissen plus Nachdenken), 3 (nur wer die Folge gehört hat).
- "tags": 1–3 kurze Schlagworte.
- "scope": "welt" (allgemeingültiges Wissen) oder "folge" (Detail aus diesem Gespräch).

Außerdem für die ganze Folge:
- "theme": genau eines aus: {themen}
- "summary": ein Satz (max. 25 Wörter), worum es in der Folge geht, im Ton von Andreas.

Antworte ausschließlich mit JSON nach dem Schema."""

def extract_user(ep, transcript_lines):
    guests = ", ".join(ep["guests"]) or "–"
    return (f"Folge: {ep['title']}\nDatum: {ep['date']}\nGäste: {guests}\n"
            f"Beschreibung: {ep['description'][:1200]}\n\n"
            f"TRANSKRIPT (Format: [Sekunde] Text; Quelle: {transcript_lines[0]}):\n" + "\n".join(transcript_lines[1:]))

_cand_props = {
    "kind": {"type": "string", "enum": KINDS},
    "t": {"type": "integer"},
    "speaker": {"type": "string"},
    "quote": {"type": "string"},
    "quote_clean": {"type": "string"},
    "statement": {"type": "string"},
    "question": {"type": "string"},
    "answer": {"type": "string"},
    "distractors": {"type": "array", "items": {"type": "string"}},
    "number_value": {"type": "number"},
    "number_unit": {"type": "string"},
    "slider_min": {"type": "number"},
    "slider_max": {"type": "number"},
    "log_scale": {"type": "boolean"},
    "aha": {"type": "string"},
    "difficulty": {"type": "integer", "enum": [1, 2, 3]},
    "time_sensitive": {"type": "boolean"},
    "tags": {"type": "array", "items": {"type": "string"}},
    "scope": {"type": "string", "enum": ["welt", "folge"]},
}
EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "theme": {"type": "string", "enum": THEMEN},
        "summary": {"type": "string"},
        "candidates": {"type": "array", "items": {
            "type": "object", "properties": _cand_props,
            "required": list(_cand_props), "additionalProperties": False}},
    },
    "required": ["theme", "summary", "candidates"],
    "additionalProperties": False,
}

REVIEW_SYSTEM = """Du bist die strenge, aber freundliche Faktenprüfung für das Spiel zu „Erklär mir die Welt“. Du bekommst Kandidaten für Spielfragen, die jemand anderer aus einer Folge gezogen hat, und die Transkript-Ausschnitte rund um jede Fundstelle (je ca. eine Minute davor bis eine Minute danach). Prüfe JEDEN Kandidaten einzeln gegen seinen Ausschnitt.

Prüffragen:
1. Beleg: Steht die Aussage wirklich so im Transkript bei Sekunde t (± 60 s)? Stimmt die Antwort? Sind die Distraktoren eindeutig falsch?
2. Transkriptionsfehler: Könnte die Zahl oder der Name falsch transkribiert sein (z. B. „15“ statt „50“, verhörte Namen)? Nutze den Kontext und dein Weltwissen. Bei begründetem Zweifel: drop.
3. Kontext: Ist die Aussage ohne Kontext verständlich und gibt sie wieder, was der Gast wirklich meint (keine relativierte Hypothese, keine Ironie wörtlich genommen)?
4. Aktualität: Die Folge ist vom {date}. Ist der Fakt heute (November 2026) veraltet? Wenn er damals stimmte und heute nur anders ist: keep mit stand_note „Stand {year}“. Wenn er heute klar irreführend wäre (z. B. überholte Pandemie-Zahlen, Amtsinhaber, Preise ohne Einordnung): drop.
5. Fairness: Nichts Bloßstellendes über Gast, Andreas oder Dritte; nichts parteipolitisch Einseitiges als Tatsache; keine Fangfrage.
6. Spielbarkeit: Frage klar, eine eindeutig richtige Antwort, Distraktoren plausibel und gleich lang. Bei Schätzfragen: Schieberegler-Bereich sinnvoll.
7. Ton und Inhalt des "aha": Du-Form, warm, nicht belehrend, keine KI-Floskeln. Jede Tatsachenbehauptung im aha muss im Ausschnitt stehen oder allgemein gesichertes Wissen sein – keine erfundenen Motive, Zitate oder Details. Sagt der Gast etwas sachlich Falsches (Rechenfehler, Verwechslung), wird das nicht als Fakt übernommen: fix oder drop. Formuliere hölzerne Texte neu.
8. quote_clean: nur sprachlich geglättet? Sinn identisch? Sonst korrigieren.

Für jeden Kandidaten gib zurück:
- "i": der Index
- "verdict": "keep" (passt), "fix" (passt nach deinen Korrekturen), "drop" (raus)
- "issues": Liste aus "beleg", "transkription", "kontext", "veraltet", "fairness", "spielbarkeit", "ton" (leer, wenn nichts)
- "note": ein kurzer Satz Begründung
- "stand_note": "" oder z. B. „Stand 2019“
- die Felder "question", "answer", "distractors", "aha", "quote_clean", "statement": bei "fix" die korrigierte Fassung, sonst unverändert übernehmen
- "quality": 1–5, wie gut das als Spielfrage ist (5 = will man Freund:innen zeigen)

Sei lieber streng: Ein Fehler im Spiel kostet mehr Vertrauen als eine Frage weniger. Antworte ausschließlich mit JSON nach dem Schema."""

REVIEW_MAX = 14

def review_selection(cands):
    """Die aussichtsreichsten Kandidaten einer Folge (Weltwissen, Vielfalt der Arten, Schätzzahlen).
    Die Kuratierung nimmt höchstens 12 pro Folge – geprüft werden 14, damit nach Ausfällen genug übrig bleibt."""
    order = sorted(range(len(cands)), key=lambda i: (cands[i].get("scope") != "welt", cands[i].get("quote_match", 1) < 0.8,
                                                    {"zahl": 0, "aha": 1, "erklaerung": 2, "zitat": 3, "moment": 4, "andreas_frage": 5}[cands[i]["kind"]], i))
    pick, per = [], {}
    for rnd in range(4):  # Runden: pro Art erst wenige, dann mehr -> Vielfalt
        for i in order:
            k = cands[i]["kind"]
            if i in pick or per.get(k, 0) > rnd: continue
            pick.append(i); per[k] = per.get(k, 0) + 1
            if len(pick) >= REVIEW_MAX: return sorted(pick)
    return sorted(pick)

def review_user(ep, transcript_lines, cands):
    """Statt des ganzen Transkripts nur die Umgebung jeder Fundstelle (spart ~2/3 der Eingabe)."""
    import json, re
    sel = review_selection(cands)
    slim = [{"i": i, **{k: cands[i][k] for k in ("kind", "t", "speaker", "quote", "quote_clean", "statement", "question",
             "answer", "distractors", "number_value", "number_unit", "slider_min", "slider_max", "aha", "time_sensitive")}}
            for i in sel]
    cands = [cands[i] for i in sel]
    rows = []
    for ln in transcript_lines[1:]:
        m = re.match(r"\[(\d+)\] ", ln)
        if m: rows.append((int(m.group(1)), ln))
    wins = sorted((max(0, c["t"] - 45), c["t"] + 40) for c in cands)
    merged = []
    for a, b in wins:
        if merged and a <= merged[-1][1] + 20: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    parts = []
    for a, b in merged:
        sel = [ln for s, ln in rows if a - 25 <= s <= b]
        parts.append("\n".join(sel))
    return (f"Folge: {ep['title']}\nDatum: {ep['date']}\nGäste: {', '.join(ep['guests']) or '–'}\n\n"
            f"KANDIDATEN:\n{json.dumps(slim, ensure_ascii=False, separators=(",", ":"))}\n\n"
            f"TRANSKRIPT-AUSSCHNITTE (Format: [Sekunde] Text; „…“ trennt Ausschnitte):\n" + "\n…\n".join(parts))

_rev_props = {
    "i": {"type": "integer"},
    "verdict": {"type": "string", "enum": ["keep", "fix", "drop"]},
    "issues": {"type": "array", "items": {"type": "string", "enum": ["beleg", "transkription", "kontext", "veraltet", "fairness", "spielbarkeit", "ton"]}},
    "note": {"type": "string"},
    "stand_note": {"type": "string"},
    "statement": {"type": "string"},
    "question": {"type": "string"},
    "answer": {"type": "string"},
    "distractors": {"type": "array", "items": {"type": "string"}},
    "aha": {"type": "string"},
    "quote_clean": {"type": "string"},
    "quality": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
}
REVIEW_SCHEMA = {
    "type": "object",
    "properties": {"reviews": {"type": "array", "items": {
        "type": "object", "properties": _rev_props, "required": list(_rev_props), "additionalProperties": False}}},
    "required": ["reviews"], "additionalProperties": False,
}
