---
name: wiki-migrate
description: "Use to normalize an EXISTING wiki that predates the standard or has drifted, bringing it to the agent-wiki layout. Triggers: 'migrate the wiki', 'normalize the wiki', 'bring this wiki up to standard', 'fix the wiki structure'."
---

# wiki-migrate

**Dry-run:** if invoked with `--dry-run` (or "dry run" / "plan"), do steps 1–2 (read +
audit) and output a CHANGE PLAN — every file you would create or modify, each with a
one-line summary and a proposed diff — then STOP without writing or committing. This is
the audit-before-you-commit path. (Without `--dry-run`, step 3 still proposes before
rewriting, but `--dry-run` guarantees a no-write report you can review in full.)

1. Read the existing wiki. Identify deviations from PROTOCOL.md (missing index
   manifest entries, non-standard log format, pages not cross-linked, protocol prose
   sitting in CLAUDE.md instead of pointing at the plugin).
2. Audit for knowledge stored OUTSIDE the wiki — the most common drift:
   - `.claude/agents/*` persona files: these should define ROLE/BEHAVIOR and point at
     the wiki (e.g. "read contracts.md"), NOT duplicate domain facts. Flag any embedded
     domain knowledge, and especially STALE facts that contradict the wiki (e.g. a
     persona hardcoding an old contract value). Cross-check persona claims against the
     wiki pages they reference.
   - Stray memory/notes files (MEMORY.md, notes*.md, scratch*.md, ad-hoc docs) holding
     domain knowledge that belongs in the wiki.
   - **Per-project auto-memory** at `~/.claude/projects/<ENCODED>/memory/`. The encoded
     dir name is the repo's ABSOLUTE path with every `/` and `_` replaced by `-` — so it
     **begins with a leading `-`** (the path starts with `/`). DON'T hand-guess it; compute
     it from the repo root:
     ```
     dir="$HOME/.claude/projects/$(cd <repo> && pwd | sed 's#[/_]#-#g')/memory"
     ls -la "$dir" 2>/dev/null   # if empty, fall back to: ls ~/.claude/projects/ | grep <reponame>
     ```
     e.g. `/home/u/my_app` → `~/.claude/projects/-home-u-my-app/memory/`.
     This store is per-user and NOT in git. Flag `project_*` / domain-shaped entries (facts
     about the system) for wiki ingest; LEAVE `user_*` / `feedback_*` / preference entries
     in memory. Propose ingest — never move personal memory into the shared wiki.
3. Propose the changes to the user BEFORE rewriting (this operation edits existing
   knowledge — confirm before destructive normalization). Include persona/stray-file
   findings in the proposal.
4. On approval, normalize: rebuild index.md as a complete manifest, normalize log.md to pass the ERROR-level discipline checks (one `## [date] op | subject`
   line per entry; strip body content — migrate any genuine durable fact into a page via normal
   routing, never silently delete knowledge; sort into non-decreasing date order; fix or drop
   invalid ops; shorten over-length subjects),
   replace the CLAUDE.md protocol prose with the thin snippet (replace only that section —
   don't clobber other CLAUDE.md content), point personas at the wiki, and reconcile any
   stale embedded facts to the wiki SSOT (move the fact into the relevant wiki page; leave
   the persona referencing it).
5. **Fix `.claude/settings.json` — enable the plugin without losing anything.** This step
   also REPAIRS repos migrated by older plugin versions, so re-running migrate self-heals:
   - End state: `enabledPlugins` is an OBJECT/record — `{ "agent-wiki@omnilert-plugins": true, …others… }`. Add the agent-wiki entry if missing.
   - **Legacy array → record:** if `enabledPlugins` is an ARRAY (old form, rejected by
     current Claude Code / `/doctor`), convert it to the record object, keeping every
     existing entry as `"name@marketplace": true`.
   - **Merge, never overwrite:** preserve every other top-level key in the file.
   - **Suspected-overwrite recovery (data loss):** if the file now contains essentially only
     `enabledPlugins`, check whether it used to hold more, and restore from git if so:
     ```
     git log -p -- .claude/settings.json                    # did an earlier commit have permissions/hooks/env/etc.?
     git show <pre-migrate-commit>^:.claude/settings.json   # the lost content
     ```
     Merge any lost keys back in (alongside the agent-wiki entry). Note: `settings.local.json`
     was never affected by the bug — leave it alone.
   - If `settings.json` is absent, create it with just the agent-wiki record entry.
6. Run the linter; resolve all errors and report remaining warnings.
7. Append a `migrate` line to log.md.
