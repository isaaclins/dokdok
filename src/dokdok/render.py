"""Assemble the sections into one markdown document and hand it to pandoc."""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

from . import ailog
from .project import Project


TOC_FIELD = ('```{{=openxml}}\n<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr><w:r><w:t>{title}</w:t></w:r></w:p>'
             '<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
             '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>{title}</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>\n```\n\n')
PAGE_BREAK = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'


def _hint_block(p: Project, text: str) -> str:
    body = " ".join(line.strip() for line in text.strip().splitlines())
    return f'::: {{custom-style="Hint"}}\n*{p.doctype.hint_label}:* {body}\n:::\n\n'


def assemble(p: Project, target: str = "default", final: bool = False) -> str:
    tcfg = {**p.doctype.targets.get(target, {}), **p.config.get("targets", {}).get(target, {})}
    audience = tcfg.get("audience")
    fmt = tcfg.get("format", "docx")
    show_hints = p.doctype.hints == "visible" and not final
    breaks = p.doctype.page_breaks and fmt == "docx"
    meta = {k: v for k, v in p.config.items() if k not in ("doctype", "targets", "derive")}
    meta.setdefault("lang", p.doctype.lang)
    meta.setdefault("toc-title", p.doctype.toc_title)
    parts = []
    title_tpl = (p.doctype.path / p.doctype.title_page) if p.doctype.title_page else None
    if title_tpl and title_tpl.exists():
        # own title page from the doctype's template; keep pandoc from adding its title block
        import re
        vals = {k: str(v) for k, v in meta.items() if isinstance(v, (str, int))}
        tpl = re.sub(r"\{(\w+)\}", lambda m: vals.get(m.group(1), f"[{m.group(1)}]"), title_tpl.read_text(encoding="utf-8"))
        parts.append(tpl.rstrip() + "\n\n")
        if breaks: parts.append(PAGE_BREAK)
        meta = {k: v for k, v in meta.items() if k not in ("title", "subtitle", "author", "date")}
    if fmt == "docx":
        parts.append(TOC_FIELD.format(title=p.doctype.toc_title))
        if breaks: parts.append(PAGE_BREAK)
    front = "---\n" + "".join(f"{k}: {v!r}\n" for k, v in meta.items() if isinstance(v, (str, int))) + "---\n\n"
    parts.insert(0, front)
    for spec in p.doctype.sections:
        if spec.only_for and audience not in spec.only_for:
            continue
        if breaks and len(parts) > 1 and parts[-1] != PAGE_BREAK:
            parts.append(PAGE_BREAK)
        if spec.generated == "sources":
            parts.append(f"# {spec.title}\n\n::: {{#refs}}\n:::\n\n")
            continue
        if spec.generated == "ai-log":
            parts.append(f"# {spec.title}\n\n{ailog.table(p.root, p.doctype.lang)}\n")
            continue
        if spec.generated == "glossary":
            rows = [f"| {g['term']} | {g['definition']} |" for g in sorted(p.glossary(), key=lambda g: g["term"].lower())]
            parts.append(f"# {spec.title}\n\n| | |\n|---|---|\n" + "\n".join(rows) + "\n\n")
            continue
        if spec.generated in ("figures", "tables"):
            parts.append(f"# {spec.title}\n\n" + _caption_list(p, spec.generated, audience) + "\n\n")
            continue
        sf = p.section(spec.id)
        if sf is None:
            continue
        hint = _hint_block(p, "\n".join(sf.hints())) if show_hints and sf.hints() else ""
        if spec.repeat:
            parts.append(f"# {spec.title}\n\n{hint}")
            for e in sf.entries:
                head = spec.entry_title.format(title=e.meta.get("title", e.path.stem), date=e.meta.get("date", e.path.stem))
                parts.append(f"## {head}\n\n{_shift(e.text.strip())}\n\n")
            continue
        parts.append(f"# {spec.title}\n\n{hint}{sf.text.strip()}\n\n")
    md = "".join(parts)
    if audience:
        md = _filter_audience(md, audience)
    return md


LABELS = {"de": ("Abbildung", "Tabelle"), "en": ("Figure", "Table"), "fr": ("Figure", "Tableau"), "it": ("Figura", "Tabella")}


def _caption_list(p: Project, kind: str, audience) -> str:
    """Numbered list of figure or table captions in document order (no page numbers)."""
    import re
    pat = re.compile(r"!\[(.+?)\]\(") if kind == "figures" else re.compile(r"^Table:\s*(.+)$", re.M)
    label = LABELS.get(p.doctype.lang[:2], LABELS["en"])[0 if kind == "figures" else 1]
    caps = []
    for spec in p.doctype.sections:
        if spec.generated or (spec.only_for and audience not in spec.only_for):
            continue
        sf = p.section(spec.id)
        if sf is None:
            continue
        for src in (sf.entries or [sf]):
            text = _filter_audience(src.text, audience) if audience else src.text
            caps += pat.findall(text)
    return "\n".join(f"{label} {i}: {c}  " for i, c in enumerate(caps, 1)) or "–"


def _shift(md: str) -> str:
    """Demote headings one level (entries sit under their own ##)."""
    import re
    return re.sub(r"^(#{1,5}) ", r"#\1 ", md, flags=re.M)


def _filter_audience(md: str, audience: str) -> str:
    """Drop `::: {.only-for="x"}` … `:::` blocks whose audience doesn't match."""
    import re
    def keep(m):
        return m.group(2) if audience in m.group(1).split(",") else ""
    return re.sub(r':::\s*\{\.only-for="([^"]+)"\}\n(.*?)\n:::\n?', keep, md, flags=re.S)


def render(p: Project, target: str = "default", pdf: bool = False, final: bool = False) -> list[Path]:
    if not shutil.which("pandoc"):
        raise SystemExit("pandoc not found — run `dokdok doctor`")
    tcfg = {**p.doctype.targets.get(target, {}), **p.config.get("targets", {}).get(target, {})}
    fmt = tcfg.get("format", "docx")
    out_dir = p.root / "out"; out_dir.mkdir(exist_ok=True)
    name = p.config.get("filename") or f"{p.root.name}{'' if target == 'default' else '-' + target}"
    out = out_dir / f"{name}.{fmt}"
    md = assemble(p, target, final=final)
    (out_dir / f"{name}.md").write_text(md, encoding="utf-8")   # kept for debugging
    cmd = ["pandoc", "-f", "markdown", "-o", str(out), "--resource-path", str(p.root)]
    if fmt != "docx":
        cmd.append("--toc")           # docx gets its own TOC field after the title page
    if p.doctype.number_sections:
        cmd.append("--number-sections")
    if fmt in ("html", "html5"):
        cmd += ["--standalone", "--embed-resources"]
    if p.sources_path.exists():
        cmd += ["--citeproc", "--bibliography", str(p.sources_path)]
    if fmt == "docx":
        cmd += ["--reference-doc", str(_reference_with_hint_style(p, out_dir))]
    for lua in sorted((p.doctype.path / "filters").glob("*.lua")):
        cmd += ["--lua-filter", str(lua)]
    subprocess.run(cmd, input=md, text=True, encoding="utf-8", check=True)
    if fmt == "docx":
        sanitize_docx(out)
    outs = [out]
    if pdf and fmt == "docx":
        outs.append(docx_to_pdf(out))
    return outs


def _pandoc_default_reference(out_dir: Path) -> Path:
    f = out_dir / ".pandoc-reference.docx"
    if not f.exists():
        f.write_bytes(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout)
    return f


def _reference_with_hint_style(p: Project, out_dir: Path) -> Path:
    """The doctype's reference.docx made safe for pandoc:
    - every style pandoc's docx writer uses (Compact, Table, First Paragraph, captions, …) that the
      reference lacks is merged in from pandoc's default reference — a template hollowed from a
      school's Word file rarely has them, and without them tables and captions render garbled;
    - a grey, shaded «Hint» paragraph style is added if missing, for visible hints."""
    import re
    import zipfile
    default = _pandoc_default_reference(out_dir)
    src = p.doctype.reference_docx or default
    with zipfile.ZipFile(default) as z:
        default_styles = z.read("word/styles.xml")
    dst = out_dir / ".reference.docx"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.endswith("/"):
                continue
            data = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                have = set(re.findall(rb'w:styleId="([^"]+)"', data))
                missing = [m.group(0) for m in re.finditer(rb"<w:style\b[^>]*>.*?</w:style>", default_styles, re.S)
                           if re.search(rb'w:styleId="([^"]+)"', m.group(0)).group(1) not in have]
                extra = b"".join(missing)
                if b'w:styleId="Hint"' not in have:
                    extra += (b'<w:style w:type="paragraph" w:customStyle="1" w:styleId="Hint"><w:name w:val="Hint"/>'
                              b'<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
                              b'<w:spacing w:before="120" w:after="120"/><w:ind w:left="170" w:right="170"/></w:pPr>'
                              b'<w:rPr><w:i/><w:color w:val="595959"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>')
                data = data.replace(b"</w:styles>", extra + b"</w:styles>")
            zout.writestr(item, data)
    return dst


def sanitize_docx(path: Path) -> None:
    """Drop zip directory entries and their content-type Overrides. A reference.docx re-zipped by
    hand (`zip -r`) carries `word/media/` as an entry; pandoc copies it and Word then refuses the
    file with "unreadable content"."""
    import re
    import zipfile
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        if not any(i.filename.endswith("/") for i in items):
            return
        parts = [(i, z.read(i.filename)) for i in items if not i.filename.endswith("/")]
    tmp = path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in parts:
            if info.filename == "[Content_Types].xml":
                data = re.sub(rb'<Override PartName="/[^"]*/"[^>]*/>\s*', b"", data)
            out.writestr(info, data)
    tmp.replace(path)


LO_PROFILE = Path(tempfile.gettempdir()) / "dokdok-lo"


def _soffice() -> str | None:
    candidates = [Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")]
    for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if pf:
            candidates.append(Path(pf) / "LibreOffice" / "program" / "soffice.exe")
    return shutil.which("soffice") or next((str(c) for c in candidates if c.exists()), None)


def docx_to_pdf(docx: Path) -> Path:
    """LibreOffice headless first (works unattended, in CI, on Linux); Word on macOS as a fallback.
    A script run inside LibreOffice updates the TOC and fields before export — plain
    `--convert-to pdf` would leave pandoc's TOC field empty."""
    pdf = docx.with_suffix(".pdf")
    soffice = _soffice()
    if soffice:
        scripts = LO_PROFILE / "user" / "Scripts" / "python"
        scripts.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(__file__).with_name("lo_export.py"), scripts / "dokdok.py")
        cmd = [soffice, f"-env:UserInstallation={LO_PROFILE.as_uri()}", "--headless", "--norestore",
               "vnd.sun.star.script:dokdok.py$export_pdf?language=Python&location=user"]
        # LibreOffice embeds a Python interpreter that resolves `python3` via PATH; a venv's bin
        # dir there (or PYTHON*/VIRTUAL_ENV vars) makes it fail to initialise and soffice aborts.
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "VIRTUAL_ENV", "UV_"))}
        env["PATH"] = os.pathsep.join(d for d in env.get("PATH", "").split(os.pathsep)
                                      if not (Path(d).parent / "pyvenv.cfg").exists())
        env.update(DOKDOK_IN=str(docx), DOKDOK_OUT=str(pdf))
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
        except subprocess.TimeoutExpired:
            raise SystemExit("LibreOffice hung. On macOS, open LibreOffice once by hand after installing "
                             "(Gatekeeper first-launch dialog), then retry.")
        if not pdf.exists():
            log = pdf.with_suffix(".pdf.log")
            detail = log.read_text(encoding="utf-8") if log.exists() else (r.stderr or r.stdout)
            raise SystemExit("LibreOffice did not produce a PDF. On Debian/Ubuntu install "
                             "libreoffice-script-provider-python.\n" + detail.strip())
        pdf.with_suffix(".pdf.log").unlink(missing_ok=True)
        return pdf
    if platform.system() == "Darwin" and Path("/Applications/Microsoft Word.app").exists():
        script = f'''
        with timeout of 90 seconds
        tell application "Microsoft Word"
            set d to open file name "{docx}"
            try
                update table of contents 1 of d
            end try
            repeat with i from 1 to (count of fields of d)
                update field field i of d
            end repeat
            save d
            save as d file name "{pdf}" file format format PDF
            close d saving no
        end tell
        end timeout'''
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=120)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            raise SystemExit("Word could not export the PDF (is the screen locked?). "
                             "Install LibreOffice for unattended PDF: brew install --cask libreoffice") from e
        return pdf
    raise SystemExit("no PDF converter: install LibreOffice (brew install --cask libreoffice)")
