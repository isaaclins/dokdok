---
name: interview
description: Write the thesis introduction (motivation, research questions, methods) by asking the student the guideline's questions in chat, then drafting from their answers. Use when the introduction is empty or the student says they don't know how to start.
---

# Interview the student, then draft the introduction

The introduction must be in the student's own words and cover: personal motivation,
aim and research questions, approach and methods. Don't guess any of it — ask.

1. Ask **one question at a time**, in plain language, and wait for the answer:
   - What is your topic, and why this one — what's your personal connection?
   - What do you want to know at the end? (aim, one sentence)
   - Which 2–4 concrete questions will the thesis answer?
   - How will you find out — reading, an interview, an experiment, a survey, your own experience?
     (the guideline requires at least two methods)
2. Draft `doc/01-introduction.md` from the answers. Keep their phrasing where it works;
   fix grammar, don't change meaning. Leave `[placeholders]` for anything they didn't say.
3. Show the draft, ask what's wrong, revise once.
4. `dokdok log --tool "<you>" "Drafted the introduction from an interview with the student" --outcome "…"`
   and `dokdok check`.
