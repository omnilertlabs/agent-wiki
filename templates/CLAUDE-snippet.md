## Wiki
Project/domain knowledge for this repo lives in `.claude/wiki/`, managed by the
`agent-wiki` plugin.

Follow the rest of this section only when the plugin is active in your session — its
"AGENT-WIKI ROUTING RULES" notice appears at session start, and `wiki-*` skills are in
your skill list. When it is not active, ignore `.claude/wiki/` entirely: do not read it,
cite it, or write to it.

When active, read `.claude/wiki/index.md` before acting on any task, then the pages
relevant to your task. The wiki is the single source of truth for project/domain
knowledge. Full method: the plugin's PROTOCOL.md.
Ingest durable discoveries; Query answers from the wiki; run wiki-lint before release.
