"""Turn a scenario's `_source/` (markdown + brand jsons) into the dump the agent sees.
Convention per scenario folder:
  _source/reference.md + _source/reference.brand.json  → dump/<RefName>.docx  (the styled 'look')
  _source/*.md that start with 'FILE: <name.ext>'      → dump/<name.ext> (docx via a plain brand, pdf, or left as md/csv/txt)
  _source/plain/*                                       → copied verbatim into dump/
Everything is fictional; no real brands.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import brand as B  # noqa: E402


def build(scenario: Path):
    src = scenario / "_source"; dump = scenario / "dump"
    if dump.exists(): shutil.rmtree(dump)
    dump.mkdir(parents=True)
    for j in src.glob("*.brand.json"):
        stem = j.name[:-len(".brand.json")]
        md = src / f"{stem}.md"
        b = json.loads(j.read_text(encoding="utf-8"))
        out = dump / f"{b.get('filename', stem)}.docx"
        logo = out.with_name("logo.png"); B.logo(b, logo)
        B.styled_docx(b, md, out, logo)
        B.pdf(out); logo.unlink(missing_ok=True)
        print("styled", out.name)
    for f in src.glob("*"):
        if f.suffix in (".md",) and not (src / f"{f.stem}.brand.json").exists():
            # a dump file with a FILE: header decides its real name/type
            head = f.read_text(encoding="utf-8").splitlines()[0]
            if head.startswith("FILE:"):
                name = head.split(":", 1)[1].strip(); body = f.read_text(encoding="utf-8").split("\n", 1)[1]
                (dump / name).write_text(body, encoding="utf-8"); print("file", name)
    plain = src / "plain"
    if plain.exists():
        for f in plain.iterdir():
            shutil.copy(f, dump / f.name); print("plain", f.name)
    print(f"✔ {scenario.name}: {len(list(dump.iterdir()))} files in dump/")


if __name__ == "__main__":
    build(Path(sys.argv[1]).resolve())
