import os, glob, re

SKILLS = os.path.join(os.path.dirname(__file__), "..", "skills")

def _frontmatter(path):
    text = open(path).read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} missing frontmatter"
    return m.group(1)

def test_all_skills_present_with_frontmatter():
    dirs = sorted(os.path.basename(os.path.dirname(p))
                  for p in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")))
    assert dirs == ["wiki-compact", "wiki-ingest", "wiki-init", "wiki-lint", "wiki-migrate",
                    "wiki-query", "wiki-uninstall"]
    for p in glob.glob(os.path.join(SKILLS, "*", "SKILL.md")):
        fm = _frontmatter(p)
        assert "name:" in fm and "description:" in fm
        assert len(fm) > 40, f"{p} description too thin"


def test_reconcile_exempts_history_pages():
    """Reconcile rewrites superseded claims OUT of pages. A `*-history.md` page exists to HOLD
    superseded claims — the reasoning trail for rejected approaches and overturned measurements —
    so running reconcile over one destroys exactly what it was created to keep, including the
    evidence that stops an abandoned approach being retried. The exemption must be stated in the
    skill (which the agent reads) and in PROTOCOL.md (the method of record)."""
    skill = open(os.path.join(SKILLS, "wiki-compact", "SKILL.md")).read()
    assert "*-history.md" in skill, "wiki-compact must name the history-page convention"
    assert "ARCHIVE PAGE" in skill, "wiki-compact must name the explicit archive marker"
    # The exemption has to sit in the reconcile section, not merely somewhere in the file.
    reconcile = skill.split("## reconcile")[1].split("## compact-log")[0]
    assert "EXEMPT" in reconcile.upper(), "the exemption must be in the reconcile section"

    protocol = open(os.path.join(os.path.dirname(__file__), "..", "PROTOCOL.md")).read()
    assert "*-history.md" in protocol and "exempt from reconcile" in protocol.lower(), \
        "PROTOCOL.md must document history pages as a reconcile-exempt page class"


def test_all_manifests_declare_the_same_version():
    """Three manifests carry the version: plugin.json, marketplace.json, gemini-extension.json.
    They have already drifted once (54b45f6 'bump gemini-extension.json to v0.2.6 (was missed)'),
    which ships a plugin whose advertised version depends on which file the host reads. Pin it."""
    import json
    root = os.path.join(os.path.dirname(__file__), "..")
    plugin = json.load(open(os.path.join(root, ".claude-plugin", "plugin.json")))["version"]
    gemini = json.load(open(os.path.join(root, "gemini-extension.json")))["version"]
    market = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json")))
    entries = market.get("plugins") or market.get("extensions") or []
    versions = {e.get("version") for e in entries if isinstance(e, dict) and "version" in e}
    assert versions == {plugin}, f"marketplace.json {versions} != plugin.json {plugin}"
    assert gemini == plugin, f"gemini-extension.json {gemini} != plugin.json {plugin}"
