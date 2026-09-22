
# Firmenstandards Softwareentwicklung
## Nordlicht Logistik AG · Abteilung ICT
### Version 3.2 – gültig ab 01.01.2026

Diese Standards gelten für alle intern entwickelten Anwendungen sowie für Lernendenarbeiten (inkl. IPA).

---

## 1. Allgemeine Grundsätze

- Lesbarkeit vor Cleverness. Code wird häufiger gelesen als geschrieben.
- Kleinste sinnvolle Änderung. Kein Refactoring «bei Gelegenheit» ausserhalb der Aufgabe.
- Keine Geheimnisse (Passwörter, Tokens) im Repository.

## 2. Namensgebung

- Sprache im Code: **Englisch** (Bezeichner, Kommentare). Fachbegriffe der Domäne dürfen deutsch bleiben, wenn sie im Betrieb so verwendet werden (z. B. `kommissionierung`).
- Variablen und Funktionen: `camelCase`
- Konstanten: `UPPER_SNAKE_CASE`
- Dateien für Node.js-Module: `kebab-case.js`
- Keine Abkürzungen ausser etablierte (`id`, `csv`, `ean`).

## 3. JavaScript / Node.js

- Node.js LTS (aktuell 20.x). Kein Wechsel der Major-Version während eines Projekts.
- `const` vor `let`; `var` ist verboten.
- Strikte Gleichheit (`===`), nie `==`.
- Ein Modul = eine Verantwortung. Datei nicht über 300 Zeilen.
- Fehler werden als `Error`-Objekte geworfen, nie als String.
- Externe Eingaben (CSV, Argumente) werden validiert, bevor sie verarbeitet werden.

## 4. Testing

- Testframework für Shell-/CLI-Werkzeuge: **BATS** (Bash Automated Testing System).
- Jede öffentliche Funktion und jeder CLI-Aufruf braucht mindestens einen Test.
- Testdateien liegen unter `test/` und enden auf `.bats`.
- Ein Testfall prüft genau ein Verhalten. Namensschema: `@test "resolves known article by ean"`.
- Testdaten (Beispiel-CSV) liegen unter `test/fixtures/`.
- Vorgehen: testgetrieben (TDD) – erst der fehlschlagende Test, dann die Implementierung.
- Vor jedem Commit müssen alle Tests grün sein (`bats test/`).

Beispiel:

```bash
@test "picklist is sorted by warehouse location" {
  run node bin/picklist.js --in test/fixtures/stock.csv
  [ "$status" -eq 0 ]
  [ "${lines[0]}" = "A-01-02;Schrauben M6;120" ]
}
```

## 5. Git / Commit-Konventionen

- Ein Commit = eine abgeschlossene, lauffähige Änderung.
- Commit-Message nach **Conventional Commits**:
  - `feat:` neue Funktion
  - `fix:` Fehlerbehebung
  - `test:` Tests hinzugefügt/geändert
  - `docs:` Dokumentation
  - `refactor:` Umbau ohne Verhaltensänderung
  - `chore:` Aufräumarbeiten, Konfiguration
- Betreff in der Befehlsform, klein, ohne Punkt am Ende, max. 72 Zeichen.
- Deutsch oder Englisch, aber innerhalb eines Projekts einheitlich.
- Kein Direkt-Push auf `main` ohne grüne Tests.

Beispiele:
```
feat: parse stock csv into article records
fix: handle empty quantity column
test: add cases for invalid location code
```

## 6. Dokumentation

- Jedes Repository enthält eine `README.md` mit: Zweck, Voraussetzungen, Installation, Aufruf/Beispiel, Tests ausführen.
- Öffentliche Funktionen erhalten einen kurzen JSDoc-Block (Zweck, Parameter, Rückgabe).
- Vorlage für den Funktionskopf:

```js
/**
 * Kurzbeschreibung der Funktion.
 * @param {Typ} name - Bedeutung
 * @returns {Typ} Bedeutung
 */
```

- Keine auskommentierten Code-Blöcke im Repository. Was weg soll, wird gelöscht (Git bewahrt die Historie).

## 7. Ablage

- Quellcode unter Versionskontrolle (interne GitLab-Instanz).
- Keine Binärdateien oder generierten Artefakte im Repository (`.gitignore` pflegen).
