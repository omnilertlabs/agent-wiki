---
name: wiki-uninstall
description: "Use to remove agent-wiki from a repo — the CLAUDE.md snippet, the settings.json entry, and optionally .claude/wiki/ itself. Triggers: 'uninstall the wiki', 'remove agent-wiki from this repo', 'tear down the wiki', 'stop using the wiki here'."
---

# wiki-uninstall

Reverses `wiki-init`. Disabling the plugin is not enough on its own: `wiki-init`
writes into files this repo owns and version-controls, and those survive the plugin.

**Dry-run:** if invoked with `--dry-run` (or "dry run" / "plan"), do all the analysis
and output a CHANGE PLAN — every file you would modify or delete, each with a one-line
summary and a proposed diff — then STOP. Write nothing, commit nothing. The user
reviews and re-runs without `--dry-run` to apply.

**Ask before running.** Deleting `.claude/wiki/` destroys knowledge that exists
nowhere else. Establish which of the two the user wants:

- **Detach** (default) — remove the wiring, keep `.claude/wiki/` on disk. Agents stop
  using it; the pages stay readable by humans and the decision is reversible.
- **Full removal** — also delete `.claude/wiki/`. Only on an explicit, unambiguous
  request. Never infer it from "uninstall".

## Steps

1. **CLAUDE.md** — remove only the `## Wiki` section `wiki-init` appended (from the
   `## Wiki` heading to the next heading of the same level or EOF). Leave every other
   line untouched; the file is the user's, not the plugin's. If the section has been
   edited beyond recognition, show it and ask rather than guessing at its bounds.
   Check `AGENTS.md` too — a repo may symlink `CLAUDE.md` to it, in which case editing
   either edits both, so do not process the same inode twice.

2. **`.claude/settings.json`** — remove the `"agent-wiki@omnilert-plugins"` key from
   `enabledPlugins` by MERGING, never overwriting: parse the JSON, delete that one key,
   preserve every other key and any other enabled plugin. If `enabledPlugins` is left
   empty, remove the empty object rather than leaving `{}` behind.

3. **`.claude/wiki/`** — only under full removal, and only after the user has confirmed
   in this session. Before deleting, tell them what is being lost: the page count and
   the top-level titles from `index.md`.

4. **Report what was left behind.** Anything else the wiki accumulated is out of scope
   and must be named rather than silently skipped: wiki links (`[[page]]`) in commit
   messages or PR bodies, `wiki-*` references in other agent instructions, CI steps
   calling `wiki_lint.py`. List what you found; do not rewrite history.

## Exit

State plainly which of detach or full removal was performed, and what remains. If the
wiki directory was kept, say where it is and that nothing reads it any more.
