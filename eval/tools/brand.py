"""Make a fictional organisation's Word look: a logo PNG and a styled docx from markdown with the
logo in the header and a footer line. Used to build eval material that has a *distinct* look per
world, so leakage of one world's style/content into another is unambiguous.

    python eval/tools/brand.py build <brand.json> <in.md> <out.docx>
brand.json: {"name": "...", "tagline": "...", "color": "1F4E79", "font": "Calibri",
             "footer": "Nordlicht Logistik AG · IPA 2026", "logo_text": "NL"}
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def logo(brand: dict, path: Path) -> None:
    color = tuple(int(brand["color"][i:i + 2], 16) for i in (0, 2, 4))
    im = Image.new("RGBA", (720, 160), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 160, 160), 28, fill=color)
    try:
        big = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 88)
        small = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 40)
        tiny = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 26)
    except OSError:
        big = small = tiny = ImageFont.load_default()
    d.text((80, 80), brand["logo_text"], fill="white", font=big, anchor="mm")
    d.text((185, 55), brand["name"], fill=color, font=small, anchor="lm")
    d.text((185, 108), brand["tagline"], fill=(90, 90, 90), font=tiny, anchor="lm")
    im.save(path)


HEADER_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
<w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="3240000" cy="720000"/><wp:docPr id="901" name="logo"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="logo.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdLogo"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="3240000" cy="720000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="{color}"/></w:pBdr><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">{header_text}</w:t></w:r></w:p>
</w:hdr>'''
FOOTER_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="6" w:space="1" w:color="{color}"/></w:pBdr><w:tabs><w:tab w:val="right" w:pos="9000"/></w:tabs><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr></w:pPr>
<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">{footer}</w:t></w:r><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:tab/><w:t xml:space="preserve">Seite </w:t></w:r>
<w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:color w:val="7F7F7F"/><w:sz w:val="16"/></w:rPr><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
</w:ftr>'''
HEADER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.png"/></Relationships>'''


def styled_docx(brand: dict, md: Path, out: Path, logo_png: Path) -> None:
    """pandoc → docx, then: fonts/colours in styles.xml, header with logo, footer with page numbers."""
    subprocess.run(["pandoc", "-f", "markdown", "-o", str(out), "--toc", "--number-sections", str(md)], check=True)
    color = brand["color"].encode(); font = brand["font"].encode()
    tmp = out.with_suffix(".tmp")
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                data = re.sub(rb"<w:rFonts\b[^>]*/>", b'<w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s" w:eastAsia="%s"/>' % ((font,) * 4), data, flags=re.S)
                data = re.sub(rb'<w:color w:val="[0-9A-F]{6}"\s+w:themeColor="accent1"[^>]*/>', b'<w:color w:val="%s"/>' % color, data, flags=re.S)
            elif item.filename == "word/document.xml":
                data = data.replace(b"<w:sectPr>", b'<w:sectPr><w:headerReference w:type="default" r:id="rIdHdr"/><w:footerReference w:type="default" r:id="rIdFtr"/>', 1)
                if b"rIdHdr" not in data:   # sectPr with attributes
                    data = re.sub(rb"(<w:sectPr\b[^>]*>)", rb'\1<w:headerReference w:type="default" r:id="rIdHdr"/><w:footerReference w:type="default" r:id="rIdFtr"/>', data, count=1)
            elif item.filename == "word/_rels/document.xml.rels":
                data = data.replace(b"</Relationships>", b'<Relationship Id="rIdHdr" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/><Relationship Id="rIdFtr" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>')
            elif item.filename == "[Content_Types].xml":
                data = data.replace(b"</Types>", b'<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>' + (b"" if b'Extension="png"' in data else b'<Default Extension="png" ContentType="image/png"/>') + b"</Types>")
            zout.writestr(item, data)
        zout.writestr("word/header1.xml", HEADER_XML.format(color=brand["color"], header_text=brand.get("header", brand["name"])))
        zout.writestr("word/footer1.xml", FOOTER_XML.format(color=brand["color"], footer=brand["footer"]))
        zout.writestr("word/_rels/header1.xml.rels", HEADER_RELS)
        zout.writestr("word/media/logo.png", logo_png.read_bytes())
    tmp.replace(out)


def pdf(docx: Path) -> Path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from dokdok.render import docx_to_pdf
    return docx_to_pdf(docx)


if __name__ == "__main__":
    cmd, brand_file, src, dst = sys.argv[1:5]
    brand = json.loads(Path(brand_file).read_text(encoding="utf-8"))
    logo_png = Path(dst).with_name("logo.png")
    logo(brand, logo_png)
    if cmd == "build":
        styled_docx(brand, Path(src), Path(dst), logo_png)
        if "--pdf" in sys.argv:
            pdf(Path(dst))
        print("✔", dst)
