"""A project: dokdok.yaml + doc/*.md + sources.yaml."""
from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml

from . import doctype as dt

FRONT = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
HINT = re.compile(r"<!--\s*dokdok:hint.*?-->\s*", re.S)
HINT_TEXT = re.compile(r"<!--\s*dokdok:hint(.*?)-->", re.S)


@dataclass
class SectionFile:
    path: Path
    id: str
    body: str        # markdown without front matter, hints kept
    meta: dict = field(default_factory=dict)
    entries: list["SectionFile"] = field(default_factory=list)   # for repeat sections: one per file

    @property
    def text(self) -> str:
        """Body without hints — what gets checked and counted."""
        return HINT.sub("", self.body)

    def hints(self) -> list[str]:
        return [m.strip() for m in HINT_TEXT.findall(self.body)]


@dataclass
class Project:
    root: Path
    config: dict
    doctype: dt.Doctype
    sections: list[SectionFile]

    @property
    def sources_path(self) -> Path:
        return self.root / "sources.yaml"

    def sources(self) -> list[dict]:
        if not self.sources_path.exists():
            return []
        d = yaml.safe_load(self.sources_path.read_text(encoding="utf-8")) or {}
        return d.get("references", []) if isinstance(d, dict) else d

    def section(self, sid: str) -> SectionFile | None:
        return next((s for s in self.sections if s.id == sid), None)

    def glossary(self) -> list[dict]:
        f = self.root / "glossary.yaml"
        return (yaml.safe_load(f.read_text(encoding="utf-8")) or []) if f.exists() else []


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for cand in (p, *p.parents):
        if (cand / "dokdok.yaml").exists():
            return cand
    raise SystemExit("not inside a dokdok project (no dokdok.yaml found)")


def load(start: Path | None = None) -> Project:
    root = find_root(start)
    cfg = yaml.safe_load((root / "dokdok.yaml").read_text(encoding="utf-8")) or {}
    ref = cfg.get("doctype")
    if not ref:
        raise SystemExit("dokdok.yaml has no `doctype:`")
    if (root / ref / "doctype.yaml").exists():
        ref = str(root / ref)
    doc = dt.load(ref)
    sections = []
    for f in sorted((root / "doc").glob("*.md")):
        sections.append(_read(f))
    for spec in doc.sections:                       # repeat sections live in doc/<id>/*.md
        d = root / "doc" / spec.id
        if spec.repeat and d.is_dir():
            entries = [_read(f, sid=spec.id) for f in sorted(d.glob("*.md"))]
            sections.append(SectionFile(path=d, id=spec.id, body="", entries=entries))
    return Project(root=root, config=cfg, doctype=doc, sections=sections)


def _read(f: Path, sid: str | None = None) -> SectionFile:
    raw = f.read_text(encoding="utf-8")
    m = FRONT.match(raw)
    meta = (yaml.safe_load(m.group(1)) if m else {}) or {}
    body = raw[m.end():] if m else raw
    return SectionFile(path=f, id=sid or meta.get("section") or f.stem.split("-", 1)[-1], body=body, meta=meta)
