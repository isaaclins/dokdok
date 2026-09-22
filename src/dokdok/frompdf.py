"""`dokdok types from-pdf`: a doctype whose look is taken from a PDF (when there is no Word file).

What a PDF can give us, via poppler: the logo (first embedded image on page 1), the running header
and footer lines (first/last text line of page 2), a font family guess, the page size. From that we
build a reference.docx: pandoc's default with the font patched, headings in the logo's dominant
colour, the logo in the header, a footer line with page numbers. Structure never comes from the
PDF — it's style only."""
from dataclasses import dataclass, field
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

import yaml

KNOWN_FONTS = ["Arial", "Helvetica", "Calibri", "Verdana", "Georgia", "Times New Roman", "Cambria",
               "Garamond", "Segoe UI", "Tahoma", "Trebuchet", "Roboto", "Open Sans", "Source Sans"]

HEADER_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
{logo}<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="{color}"/></w:pBdr></w:pPr><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r></w:p>
</w:hdr>'''
LOGO_P = '''<w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="901" name="logo"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="logo.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdLogo"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
'''
FOOTER_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="6" w:space="1" w:color="{color}"/></w:pBdr><w:tabs><w:tab w:val="right" w:pos="9000"/></w:tabs></w:pPr><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:tab/></w:r><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
</w:ftr>'''
HEADER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.png"/></Relationships>'''


@dataclass
class Look:
    logo: Path | None = None
    logo_size: tuple[int, int] = (0, 0)
    header: str = ""
    footer: str = ""
    font: str | None = None
    color: str = "000000"
    pages: int = 0
    notes: list[str] = field(default_factory=list)


def _run(*cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def analyse(pdf: Path, work: Path) -> Look:
    look = Look()
    if not shutil.which("pdfimages"):
        raise SystemExit("poppler is required for from-pdf (brew install poppler / apt install poppler-utils)")
    look.pages = int(re.search(r"Pages:\s+(\d+)", _run("pdfinfo", str(pdf))).group(1) or 0)
    # logo: first raster image on page 1 that is wider than tall (a banner/logo, not a photo)
    listing = _run("pdfimages", "-list", "-f", "1", "-l", "1", str(pdf)).splitlines()[2:]
    imgs = [l.split() for l in listing if l.split() and l.split()[2] == "image"]
    if imgs:
        num, w, h = int(imgs[0][1]), int(imgs[0][3]), int(imgs[0][4])
        _run("pdfimages", "-png", "-f", "1", "-l", "1", str(pdf), str(work / "img"))
        cand = sorted(work.glob("img-*.png"))
        if cand:
            look.logo = _with_alpha(cand, listing); look.logo_size = (w, h)
            look.color = _dominant_colour(look.logo) or look.color
    else:
        look.notes.append("no embedded image on page 1 — no logo; header will be text only")
    # header/footer: first and last text line of page 2 (page 1 is usually a title page)
    page = 2 if look.pages >= 2 else 1
    lines = [l.strip() for l in _run("pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-").splitlines() if l.strip()]
    if len(lines) >= 2:
        look.header = lines[0]
        foot = re.sub(r"\s{2,}(Seite|Page|S\.|p\.)?\s*\d+\s*(von|of|/)?\s*\d*\s*$", "", lines[-1]).strip()
        look.footer = foot
    # the running lines name the *other* person; keep the organisation part, tokenise the rest
    org = re.split(r"\s*[·|•–-]\s*", look.footer)[0].strip() if look.footer else ""
    look.notes.append(f"header in PDF: «{look.header}» / footer: «{look.footer}» — replaced by {{title}} · {{author}} tokens (set header:/footer: in dokdok.yaml to change)")
    look.header = "{title} · {author}"
    look.footer = (org + " · " if org else "") + "{author}"
    # font: first known family among the PDF's fonts
    fonts = _run("pdffonts", str(pdf))
    for fam in KNOWN_FONTS:
        if re.search(fam.replace(" ", r"\s*"), fonts, re.I):
            look.font = fam; break
    if not look.font:
        look.notes.append("font family not recognised from the PDF — keeping pandoc's default; set it in the reference.docx if it matters")
    return look


def _with_alpha(files: list[Path], listing: list[str]) -> Path:
    """PDFs keep transparency as a separate soft mask (smask) right after the image; merge it back."""
    rows = [l.split() for l in listing if l.split()]
    if len(files) >= 2 and len(rows) >= 2 and rows[1][2] == "smask":
        try:
            from PIL import Image
            im = Image.open(files[0]).convert("RGBA"); mask = Image.open(files[1]).convert("L").resize(im.size)
            im.putalpha(mask); out = files[0].with_name("logo.png"); im.save(out); return out
        except Exception:
            pass
    return files[0]


def _dominant_colour(png: Path) -> str | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(png).convert("RGB").resize((64, 64))
    counts: dict[tuple, int] = {}
    for px in im.getdata():
        if max(px) - min(px) < 40 or sum(px) > 690 or sum(px) < 60:   # skip greys, white, black
            continue
        counts[px] = counts.get(px, 0) + 1
    if not counts:
        return None
    r, g, b = max(counts, key=counts.get)
    return f"{r:02X}{g:02X}{b:02X}"


def build_reference(look: Look, out: Path) -> None:
    base = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout
    tmp = out.with_suffix(".base.docx"); tmp.write_bytes(base)
    with zipfile.ZipFile(tmp) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                if look.font:
                    f = look.font.encode()
                    data = re.sub(rb"<w:rFonts\b[^>]*/>", b'<w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s" w:eastAsia="%s"/>' % ((f,) * 4), data, flags=re.S)
                data = re.sub(rb'<w:color w:val="[0-9A-F]{6}"\s+w:themeColor="accent1"[^>]*/>', b'<w:color w:val="%s"/>' % look.color.encode(), data, flags=re.S)
            elif item.filename == "word/document.xml":
                data = re.sub(rb"(<w:sectPr\b[^>]*>)", rb'\1<w:headerReference w:type="default" r:id="rIdHdr"/><w:footerReference w:type="default" r:id="rIdFtr"/>', data, count=1)
            elif item.filename == "word/_rels/document.xml.rels":
                data = data.replace(b"</Relationships>", b'<Relationship Id="rIdHdr" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/><Relationship Id="rIdFtr" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>')
            elif item.filename == "[Content_Types].xml":
                extra = b'<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                if b'Extension="png"' not in data:
                    extra += b'<Default Extension="png" ContentType="image/png"/>'
                data = data.replace(b"</Types>", extra + b"</Types>")
            zout.writestr(item, data)
        logo_xml = ""
        if look.logo:
            w, h = look.logo_size or (720, 160)
            cx = 2520000; cy = int(cx * h / max(w, 1))
            logo_xml = LOGO_P.format(cx=cx, cy=cy)
            zout.writestr("word/media/logo.png", look.logo.read_bytes())
            zout.writestr("word/_rels/header1.xml.rels", HEADER_RELS)
        zout.writestr("word/header1.xml", HEADER_XML.format(logo=logo_xml, color=look.color, text=_xml(look.header)))
        zout.writestr("word/footer1.xml", FOOTER_XML.format(color=look.color, text=_xml(look.footer)))
    tmp.unlink()


def _xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def create(pdf: Path, dest: Path, name: str, lang: str = "de-CH") -> tuple[Path, Look]:
    dest = dest / name
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    dest.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as td:
        look = analyse(pdf, Path(td))
        build_reference(look, dest / "reference.docx")
    doc = {"name": name, "title": f"{pdf.stem} (from-pdf, style only)", "lang": lang,
           "spelling": {"no_eszett": lang.startswith("de")},
           "sections": [{"id": "sources", "title": "Quellenverzeichnis" if lang.startswith("de") else "References", "generated": "sources"}],
           "checks": ["every_citation_resolves", "every_source_cited", "every_figure_has_caption", "no_placeholders_in_final"],
           "targets": {"default": {"format": "docx"}}}
    (dest / "doctype.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    (dest / "AGENTS.md").write_text(f"# {pdf.stem}\n\nDoctype generated from `{pdf.name}` (look only). Fill in the writing rules and the sections from the guideline.\n", encoding="utf-8")
    return dest, look
