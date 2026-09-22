# dokdok install (written for agents)

You are installing dokdok for the user. Do each step, read errors, adapt.

1. Detect: OS, which agent you are (Claude Code / Codex / pi / other), whether
   `uv`, `pipx`, `brew`, `pandoc` exist.
2. Install the CLI:
   - `uv tool install git+https://github.com/isaaclins/dokdok` (preferred), or
   - `pipx install git+https://github.com/isaaclins/dokdok`.
   Install pandoc if missing (`brew install pandoc` / distro package).
   `dokdok doctor` must show ✔ for pandoc.
3. Install the skill for *your* agent:
   - Claude Code → `claude plugin marketplace add isaaclins/dokdok && claude plugin install dokdok@dokdok`
     (or copy the repo's `skills/dokdok/` folder to `~/.claude/skills/dokdok/`)
   - Codex → copy the repo's `skills/dokdok/` folder to `~/.codex/skills/dokdok/`
   - pi → `pi install git:github.com/isaaclins/dokdok`
   (Clone the repo to a temp dir to get the folder if needed.)
4. Verify: in a temp dir, `dokdok new smoke --type school-thesis && cd smoke && dokdok render`.
   A `out/smoke.docx` must appear. Delete the temp dir.
5. Tell the user in one sentence what was installed and that they can now say
   things like "I need to write my thesis / final report / a pentest report".
   Do not explain the internals.

To update: repeat step 2 with `--force` / `pipx upgrade` and step 3.
To uninstall: `uv tool uninstall dokdok` (or `pipx uninstall dokdok`) and remove the skill folder.
