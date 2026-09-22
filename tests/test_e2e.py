"""End-to-end: new → check → render on the example doctype. Needs pandoc."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCTYPE = REPO / "doctypes" / "school-thesis"
pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")


def dokdok(*args, cwd):
    return subprocess.run([sys.executable, "-m", "dokdok.cli", *args], cwd=cwd, text=True, capture_output=True)


@pytest.fixture
def project(tmp_path):
    r = dokdok("new", "thesis", "--type", str(DOCTYPE), "--title", "T", "--author", "A", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    return tmp_path / "thesis"


def test_new_creates_skeleton(project):
    names = sorted(p.name for p in (project / "doc").iterdir())
    assert names == ["01-einleitung.md", "02-hauptteil.md", "03-schlusswort.md", "05-anhang.md"]
    assert "dokdok:hint" in (project / "doc" / "01-einleitung.md").read_text()
    assert "dokdok check" in (project / "AGENTS.md").read_text()


def test_check_finds_errors(project):
    (project / "doc" / "02-hauptteil.md").write_text(
        "---\nsection: hauptteil\n---\n\n## X\n\nDie Straße [@fehlt]. ![](a.png)\n")
    r = dokdok("check", cwd=project)
    assert r.returncode == 1
    for msg in ("contains ß", "has no caption", "[@fehlt] cited but not in sources.yaml"):
        assert msg in r.stdout


def test_check_final_flags_placeholders(project):
    assert "placeholder" not in dokdok("check", cwd=project).stdout
    assert "placeholder" in dokdok("check", "--final", cwd=project).stdout


def test_render_docx(project):
    (project / "doc" / "02-hauptteil.md").write_text(
        "---\nsection: hauptteil\n---\n\n## Kapitel\n\nText mit Quelle [@q1].\n")
    (project / "sources.yaml").write_text(
        "references:\n  - id: q1\n    type: book\n    title: Ein Buch\n    issued: {year: 2020}\n")
    r = dokdok("render", cwd=project)
    assert r.returncode == 0, r.stderr
    docx = project / "out" / "thesis.docx"
    assert docx.exists() and docx.stat().st_size > 5000
    md = (project / "out" / "thesis.md").read_text()
    assert "dokdok:hint" not in md
    assert "# Quellenverzeichnis" in md


def test_audience_target(tmp_path):
    from dokdok import render
    md = render._filter_audience(
        'a\n::: {.only-for="blue-team"}\nfix it\n:::\nb\n::: {.only-for="exec"}\nsummary\n:::\n', "exec")
    assert "fix it" not in md and "summary" in md


def test_toc_title_follows_lang(project):
    from dokdok import project as prj, render
    md = render.assemble(prj.load(project))
    assert "toc-title: 'Inhaltsverzeichnis'" in md


def test_ai_log_renders(project):
    r = dokdok("log", "--tool", "Claude Code", "Einleitung aus Konzept", "--outcome", "gegengelesen", cwd=project)
    assert r.returncode == 0, r.stderr
    from dokdok import project as prj, render
    md = render.assemble(prj.load(project))
    assert "# KI-Protokoll" in md and "| Claude Code | Einleitung aus Konzept | gegengelesen |" in md
