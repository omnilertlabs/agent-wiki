import subprocess, os, json

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "session-start.py")


def _run(cwd=None):
    return subprocess.run(["python3", os.path.abspath(HOOK)],
                          capture_output=True, text=True, cwd=cwd)


def _git_repo_with_wiki(tmp_path, commit=True):
    """A git repo containing .claude/wiki/index.md, optionally committed."""
    wiki = tmp_path / ".claude" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# index\n")
    run = lambda *a: subprocess.run(a, cwd=tmp_path, capture_output=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "t")
    if commit:
        run("git", "add", "-A")
        run("git", "commit", "-qm", "init")
    return wiki


def test_session_start_emits_routing_rules():
    out = subprocess.run(["python3", HOOK], capture_output=True, text=True)
    assert out.returncode == 0
    assert "index.md" in out.stdout
    assert "single source of truth" in out.stdout.lower()
    assert "memory" in out.stdout.lower()


def test_no_warning_when_wiki_clean(tmp_path):
    _git_repo_with_wiki(tmp_path, commit=True)
    out = _run(cwd=tmp_path)
    assert out.returncode == 0
    assert "index.md" in out.stdout                       # routing rules still emitted
    assert "UNCOMMITTED WIKI" not in out.stdout


def test_warns_when_wiki_dirty(tmp_path):
    wiki = _git_repo_with_wiki(tmp_path, commit=True)
    (wiki / "arch.md").write_text("# arch\nuncommitted ingest\n")   # untracked page
    out = _run(cwd=tmp_path)
    assert out.returncode == 0
    assert "UNCOMMITTED WIKI CHANGES DETECTED" in out.stdout
    assert "arch.md" in out.stdout
    assert "reset --hard" in out.stdout                    # the destructive-op guard
    assert "compacted" in out.stdout.lower()               # the why


def test_warns_on_modified_tracked_page(tmp_path):
    wiki = _git_repo_with_wiki(tmp_path, commit=True)
    (wiki / "index.md").write_text("# index\nmodified\n")
    out = _run(cwd=tmp_path)
    assert out.returncode == 0
    assert "UNCOMMITTED WIKI CHANGES DETECTED" in out.stdout
    assert "index.md" in out.stdout


def test_survives_non_git_dir(tmp_path):
    """A session outside a git repo must still start cleanly (rules only, no crash)."""
    out = _run(cwd=tmp_path)
    assert out.returncode == 0
    assert "index.md" in out.stdout
    assert "UNCOMMITTED WIKI" not in out.stdout
