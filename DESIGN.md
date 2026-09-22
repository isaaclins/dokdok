# dokdok — design

Structured documents, written by agents, that come out as real Word/PDF files
in the format a school, a company or a client demands.

Status: design only. Nothing here is built yet.

## The problem

Every "write a formal document" task looks the same:

    rules of the document type      (guideline, template, grading grid, house style)
  + source material                 (concept, notes, emails, scans, git log, exports)
  + an agent
  → draft in an intermediate format
  → rendered docx / pdf / html

Today each person rebuilds this from scratch. Three fictional but typical cases:

- **Mara, apprentice developer.** Her final project report has a 40-page
  guideline, mandatory chapters, a daily work journal and an AI-usage
  declaration. She bends a static-site generator into a printer and spends
  weeks fighting it because her agent never quite learns the shortcodes.
- **Jonas, 19, painter apprentice.** His school hands him a Word template and a
  guideline PDF for his thesis. He is told "use Word". He is not technical and
  has no idea how to get an agent to help him with a .docx.
- **Nadia, red-team lead.** Every engagement ends in the same report structure,
  and she needs an executive version and a blue-team version from the same
  findings. She has a `make report-for-blue-team` and a pile of scripts nobody
  else can run.

All three are the same shape, with the rules encoded ad hoc and no feedback loop
for the agent except a human looking at the output. And a .docx is only a zip of
XML — an agent can produce it, if it knows the rules.

## Prior art we are copying, not reinventing

| Tool                | Their name for it            | We take                                   |
|---------------------|------------------------------|-------------------------------------------|
| LaTeX               | `\documentclass`             | "the type defines structure and style"    |
| Quarto              | extensions, profiles         | md → docx/pdf/html via pandoc; profiles   |
| vale                | style packages               | lint rules as data, shipped in packages   |
| cargo / npm         | `new`, `add`, `check`        | the verbs                                 |
| pentest report tools | designs, templates           | pentest reporting is a doctype, not a product |
| Agent Skills        | SKILL.md                     | how agents learn about dokdok             |

The only genuinely new part: **a document type can ship agent behaviour**
(skills, scripts, checks), not just structure and style. Prior art predates agents.

## Three nouns, four verbs

    project   = folder of markdown sections + dokdok.yaml     (a cargo crate)
    doctype   = package: structure + style + rules + tools     (a documentclass)
    target    = one rendered output of a project               (a build profile)

    dokdok new <name> --type <doctype>
    dokdok add <doctype>              # from git or registry
    dokdok check [--final]            # lint against the doctype's rules
    dokdok render [target]            # docx first, pdf/html derived

Humans mostly never type these. The agent does. See "Who types what".

## Project layout

    thesis/
    ├─ dokdok.yaml        author, class, title, deadline, targets …
    ├─ doc/
    │  ├─ 01-einleitung.md
    │  ├─ …
    │  └─ 99-anhang.md
    ├─ sources.yaml       citations, referenced as [@id]
    ├─ AGENTS.md          generated from the doctype — the writing rules
    └─ .claude/skills/    skills the doctype shipped (optional)

Section files are plain markdown with a one-line front matter (`section: id`).
Hints from the doctype live in `<!-- dokdok:hint … -->` comments and are
stripped on render. Figures, tables, citations use pandoc conventions.
Audience-specific blocks use `::: {.only-for="blue-team"}`.

## Doctype layout

    school-thesis/
    ├─ doctype.yaml       sections (order, required, subsections, word counts,
    │                     repeat: daily, generated: sources), checks, hints
    ├─ reference.docx     styles, numbering, header/footer, logo, margins
    ├─ cover.docx         optional static pages pandoc can't reproduce
    ├─ AGENTS.md          tone, citation format, declarations, what "done" means
    ├─ filters/           lua: hints, KI marks, captions, declarations
    ├─ skills/            optional: agent skills (interview, journal-from-git, nessus-import)
    └─ examples/

Fidelity contract of `reference.docx`: fonts, heading styles, colours,
numbering, header/footer, margins, page numbers round-trip 1:1. Free-form
layout (text boxes, floating images, magazine covers) is carried over as
static pages via `cover.docx`, not regenerated.

### Creating a doctype

- By hand: `dokdok types new <name>` → edit yaml, restyle reference.docx in Word.
- From an existing Word file you like:
  `dokdok types from-docx file.docx` hollows the body out into reference.docx,
  turns the heading outline into sections, turns placeholder text into hints,
  reports what it could not capture. The agent then does the semantic part
  (reads the guideline, marks required sections, writes AGENTS.md).
- From a dump of guideline PDFs: the agent reads them and writes the doctype;
  dokdok provides the lint (`dokdok types lint`) and the skeleton render to
  compare against the original.

### Distribution

Doctypes are git-addressable folders (`dokdok add github.com/org/school-thesis`),
like Homebrew taps. A registry UI is a later concern.

## Targets

Same sources, several outputs, chosen by the doctype:

    dokdok render            # default target
    dokdok render exec       # summary, no remediation detail
    dokdok render blue-team  # full findings + fixes
    dokdok render website    # html for the interview partner

## Checks

The checker is the product. Everything that caused the IPA back-and-forth
becomes a rule in `doctype.yaml`:

- required sections / subsections present, in order
- word and quote-share limits
- every figure has a source, every citation resolves, every source is cited
- spelling constraints (no ß), placeholder scan (`--final`)
- doctype-specific lua/python checks (CVSS parses, declaration present, …)

Output is red/green per file, written for an agent to act on.

## Who types what

| Person            | Interface                                        |
|-------------------|--------------------------------------------------|
| Jonas (non-technical) | chat only, never sees the CLI                |
| Mara, Nadia       | chat + CLI directly, in `make` and CI            |
| doctype author    | a folder + `dokdok types lint`                   |

## How agents learn about dokdok

Two layers:

1. **Global skill** — `SKILL.md` describing when to use dokdok. Same file for
   Claude Code, Codex, pi (skills are a shared format).
2. **Per-project `AGENTS.md`** — generated on `new` from the doctype. Any agent
   reads it; no skill required inside a project.

Distribution per agent:

- Claude Code: plugin or `~/.claude/skills/dokdok`
- Codex: `~/.codex/skills/dokdok`
- pi: `pi install git:<dokdok repo>` (package bundles the skill)
- Claude desktop / Cowork: skill upload + a `.mcpb` desktop extension wrapping
  the CLI as MCP tools (the sandbox can't run host binaries). The only place
  MCP is needed.

## Install is a prompt

    Install dokdok: read https://dokdok.dev/install.md and follow it.

`install.md` is written for agents: detect OS and agent, install the CLI
(brew/pipx), install the skill into the right place, run `dokdok doctor` and a
smoke render, report in one sentence. Same doc serves for update/uninstall.
The agent handles the messy branches by reading errors, not by us anticipating
them.

## Tech decisions

- Renderer: pandoc by default (`reference.docx`, citations, captions, TOC),
  behind a plugin interface so Typst/Marp/python-docx can slot in per doctype.
- docx is the primary artifact; PDF derived via LibreOffice headless (Word via
  AppleScript on macOS for exact field refresh).
- CLI in Python, shipped via brew/pipx, pandoc bundled or declared dependency.
- Sections re-render only when stale; a section may declare `derive_from:`
  inputs (git log, test results, exports) so generated chapters never drift.
- KI-Protokoll auto-logged from agent sessions (schools require it, agents forget).

## Explicitly not doing (now)

- GUI, web editor, Word add-in
- our own layout engine
- a registry website

## First milestone

Take one real school-thesis template plus its guideline PDF, build a
`school-thesis` doctype from it, and reproduce a filled thesis from `doc/*.md`
through `dokdok render` — with `dokdok check` catching what the guideline
currently only says in prose. If that holds, the base holds.
