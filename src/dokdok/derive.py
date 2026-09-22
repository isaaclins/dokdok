"""Sections derived from inputs: files/globs or the project's git log.

dokdok does not write the text — the agent does. dokdok tracks whether a section is stale
(an input changed after the section was last written) and hands over the inputs on request.
Configured per section in doctype.yaml (`derive_from:`) or per project in dokdok.yaml
(`derive: {section-id: [...]}`), the project winning.
"""
from dataclasses import dataclass
from pathlib import Path
import datetime as dt
import shutil
import subprocess

from .project import Project, SectionFile

GIT = "git-log"


@dataclass
class Input:
    name: str
    changed: dt.datetime | None    # newest change we can see, None if unavailable
    note: str = ""


def sources(p: Project, sid: str) -> list[str]:
    return p.config.get("derive", {}).get(sid) or (p.doctype.section(sid).derive_from if p.doctype.section(sid) else [])


def _git_ok(root: Path) -> bool:
    return shutil.which("git") is not None and (root / ".git").exists()


def inputs(p: Project, sid: str) -> list[Input]:
    out = []
    for src in sources(p, sid):
        if src == GIT:
            if not _git_ok(p.root):
                out.append(Input(GIT, None, "no git repository here (or git not installed) — skipped"))
                continue
            r = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=p.root, capture_output=True, text=True)
            ts = dt.datetime.fromisoformat(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
            out.append(Input(GIT, ts))
        else:
            files = [f for f in p.root.glob(src) if f.is_file()]
            if not files:
                out.append(Input(src, None, "no such file"))
                continue
            newest = max(dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc) for f in files)
            out.append(Input(src, newest))
    return out


def written(sf: SectionFile) -> dt.datetime:
    files = [e.path for e in sf.entries] or [sf.path]
    return max(dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc) for f in files)


def stale(p: Project, sf: SectionFile) -> list[Input]:
    """Inputs that changed after the section was last written."""
    w = written(sf)
    return [i for i in inputs(p, sf.id) if i.changed and i.changed.astimezone(dt.timezone.utc) > w]


def dump(p: Project, sid: str, since: dt.datetime | None = None) -> str:
    """The inputs' content, for the agent to read. Git: commits since the section was last written."""
    parts = []
    for src in sources(p, sid):
        if src == GIT:
            if not _git_ok(p.root):
                parts.append(f"## {GIT}\n\n(no git repository — nothing to read)\n")
                continue
            cmd = ["git", "log", "--date=iso", "--stat", "--format=%n%h %ad%n%s%n%b"]
            if since:
                cmd.append(f"--since={since.isoformat()}")
            r = subprocess.run(cmd, cwd=p.root, capture_output=True, text=True, encoding="utf-8")
            parts.append(f"## {GIT}\n\n```\n{r.stdout.strip() or '(no commits in range)'}\n```\n")
        else:
            for f in sorted(p.root.glob(src)):
                if f.is_file():
                    parts.append(f"## {f.relative_to(p.root)}\n\n```\n{f.read_text(encoding='utf-8', errors='replace')[:20000]}\n```\n")
    return "\n".join(parts) or "(no inputs configured)"
