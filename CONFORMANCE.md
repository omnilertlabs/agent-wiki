# Linter Conformance Contract

Behavior contract for ports of `scripts/wiki_lint.py` (Tier 1). The Python
implementation in this repo is the reference; where a ruling notes the reference
was previously divergent, the ruling — not the old behavior — is normative.
Rulings issued 2026-08-18 by the reference maintainer, in response to measured
divergences from in-flight Go and Node ports.

## Matching contract

- **In-spec input:** implementations must agree on the full issue set — `(code,
  severity)` per finding, anchored to the same file and line.
- **Out-of-spec input** (violates the grammar below): implementations must emit
  **at least one ERROR anchored to the offending line/construct**; the exact code
  is unspecified. Example: a non-ASCII op is `log-op` in the reference (Unicode
  `\w` matched, membership check failed) and `log-body` in an ASCII port (entry
  regex failed). Both are conforming.
- Conformance corpora should encode must-accept / must-reject plus the in-spec
  issue sets, not incidental reference behavior.

## Rulings

### 1. Line termination — LF, with CRLF tolerance
A log line terminates at `\n`; one immediately preceding `\r` is stripped. No
other character is a line terminator. Control characters (FF, VT, FS, GS, RS,
NEL, LS, PS) have no structural meaning and may appear inside a subject.
*History:* the reference used Python `splitlines()` (nine separators) and
rejected e.g. a form feed inside a subject; that behavior was incidental and is
removed. Ports must not implement the nine-separator splitter.

### 2. Log-entry grammar — ASCII by design
`## [YYYY-MM-DD] <op> | <subject>` where the date is ASCII `[0-9]`, the op is
ASCII lowercase from `ingest | query | supersede | migrate | compact`, and the
subject is any non-empty text to end-of-line. Unicode digits in the date are
**must-reject** (the reference previously mis-accepted them via Python's
Unicode `\d`). Date order uses lexicographic comparison of the ASCII date
string (equivalent to chronological for valid dates); dates are non-decreasing.

### 3. Subject length — Unicode code points
`log-subject` fires when the subject exceeds 80 **Unicode code points** — not
bytes (Go: `utf8.RuneCountInString`, not `len`).

### 4. Special files — infrastructure, not pages
`index.md`, `log.md`, `log-archive.md` are not topic pages: excluded from page
discovery, never *declared* in the index (an index link to one is navigation
and does not create a `dangling-index-entry`), and always **valid link
targets** from any page. *History:* the reference previously emitted false
`broken-wiki-link` / `dangling-index-entry` for references to `log-archive.md`;
incidental, fixed.

### 5. Flat wiki — enforced by detection, not recursion
The wiki is flat by design (the index manifest is the hierarchy; bare-name
cross-links and special-file recognition depend on a flat namespace). Page
discovery is non-recursive. Any `.md` file in a subdirectory of the wiki dir is
a `nested-pages` ERROR naming the un-inspected files. Recursive support is out
of scope for the standard; a nested layout is a deliberate fork, not a pending
feature.

### 6. Index targets — bare or diagnosed
A local `.md` index target containing `/` is an `index-target-not-bare` ERROR.
*History:* such targets were previously discarded silently and validated by
nothing.

### 7. Code-ref heuristic — scope is deliberate
`dead-code-ref` inspects **backtick spans only** (anywhere in a page, including
inside HTML comments), and only tokens that contain `/`, end in an extension,
and are repo-relative (no leading `/` or `~`, no `<placeholders>`, no
whitespace). Out of scope by design: dotted symbols (`Type.Method` — needs
language awareness), bare directory refs (`pkg/dir/`), and un-backticked paths
in page metadata. Tip: backtick the paths in metadata conventions and they are
checked for free.

### 8. Out of core scope
Recursive wikis (ruling 5); provenance-as-admission (claims without code
anchors are first-class — see PROTOCOL.md reconcile's no-code-anchor
escalation path); symbol resolution; warning suppression/baselines (the
sanctioned CI postures are `--strict` on a warning-clean wiki, or errors-only
by omitting `--strict`).
