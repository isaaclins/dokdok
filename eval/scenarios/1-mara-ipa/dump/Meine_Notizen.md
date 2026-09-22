
# Meine Notizen zur IPA – Mara

kurz mal alles aufschreiben was mir zum Projekt einfällt, bevor ichs vergesse

## Worum gehts

Die Kommissionierer im Lager kriegen ihre Pick-Liste heute aus einem Excel. Der Schichtleiter (Beni) exportiert am Morgen die offenen Aufträge, kopiert die in ein Excel-Sheet mit tausend Formeln und sortiert von Hand. Dann druckt ers aus. Dauert jeden Morgen ~20-30 min und wenn Beni krank ist weiss keiner genau wie das Sheet geht -> Chaos.

Meine Idee: ein kleines CLI-Tool das aus dem Lagerbestand-CSV (Export aus NoLoWMS) automatisch eine optimierte Pick-Liste macht. Optimiert = sortiert nach Lagerplatz, damit der Weg im Lager kurz ist. Reihenfolge Gang -> Regal -> Ebene. Also nicht kreuz und quer durchs Lager rennen.

Lagerplatz-Format bei uns: `A-01-02` = Gang A, Regal 01, Ebene 02. Gänge A bis F. Das kann man super als Sortierschlüssel nehmen.

## Messbare Ziele (muss ich noch schärfer machen)

- Ziel 1: Pick-Liste wird in unter 2 Sekunden generiert für eine typische CSV (~400 Positionen). messbar, ok.
- Ziel 2: Weglänge kürzer als bei der manuellen Liste. Wie mess ich das?? vielleicht Anzahl Gang-Wechsel zählen? Idee: alte Liste vs neue Liste, Gangwechsel vergleichen. muss ich mir überlegen.
- Ziel 3: Zeitersparnis für Beni am Morgen. Von ~25 min auf quasi 0 (nur noch Befehl ausführen). schwer objektiv zu messen aber kann ich mit Beni stoppen.
- Ziel 4: keine manuellen Excel-Fehler mehr. tests decken das ab.

-> muss aufpassen dass die Ziele wirklich MESSBAR sind, der Leitfaden pocht da drauf.

## Stack

- Node.js (kann ich am besten, hab ich schon bei den ÜK gemacht)
- reines CLI, kein Frontend. Input CSV -> Output CSV oder Konsolentabelle
- CSV parsen: erst überlegt eine lib zu nehmen aber unsere CSVs sind simpel (Semikolon getrennt, Schweiz halt), mach ich vielleicht selber. weniger Abhängigkeiten = besser laut Firmenstandard
- Tests mit BATS weil Firmenstandard für CLI-Zeug. muss ich mich noch reinfinden, kenn eher jest
- Git auf der internen GitLab

## Painpoints vom jetzigen Excel-Prozess (Beni-Interview Notizen)

- Sheet ist über Jahre gewachsen, keiner blickt durch
- Sortierung macht Beni teilweise von Hand -> Fehler
- wenn ein Artikel keinen Lagerplatz hat rutscht er im Excel einfach nach oben und wird übersehen
- Mengenspalte manchmal leer -> Formel gibt #WERT und die Zeile fehlt auf dem Ausdruck. schon 2x passiert dass was vergessen ging
- kein Backup, das File liegt auf Benis Desktop lol

## Randfälle an die ich denken muss

- leere Mengenspalte (siehe oben, häufig!)
- Artikel ohne Lagerplatz -> darf NICHT verschwinden, muss ans Ende oder in eigene Liste
- doppelte Artikelnummer in der CSV (kommt vor bei mehreren Chargen) -> zusammenzählen? oder getrennt? fragen.
- ungültiges Lagerplatz-Format
- Komma vs Punkt bei Mengen (Stück sind ganzzahlig, sollte kein Problem sein, aber Gewicht?)

## Grober Zeitplan (hab 10 Tage / ~40h)

- Tag 1: informieren, Beni nochmal löchern, CSV-Beispiele sammeln
- Tag 2: planen, Anforderungen FA01 usw aufschreiben, Testfälle
- Tag 3: entscheiden (CSV lib ja/nein, Sortierstrategie)
- Tag 4-7: realisieren, TDD. erst CSV-Parser, dann Sortierung, dann Sonderfälle, dann Ausgabe
- Tag 8: kontrollieren, mit Beni echte Daten testen
- Tag 9: auswerten + Doku
- Tag 10: Puffer (brauch ich sicher)

## offene Fragen

- doppelte Artikelnummern zusammenfassen oder nicht -> Beni fragen
- soll die Ausgabe drucken können oder reicht CSV das er dann druckt? erstmal CSV
- Format vom Lagerplatz immer 3-teilig? gibts Ausnahmen im Aussenlager? checken

todo: KI-Verzeichnis nicht vergessen, der Leitfaden will das zwingend. Ich nutz ja Copilot ab und zu.
