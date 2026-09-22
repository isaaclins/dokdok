#!/usr/bin/env python3
"""Patch reference.docx (extracted style-only from Lia's VA) so dokdok's hint
boxes use the school's own «VAHinweis» look (grey italic, indented) instead
of the generic default. Adds a paragraph style "Hint" cloned from VAHinweis
with a light shading fill added, since dokdok looks for styleId="Hint".
Rerun after re-extracting reference.docx from a new source file.
    python3 doctypes/sfgz-va/make-reference.py
"""
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
REF = HERE / "reference.docx"

HINT_STYLE = (
    b'<w:style w:type="paragraph" w:customStyle="1" w:styleId="Hint">'
    b'<w:name w:val="Hint"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
    b'<w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
    b'<w:spacing w:before="120" w:after="120" w:line="264" w:lineRule="auto"/>'
    b'<w:ind w:left="170" w:right="170"/></w:pPr>'
    b'<w:rPr><w:i/><w:color w:val="6E6E6E"/><w:sz w:val="20"/></w:rPr></w:style>'
)

HEADER_OLD = "Vertiefungsarbeit ABU  ·  Kreuzbandriss – Vorbeugung, Behandlung und Rehabilitation"
HEADER_NEW = "Vertiefungsarbeit ABU  ·  [Arbeitstitel einfügen]"
FOOTER_OLD = "Lia Eberhardt  |  ML24A  |  Schule für Gestaltung Zürich"
FOOTER_NEW = "Kaya [Nachname]  |  [Klasse]  |  Schule für Gestaltung Zürich"

tmp = HERE / "_patched.docx"
with zipfile.ZipFile(REF) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename.endswith("/"):
            continue
        data = zin.read(item.filename)
        if item.filename == "word/styles.xml" and b'w:styleId="Hint"' not in data:
            data = data.replace(b"</w:styles>", HINT_STYLE + b"</w:styles>")
        if item.filename == "word/header1.xml":
            data = data.replace(HEADER_OLD.encode(), HEADER_NEW.encode())
        if item.filename == "word/footer1.xml":
            data = data.replace(FOOTER_OLD.encode(), FOOTER_NEW.encode())
        zout.writestr(item, data)
tmp.replace(REF)
print("✔ reference.docx patched with Hint style + placeholder header/footer")
