# dokdok

Structured documents, written by agents, rendered as real Word/PDF files in
whatever format a school, company or client demands.

    pipx install git+https://github.com/isaaclins/dokdok   # or: uv tool install …
    dokdok new thesis --type school-thesis
    cd thesis && dokdok check && dokdok render

Or let your agent do it — paste this into Claude Code, Codex or pi:

    Install dokdok: read https://raw.githubusercontent.com/isaaclins/dokdok/main/install.md and follow it.

## What's in a project

    thesis/
    ├─ dokdok.yaml      title, author, doctype
    ├─ doc/*.md         one markdown file per section, hints as <!-- dokdok:hint --> comments
    ├─ sources.yaml     citations (CSL YAML), referenced as [@id]
    ├─ AGENTS.md        the document's rules — generated from the doctype
    └─ out/             rendered docx / pdf / html (never edited by hand)

## What's in a doctype

    school-thesis/
    ├─ doctype.yaml     sections, required subsections, word limits, checks, hints
    ├─ reference.docx   styles, header/footer, logo — edit in Word
    ├─ AGENTS.md        writing rules for the agent
    ├─ sections/        optional section templates
    ├─ filters/         optional pandoc lua filters
    └─ skills/          optional agent skills shipped with the type

Bundled: `school-thesis` (vocational-school thesis), `school-thesis-de` (same, German),
`ipa` (Swiss IT apprenticeship final project, IPERKA, daily journal) and `pentest-report`
(two targets: `exec` and `blue-team` from the same findings).

Make one from a Word file you like: `dokdok types from-docx file.docx`.
Install one: `dokdok add <folder-or-git-url>`.

## Commands

    dokdok new <name> --type <doctype>     project from a doctype
    dokdok entry <section> [--date] [--title]  add an entry to a repeat section (journal day)
    dokdok check [--final]                 lint against the doctype's rules
    dokdok render [target] [--pdf]         docx by default; pdf via LibreOffice
    dokdok add <source>                    install a doctype
    dokdok types list | lint | from-docx   manage doctypes
    dokdok doctor                          check the toolchain

Needs `pandoc`. PDF needs LibreOffice (or Word on macOS).

The repo is also the agent skill: a Claude Code plugin (`.claude-plugin/`) and a pi package
(`package.json`), both pointing at `skills/dokdok/SKILL.md`. Codex users copy that folder.

See [DESIGN.md](DESIGN.md) for the why. `examples/thesis` is a small fictional
project you can render right away.
