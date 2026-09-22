# Doctypes

A doctype is a folder. Only `doctype.yaml` is required.

    my-type/
    ├─ doctype.yaml     structure, rules, checks, targets
    ├─ reference.docx   styles, header/footer, logo, margins (pandoc reference doc) — edit in Word
    ├─ AGENTS.md        writing rules; copied into every project's AGENTS.md
    ├─ sections/<id>.md starting content for a section (instead of empty subsection headings)
    ├─ filters/*.lua    pandoc lua filters, applied in name order
    └─ skills/          agent skills, copied into the project's .claude/skills/

## doctype.yaml

```yaml
name: school-thesis            # identifier, also the folder name
title: School thesis            # shown in `dokdok types list`
lang: de-CH                     # pandoc lang; picks the default toc_title
toc_title: Inhaltsverzeichnis   # optional override
number_sections: true           # false if reference.docx heading styles number themselves
spelling:
  no_eszett: true               # error on ß

sections:                       # rendered in this order
  - id: einleitung              # doc/NN-<id>.md
    title: Einleitung           # becomes the H1; files start at ##
    required: true              # error if the file is missing
    subsections: [A, B]         # ## headings that must exist
    words: { min: 300, max: 450 }   # warning outside the range
    hint: |                     # shown as <!-- dokdok:hint --> in the new file
      Guidance for the writer.
    only_for: [blue-team]       # rendered only in targets with that audience
  - id: quellen
    title: Quellenverzeichnis
    generated: sources          # from sources.yaml (CSL YAML, cited as [@id])
  - id: ki-protokoll
    title: KI-Protokoll
    generated: ai-log           # from ai-log.yaml (`dokdok log`)

checks:                         # which rules `dokdok check` applies
  - every_citation_resolves     # [@id] must exist in sources.yaml
  - every_source_cited          # warn on unused sources
  - every_figure_has_caption    # ![caption](path) needs a caption
  - no_placeholders_in_final    # `--final`: no [placeholders], no leftover hints

targets:                        # `dokdok render <name>`
  default:   { format: docx }
  exec:      { format: docx, audience: exec }
  blue-team: { format: docx, audience: blue-team }
  web:       { format: html }
```

Inside a section, audience-specific blocks:

    ::: {.only-for="blue-team"}
    …
    :::

## Making one

- From scratch: copy the closest bundled doctype, edit the yaml, restyle `reference.docx` in Word.
- From a Word file you like: `dokdok types from-docx file.docx` — keeps its styles/header/footer,
  turns the heading outline into sections and placeholder text into hints.
- Check it: `dokdok types lint <folder>`, then `dokdok new smoke --type <folder> && cd smoke && dokdok render`.
- Share it: any git repo or folder; users run `dokdok add <folder-or-git-url>`.
