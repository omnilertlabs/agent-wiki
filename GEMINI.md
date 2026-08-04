@./PROTOCOL.md

## Gemini-specific notes

You are running the **agent-wiki** standard as a Gemini CLI extension. The full method
is in PROTOCOL.md (imported above) — follow it.

- **Read `.claude/wiki/index.md` first** in any repo you work in. The wiki is the single
  source of truth for project/domain knowledge.
- **Knowledge routing:** domain / architecture / contract / ops facts → a wiki page (git,
  shared); personal preferences → your own memory; never stash domain facts in stray docs
  or agent persona files.
- **Lint** with the bundled linter (standard-library Python, no dependencies):
  `python3 ~/.gemini/extensions/agent-wiki/scripts/wiki_lint.py --wiki .claude/wiki --repo .`
  (Use `--strict` in CI; `--memory-file <path>` to also check a MEMORY.md.)
- **No slash commands or hooks under Gemini.** Perform Ingest / Query / Lint by following
  the steps in PROTOCOL.md. For a migrate/init, do the analysis and — when previewing —
  emit a change plan and write nothing (the `--dry-run` behavior), then apply on request.
