#!/bin/sh
# Regenerates site/img/*.png from the example project. Uses QuickLook (macOS) to
# rasterise HTML and docx, so it works headless. Run from the repo root.
set -e
OUT=site/img; TMP=$(mktemp -d); mkdir -p "$OUT"

# 1. the terminal recording: see record.sh (asciinema + agg)

# 2. the document — first page of the rendered example
# real PDF rendering via LibreOffice when available, QuickLook's docx preview otherwise
if (cd examples/thesis && dokdok render --pdf >/dev/null 2>&1) && command -v pdftoppm >/dev/null; then
  pdftoppm -png -r 110 -f 1 -l 1 examples/thesis/out/thesis.pdf "$TMP/docx" && mv "$TMP"/docx-*.png "$OUT/docx.png"
else
  (cd examples/thesis && dokdok render >/dev/null)
  qlmanage -t -s 1400 -o "$TMP" examples/thesis/out/thesis.docx >/dev/null 2>&1 && mv "$TMP/thesis.docx.png" "$OUT/docx.png"
fi

# 3. the conversation — what it looks like inside Claude Code in the terminal (illustration, not a recording)
cat > "$TMP/chat.html" <<'HTML'
<html><head><meta charset="utf-8"><style>
body{margin:0;background:#1d1f21;padding:26px 30px;font:15px/1.55 Menlo,monospace;color:#e6e6e6}
.p{color:#8a8f98} .u{color:#e6e6e6} .a{color:#c9d1d9;margin:14px 0 0} .d{color:#8a8f98}
</style></head><body>
<div><span class="p">&gt;</span> <span class="u">I have to write my thesis. The material from school and my concept are in material/.</span></div>
<div class="a">Read material/guideline.pdf, material/template.docx, material/concept.md.<br>
Found doctype <b>school-thesis</b> — it matches the guideline. Created <b>thesis/</b> with 5 sections.<br><br>
Filled in from your concept: the motivation, the three research questions and the methods.<br>
Left <b>[placeholders]</b> for what only you can write: the interview and your hive diary.<br><br>
<span class="d">$ dokdok check</span> → 0 errors, 2 warnings (word counts)<br>
<span class="d">$ dokdok render</span> → out/thesis.docx<br><br>
Want to look at the Word file first, or continue with the interview questions?</div>
<div style="margin-top:14px"><span class="p">&gt;</span> <span class="u">word first</span></div>
<div class="a">Opened out/thesis.docx. 6 placeholders left — those are yours.</div>
</body></html>
HTML
qlmanage -t -s 1400 -o "$TMP" "$TMP/chat.html" >/dev/null 2>&1 && mv "$TMP/chat.html.png" "$OUT/chat.png"
# trim the empty space QuickLook leaves below the content
uv run --quiet --with pillow python3 - "$OUT"/chat.png "$OUT"/docx.png <<'PY'
import sys
from PIL import Image, ImageChops
for f in sys.argv[1:]:
    im = Image.open(f).convert("RGB")
    bg = Image.new("RGB", im.size, im.getpixel((im.width - 2, im.height - 2)))
    box = ImageChops.difference(im, bg).getbbox()
    if box:
        pad = 24
        im.crop((0, 0, im.width, min(im.height, box[3] + pad))).save(f)
PY
rm -rf "$TMP"; ls -la "$OUT"
