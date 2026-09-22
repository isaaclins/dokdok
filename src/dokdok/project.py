"""A project: dokdok.yaml + doc/*.md + sources.yaml."""
from dataclasses import dataclass
from pathlib import Path
import re
import yaml

from . import doctype as dt

FRONT = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
HINT = re.compile(r"<!--\s*dokdok:hint.*?-->\s*", re.S)


@dataclass
class SectionFile:
    path: Path
    id: str
    body: str        # markdown without front matter, hints kept

    @property
    def text(self) -> str:
        """Body without hints — what gets rendered and counted."""
        return HINT.sub("", self.body)


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
        d = yaml.safe_load(self.sources_path.read_text()) or {}
        return d.get("references", []) if isinstance(d, dict) else d

    def section(self, sid: str) -> SectionFile | None:
        return next((s for s in self.sections if s.id == sid), None)


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for cand in (p, *p.parents):
        if (cand / "dokdok.yaml").exists():
            return cand
    raise SystemExit("not inside a dokdok project (no dokdok.yaml found)")


def load(start: Path | None = None) -> Project:
    root = find_root(start)
    cfg = yaml.safe_load((root / "dokdok.yaml").read_text()) or {}
    ref = cfg.get("doctype")
    if not ref:
        raise SystemExit("dokdok.yaml has no `doctype:`")
    if (root / ref / "doctype.yaml").exists():
        ref = str(root / ref)
    doc = dt.load(ref)
    sections = []
    for f in sorted((root / "doc").glob("*.md")):
        raw = f.read_text()
        m = FRONT.match(raw)
        meta = yaml.safe_load(m.group(1)) if m else {}
        body = raw[m.end():] if m else raw
        sid = (meta or {}).get("section") or f.stem.split("-", 1)[-1]
        sections.append(SectionFile(path=f, id=sid, body=body))
    return Project(root=root, config=cfg, doctype=doc, sections=sections)
