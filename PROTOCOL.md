# Agent-Wiki Protocol

The wiki is the single source of truth for project/domain knowledge. It lives at
`.claude/wiki/` and is committed to git so the whole team shares it.

## Layout
- `index.md` — the manifest. Declares every page in a table (Page | Contents).
- `<topic>.md` — dense, AI-optimized topic pages. One clear topic each.
- `log.md` — append-only journal. Lines: `## [YYYY-MM-DD] <op> | <subject>`.
- `log-archive.md` — overflow for compacted log entries (same format, created by wiki-compact
  when log.md exceeds 200 entries). Linted for structure but exempt from the size warning.
- `<topic>-history.md` — an OPTIONAL archive page holding a topic's superseded reasoning trail:
  rejected approaches, measurements that were later overturned, and why. **Reconcile-exempt** —
  see below. Use one when a topic page's history is worth keeping but would bury the current
  state; the live page stays lean and links to it.

## Write discipline per file
- `log.md` is the **only** append-only file. One line per operation:
  `## [YYYY-MM-DD] <op> | <subject>`. No bodies, bullet notes, test output, or nested
  content. Ops: `ingest | query | supersede | migrate | compact`. Dates are non-decreasing.
- Pages are **semantic knowledge, edited in place.** Never append a competing fact beside
  an old one; when a fact changes, supersede it (rewrite). Pages are not journals.
- **History pages are the ONE exception, and are exempt from reconcile.** A `*-history.md`
  page (or any page whose first 20 lines declare `ARCHIVE PAGE`) exists precisely to hold
  claims that are no longer true. Rewriting a superseded claim OUT of one destroys the record
  it was created to keep — including the evidence for why an approach was abandoned, which is
  what stops it being retried. Reconcile reads history pages (they are useful for dating a
  conflict) but never edits their CLAIMS. One narrow edit is permitted: **outward address
  repair.** Frame prose on a history page may point at live artifacts; when such an address
  goes STALE (moved, renamed, re-keyed — including a live-but-lying alias that still resolves
  on click while the target now shows different keys and searches find nothing), ANNOTATE it:
  append a dated route to the SAME artifact beside the original text, e.g.
  "*(later moved to <tracker> and renumbered — see <live-page>.md)*". Address repair only ADDS
  a route: never delete or reword the original text, never re-aim at a different artifact, and
  leave claims about the address ("mapped 1:1 to ...") untouched. Log it as `ingest` (purely
  additive). A live page must never depend on a history page for a
  CURRENT fact; if reconcile finds one that does, fix the LIVE page.
- Auto-memory holds thin personal preferences, not git — never domain facts.

**The log is the only append-only file. Pages are rewritten. Neither is a scratchpad.**
The linter enforces the log rules at ERROR level, so a malformed log blocks the next Ingest.

## Knowledge routing (where things go)
- Domain / architecture / contract / ops fact -> a wiki page (git, shared).
- Personal preference / workstyle / correction -> agent auto-memory (thin, NOT git).
- Never -> MEMORY.md bloat or stray project docs.

## Session start (before answering anything)
Run `git status --short .claude/wiki/`. If any page is modified or untracked:
1. **Surface it to the user immediately** — name the files, summarize what each uncommitted
   change contains.
2. **Do NOT assume it is someone else's WIP.** Uncommitted wiki edits are almost always a
   prior (often compacted) agent session whose Ingest never landed.
3. **Ask whether to land it before starting new work** — uncommitted wiki content is invisible
   to a fresh clone, to teammates, and to your own future self after a context compaction.
4. **Never `git reset --hard`, `git checkout --`, or `git clean` while `.claude/wiki/` is dirty**
   until it is committed or the user explicitly abandons it.

## Operations
Mutating operations (Ingest, plus the wiki-init/wiki-migrate lifecycle skills) accept
`--dry-run`: emit a change plan (files to create/modify + summaries/diffs) and STOP,
writing nothing, so the user can audit before applying.

### Ingest (agentic) — capture durable knowledge
Trigger: PR merged, doc changed, significant discovery.
1. Read the source. 2. Route to existing/new page. 3. Before writing, grep the target topic
for an existing claim; if the new knowledge **contradicts or updates** it, rewrite the old
claim OUT and put the new fact in its place — clean, no inline marker (old value stays in
git history, recoverable via `git log -p <page>`). 4. Update page(s) + cross-links; update
index.md if a page was added. 5. Append a log line: `supersede` when the net effect changed
an existing fact, else `ingest` (purely additive).
6. Run `wiki_lint.py` (Tier 1) as the exit gate — must pass with no errors.
7. **COMMIT on a branch + open a PR.** An Ingest ends with landed knowledge, not an edited
   file — an ingest left in the working tree is a LOST ingest. If you cannot push (no auth,
   detached env), say so explicitly and tell the user the knowledge is UNLANDED.

### Query (agentic) — answer from the wiki
Trigger: substantive question about the system.
1. Read index.md (the retrieval anchor). 2. Grep the wiki dir; read matching pages.
3. Answer WITH page citations. 4. If the synthesis is novel and non-obvious, file a
new page + add it to index.md. 5. Append a `query` line to log.md.
**You read the WORKING TREE, not the committed wiki.** If a page you cite is dirty per the
session-start check, SAY SO in the citation ("this section is uncommitted") — otherwise you
present unlanded work as established fact. Before a Query that will drive a decision, `git fetch`
and note whether the default branch moved; if fetch fails (auth), state that the answer is from a
possibly-stale local copy.

### Lint — verify integrity
Tier 1 (deterministic): run `python3 scripts/wiki_lint.py --wiki .claude/wiki --repo .`.
Errors: undeclared-page, dangling-index-entry, index-target-not-bare, broken-wiki-link,
nested-pages, log-body, log-order, log-op. Warnings: orphan-page, dead-code-ref,
log-subject, log-size, memory-bloat. Tier 1 never writes anything — it is the exit gate
inside mutating ops and runs in CI. Ports of the linter follow CONFORMANCE.md.
Tier 2 (agentic, on request): gaps (topics lacking a page), staleness vs code,
oversized pages, cross-page contradictions (delivered by the wiki-compact `reconcile` sweep),
knowledge stored outside the wiki (`.claude/agents/*` personas, stray
memory/notes files, or the per-project auto-memory at `~/.claude/projects/<ENCODED>/memory/`
— the dir is the repo's absolute path with `/` and `_` replaced by `-`, so it has a
**leading `-`**; compute it as `~/.claude/projects/$(pwd | sed 's#[/_]#-#g')/memory`. Domain
facts there belong in the wiki; personas reference it and `user_*`/`feedback_*` preference
memory stays), and — rarely — extending wiki_lint.py with a new check kind.
A completed Tier 2 sweep records itself as a `query` log line (e.g.
`## [YYYY-MM-DD] query | tier2 deep lint — N findings`) so sweep recency is answerable;
any fixes the sweep makes log additionally as their own ops. Findings whose fix is
genuinely deferred route to the team's work tracker — the wiki holds knowledge, not tasks.

### Compact & reconcile (agentic) — keep memory lean
Trigger: wiki_lint reports `log-size`, or facts have drifted into conflict. Run the
`wiki-compact` skill (`--dry-run` to preview).
- **reconcile:** find claims that are SUPERSEDED or IN CONFLICT — within a page and across
  pages. Stale = conflicting, NOT old (there is no age signal). For a figure stored with a
  recipe (see Figures), recompute per the recipe: a mismatch is a conflict with the source
  of truth even with no competing claim; a FROZEN dated measurement is never recomputed
  into a "correction" — a new measurement supersedes it explicitly or not at all.
  Arbitrate with `git log`/
  `git blame` recency + verification against code; code-backed wins, else newer; a genuine
  tie with no code anchor is escalated to the user. Resolve via the supersession protocol
  (clean rewrite, `supersede` log op). This is the agentic cross-page contradiction check.
- **compact-log:** when `log.md` exceeds 200 entries, move the oldest into `log-archive.md`,
  keeping the 100 most recent; append a `compact` log line. Nothing is deleted.

## Page format
Dense, structured, token-efficient markdown. Cross-link related pages. Not prose.
Backticked repo-relative paths are validated (dead-code-ref), so write illustrative or
made-up example paths with `<placeholder>` segments — the linter skips those by design;
a realistic-looking fake path fires the check from the page that defines it.

## Figures (counts, sizes, timings, versions, line numbers)
A figure differs from a claim: it can be RE-DERIVED, which gives it a staleness signal
claims lack — recompute and compare. State every figure as one of three kinds:
- **Derive-on-demand** — store the procedure, not the value, when derivation is cheap
  (a command, a query, a script). Most figure drift comes from storing what could be derived.
- **Stored with recipe** — value + derivation recipe + date, kept together. The recipe makes
  a lone figure falsifiable: reconcile may recompute it, and a mismatch is a CONFLICT with
  the source of truth even when no competing claim exists. (The backticked-path convention
  generalized: a stored reference carries its own checkability.) A bare figure with no
  recipe is unverifiable — treat it as an ordinary claim.
- **Frozen measurement** — a dated record of a past event ("measured N on DATE with
  INPUTS"). Recomputing produces a NEW measurement that may supersede it explicitly; it
  never silently "corrects" the old one. Reference results (below) are the live-page
  instance; superseded measurement trails belong in a history page.
"Stale = conflicting, NOT old" stands: age is still not a signal. Recomputability is how a
figure's conflict is DETECTED — including the self-consistent table that agrees with itself
and disagrees with the world.

## Reproducible procedures (configs, runs, benchmarks)
When a page documents something an agent will RE-RUN (env vars, CLI flags, per-dataset inputs,
acceptance numbers), documenting it is not enough — a doc that CAN be silently ignored WILL be:
- Make the validated values the **code defaults**, so a bare run reproduces the reference.
- Provide **one runner script** that encodes the config + inputs; point the page at it.
- State the **reference results to reproduce BEFORE trusting any A/B**, and name the exact
  inputs (e.g. which ground-truth file) — including which inputs are NOT valid.
