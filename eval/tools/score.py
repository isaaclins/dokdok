"""Score every run under eval/results/ against a checklist and write report.md.
Each scenario folder has a `leak.txt` listing forbidden strings (the reference world's content:
other person's name, their topic, their org) — any hit in the produced docx is a leak (bad).
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "eval" / "results"
SCEN = REPO / "eval" / "scenarios"


def plain(docx: Path) -> str:
    try:
        return subprocess.run(["pandoc", str(docx), "-t", "plain"], capture_output=True, text=True, encoding="utf-8").stdout
    except Exception:
        return ""


def score_run(scen_name: str, run_dir: Path) -> dict:
    meta = {}
    ans = (run_dir / "antwort.txt").read_text(encoding="utf-8", errors="replace") if (run_dir / "antwort.txt").exists() else ""
    m = re.search(r"exit=(\d+) engine=(\w+) model=(\S+) seconds=(\d+)", ans)
    meta.update(exit=int(m.group(1)) if m else None, engine=m.group(2) if m else "?",
                model=m.group(3) if m else "?", seconds=int(m.group(4)) if m else None)
    docx = [f for f in run_dir.glob("*.docx")]
    meta["docs"] = len(docx)
    lint = (run_dir / "lint.txt").read_text(encoding="utf-8") if (run_dir / "lint.txt").exists() else ""
    ref = re.search(r"reference\.docx: (\d+) header.*?(\d+) image", lint)
    meta["style_kept"] = bool(ref and int(ref.group(1)) >= 1 and int(ref.group(2)) >= 1)
    if not ref and docx:                     # no doctype captured: judge the document itself
        with zipfile.ZipFile(docx[0]) as z:
            names = z.namelist()
            meta["style_kept"] = any(n.startswith("word/header") for n in names) and any(n.startswith("word/media/") for n in names)
    # leakage
    leakfile = SCEN / scen_name / "leak.txt"
    forbidden = [l.strip() for l in leakfile.read_text(encoding="utf-8").splitlines() if l.strip()] if leakfile.exists() else []
    leaks = {}
    attribution = re.compile(r"\b(stil|style|vorlage|template|layout|look|gestaltung|formatierung|referenz|reference)\b", re.I)
    for f in docx:
        for line in plain(f).splitlines():
            if attribution.search(line):      # "style taken from X's document" is honest, not a leak
                continue
            low = line.lower()
            for w in forbidden:
                if w.lower() in low:
                    leaks[w] = leaks.get(w, 0) + low.count(w.lower())
    meta["leaks"] = leaks
    meta["clean"] = (len(leaks) == 0)
    # pages
    pages = 0
    for p in run_dir.glob("*.pdf"):
        r = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True)
        mm = re.search(r"Pages:\s+(\d+)", r.stdout)
        pages = max(pages, int(mm.group(1)) if mm else 0)
    meta["pages"] = pages
    # docx sanity: no directory entries
    ok = True
    for f in docx:
        with zipfile.ZipFile(f) as z:
            if any(n.endswith("/") for n in z.namelist()):
                ok = False
    meta["docx_ok"] = ok and bool(docx)
    # hint boxes present (grey guidance)
    meta["hints"] = any(b'w:styleId="Hint"' in zipfile.ZipFile(f).read("word/styles.xml") for f in docx) if docx else False
    # produced anything at all
    meta["produced"] = bool(docx)
    meta["asked"] = (not docx) and bool(re.search(r"\?\s*$", ans.strip().splitlines()[-2] if len(ans.strip().splitlines()) > 1 else "", re.M)) \
        or (not docx and bool(re.search(r"(wie möchtest du|brauche ich noch|which do you|could you tell me|frage an dich|\?$)", ans, re.I | re.M)))
    meta["quota"] = ("usage limit" in ans) and not docx
    return meta


def main():
    rows = []
    for scen in sorted(d for d in RESULTS.iterdir() if d.is_dir()) if RESULTS.exists() else []:
        for run in sorted(scen.iterdir()):
            if run.is_dir():
                rows.append((scen.name, run.name, score_run(scen.name, run)))
    # report
    out = ["# dokdok eval\n"]
    by_scen = {}
    for s, r, m in rows:
        by_scen.setdefault(s, []).append((r, m))
    for s, runs in by_scen.items():
        out.append(f"\n## {s}\n")
        out.append("| run | engine/model | produced | style | clean | docx ok | hints | pages | secs | leaks |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for r, m in runs:
            tick = lambda b: "✓" if b else "✗"
            status = "quota" if m["quota"] else ("asked" if m["asked"] else ("✓" if m["produced"] else "✗"))
            out.append(f"| {r} | {m['engine']}/{m['model']} | {status} | {tick(m['style_kept'])} | "
                       f"{tick(m['clean'])} | {tick(m['docx_ok'])} | {tick(m['hints'])} | {m['pages']} | {m['seconds']} | "
                       f"{', '.join(f'{k}×{v}' for k,v in m['leaks'].items()) or '—'} |")
        # pair agreement
        keys = ["produced", "style_kept", "clean", "docx_ok", "hints"]
        pairs = {}
        for r, m in runs:
            cfg = f"{m['engine']}/{m['model']}"
            pairs.setdefault(cfg, []).append(m)
        for cfg, ms in pairs.items():
            if len(ms) == 2:
                agree = sum(ms[0][k] == ms[1][k] for k in keys)
                out.append(f"\n_{cfg} pair agreement: {agree}/{len(keys)} checklist items_")
    (RESULTS / "report.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
