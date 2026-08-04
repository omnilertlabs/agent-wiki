---
name: wiki-lint
description: "Use when asked to lint the wiki, check the wiki for broken links or dead references, verify wiki integrity, find orphan pages, or check whether the wiki is consistent/up to date. Runs the deterministic structural linter (Tier 1) and, with --deep, the agentic semantic checks (Tier 2)."
---

# wiki-lint

## Tier 1 (deterministic — always run first)
Run: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/wiki_lint.py --wiki .claude/wiki --repo .`
Add `--memory-file <path>` to also check MEMORY.md thinness. Add `--strict` for CI.
Report the errors and warnings verbatim. Errors must be fixed before release.

## Tier 2 (agentic — only when the user asks for a deep lint)
Read every wiki page and assess:
- Gaps: topics referenced across pages but lacking a dedicated page.
- Staleness: claims that contradict current code (spot-check with grep/read).
- Oversized pages that should be split.
- Knowledge stored outside the wiki: scan `.claude/agents/*` persona files, stray
  memory/notes files, AND the per-project auto-memory at
  `~/.claude/projects/<ENCODED>/memory/` (the dir is the repo's absolute path with `/` and
  `_` replaced by `-`, so it has a **leading `-`**; compute it:
  `ls "$HOME/.claude/projects/$(pwd | sed 's#[/_]#-#g')/memory"`). Flag embedded domain
  knowledge and persona facts that
  contradict the wiki (e.g. a hardcoded contract value the wiki has since changed), and
  domain-shaped `project_*` memory entries. Domain facts belong in the wiki SSOT;
  personas reference it, and `user_*`/`feedback_*`/preference memory stays put.
- Linter-evolution (rare): if a genuinely new KIND of invariant should be enforced
  mechanically, extend scripts/wiki_lint.py with a new check + test, then it
  propagates to all repos on the next plugin version bump.
