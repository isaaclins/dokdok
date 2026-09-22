"""Lint a project against its doctype. Output is per file, written for an agent to act on."""
from dataclasses import dataclass
import re

from .project import Project

CITE = re.compile(r"\[@([\w:.-]+)|(?<![\w@])@([\w:.-]+)")
FIGURE = re.compile(r"!\[(.*?)\]\((.*?)\)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$", re.M)
PLACEHOLDER = re.compile(r"\[(?:…|\.\.\.|TODO|TBD)[^\]]*\]|\bTODO\b|\bTBD\b|\[[^\]\n]{0,120}\]")


@dataclass
class Finding:
    file: str
    level: str      # "error" | "warn" | "ok"
    msg: str


def _words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def run(p: Project, final: bool = False) -> list[Finding]:
    out: list[Finding] = []
    rel = lambda f: str(f.relative_to(p.root))
    checks = set(p.doctype.checks)
    src_ids = {s.get("id") for s in p.sources()}
    cited: set[str] = set()

    # sections that exist in the doctype
    for spec in p.doctype.sections:
        if spec.generated:
            continue
        sf = p.section(spec.id)
        if sf is None or (spec.repeat and not sf.entries):
            if spec.required:
                out.append(Finding("doc/", "error", f"required section «{spec.title}» ({spec.id}) missing"
                                   + (" (no entries yet — `dokdok entry`)" if spec.repeat else "")))
            continue
        if spec.repeat:
            out.append(Finding(rel(sf.path) + "/", "ok", f"{len(sf.entries)} entries"))
            continue
        f = rel(sf.path)
        text = sf.text
        heads = [h.strip() for h in HEADING.findall(text)]
        missing = [s for s in spec.subsections if s not in heads]
        if spec.subsections:
            if missing:
                out.append(Finding(f, "error", f"subsections missing: {', '.join(missing)}"))
            else:
                out.append(Finding(f, "ok", f"{len(spec.subsections)}/{len(spec.subsections)} required subsections present"))
        n = _words(text)
        lo, hi = spec.words.get("min"), spec.words.get("max")
        if lo and n < lo:
            out.append(Finding(f, "warn", f"{n} words (target {lo}–{hi or '…'})"))
        elif hi and n > hi:
            out.append(Finding(f, "warn", f"{n} words (target {lo or '…'}–{hi})"))

    # file-level checks
    for sf in [s for s in p.sections if not s.entries] + [e for s in p.sections for e in s.entries]:
        f = rel(sf.path)
        text = sf.text
        if p.doctype.section(sf.id) is None:
            out.append(Finding(f, "warn", f"section id «{sf.id}» not in doctype"))
        for m in CITE.finditer(text):
            cited.add(m.group(1) or m.group(2))
        if "every_figure_has_caption" in checks:
            for cap, path in FIGURE.findall(text):
                if not cap.strip():
                    out.append(Finding(f, "error", f"figure {path} has no caption"))
        if p.doctype.spelling.get("no_eszett") and "ß" in text:
            out.append(Finding(f, "error", "contains ß (use ss)"))
        if final:
            if "dokdok:hint" in sf.body:
                out.append(Finding(f, "error", "hint comment still present (delete once the section is written)"))
            ph = PLACEHOLDER.findall(text)
            if ph:
                out.append(Finding(f, "error", f"{len(ph)} placeholder(s) left: {ph[0][:40]!r} …"))

    if "every_citation_resolves" in checks:
        for c in sorted(cited - src_ids):
            out.append(Finding("sources.yaml", "error", f"[@{c}] cited but not in sources.yaml"))
    if "every_source_cited" in checks:
        for s in sorted(src_ids - cited):
            out.append(Finding("sources.yaml", "warn", f"source «{s}» never cited"))
    return out


def report(findings: list[Finding]) -> int:
    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)
    mark = {"ok": "✔", "warn": "⚠", "error": "✖"}
    for file, fs in by_file.items():
        print(file)
        for f in fs:
            print(f"  {mark[f.level]} {f.msg}")
    errs = sum(f.level == "error" for f in findings)
    warns = sum(f.level == "warn" for f in findings)
    print(f"{errs} error(s), {warns} warning(s)")
    return 1 if errs else 0
