"""Header/footer text: tokens substituted, overrides replace the original author's running lines."""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")


def run(*a, cwd):
    return subprocess.run([sys.executable, "-m", "dokdok.cli", *a], cwd=cwd, text=True, encoding="utf-8", capture_output=True)


def running_text(docx: Path) -> str:
    import re
    with zipfile.ZipFile(docx) as z:
        return " ".join(re.sub(r"<[^>]+>", " ", z.read(n).decode()) for n in z.namelist() if re.match(r"word/(header|footer)\d*\.xml$", n))


def test_from_pdf_and_header_override(tmp_path):
    # a styled reference docx (with someone else's running header) → its PDF → from-pdf
    sys.path.insert(0, str(REPO / "eval" / "tools")); import brand as B
    b = {"name": "Schule Example", "tagline": "Abteilung X", "color": "5B3A8C", "font": "Verdana", "footer": "Schule Example · Bericht · J. Other", "logo_text": "SE", "header": "Bericht · Thema von Jonas Other · Jonas Other"}
    md = tmp_path / "ref.md"; md.write_text("# Kapitel\n\nText.\n\n# Zweites\n\nMehr.\n", encoding="utf-8")
    logo = tmp_path / "logo.png"; B.logo(b, logo); ref = tmp_path / "ref.docx"; B.styled_docx(b, md, ref, logo)
    if not (shutil.which("soffice") or Path("/Applications/LibreOffice.app").exists()):
        pytest.skip("LibreOffice needed to make the PDF")
    from dokdok.render import docx_to_pdf
    pdf = docx_to_pdf(ref)
    r = run("types", "from-pdf", str(pdf), "--dest", str(tmp_path / "types"), "--name", "se", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "logo: extracted" in r.stdout and "{title}" in r.stdout
    assert run("new", "p", "--type", str(tmp_path / "types" / "se"), "--title", "Mein Bericht", "--author", "Lia Brunner", cwd=tmp_path).returncode == 0
    (tmp_path / "p" / "doc" / "00-x.md").write_text("---\nsection: x\n---\n\n## A\n\nText.\n", encoding="utf-8")
    assert run("render", cwd=tmp_path / "p").returncode == 0
    t = running_text(tmp_path / "p" / "out" / "p.docx")
    assert "Lia Brunner" in t and "Mein Bericht" in t and "Jonas" not in t
    # from-docx keeps the original's running lines; an override in dokdok.yaml replaces them
    assert run("types", "from-docx", str(ref), "--dest", str(tmp_path / "types"), "--name", "sd", "--style-only", cwd=tmp_path).returncode == 0
    assert "Jonas Other" in run("types", "lint", str(tmp_path / "types" / "sd"), cwd=tmp_path).stdout
    assert run("new", "q", "--type", str(tmp_path / "types" / "sd"), "--title", "Mein Bericht", "--author", "Lia Brunner", cwd=tmp_path).returncode == 0
    (tmp_path / "q" / "dokdok.yaml").write_text((tmp_path / "q" / "dokdok.yaml").read_text() + "header: '{title} · {author}'\nfooter: 'Schule Example · {author}'\n", encoding="utf-8")
    (tmp_path / "q" / "doc" / "00-x.md").write_text("---\nsection: x\n---\n\n## A\n\nText.\n", encoding="utf-8")
    assert run("render", cwd=tmp_path / "q").returncode == 0
    t = running_text(tmp_path / "q" / "out" / "q.docx")
    assert "Lia Brunner" in t and "Jonas" not in t and "Schule Example" in t
