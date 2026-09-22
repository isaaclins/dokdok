"""ipa doctype: repeat (journal) sections, glossary, figure/table lists."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")


def run(*a, cwd):
    return subprocess.run([sys.executable, "-m", "dokdok.cli", *a], cwd=cwd, text=True, encoding="utf-8", capture_output=True)


def test_journal_glossary_and_lists(tmp_path):
    assert run("new", "ipa", "--type", str(REPO / "doctypes" / "ipa"), cwd=tmp_path).returncode == 0
    p = tmp_path / "ipa"
    assert "no entries yet" in run("check", cwd=p).stdout
    assert run("entry", "arbeitsjournal", "--date", "2026-03-10", "--title", "Tag 2", cwd=p).returncode == 0
    assert run("entry", "arbeitsjournal", "--date", "2026-03-09", "--title", "Tag 1", cwd=p).returncode == 0
    assert run("entry", "arbeitsjournal", "--date", "2026-03-09", cwd=p).returncode != 0   # exists
    (p / "glossary.yaml").write_text("- term: CLI\n  definition: Kommandozeile.\n", encoding="utf-8")
    (p / "doc" / "07-informieren.md").write_text(
        "---\nsection: informieren\n---\n\n## Ist-Analyse\n\n![Ablauf heute](a.svg)\n\n## Soll-Analyse\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n\nTable: Anforderungen\n\n## Anforderungskatalog\n\nx\n", encoding="utf-8")
    assert "2 entries" in run("check", cwd=p).stdout
    from dokdok import project as prj, render
    md = render.assemble(prj.load(p))
    assert md.index("## Tag 1 – 2026-03-09") < md.index("## Tag 2 – 2026-03-10")   # sorted by date
    assert "### Zusammenfassung" in md                                            # entry headings nested
    assert "| CLI | Kommandozeile. |" in md
    assert "Abbildung 1: Ablauf heute" in md and "Tabelle 1: Zeitplan Soll/Ist" in md and "Anforderungen" in md
    assert run("render", cwd=p).returncode == 0
