# Changelog

<!-- Merge to main is the release, so version headers carry no dates: a release's date
     is derivable on demand from git (the merge commit of its version-bump PR, e.g.
     `git log --merges --date=iso-strict --format='%cd %s' -- .claude-plugin/plugin.json`),
     quoted in UTC — GitHub's merged_at and git's committer-local dates disagree across
     midnight. A stored date can't be known before the merge lands and goes stale if it
     slips. -->

## 0.2.12

### Added

- `wiki-uninstall` skill and `/wiki-uninstall` command — reverses `wiki-init`.
  Removes the `## Wiki` section from CLAUDE.md and the `enabledPlugins` entry
  from `.claude/settings.json`, and reports anything it deliberately left alone
  (wiki links in history, CI steps calling `wiki_lint.py`). Defaults to
  *detaching*: `.claude/wiki/` is kept on disk unless full removal is asked for
  explicitly, since those pages may be the only copy of what they record.
  Until now the plugin had an install path and no teardown.

### Fixed

- `templates/CLAUDE-snippet.md` now gates its instructions on the plugin being
  active in the session. The snippet is appended to a repo's CLAUDE.md by
  `wiki-init` and is version-controlled, so it outlived the plugin: disabling or
  uninstalling stopped the SessionStart hook but left an unconditional "read
  `.claude/wiki/index.md` before acting on any task" in force. Agents kept
  reading and citing the wiki with no way to turn it off short of editing
  CLAUDE.md by hand — including during the uninstall/reinstall upgrade the
  README documents, which every upgrade without auto-update goes through. The
  gate keys on two things an agent can observe for itself: the "AGENT-WIKI
  ROUTING RULES" notice and the presence of `wiki-*` skills.

  Existing repos keep the old snippet until it is replaced — `wiki-init`
  appends and never rewrites. `wiki-uninstall` removes it; the current text is
  in `templates/CLAUDE-snippet.md`.

## 0.2.11

### Changed

- `PROTOCOL.md` Figures: the marker forms are now pinned, requested by a
  downstream adopter building a docs-side figure checker on the wiki
  convention. Stored-with-recipe: `<value> (recipe: <command-in-backticks>,
  as of YYYY-MM-DD)`; a backticked recipe is runnable, a prose recipe is
  descriptive (agent-only) — backticks are the checkability discriminator,
  as for paths. Derive-on-demand has no marker (the backticked command
  stands where the number would); frozen keeps its sentence shape
  ("measured N on YYYY-MM-DD with `INPUTS`"), distinguished from
  stored-with-recipe by phrasing. No linter behavior change.

## 0.2.10

Ruling-7 (`dead-code-ref`) revision, from a downstream adopter's conformance
review: the reference diverged from ruling 7's own text in two places, and one
piece of existing behavior was undocumented. No new checks; a conforming wiki's
verdicts change only where a page carries out-of-spec tokens.

### Fixed

- **`..` path segments are no longer resolved against the host.** A backticked
  `../sibling/x.py` (or `docs/../../x.py`) was checked via `repo_root / ref`,
  which walks out of the repo — so the warning count depended on which sibling
  checkouts existed on the machine. Any token with a `..` path segment (segment
  equality, not substring) is now not checkable, like leading `/` and `~`.
- **Any whitespace character disqualifies a span**, not only a literal space.
  A tab or CR inside a span was previously checked as one path and produced a
  false `dead-code-ref`.

### Changed

- CONFORMANCE ruling 7 consolidated: repo-relative means no leading `/` or `~`,
  no `..` segment, no `<placeholders>`, no whitespace of any kind; resolution is
  against the working tree relative to the repo root; the `:N` / `:N-M` line
  suffix is documented as decoration — stripped and never validated (a stale
  line number is an authoring concern per PROTOCOL's Figures section, not a
  linter finding); shorthand and pattern notation (`file.ts` for `src/file.ts`,
  `{a,b}.md`) are named out of scope — out-of-spec notation is fixed in the
  page, not blessed by the linter.
- Changelog header: release dates are quoted in UTC (GitHub's `merged_at` and
  git's committer-local dates disagree across midnight).

## 0.2.9

Conformance follow-ups from port testing (found by a downstream Node port).

### Fixed

- **The CLI no longer treats a lone CR as a line terminator.** Log files are
  now read byte-preserving (`newline=""`); through 0.2.8, Python's default
  universal-newlines read translated a lone `\r` to `\n` before the checker
  ran, so the CLI reported one `log-body` error per CR-separated fragment
  while the checker itself — correctly, per CONFORMANCE ruling 1 — saw one
  line. Byte-verbatim ports were already conforming.

### Added

- `PROTOCOL.md` gains a **Figures** section (proposed from field experience by
  a downstream adopter): every figure is derive-on-demand (store the
  procedure, not the value), stored-with-recipe (value + recipe + date — the
  recipe makes a lone figure falsifiable), or a frozen dated measurement
  (superseded explicitly by a new measurement, never silently "corrected").
  Reconcile (protocol and wiki-compact skill) now recomputes recipe-bearing
  figures — a mismatch is a conflict with the source of truth even when no
  competing claim exists. "Stale = conflicting, NOT old" is unchanged: age is
  still not a signal; recomputability is a detection mode for conflict.
- **Outward address repair** — the one permitted edit on a history page
  (ruled on a live downstream case): when archive-page frame prose points at a live
  artifact whose address went stale (moved/renamed/re-keyed, including an
  alias that still resolves on click but fails search), append a dated route
  to the SAME artifact beside the original text. Additive only — never delete
  or reword the original, never re-aim at a different artifact; claims stay
  frozen. Logged as `ingest`. In PROTOCOL.md and the wiki-compact skill, in
  parity.

### Changed

- CONFORMANCE ruling 1 wording amended to match intended (and reference)
  behavior: a line terminates at LF **or at end-of-input**, and one CR
  immediately preceding the terminator is stripped — so a final unterminated
  line ending in a bare CR does not count that CR toward the subject length.
  The read layer is explicitly inside the contract.
- Changelog version headers no longer carry dates or "unreleased" markers:
  merge-is-release means the date is unknowable before landing and stale
  after slipping (0.2.8 shipped reading "unreleased"). Per this release's own
  Figures rule, the date is derive-on-demand — the header comment states the
  git derivation.

## 0.2.8

Linter behavior release: aligns `wiki_lint.py` with the new `CONFORMANCE.md`
contract written for the ports of the linter to other languages. Some wikis
that passed under 0.2.7 will fail under 0.2.8 — the new failures are listed
first.

### Upgrade impact — new ERRORs you may see

- **`nested-pages`** (new check): any `.md` file in a subdirectory of
  `.claude/wiki/` is now an ERROR. Previously a nested wiki was silently
  half-inspected (nested pages skipped entirely) while reporting misleading
  errors. The standard is flat by design; fix by prefix-flattening
  (`bugs/foo.md` → `bugs-foo.md`) with the index table carrying the grouping.
- **`index-target-not-bare`** (new check): a local `.md` link target in
  `index.md` that contains `/` is now an ERROR. Previously such targets were
  silently discarded and validated by nothing.
- **Unicode digits in log dates are now rejected.** `## [YYYY-MM-DD] ...`
  requires ASCII `[0-9]`; a date written with e.g. Arabic-Indic digits
  previously passed by accident (Python's Unicode `\d`) and now fails as
  `log-body`.

### Fixed — false errors removed

- Linking to `log-archive.md` from any page no longer reports a false
  `broken-wiki-link`; an `index.md` link to `log.md` or `log-archive.md` no
  longer reports a false `dangling-index-entry`. These files are
  infrastructure: always valid link targets, never page declarations.
- A form feed (or other non-LF control character) inside a log subject no
  longer rejects the log. Lines terminate at LF (CRLF tolerated); other
  control characters have no structural meaning.

### Added

- `CONFORMANCE.md` — the linter's behavior contract for ports (Go/Node in
  progress), including the in-spec/out-of-spec matching rules.
- `wiki-lint` skill: the Tier 2 checklist gains the contradiction check
  (within-page and cross-page), delegating to the `wiki-compact` reconcile
  procedure — `PROTOCOL.md` listed it but the skill omitted it.
- `PROTOCOL.md`: a completed Tier 2 sweep records itself as a `query` log
  line, so "when was this wiki last swept" has a positive answer; findings
  whose fix is deferred route to the team's work tracker, not the wiki.
- `PROTOCOL.md` page format: write illustrative example paths with
  `<placeholder>` segments — a realistic-looking fake path fires
  `dead-code-ref` from the very page that uses it as an example.

### Changed

- Log-entry grammar is ASCII by design (`[0-9]` dates, `[a-z]` ops). A
  non-lowercase op (e.g. `Ingest`) now fails as `log-body` instead of
  `log-op` — still an ERROR either way.
- Documented (no Python behavior change): the 80-char `log-subject` limit is
  measured in Unicode code points, not bytes.

## 0.2.7

Initial public release.
