"""End-to-end: new → check → render on the example doctype. Needs pandoc."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCTYPE = REPO / "doctypes" / "school-thesis"
DOCTYPE_DE = REPO / "doctypes" / "school-thesis-de"
pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")


def dokdok(*args, cwd):
    return subprocess.run([sys.executable, "-m", "dokdok.cli", *args], cwd=cwd, text=True, encoding="utf-8", capture_output=True)


@pytest.fixture
def project(tmp_path):
    r = dokdok("new", "thesis", "--type", str(DOCTYPE), "--title", "T", "--author", "A", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    return tmp_path / "thesis"


def test_new_creates_skeleton(project):
    names = sorted(p.name for p in (project / "doc").iterdir())
    assert names == ["01-introduction.md", "02-main-part.md", "03-conclusion.md", "05-appendix.md"]
    assert "dokdok:hint" in (project / "doc" / "01-introduction.md").read_text(encoding="utf-8")
    assert "dokdok check" in (project / "AGENTS.md").read_text(encoding="utf-8")


def test_check_finds_errors(project):
    (project / "doc" / "02-main-part.md").write_text(
        "---\nsection: main-part\n---\n\n## X\n\nText [@missing]. ![](a.png)\n", encoding="utf-8")
    r = dokdok("check", cwd=project)
    assert r.returncode == 1
    for msg in ("has no caption", "[@missing] cited but not in sources.yaml"):
        assert msg in r.stdout


def test_german_doctype_flags_eszett_and_localises_toc(tmp_path):
    assert dokdok("new", "de", "--type", str(DOCTYPE_DE), cwd=tmp_path).returncode == 0
    p = tmp_path / "de"
    (p / "doc" / "02-hauptteil.md").write_text("---\nsection: hauptteil\n---\n\n## X\n\nDie Straße.\n", encoding="utf-8")
    assert "contains ß" in dokdok("check", cwd=p).stdout
    from dokdok import project as prj, render
    assert "toc-title: 'Inhaltsverzeichnis'" in render.assemble(prj.load(p))


def test_check_final_flags_placeholders_and_hints(project):
    out = dokdok("check", cwd=project).stdout
    assert "placeholder" not in out and "hint comment" not in out
    out = dokdok("check", "--final", cwd=project).stdout
    assert "placeholder" in out and "hint comment still present" in out


def test_render_docx(project):
    (project / "doc" / "02-main-part.md").write_text(
        "---\nsection: main-part\n---\n\n## Chapter\n\nText with a source [@q1].\n", encoding="utf-8")
    (project / "sources.yaml").write_text(
        "references:\n  - id: q1\n    type: book\n    title: A Book\n    issued: {year: 2020}\n", encoding="utf-8")
    r = dokdok("render", cwd=project)
    assert r.returncode == 0, r.stderr
    docx = project / "out" / "thesis.docx"
    assert docx.exists() and docx.stat().st_size > 5000
    md = (project / "out" / "thesis.md").read_text(encoding="utf-8")
    assert "dokdok:hint" not in md
    assert "# References" in md


def test_audience_target(tmp_path):
    from dokdok import render
    md = render._filter_audience(
        'a\n::: {.only-for="blue-team"}\nfix it\n:::\nb\n::: {.only-for="exec"}\nsummary\n:::\n', "exec")
    assert "fix it" not in md and "summary" in md



def test_ai_log_renders(project):
    r = dokdok("log", "--tool", "Claude Code", "Drafted the introduction", "--outcome", "reviewed", cwd=project)
    assert r.returncode == 0, r.stderr
    from dokdok import project as prj, render
    md = render.assemble(prj.load(project))
    assert "# AI usage log" in md and "| Claude Code | Drafted the introduction | reviewed |" in md


@pytest.mark.skipif(not __import__("dokdok.render", fromlist=["_soffice"])._soffice(), reason="LibreOffice not installed")
def test_render_pdf_has_toc(project):
    r = dokdok("render", "--pdf", cwd=project)
    assert r.returncode == 0, r.stderr
    pdf = project / "out" / "thesis.pdf"
    assert pdf.exists() and pdf.stat().st_size > 10_000
    if shutil.which("pdftotext"):
        txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, encoding="utf-8").stdout
        assert "Table of Contents" in txt and "1.1 Topic" in txt   # TOC entries were generated
