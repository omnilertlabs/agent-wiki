---
name: wiki-init
description: "Use to set up a brand-new agent-wiki in a repo that does not have one yet. Triggers: 'initialize the wiki', 'set up the wiki here', 'scaffold a wiki', 'add agent-wiki to this repo'."
---

# wiki-init

**Dry-run:** if invoked with `--dry-run` (or "dry run" / "plan"), do all the analysis
and output a CHANGE PLAN — every file you would create or modify, each with a one-line
summary (and a proposed diff for edits to existing files) — then STOP. Write nothing,
commit nothing. The user reviews and re-runs without `--dry-run` to apply.

1. Create `.claude/wiki/` and copy `${CLAUDE_PLUGIN_ROOT}/templates/index.md` and
   `templates/log.md` into it.
2. APPEND `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE-snippet.md` to the repo's CLAUDE.md
   (create it if absent). Append — never overwrite existing CLAUDE.md content.
3. Enable the plugin in `.claude/settings.json` by MERGING, never overwriting the file:
   if it exists, parse the JSON and add `"agent-wiki@omnilert-plugins": true` under the
   `enabledPlugins` object (create that object if missing), preserving every other key and
   any other already-enabled plugin; if absent, create it with just that entry.
   `enabledPlugins` is an OBJECT/record (`{ "name@marketplace": true }`), NOT an array (the
   array form is rejected by current Claude Code). See `${CLAUDE_PLUGIN_ROOT}/templates/settings-snippet.json`.
4. Seed initial pages from the codebase: read the README and key sources, then create
   a few topic pages (architecture, contracts) using `templates/page.md`. Declare each
   in index.md.
5. Run the linter as the exit gate; fix errors.
6. Append an `ingest | initial wiki scaffold` line to log.md.
