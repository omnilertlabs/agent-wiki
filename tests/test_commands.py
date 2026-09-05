import os, glob, re

CMDS = os.path.join(os.path.dirname(__file__), "..", "commands")

def test_commands_each_invoke_their_skill():
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CMDS, "*.md")))
    assert files == ["wiki-compact.md", "wiki-ingest.md", "wiki-init.md", "wiki-lint.md",
                     "wiki-migrate.md", "wiki-query.md", "wiki-uninstall.md"]
    for p in glob.glob(os.path.join(CMDS, "*.md")):
        text = open(p).read()
        assert re.match(r"^---\n.*description:.*\n---\n", text, re.S), f"{p} bad frontmatter"
        name = os.path.basename(p)[:-3]
        assert name in text, f"{p} should reference its skill {name}"
