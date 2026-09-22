---
name: dokdok
description: Write structured documents that must follow a required format — school theses, apprenticeship final reports, pentest/engagement reports, anything where someone hands over a template, guideline or grading grid — and deliver them as real Word/PDF files. Use when a user needs to write such a document, has a Word template they want reproduced, or asks to check a document against its rules.
---

# dokdok

dokdok is a CLI that turns markdown sections + a *doctype* (structure, style,
rules, tools) into docx/pdf/html. You do the writing; dokdok gives you rails and
a red/green check so you know when the document is actually complete.

## When the user needs to write a document

1. `dokdok types list` — is there a doctype for it? If not, see "Creating a doctype".
2. `dokdok new <folder> --type <doctype> --title "…" --author "…"`
3. Read the generated `AGENTS.md` and every `<!-- dokdok:hint -->` in `doc/`.
4. Read whatever material the user gives you (concept, notes, guideline, emails)
   and fill `doc/*.md`. Add sources to `sources.yaml` (CSL YAML). Delete hints
   once a section is written. Leave `[visible placeholders]` for things only
   the user can supply — never invent them.
5. `dokdok log --tool "<your name>" "<what you wrote>" --outcome "<what the user does with it>"` —
   once per working session. Schools require this record; it renders automatically.
6. `dokdok check` → fix every ✖, then `dokdok render` (add `--pdf` if wanted).
7. Tell the user what is in `out/` and what still needs *them* (placeholders).

Before a submission: `dokdok check --final`.

## Creating a doctype

A doctype is a folder: `doctype.yaml` (sections, required subsections, word
limits, checks, hints), `reference.docx` (styles — edit in Word), `AGENTS.md`
(writing rules), optional `sections/<id>.md` templates and `filters/*.lua`.

- From a guideline PDF / grading grid: read it, write `doctype.yaml` from its
  required chapters, put grading points into `hint:`s, write AGENTS.md.
- From a Word file the user likes: copy it to `reference.docx` and delete the
  body text in Word (keep headers/footers/styles). Use its heading outline for
  `sections:`.
- `dokdok types lint <folder>` then `dokdok new smoke --type <folder> && cd smoke && dokdok render`
  and compare `out/` with the original.
- Install for reuse: `dokdok add <folder-or-git-url>`.

## Rules

- Never edit `out/`. Never claim "done" without a clean `dokdok check`.
- If `dokdok` is missing, follow `install.md` in the dokdok repo.
