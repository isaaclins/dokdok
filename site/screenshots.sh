#!/bin/sh
# Regenerates site/img/*.png from the example project. Uses QuickLook (macOS) to
# rasterise HTML and docx, so it works headless. Run from the repo root.
set -e
OUT=site/img; TMP=$(mktemp -d); mkdir -p "$OUT"

# 1. the check — on a copy of the example with two deliberate mistakes, so red shows
cp -r examples/thesis "$TMP/thesis"
printf '\n![](img/knie.svg)\n\nDie Straße war naß [@fehlt].\n' >> "$TMP/thesis/doc/02-hauptteil.md"
CHECK=$(cd "$TMP/thesis" && dokdok check || true)
python3 - "$CHECK" "$TMP/check.html" <<'PY'
import html, sys
out = html.escape(sys.argv[1]).replace("✔", '<b class="ok">✔</b>').replace("✖", '<b class="err">✖</b>').replace("⚠", '<b class="warn">⚠</b>')
open(sys.argv[2], "w").write(f'''<html><head><meta charset="utf-8"><style>
body{{margin:0;background:#1d1f21;padding:28px 32px}} pre{{margin:0;font:15px/1.5 Menlo,monospace;color:#e6e6e6;white-space:pre-wrap}}
.ok{{color:#5fbf7a}} .err{{color:#ff6b6b}} .warn{{color:#e9c46a}} .p{{color:#8a8f98}}</style></head>
<body><pre><span class="p">$</span> dokdok check\n{out}</pre></body></html>''')
PY
qlmanage -t -s 1400 -o "$TMP" "$TMP/check.html" >/dev/null 2>&1 && mv "$TMP/check.html.png" "$OUT/check.png"

# 2. the document — first page of the rendered example
# real PDF rendering via LibreOffice when available, QuickLook's docx preview otherwise
if (cd examples/thesis && dokdok render --pdf >/dev/null 2>&1) && command -v pdftoppm >/dev/null; then
  pdftoppm -png -r 110 -f 1 -l 1 examples/thesis/out/thesis.pdf "$TMP/docx" && mv "$TMP"/docx-*.png "$OUT/docx.png"
else
  (cd examples/thesis && dokdok render >/dev/null)
  qlmanage -t -s 1400 -o "$TMP" examples/thesis/out/thesis.docx >/dev/null 2>&1 && mv "$TMP/thesis.docx.png" "$OUT/docx.png"
fi

# 3. the chat — an illustration of the conversation (not a recording)
cat > "$TMP/chat.html" <<'HTML'
<html><head><meta charset="utf-8"><style>
body{margin:0;background:#fbfaf7;padding:28px 32px;font:16px/1.5 -apple-system,Helvetica,sans-serif;color:#1a1a1a}
.u{margin:0 0 18px 80px;background:#e8efe9;border-radius:14px 14px 2px 14px;padding:12px 16px}
.a{margin:0 80px 18px 0;background:#fff;border:1px solid #e4e1da;border-radius:14px 14px 14px 2px;padding:12px 16px}
.f{display:inline-block;background:#f0eee8;border:1px solid #e4e1da;border-radius:6px;padding:2px 8px;font-size:14px;margin:4px 6px 0 0}
</style></head><body>
<div class="u">Ich muss meine Vertiefungsarbeit schreiben. Hier sind die Sachen von der Schule.<br>
<span class="f">Leitfaden_VA.pdf</span><span class="f">Vorlage_VA.docx</span><span class="f">Mein_Konzept.docx</span><span class="f">Interviewfragen.docx</span></div>
<div class="a">Ich habe den Leitfaden und die Vorlage gelesen und daraus den Dokumenttyp gebaut. Dein Projekt steht: 11 Kapitel in der richtigen Reihenfolge, Logo und Formatierung wie in der Schulvorlage.<br><br>
Aus deinem Konzept habe ich die Einleitung, die drei Fragestellungen und die Interviewfragen übernommen. Was nur du schreiben kannst, ist als <code>[Platzhalter]</code> markiert – zum Beispiel der Erfahrungsbericht und das Porträt deines Interviewpartners.<br><br>
Willst du die Word-Datei zuerst anschauen, oder sollen wir mit dem Interview weitermachen?</div>
<div class="u">Word anschauen</div>
<div class="a">Geöffnet: <code>out/VA_Jonas_Muster.docx</code>. Der Check ist grün bis auf 6 Platzhalter – die sind für dich.</div>
</body></html>
HTML
qlmanage -t -s 1400 -o "$TMP" "$TMP/chat.html" >/dev/null 2>&1 && mv "$TMP/chat.html.png" "$OUT/chat.png"
# trim the empty space QuickLook leaves below the content
uv run --quiet --with pillow python3 - "$OUT"/check.png "$OUT"/chat.png "$OUT"/docx.png <<'PY'
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
