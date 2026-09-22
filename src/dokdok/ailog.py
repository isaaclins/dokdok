"""AI-usage log: schools and companies require a record of what the agent did.
`dokdok log --tool "Claude Code" "purpose" [--outcome "..."]` appends to ai-log.yaml;
a section with `generated: ai-log` renders it as a table."""
from datetime import date
from pathlib import Path
import yaml

FILE = "ai-log.yaml"
HEADERS = {"de": ("Datum", "KI-Tool", "Zweck", "Umgang mit dem Ergebnis"),
           "en": ("Date", "AI tool", "Purpose", "What was done with the result")}


def append(root: Path, tool: str, purpose: str, outcome: str = "") -> None:
    f = root / FILE
    entries = yaml.safe_load(f.read_text(encoding="utf-8")) or [] if f.exists() else []
    entries.append({"date": date.today().isoformat(), "tool": tool, "purpose": purpose, "outcome": outcome})
    f.write_text(yaml.safe_dump(entries, allow_unicode=True, sort_keys=False), encoding="utf-8")


def table(root: Path, lang: str) -> str:
    f = root / FILE
    entries = yaml.safe_load(f.read_text(encoding="utf-8")) or [] if f.exists() else []
    h = HEADERS.get(lang[:2], HEADERS["en"])
    rows = [f"| {h[0]} | {h[1]} | {h[2]} | {h[3]} |", "|---|---|---|---|"]
    for e in entries:
        d = ".".join(reversed(e["date"].split("-"))) if lang.startswith("de") else e["date"]
        rows.append(f"| {d} | {e['tool']} | {e['purpose']} | {e.get('outcome', '')} |")
    return "\n".join(rows) + "\n"
