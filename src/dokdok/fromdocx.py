"""`dokdok types from-docx`: turn a Word file the user likes into a doctype.

Keeps styles, numbering, headers/footers, page setup (→ reference.docx with an empty body).
Turns the heading outline into sections/subsections and placeholder-looking text into hints.
Reports what could not be captured (text boxes, floating drawings, tables in the body).
"""
from dataclasses import dataclass, field
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

import yaml

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
def q(tag): return f"{{{W}}}{tag}"


@dataclass
class Outline:
    sections: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _heading_levels(styles_xml: bytes) -> dict[str, int]:
    """styleId → heading level, via the locale-independent w:name ('heading 1', 'Überschrift 1' → also 1)."""
    levels = {}
    root = ET.fromstring(styles_xml)
    for st in root.findall("w:style", NS):
        name = st.find("w:name", NS)
        sid = st.get(q("styleId"))
        if name is None or not sid:
            continue
        m = re.match(r"(?:heading|überschrift|titre|título)\s*(\d)", name.get(q("val"), ""), re.I)
        if m:
            levels[sid] = int(m.group(1))
    return levels


def _para_text(p) -> str:
    return "".join(t.text or "" for t in p.iter(q("t")))


def _looks_like_hint(p, text: str) -> bool:
    if re.fullmatch(r"\s*[\[\(«].*[\]\)»]\s*", text, re.S):
        return True
    rpr = p.find("w:pPr/w:rPr", NS)
    runs = p.findall("w:r", NS)
    if runs and all(r.find("w:rPr/w:i", NS) is not None for r in runs):
        return True
    color = p.find(".//w:color", NS)
    if color is not None and color.get(q("val"), "").lower() in ("808080", "7f7f7f", "595959", "6e6e6e", "a6a6a6"):
        return True
    return False


def slug(s: str) -> str:
    s = re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", s)   # strip "1.2 "
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "section"


def outline(docx: Path) -> Outline:
    out = Outline()
    with zipfile.ZipFile(docx) as z:
        levels = _heading_levels(z.read("word/styles.xml"))
        body = ET.fromstring(z.read("word/document.xml")).find("w:body", NS)
    cur = None
    tables = len(body.findall("w:tbl", NS))
    if tables:
        out.notes.append(f"{tables} table(s) in the body were not carried over (add them to sections/*.md as pipe tables)")
    if body.find(".//w:txbxContent", NS) is not None:
        out.notes.append("text boxes found — kept only if they sit in the header/footer; body ones need cover.docx")
    if body.find(".//w:drawing", NS) is not None:
        out.notes.append("images in the body were dropped (header/footer images are kept)")
    for p in body.findall("w:p", NS):
        text = _para_text(p).strip()
        st = p.find("w:pPr/w:pStyle", NS)
        lvl = levels.get(st.get(q("val")) if st is not None else "", 0)
        if lvl == 1 and text:
            cur = {"id": slug(text), "title": re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", text), "required": True,
                   "subsections": [], "hints": []}
            out.sections.append(cur)
        elif lvl == 2 and text and cur is not None:
            cur["subsections"].append(re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", text))
        elif text and cur is not None and _looks_like_hint(p, text):
            cur["hints"].append(text)
    return out


def hollow(src: Path, dst: Path) -> None:
    """Copy the docx, replacing the body with just its final sectPr (page setup + header/footer refs).
    Done as byte surgery so namespace prefixes and everything else stay exactly as Word wrote them."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                head, _, rest = data.partition(b"<w:body>")
                sect = re.findall(rb"<w:sectPr\b(?:(?!<w:sectPr\b).)*?</w:sectPr>", rest, re.S)
                last_sect = sect[-1] if sect else b""
                data = head + b"<w:body><w:p/>" + last_sect + b"</w:body></w:document>"
            zout.writestr(item, data)


def create(docx: Path, dest: Path, name: str | None = None, lang: str = "de-CH") -> tuple[Path, Outline]:
    name = name or slug(docx.stem)
    dest = dest / name
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    (dest / "sections").mkdir(parents=True)
    hollow(docx, dest / "reference.docx")
    ol = outline(docx)
    sections = []
    for s in ol.sections:
        d = {"id": s["id"], "title": s["title"], "required": True}
        if s["subsections"]:
            d["subsections"] = s["subsections"]
        if s["hints"]:
            d["hint"] = "\n".join(s["hints"])
        sections.append(d)
    if not any(s["id"] in ("quellen", "quellenverzeichnis", "sources", "references", "literatur") for s in sections):
        sections.append({"id": "quellen", "title": "Quellenverzeichnis", "generated": "sources"})
    doc = {"name": name, "title": f"{docx.stem} (from-docx)", "lang": lang,
           "spelling": {"no_eszett": lang.startswith("de")},
           "sections": sections,
           "checks": ["every_citation_resolves", "every_source_cited", "every_figure_has_caption",
                      "no_placeholders_in_final"],
           "targets": {"default": {"format": "docx"}}}
    (dest / "doctype.yaml").write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100))
    (dest / "AGENTS.md").write_text(
        f"# {docx.stem}\n\nDoctype generated from `{docx.name}`. Fill in the writing rules:\n\n"
        "- language, tone, citation format\n- what must never be invented\n- what \"done\" means for this document\n")
    return dest, ol
