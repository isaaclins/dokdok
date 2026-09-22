"""Load a doctype (folder with doctype.yaml) by path or name."""
from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml

HINT_LABELS = {"de": "Hinweis", "fr": "Remarque", "it": "Nota", "en": "Note"}
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
    generated: str | None = None   # "sources" | "ai-log" | "glossary" | "figures" | "tables"
    only_for: list[str] = field(default_factory=list)
    repeat: str | None = None      # "daily": doc/<id>/YYYY-MM-DD.md, one ## per file, sorted by date
    derive_from: list[str] = field(default_factory=list)   # inputs: file globs or "git-log"; see derive.py
    entry_title: str = "{title}"   # heading for repeat entries; {title} {date} from the entry's front matter


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
    hints: str                 # "visible" (grey paragraphs in the document, stripped by --final) | "hidden"
    hint_label: str
    page_breaks: bool          # new page before every top-level section
    title_page: str | None     # markdown template (relative to the doctype) with {title} {author} {key} placeholders

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
    d = yaml.safe_load((path / "doctype.yaml").read_text(encoding="utf-8")) or {}
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
        hints=d.get("hints", "visible"),
        hint_label=d.get("hint_label", HINT_LABELS.get(d.get("lang", "en")[:2], "Note")),
        page_breaks=d.get("page_breaks", True),
        title_page=d.get("title_page"),
    )
