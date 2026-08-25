---
name: wiki-compact
description: "Use to keep the wiki lean: reconcile superseded/conflicting facts and roll an oversized log into the archive. Triggers: 'compact the wiki', 'reconcile the wiki', 'the log is too long', 'clean up stale or conflicting facts', or when wiki_lint reports log-size."
---

# wiki-compact

Two maintenance operations. With no argument, run both. `reconcile` runs only the conflict
sweep; `compact-log` runs only the log compaction.

**Dry-run:** if invoked with `--dry-run` (or "dry run" / "plan"), do all analysis and output
a CHANGE PLAN — every conflict found with its proposed rewrite diff, and the log entries that
would move to the archive — then STOP. Write nothing, commit nothing.

## reconcile — resolve superseded/conflicting facts

Stale means SUPERSEDED or IN CONFLICT, not old. Do NOT use dates/age as the signal.

**⛔ HISTORY PAGES ARE EXEMPT — never edit them.** A page named `*-history.md`, or one whose
first 20 lines declare `ARCHIVE PAGE`, exists to hold claims that are no longer true: rejected
approaches, overturned measurements, and the reasoning behind both. A superseded claim there is
the CONTENT, not a defect. Rewriting it out destroys the record — including the evidence for why
an approach was abandoned, which is what stops someone retrying it. READ them (they are the
fastest way to date a conflict and to see whether a claim was already overturned once), but every
rewrite lands on a LIVE page. If a live page depends on a history page for a CURRENT fact, that is
the defect — fix the live page.
ONE additive edit is allowed on a history page (PROTOCOL.md, outward address repair): when its
frame prose points at a live artifact whose address went stale — moved/renamed/re-keyed,
including an alias that still resolves on click but no longer matches what the target shows —
append a dated route to the SAME artifact beside the original text. Never delete or reword the
original, never re-aim at a different artifact, leave claims about the address untouched. Log as
`ingest`.

1. Read `index.md`; enumerate declared pages.
2. Find claims that conflict or are superseded — WITHIN each page, and ACROSS pages. Use
   cross-links to choose which page-pairs to compare; don't naively compare every pair.
   Skip history pages as EDIT targets (above); a live-vs-history disagreement is expected and
   is not a conflict. For a figure stored with a recipe (PROTOCOL.md, Figures), recompute
   per the recipe — a mismatch is a conflict with the source of truth even when no competing
   claim exists. A FROZEN dated measurement ("measured N on DATE ...") is a record, not a
   present-state assertion: never recompute it into a "correction"; a new measurement
   supersedes it explicitly or the old one stands.
3. Arbitrate each conflict:
   - `git log -p <page>` / `git blame` on the conflicting lines → which claim is newer.
   - Verify both claims against the code / source of truth.
   - Winner = code-backed; else the newer one. A genuine tie with no code anchor → STOP and
     ask the user. Never guess.
4. Resolve via the supersession protocol: rewrite the losing claim OUT cleanly — NO inline
   strikethrough or stale-block (old value stays in git history). Fix any cross-links that
   referenced the removed claim. Append `## [YYYY-MM-DD] supersede | <subject>` to log.md.

## compact-log — roll an oversized log into the archive

1. Count entries (`## [date] op | subject` lines) in `log.md`. If 200 or fewer, no-op.
2. Move the OLDEST entries into `log-archive.md` (create it if absent, with a `# Wiki Operation
   Log (archive)` title; append preserving chronological order) until `log.md` holds the 100
   most recent entries. Keep the title + guidance comment at the top of `log.md`.
3. Preserve each entry's exact text; do not reword subjects.
4. Append `## [YYYY-MM-DD] compact | rolled N entries to archive` to log.md.

## Exit gate

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wiki_lint.py --wiki .claude/wiki --repo .` and fix
any errors — both `log.md` and `log-archive.md` must pass. Then on a real run (not --dry-run), COMMIT on a branch + open a PR
(an unlanded compaction is a lost compaction).
