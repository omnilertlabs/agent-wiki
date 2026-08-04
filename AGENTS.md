# agent-wiki (generic agent instructions)

This repository defines the **agent-wiki** standard. The complete, tool-agnostic method
is in `PROTOCOL.md` (same directory) — read it. This file is the entry point for agents
that read `AGENTS.md` (e.g. Codex and other CLIs).

For any repo you work in:

- **Read `.claude/wiki/index.md` first.** The wiki is the single source of truth for
  project / domain knowledge.
- **Knowledge routing:** domain / architecture / contract / ops facts → a wiki page
  (git, shared); personal preferences → your own memory; never stash domain facts in
  stray docs or agent persona files.
- **Lint** with the bundled linter (standard-library Python, no dependencies), pointing
  at wherever this repo is checked out:
  `python3 <agent-wiki>/scripts/wiki_lint.py --wiki .claude/wiki --repo .`
- **Operations** (Ingest / Query / Lint), page format, and the `--dry-run` preview
  behavior are all described in `PROTOCOL.md`.

Claude Code users get this automatically as a plugin (skills, slash commands, a
SessionStart hook). Other agents follow `PROTOCOL.md` and run the linter directly.
