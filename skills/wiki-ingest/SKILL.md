---
name: wiki-ingest
description: "Use when a PR merged, a doc changed, or a significant discovery was made and the durable knowledge should be captured into the wiki. Triggers: 'ingest this into the wiki', 'update the wiki with...', 'record this in the wiki', 'document this finding'."
---

# wiki-ingest

**Dry-run:** if invoked with `--dry-run` (or "dry run" / "plan"), do all the analysis
and output a CHANGE PLAN — every file you would create or modify, each with a one-line
summary (and a proposed diff for edits to existing files) — then STOP. Write nothing,
commit nothing. The user reviews and re-runs without `--dry-run` to apply.

1. Read the source (PR diff, doc, log output).
2. Route the knowledge: which existing page, or a new page? Domain facts only —
   personal preferences go to auto-memory, never the wiki.
3. Before writing a fact, grep the target page/topic for an existing claim. If the new
   knowledge contradicts or updates it, rewrite the old claim out and place the new fact
   where it was — clean, NO inline strikethrough or stale-block. The old value is recoverable
   via `git log -p <page>`; leaving it inline is the page-bloat failure this protocol fixes.
4. Update the page(s) in dense AI-optimized form; maintain cross-links. If you added a page,
   declare it in index.md.
5. Append one log line: `## [YYYY-MM-DD] supersede | <subject>` when the ingest changed an
   existing fact, else `## [YYYY-MM-DD] ingest | <source>` (purely additive). One line only —
   no notes or output under it.
6. EXIT GATE: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wiki_lint.py --wiki .claude/wiki --repo .`
   and fix any errors before finishing.
