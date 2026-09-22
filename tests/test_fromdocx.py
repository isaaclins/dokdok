"""from-docx on a docx we build with pandoc itself (no external fixtures)."""
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from dokdok import fromdocx

pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")


@pytest.fixture
def sample_docx(tmp_path):
    md = "# Einleitung\n\n## Ziel\n\n*[Hier das Ziel beschreiben]*\n\n# Hauptteil\n\nText.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
    out = tmp_path / "sample.docx"
    subprocess.run(["pandoc", "-f", "markdown", "-o", str(out)], input=md, text=True, encoding="utf-8", check=True)
    return out


def test_outline_and_hints(sample_docx):
    ol = fromdocx.outline(sample_docx)
    assert [s["id"] for s in ol.sections] == ["einleitung", "hauptteil"]
    assert ol.sections[0]["subsections"] == ["Ziel"]
    assert ol.sections[0]["hints"] == ["[Hier das Ziel beschreiben]"]
    assert any("table" in n for n in ol.notes)


def test_create_doctype_renders(sample_docx, tmp_path):
    dest, _ = fromdocx.create(sample_docx, tmp_path / "types", name="t")
    assert (dest / "reference.docx").exists() and (dest / "doctype.yaml").exists()
    with zipfile.ZipFile(sample_docx) as z:
        had_sect = b"<w:sectPr" in z.read("word/document.xml")   # older pandoc writes none
    with zipfile.ZipFile(dest / "reference.docx") as z:
        body = z.read("word/document.xml")
    assert b"Hier das Ziel" not in body
    assert (b"<w:sectPr" in body) == had_sect
    r = subprocess.run(["pandoc", "-f", "markdown", "-o", str(tmp_path / "x.docx"),
                        "--reference-doc", str(dest / "reference.docx")], input="# Hi\n\ntext", text=True, encoding="utf-8")
    assert r.returncode == 0
