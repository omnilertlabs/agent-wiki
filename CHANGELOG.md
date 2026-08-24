# Changelog

## 0.2.9 — unreleased

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

### Changed

- CONFORMANCE ruling 1 wording amended to match intended (and reference)
  behavior: a line terminates at LF **or at end-of-input**, and one CR
  immediately preceding the terminator is stripped — so a final unterminated
  line ending in a bare CR does not count that CR toward the subject length.
  The read layer is explicitly inside the contract.
- Stamped the 0.2.8 release date below (it shipped reading "unreleased").

## 0.2.8 — 2026-08-24

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

## 0.2.7 — 2026-08-17

Initial public release.
