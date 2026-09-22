"""Assemble the sections into one markdown document and hand it to pandoc."""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

from . import ailog
from .project import Project


def assemble(p: Project, target: str = "default") -> str:
    tcfg = {**p.doctype.targets.get(target, {}), **p.config.get("targets", {}).get(target, {})}
    audience = tcfg.get("audience")
    meta = {k: v for k, v in p.config.items() if k not in ("doctype", "targets")}
    meta.setdefault("lang", p.doctype.lang)
    meta.setdefault("toc-title", p.doctype.toc_title)
    front = "---\n" + "".join(f"{k}: {v!r}\n" for k, v in meta.items() if isinstance(v, (str, int))) + "---\n\n"
    parts = [front]
    for spec in p.doctype.sections:
        if spec.only_for and audience not in spec.only_for:
            continue
        if spec.generated == "sources":
            parts.append(f"# {spec.title}\n\n::: {{#refs}}\n:::\n\n")
            continue
        if spec.generated == "ai-log":
            parts.append(f"# {spec.title}\n\n{ailog.table(p.root, p.doctype.lang)}\n")
            continue
        sf = p.section(spec.id)
        if sf is None:
            continue
        parts.append(f"# {spec.title}\n\n{sf.text.strip()}\n\n")
    md = "".join(parts)
    if audience:
        md = _filter_audience(md, audience)
    return md


def _filter_audience(md: str, audience: str) -> str:
    """Drop `::: {.only-for="x"}` … `:::` blocks whose audience doesn't match."""
    import re
    def keep(m):
        return m.group(2) if audience in m.group(1).split(",") else ""
    return re.sub(r':::\s*\{\.only-for="([^"]+)"\}\n(.*?)\n:::\n?', keep, md, flags=re.S)


def render(p: Project, target: str = "default", pdf: bool = False) -> list[Path]:
    if not shutil.which("pandoc"):
        raise SystemExit("pandoc not found — run `dokdok doctor`")
    tcfg = {**p.doctype.targets.get(target, {}), **p.config.get("targets", {}).get(target, {})}
    fmt = tcfg.get("format", "docx")
    out_dir = p.root / "out"; out_dir.mkdir(exist_ok=True)
    name = p.config.get("filename") or f"{p.root.name}{'' if target == 'default' else '-' + target}"
    out = out_dir / f"{name}.{fmt}"
    md = assemble(p, target)
    (out_dir / f"{name}.md").write_text(md, encoding="utf-8")   # kept for debugging
    cmd = ["pandoc", "-f", "markdown", "-o", str(out), "--toc", "--resource-path", str(p.root)]
    if p.doctype.number_sections:
        cmd.append("--number-sections")
    if fmt in ("html", "html5"):
        cmd += ["--standalone", "--embed-resources"]
    if p.sources_path.exists():
        cmd += ["--citeproc", "--bibliography", str(p.sources_path)]
    if fmt == "docx" and p.doctype.reference_docx:
        cmd += ["--reference-doc", str(p.doctype.reference_docx)]
    for lua in sorted((p.doctype.path / "filters").glob("*.lua")):
        cmd += ["--lua-filter", str(lua)]
    subprocess.run(cmd, input=md, text=True, encoding="utf-8", check=True)
    outs = [out]
    if pdf and fmt == "docx":
        outs.append(docx_to_pdf(out))
    return outs


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
