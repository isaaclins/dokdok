"""Load a doctype (folder with doctype.yaml) by path or name."""
from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml

TOC_TITLES = {"de": "Inhaltsverzeichnis", "fr": "Table des matières", "it": "Indice", "en": "Table of Contents"}
HOME_TYPES = Path(os.environ.get("DOKDOK_HOME", Path.home() / ".dokdok")) / "doctypes"
REPO_TYPES = Path(__file__).resolve().parents[2] / "doctypes"


@dataclass
class Section:
    id: str
    title: str
    required: bool = False
    subsections: list[str] = field(default_factory=list)
    words: dict = field(default_factory=dict)
    hint: str = ""
    generated: str | None = None   # "sources" | "figures" | None
    only_for: list[str] = field(default_factory=list)


@dataclass
class Doctype:
    path: Path
    name: str
    title: str
    lang: str
    sections: list[Section]
    checks: list[str]
    spelling: dict
    targets: dict
    number_sections: bool
    toc_title: str

    @property
    def reference_docx(self) -> Path | None:
        p = self.path / "reference.docx"
        return p if p.exists() else None

    def section(self, sid: str) -> Section | None:
        return next((s for s in self.sections if s.id == sid), None)


def resolve(ref: str) -> Path:
    """`ref` is a path to a doctype folder, or a name looked up in ~/.dokdok/doctypes and the repo."""
    p = Path(ref).expanduser()
    if (p / "doctype.yaml").exists():
        return p.resolve()
    for base in (HOME_TYPES, REPO_TYPES):
        if (base / ref / "doctype.yaml").exists():
            return (base / ref).resolve()
    raise SystemExit(f"doctype not found: {ref}  (looked in {HOME_TYPES} and {REPO_TYPES})")


def load(ref: str) -> Doctype:
    path = resolve(ref)
    d = yaml.safe_load((path / "doctype.yaml").read_text()) or {}
    sections = [Section(**s) for s in d.get("sections", [])]
    return Doctype(
        path=path,
        name=d.get("name", path.name),
        title=d.get("title", path.name),
        lang=d.get("lang", "en"),
        sections=sections,
        checks=d.get("checks", []),
        spelling=d.get("spelling", {}),
        targets=d.get("targets", {"default": {"format": "docx"}}),
        number_sections=d.get("number_sections", True),
        toc_title=d.get("toc_title", TOC_TITLES.get(d.get("lang", "en")[:2], "Table of Contents")),
    )
