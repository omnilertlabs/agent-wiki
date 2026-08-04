#!/usr/bin/env python3
"""SessionStart hook: inject agent-wiki routing rules into context.

Also performs the DIRTY-WIKI CHECK. The hook fires on `startup|clear|compact`, and the
compact case is exactly when an agent loses awareness that `.claude/wiki/` has uncommitted
edits from an earlier (now-summarized) part of its own session. Uncommitted wiki content is
invisible to git, to a fresh clone, and to the agent's future self — it gets cited as if it
were committed, and it gets destroyed by routine `git reset --hard` cleanup. Surfacing it
here makes the check enforced rather than merely documented.

Never fails a session: any git/env problem degrades to printing the routing rules only.
"""
import subprocess

WIKI = ".claude/wiki"

print(
    "AGENT-WIKI ROUTING RULES (from agent-wiki plugin):\n"
    "- Read .claude/wiki/index.md before acting on any task; it is the single "
    "source of truth for project/domain knowledge.\n"
    "- Knowledge placement:\n"
    "    * Domain / architecture / contract / ops fact -> a wiki page (git, shared).\n"
    "    * Personal preference / workstyle / correction -> agent auto-memory (thin, not git).\n"
    "    * Never put domain knowledge in MEMORY.md or stray project docs.\n"
    "- Ingest durable discoveries into the wiki; Query answers from it with citations.\n"
    "- Full method: the agent-wiki plugin PROTOCOL.md."
)


def dirty_wiki_paths():
    """Porcelain entries under the wiki dir, or [] if unavailable (not a repo, no git, no wiki)."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", WIKI],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


entries = dirty_wiki_paths()
if entries:
    shown = entries[:10]
    more = len(entries) - len(shown)
    print(
        "\nUNCOMMITTED WIKI CHANGES DETECTED (" + str(len(entries)) + " path(s)):\n"
        + "\n".join("    " + e for e in shown)
        + (f"\n    ... and {more} more" if more else "")
        + "\n"
        "- SURFACE THIS TO THE USER NOW — name the files and summarize what each change contains.\n"
        "- Do NOT assume it is someone else's WIP. Uncommitted wiki edits are almost always a\n"
        "  prior (often compacted) agent session whose Ingest never landed.\n"
        "- Ask whether to land it before starting new work; it is invisible to a fresh clone and\n"
        "  to your own future self after a compaction.\n"
        "- If you CITE a dirty page, say the section is uncommitted — otherwise you present\n"
        "  unlanded work as established fact.\n"
        "- Do NOT `git reset --hard` / `git checkout --` / `git clean` while the wiki is dirty."
    )
