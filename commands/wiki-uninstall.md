---
description: Remove agent-wiki from this repo — snippet, settings entry, optionally the wiki itself (append --dry-run to preview)
---

Use the wiki-uninstall skill to remove `agent-wiki` from this repo. If its steps aren't in
your context after the skill loads, read the installed procedure at
`~/.claude/plugins/cache/*/agent-wiki/*/skills/wiki-uninstall/SKILL.md` and follow it. If
the arguments include `--dry-run`, follow the skill's dry-run path (emit a change plan,
write nothing). Default to detaching (keep `.claude/wiki/` on disk) unless the user has
explicitly asked for the wiki directory to be deleted. $ARGUMENTS
