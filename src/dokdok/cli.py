"""dokdok — new / add / check / render / doctor / types."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from . import __version__, check as checkmod, doctype as dt, project as prj, render as rnd

MECHANICAL_RULES = """
## dokdok (mechanical rules — generated, do not edit)

- One markdown file per section in `doc/`, named `NN-<section-id>.md`, front matter `section: <id>`.
- Section titles come from the doctype; start your headings at `##`.
- `<!-- dokdok:hint … -->` comments are guidance from the doctype. Read them, then delete them when the section is written.
- Cite with `[@id]`; every id must exist in `sources.yaml` (CSL YAML under `references:`).
- Figures: `![Caption](path)` — caption is mandatory. Tables: pipe tables with a `Table: caption` line.
- Audience-specific content: `::: {.only-for="blue-team"}` … `:::`.
- Before saying you are done: run `dokdok check` (and `dokdok check --final` before submission) and fix every ✖.
- Render with `dokdok render` → `out/`. Never edit files in `out/`.
"""


def cmd_new(a):
    doc = dt.load(a.type)
    root = Path(a.name).resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"{root} exists and is not empty")
    (root / "doc").mkdir(parents=True)
    ref = str(doc.path) if Path(a.type).exists() else doc.name
    cfg = {"doctype": ref, "title": a.title or root.name, "author": a.author or ""}
    (root / "dokdok.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))
    (root / "sources.yaml").write_text("references: []\n")
    tpl_dir = doc.path / "sections"
    for i, s in enumerate(doc.sections, 1):
        if s.generated:
            continue
        tpl = tpl_dir / f"{s.id}.md"
        body = tpl.read_text() if tpl.exists() else "".join(f"## {sub}\n\n" for sub in s.subsections)
        hint = f"<!-- dokdok:hint\n{s.hint.strip()}\n-->\n\n" if s.hint else ""
        (root / "doc" / f"{i:02d}-{s.id}.md").write_text(f"---\nsection: {s.id}\n---\n\n{hint}{body}")
    agents = (doc.path / "AGENTS.md").read_text() if (doc.path / "AGENTS.md").exists() else f"# {doc.title}\n"
    (root / "AGENTS.md").write_text(agents.rstrip() + "\n" + MECHANICAL_RULES)
    if (doc.path / "skills").exists():
        shutil.copytree(doc.path / "skills", root / ".claude" / "skills", dirs_exist_ok=True)
    (root / ".gitignore").write_text("out/\n")
    print(f"✔ {root.relative_to(Path.cwd()) if root.is_relative_to(Path.cwd()) else root}  ({doc.title})")
    print(f"  {len([s for s in doc.sections if not s.generated])} sections in doc/, rules in AGENTS.md")


def cmd_add(a):
    dt.HOME_TYPES.mkdir(parents=True, exist_ok=True)
    name = a.name or a.source.rstrip("/").split("/")[-1].removesuffix(".git")
    dest = dt.HOME_TYPES / name
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    src = Path(a.source).expanduser()
    if src.exists():
        shutil.copytree(src, dest)
    else:
        subprocess.run(["git", "clone", "-q", "--depth", "1", a.source, str(dest)], check=True)
    d = dt.load(str(dest))
    print(f"✔ added {d.name} → {dest}")


def cmd_check(a):
    p = prj.load()
    sys.exit(checkmod.report(checkmod.run(p, final=a.final)))


def cmd_render(a):
    p = prj.load()
    for out in rnd.render(p, target=a.target, pdf=a.pdf):
        print(f"✔ {out.relative_to(p.root)}")


def cmd_doctor(_a):
    ok = True
    for tool, why in (("pandoc", "required for render"),
                      ("soffice", "PDF via LibreOffice (optional)"),
                      ("git", "for `dokdok add` from git (optional)")):
        found = shutil.which(tool)
        print(f"  {'✔' if found else '✖'} {tool:8} {found or '— ' + why}")
        ok &= bool(found) or tool != "pandoc"
    word = Path("/Applications/Microsoft Word.app").exists()
    print(f"  {'✔' if word else '–'} Word     {'PDF via Word (macOS)' if word else 'not found (optional)'}")
    print(f"  · doctypes: {dt.HOME_TYPES}")
    sys.exit(0 if ok else 1)


def cmd_types_list(_a):
    for base in (dt.HOME_TYPES, dt.REPO_TYPES):
        if base.exists():
            for d in sorted(base.iterdir()):
                if (d / "doctype.yaml").exists():
                    t = dt.load(str(d))
                    print(f"  {t.name:24} {t.title}   ({d})")


def cmd_types_lint(a):
    d = dt.load(a.path)
    ids = [s.id for s in d.sections]
    dup = {i for i in ids if ids.count(i) > 1}
    probs = []
    if dup:
        probs.append(f"duplicate section ids: {', '.join(sorted(dup))}")
    if not d.reference_docx:
        probs.append("no reference.docx (pandoc default styles will be used)")
    for s in d.sections:
        if not s.generated and s.required and not s.title:
            probs.append(f"section {s.id} has no title")
    for m in probs:
        print(f"  ⚠ {m}")
    print(f"  ✔ {d.name}: {len(d.sections)} sections, {len(d.checks)} checks")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dokdok")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="create a project from a doctype")
    s.add_argument("name"); s.add_argument("--type", required=True)
    s.add_argument("--title"); s.add_argument("--author")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("add", help="install a doctype from a git url or folder")
    s.add_argument("source"); s.add_argument("--name")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("check", help="lint the project against its doctype")
    s.add_argument("--final", action="store_true", help="stricter: no placeholders etc.")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("render", help="render a target into out/")
    s.add_argument("target", nargs="?", default="default")
    s.add_argument("--pdf", action="store_true", help="also convert docx → pdf")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("doctor", help="check the toolchain"); s.set_defaults(fn=cmd_doctor)

    t = sub.add_parser("types", help="manage doctypes").add_subparsers(dest="tcmd", required=True)
    s = t.add_parser("list"); s.set_defaults(fn=cmd_types_list)
    s = t.add_parser("lint"); s.add_argument("path", nargs="?", default="."); s.set_defaults(fn=cmd_types_lint)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
