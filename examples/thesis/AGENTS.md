# School thesis (example doctype)

You are helping a vocational-school student write their thesis. The student is
not technical; keep explanations short.

## Writing rules

- Plain, factual English. First person where personal motivation is asked for.
- Never invent facts, sources, interview answers or numbers. Where the student
  must supply something, leave a visible placeholder like `[date of the interview]`.
- Every claim from research gets a citation `[@id]`. Direct quotes ≤ 1/6 of the text.
- Log every session in which you wrote or substantially rewrote text with
  `dokdok log`; the guideline requires an AI usage record.

## dokdok (mechanical rules — generated, do not edit)

- One markdown file per section in `doc/`, named `NN-<section-id>.md`, front matter `section: <id>`.
- Section titles come from the doctype; start your headings at `##`.
- `<!-- dokdok:hint … -->` comments are guidance from the doctype. Read them, then delete them when the section is written.
- Cite with `[@id]`; every id must exist in `sources.yaml` (CSL YAML under `references:`).
- Figures: `![Caption](path)` — caption is mandatory. Tables: pipe tables with a `Table: caption` line.
- Audience-specific content: `::: {.only-for="blue-team"}` … `:::`.
- Every session in which you wrote or substantially rewrote text: `dokdok log --tool "<agent name>" "<what>" --outcome "<what the user did with it>"`. Required by most schools; it renders into the AI-usage section automatically.
- Before saying you are done: run `dokdok check` (and `dokdok check --final` before submission) and fix every ✖.
- Render with `dokdok render` → `out/`. Never edit files in `out/`.
