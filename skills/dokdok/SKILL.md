---
name: dokdok
description: Structured documents that must follow a required format, delivered as real Word/PDF files — school theses and templates (Vertiefungsarbeit / VA, Maturaarbeit, IPA, Abschlussarbeit, Facharbeit, Projektarbeit, Bachelorarbeit, thesis, final project report), engagement and pentest reports, anything where someone has a guideline (Leitfaden, Bewertungsraster, Vorgaben), a Word template (Vorlage) or grading grid. Use when the user needs to write such a document, wants a template built from their school's or company's Word file or guideline, or asks to check a document against its rules. Triggers in any language, e.g. "VA Vorlage bauen", "Word-Vorlage im Stil meiner Schule", "Arbeit schreiben", "modèle pour mon travail".
---

# dokdok

dokdok is a CLI that turns markdown sections + a *doctype* (structure, style, rules) into
docx/pdf. You write; dokdok gives you rails and a red/green check. The person you're helping
is usually **not technical** — a student or a busy professional.

## How to talk

- **Answer in the language the user writes in.** German in, German out.
- Talk about *the document*: chapters, the template, what's missing. Not about files,
  commands, YAML, font sizes or "doctypes" — unless the user asks how it works.
- One question at a time. Never invent content, sources or numbers; leave `[placeholders]`
  and say what only they can supply.

## Someone needs a document or a template (most common)

Typical opening: "Ich bin Kaya, bau mir eine VA-Vorlage im Stil meiner Schule" plus a pile
of files (guideline PDFs, a Word template, grading grid, their concept).

1. **Read everything they gave you first.** PDFs: `pdftotext file.pdf -` (or your PDF reader).
   Word files: `pandoc file.docx -t plain`. Note: required chapters and order, word counts,
   citation format, mandatory declarations, grading points, deadlines, formatting rules.
2. **Is there a Word file from the school/company?** (template, sample, "Vorlage", or even a
   filled example.) Then the style comes from it — never build the look by hand:
   `dokdok types from-docx <file.docx> --name <school-or-course>` keeps its fonts, heading
   styles, numbering, header, footer and logo, and turns its outline into sections. Read the
   command's report: it tells you what it could not carry over.
   No Word file? Start from the closest bundled doctype (`dokdok types list`) and copy it.
   If you must change styles inside `reference.docx` (font sizes, colours), do it the way
   `doctypes/*/make-reference.py` does — Python `zipfile`, rewriting `word/styles.xml` — and
   **never** unzip/edit/`zip -r` by hand: that adds directory entries and Word then refuses
   every document rendered from it ("unreadable content").
3. **Make the doctype match the guideline**: edit its `doctype.yaml` — sections in the
   required order, `required`, `subsections`, `words`, a `hint` per section carrying the
   guideline's demands and grading points; `AGENTS.md` with the writing rules (language,
   citation style, what must never be invented). Add `generated: sources` / `ai-log` sections
   if the guideline wants a bibliography / AI declaration.
4. **Verify before showing anything**: `dokdok types lint <folder>` prints what the
   reference.docx contains (header/footer, images, heading numbering). If the school template
   has a logo or numbered headings and lint says otherwise, fix it before continuing.
   Then `dokdok new <name> --type <folder> --title … --author …`, `cd` in, `dokdok render`,
   and look at `out/*.docx` (`pandoc out/x.docx -t plain | head -80`) — chapter order and
   numbering right? TOC present?
5. Fill what you can from their material (concept → introduction, questions, methods),
   `dokdok log --tool "<you>" "…" --outcome "…"`, `dokdok check`, fix every ✖.
6. Hand over: where the Word file is, what you filled in, what is still theirs
   (the placeholders). Offer the next step (e.g. the `interview` skill if the doctype has it).
   **Never tell the user to edit markdown files or run commands** — they tell you what to
   write next, you do it and re-render. The Word file in `out/` is what they open.

## Someone has a project already

`dokdok check` → fix ✖ → write → `dokdok log` → `dokdok render` (add `--pdf` if wanted).
Before submission: `dokdok check --final`. Never edit `out/`. Never say "done" with a red check.

## Reference

- Doctype = folder: `doctype.yaml`, `reference.docx`, `AGENTS.md`, `sections/<id>.md`
  (starting content), `skills/`. Schema: `dokdok types lint` complains about mistakes;
  field reference in the repo's `doctypes/README.md`.
- Section files: front matter `section: <id>`, headings from `##`, cite `[@id]` (sources in
  `sources.yaml`, CSL YAML), figures need captions, tables end with `Table: caption`.
- Repeat sections (journal): `dokdok entry <id> --date YYYY-MM-DD --title …`.
- Derived sections: `dokdok inputs <id>` (git only if the project is a repo — ask first;
  don't assume the user knows git).
- If `dokdok` is missing, follow `install.md` in the dokdok repo.
