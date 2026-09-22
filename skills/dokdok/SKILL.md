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
- Never invent content, sources or numbers; leave `[placeholders]` and say what only they
  can supply.
- **Deliver first, ask after.** Don't stop to ask before the document exists. If something is
  missing or wrong (a surname, a date that breaks a rule, a budget that doesn't add up), take
  the safest option, mark it visibly in the document (`[Nachname]`, a hint) and in your message,
  and keep going. Questions come at the end, with the file already on the table — the person
  can always answer and you re-render. One question at a time when you do ask.

## Someone needs a document or a template (most common)

Typical opening: "Ich bin Kaya, bau mir eine VA-Vorlage im Stil meiner Schule" plus a pile
of files (guideline PDFs, a Word template, grading grid, their concept).

1. **Read everything they gave you first.** PDFs: `pdftotext file.pdf -` (or your PDF reader).
   Word files: `pandoc file.docx -t plain`. Note: required chapters and order, word counts,
   citation format, mandatory declarations, grading points, deadlines, formatting rules.
2. **Is there a Word file that shows how it should look?** It can be anything: the school's
   blank template, a teacher's example, a friend's finished thesis, last year's winner. The
   person can't format Word themselves — that file *is* the look. Never build the look by hand:
   `dokdok types from-docx <file.docx> --name <school-or-course> --style-only` keeps its fonts,
   heading styles, numbering, header, footer and logo and throws the body away. Read the
   command's report: it tells you what it could not carry over.
   **Take only the look from that file, never its content.** Someone else's chapter titles,
   names, dates, sources, interview answers or AI-log rows do not belong in this person's
   document — an example full of another person's text is normal, not suspicious. The chapter
   structure comes from the guideline and from the person's own concept; use the example only
   to see how a finished one is organised (how many levels, where the appendix goes).
   Without `--style-only`, from-docx also turns the file's outline into sections — use that
   only for a genuinely blank template.
   **The document you hand over is always produced by dokdok from a doctype** — never a
   copied or edited version of the reference file, even if that file already looks like the
   person's own work. Only a dokdok project gives them the checks, the hint boxes that
   disappear with `--final`, the AI log and a document that can be re-rendered as they
   write. If the reference really is an earlier version of their own document, say so, and
   still rebuild it through dokdok.
   No Word file? Start from the closest bundled doctype (`dokdok types list`) and copy it.
   If you must change styles inside `reference.docx` (font sizes, colours), do it the way
   `doctypes/*/make-reference.py` does — Python `zipfile`, rewriting `word/styles.xml` — and
   **never** unzip/edit/`zip -r` by hand: that adds directory entries and Word then refuses
   every document rendered from it ("unreadable content").
3. **Make the doctype match the guideline**: edit its `doctype.yaml` — sections in the
   required order, `required`, `subsections`, `words`, a `hint` per section carrying the
   guideline's demands and grading points; `AGENTS.md` with the writing rules (language,
   citation style, what must never be invented). Add `generated: sources` / `ai-log` /
   `figures` sections if the guideline wants a bibliography / AI declaration / list of figures.
   Give it a `title_page` template (see `doctypes/school-thesis-de/sections/title.md`).

   **A template is the complete skeleton of the finished document, not a list of headings.**
   The person will write *inside* it in Word. So:
   - One chapter per research question from their concept, each with the 3–4 subchapters the
     question implies (definition → history → today → comparison, or whatever fits), plus a
     chapter for each method (interview: portrait, the interview, evaluation).
   - Under **every** subchapter a `[bracketed instruction]`: what belongs here, which interview
     questions or sources feed it, roughly how long. That's the `sections/<id>.md` file.
   - The `hint` of each section says what the guideline grades there and with how many points.
     Hints render as grey «Hinweis» boxes in the Word file — that's what the person reads.
     Hints are markdown: put literal examples like `[@id]` or `![caption](file.jpg)` in backticks.
   - Appendix: interview questions from their material, declaration templates, anything the
     guideline says is mandatory. Nothing the guideline mentions may be missing.
   Compare against a filled example if one exists: the template should have every heading the
   example has. Aim for the page count of a finished skeleton (10+ pages), not a 3-page outline.
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
