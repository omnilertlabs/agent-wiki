---
name: wiki-query
description: "Use when answering a substantive question about how this system works, its architecture, contracts, ops, or history. Triggers: 'how does X work', 'what is the contract for Y', 'check the wiki for...', 'according to the wiki...'. Answers from the wiki with page citations."
---

# wiki-query

1. Read .claude/wiki/index.md — the retrieval anchor; its Contents column maps
   keywords to pages.
2. Grep the wiki dir for your keywords; read the matching pages.
3. Answer WITH page citations (e.g. "per arch.md, ...").
4. If your synthesis is novel and non-obvious, file it as a new page and add it to
   index.md (this is an ingest).
5. Append `## [YYYY-MM-DD] query | <topic>` to log.md.
