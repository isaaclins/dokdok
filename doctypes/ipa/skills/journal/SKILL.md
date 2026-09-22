---
name: journal
description: Write today's Arbeitsjournal entry for the IPA by asking the candidate about their day and, if they agree and the project is in git, reading the commits since the last entry. Use at the end of a work day or when asked to "write the journal".
---

# Arbeitsjournal – ein Eintrag pro Arbeitstag

1. Frag nach dem Datum (Default: heute) und ob ein Eintrag schon existiert (`ls doc/arbeitsjournal`).
2. Frag: «Ist das Projekt in einem Git-Repository, und darf ich die Commits seit dem letzten
   Eintrag als Gedächtnisstütze lesen?» Nur bei Ja: `dokdok inputs arbeitsjournal`.
   Wenn die Person nicht weiss, was Git ist: kurz erklären, dann ohne weitermachen.
3. Frag nach dem Tag – eine Frage aufs Mal:
   - Was hast du heute gemacht, ungefähr mit Zeiten?
   - Was war schwierig, und wie hast du es gelöst?
   - Wer oder was hat geholfen (Personen, Tools, KI)? Was davon hast du übernommen?
   - Was nimmst du mit?
4. `dokdok entry arbeitsjournal --date YYYY-MM-DD --title "Tag N"` und den Eintrag aus den
   Antworten füllen. Soll-Zeiten aus dem Zeitplan (`doc/06-zeitplan.md`), Ist-Zeiten von der Person.
   Nichts dazuerfinden; Unklares als `[Platzhalter]`.
5. `dokdok log --tool "<du>" "Arbeitsjournal Tag N aus Gespräch verfasst" --outcome "…"`, dann `dokdok check`.
