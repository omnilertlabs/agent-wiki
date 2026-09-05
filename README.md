# agent-wiki

A Claude Code plugin that standardizes the agent-maintained wiki pattern
(Ingest / Query / Lint) across repos. Knowledge lives in a git-tracked
`.claude/wiki/`; the generic tooling lives here and is versioned in the
marketplace, so all repos stay on one method with no drift.

## What you get
- `PROTOCOL.md` — the method (readable by any agent, CC or not).
- `wiki_lint.py` — the only script: a generic structural linter (CI-able).
- `CONFORMANCE.md` — the linter's behavior contract, for ports to other languages.
- Skills + slash commands: `/wiki-init`, `/wiki-ingest`, `/wiki-query`,
  `/wiki-lint`, `/wiki-migrate`, `/wiki-compact`, `/wiki-uninstall` (or just ask in
  plain language).
- A SessionStart hook that injects knowledge-routing rules every session.

## Install — Claude Code (full experience: skills, slash commands, hook)
1. Add the marketplace:
   `/plugin marketplace add omnilertlabs/agent-wiki`
2. Install the plugin:
   `/plugin install agent-wiki@omnilert-plugins`
3. `/reload-plugins` (or restart).

A repo that has committed `.claude/settings.json` with
`"enabledPlugins": { "agent-wiki@omnilert-plugins": true }` enables it automatically on
clone. (`enabledPlugins` is an **object/record** mapping `name@marketplace` → `true`, not
an array — the array form is rejected by current Claude Code / `/doctor`.)

Both `/plugin marketplace add` and the Gemini install below clone the repo over git. The
repo is public, so no special access is needed — an HTTPS clone works out of the box. Test:
`git clone https://github.com/omnilertlabs/agent-wiki.git` should succeed.

### Update an installed plugin (Claude Code)
With marketplace **auto-update enabled** (recommended — and on by default if you used the
committed `.claude/settings.json` below), updating is two steps:

```
/plugin marketplace update omnilert-plugins   # refreshes the catalog AND upgrades installed plugins (auto-update)
/reload-plugins                               # activate the new version in-session (no restart)
```

Gotchas (these tripped us up, so they're worth stating):
- **`/plugin install` does NOT upgrade an already-installed plugin** — it just reports
  "already installed". There is no `/plugin update` command either.
- `/reload-plugins` only re-activates **whatever version is currently installed**; it does
  not pull a newer one. So if the install version didn't move, reload changes nothing.
- **Without auto-update**, force an upgrade by uninstall + reinstall:
  `/plugin uninstall agent-wiki@omnilert-plugins` then `/plugin install agent-wiki@omnilert-plugins`.
- **Disabling the plugin does not silence the wiki on its own.** `wiki-init` appends a
  `## Wiki` section to the repo's CLAUDE.md, and that file is version-controlled — it
  stays put when the plugin goes away. Since 0.2.12 the appended snippet gates itself on
  the plugin being active, so an agent ignores `.claude/wiki/` when it isn't. Repos that
  adopted the plugin earlier keep the old unconditional wording until it is replaced —
  `/wiki-uninstall` removes it, or copy the current text from
  `templates/CLAUDE-snippet.md`; `wiki-init` appends and never rewrites.
- **To remove the plugin from a repo**, run `/wiki-uninstall` (add `--dry-run` to preview).
  It takes out the CLAUDE.md section and the `.claude/settings.json` entry, and keeps
  `.claude/wiki/` unless you ask for it to be deleted.

Enable auto-update once via `/plugin` → **Marketplaces** → `omnilert-plugins` → **Enable
auto-update**, or commit it (see the settings snippet under "Adopt in a repo" / below):
```json
{
  "extraKnownMarketplaces": {
    "omnilert-plugins": {
      "source": { "source": "github", "repo": "omnilertlabs/agent-wiki" },
      "autoUpdate": true
    }
  }
}
```

## Install — Gemini CLI
Clone the repo and link it (the most reliable path — `gemini extensions install` has a
known quirk pulling repos as source archives):

```
git clone https://github.com/omnilertlabs/agent-wiki.git   # public HTTPS clone
gemini extensions link ./agent-wiki                         # link the local clone as the extension
```
Then restart Gemini — it loads `GEMINI.md` (which imports `PROTOCOL.md`) as context. To
update later, just `git pull` in that clone (no reinstall, since it's linked).

(If your git is HTTPS-authed and you prefer a managed install:
`gemini extensions install https://github.com/omnilertlabs/agent-wiki`.)

Gemini has **no slash commands or SessionStart hook** — you drive Ingest/Query/Lint by
asking (e.g. "follow the agent-wiki PROTOCOL to migrate this wiki, dry-run first"), and
run the linter directly from your clone (or the linked extension dir):
`python3 ./agent-wiki/scripts/wiki_lint.py --wiki .claude/wiki --repo .`

## Install — other agents (Codex, etc.)
No marketplace step. Clone the repo, point your agent at `AGENTS.md` / `PROTOCOL.md`, and
run the linter directly:
`python3 path/to/agent-wiki/scripts/wiki_lint.py --wiki .claude/wiki --repo .`

The wiki itself is just git-tracked files in each repo's `.claude/wiki/` — every tool and
human sees it on clone, no install required. Only the tooling (skills/commands/hook)
differs per agent.

## Adopt in a repo
- New repo: run `/wiki-init`.
- Existing/drifted wiki: run `/wiki-migrate`.

Preview before committing: append `--dry-run` to any mutating command
(`/wiki-init`, `/wiki-migrate`, `/wiki-ingest`, `/wiki-compact`, `/wiki-uninstall`) to get a change plan — every file it
would create or modify — without writing or committing anything.

## Recovering an overwritten settings.json (pre-v0.2.3)
Versions before 0.2.3 could **overwrite** `.claude/settings.json` instead of merging — a
repo that already had one could lose its other keys. Only `settings.json` was affected;
personal `settings.local.json` was never touched. `settings.json` is git-tracked, so the
old content is recoverable:

1. See what the wiki-init/migrate commit changed:
   `git log -p -- .claude/settings.json`
   If it **removed** keys, those are recoverable. (If it only *added* the file, nothing was
   lost — just fix the array→record form below.)
2. Print the pre-overwrite version (`<commit>` = the wiki-init/migrate commit):
   `git show <commit>^:.claude/settings.json`
3. Rebuild a merged file — your recovered keys **plus** the agent-wiki entry, in record form:
   ```json
   { "<your recovered keys>": "...", "enabledPlugins": { "agent-wiki@omnilert-plugins": true } }
   ```
4. Update to ≥ 0.2.3 (`/plugin marketplace update omnilert-plugins` → `/reload-plugins`) so
   it merges (never overwrites) going forward, then verify with `/doctor`.

If `settings.json` was untracked, git can't recover it — check your editor's local history;
the loss is bounded to that one file (`settings.local.json` is intact).

## CI
Add one step:
`python3 path/to/agent-wiki/scripts/wiki_lint.py --wiki .claude/wiki --repo . --strict`

## Publishing a new version (maintainers)
Edit the plugin, bump `version` in `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, and `gemini-extension.json`, add a CHANGELOG.md entry
(lead with upgrade impact — new or changed lint failures), open a PR, and merge.
Consumers then pick it up with the three commands in "Update an installed plugin" above
(Gemini users just `git pull` their linked clone).

## License
MIT — see [LICENSE](LICENSE).
