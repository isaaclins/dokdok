#!/usr/bin/env python3
"""Build reference.docx for this doctype from pandoc's default, patched to a plain school look:
Arial everywhere, black headings, hints grey. Rerun after changing anything here.
    python3 doctypes/school-thesis/make-reference.py
"""
import re
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
base = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout
tmp = HERE / "_base.docx"; tmp.write_bytes(base)

def patch_styles(xml: bytes) -> bytes:
    arial = b'<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial" w:eastAsia="Arial"/>'
    xml = re.sub(rb"<w:rFonts\b[^>]*/>", arial, xml, flags=re.S)                  # every font → Arial
    xml = re.sub(rb'<w:color w:val="[0-9A-F]{6}"\s+w:themeColor="accent1"[^>]*/>', b'<w:color w:val="000000"/>', xml, flags=re.S)  # headings → black
    return xml


with zipfile.ZipFile(tmp) as zin, zipfile.ZipFile(HERE / "reference.docx", "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/styles.xml":
            data = patch_styles(data)
        zout.writestr(item, data)
tmp.unlink()
print("✔ reference.docx")
