import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import wiki_lint as wl

def test_extract_md_links_returns_targets():
    text = "See [Arch](arch.md) and [Ops](ops.md#deploy) plus [ext](http://x)."
    assert wl.extract_md_links(text) == ["arch.md", "ops.md#deploy", "http://x"]

def test_extract_code_refs_only_pathlike_backticks():
    text = "Use `core/v2/views.py` and `scripts/wiki_lint.py:42` but not `grep` or `Foo`."
    assert wl.extract_code_refs(text) == ["core/v2/views.py", "scripts/wiki_lint.py"]

def test_parse_index_collects_local_md_links_only():
    index = "| [Arch](arch.md) | x |\n| [Ops](ops.md#deploy) | y |\n[ext](http://x.md)\n[sub](sub/z.md)"
    assert wl.parse_index(index) == {"arch.md", "ops.md"}

def test_find_pages_excludes_index_and_log(tmp_path):
    (tmp_path / "index.md").write_text("i")
    (tmp_path / "log.md").write_text("l")
    (tmp_path / "arch.md").write_text("a")
    (tmp_path / "ops.md").write_text("o")
    assert wl.find_pages(str(tmp_path)) == {"arch.md", "ops.md"}

def test_check_index_disk_flags_both_directions():
    issues = wl.check_index_disk(declared={"arch.md", "gone.md"}, on_disk={"arch.md", "extra.md"})
    codes = sorted((i.code, i.severity) for i in issues)
    assert codes == [("dangling-index-entry", "error"), ("undeclared-page", "error")]

def test_check_broken_links_flags_missing_page_target(tmp_path):
    (tmp_path / "arch.md").write_text("links to [gone](gone.md) and [ok](ops.md)")
    (tmp_path / "ops.md").write_text("no links")
    on_disk = {"arch.md", "ops.md"}
    issues = wl.check_broken_links(str(tmp_path), on_disk)
    assert [(i.code, i.severity) for i in issues] == [("broken-wiki-link", "error")]
    assert "gone.md" in issues[0].message

def test_find_orphans_flags_unlinked_page(tmp_path):
    (tmp_path / "arch.md").write_text("see [ops](ops.md)")
    (tmp_path / "ops.md").write_text("no links")
    (tmp_path / "lonely.md").write_text("nobody links me")
    index = "| [Arch](arch.md) | x |"
    on_disk = {"arch.md", "ops.md", "lonely.md"}
    issues = wl.find_orphans(str(tmp_path), on_disk, index)
    assert [(i.code, i.severity) for i in issues] == [("orphan-page", "warning")]
    assert "lonely.md" in issues[0].message

def test_check_code_refs_flags_missing_path(tmp_path):
    repo = tmp_path / "repo"
    wiki = repo / ".claude" / "wiki"
    wiki.mkdir(parents=True)
    (repo / "real.py").write_text("x = 1")
    (wiki / "arch.md").write_text("alive `real.py` dead `nope/missing.py`")
    issues = wl.check_code_refs(str(wiki), {"arch.md"}, str(repo))
    assert [(i.code, i.severity) for i in issues] == [("dead-code-ref", "warning")]
    assert "nope/missing.py" in issues[0].message

def test_check_log_discipline_clean_log_has_no_issues():
    log = "# Log\n\n## [2026-06-12] ingest | seed\n## [2026-06-13] query | auth flow\n"
    assert wl.check_log_discipline(log) == []

def test_check_log_discipline_flags_body_content():
    log = "# Log\n\n## [2026-06-12] ingest | seed\nplain note line\n- bullet note\n"
    codes = [(i.code, i.severity) for i in wl.check_log_discipline(log)]
    assert codes == [("log-body", "error"), ("log-body", "error")]

def test_check_log_discipline_flags_out_of_order_dates():
    log = "# Log\n\n## [2026-06-13] ingest | later\n## [2026-06-12] query | earlier\n"
    codes = [(i.code, i.severity) for i in wl.check_log_discipline(log)]
    assert codes == [("log-order", "error")]

def test_check_log_discipline_allows_same_day_entries():
    log = "# Log\n\n## [2026-06-12] ingest | a\n## [2026-06-12] query | b\n"
    assert wl.check_log_discipline(log) == []

def test_check_log_discipline_flags_unknown_op():
    log = "# Log\n\n## [2026-06-12] scribble | seed\n"
    codes = [(i.code, i.severity) for i in wl.check_log_discipline(log)]
    assert codes == [("log-op", "error")]

def test_check_log_discipline_allows_supersede_and_migrate_ops():
    log = "# Log\n\n## [2026-06-12] supersede | contract v2\n## [2026-06-13] migrate | normalize\n"
    assert wl.check_log_discipline(log) == []

def test_check_log_discipline_warns_on_long_subject():
    subject = "x" * 81
    log = f"# Log\n\n## [2026-06-12] ingest | {subject}\n"
    codes = [(i.code, i.severity) for i in wl.check_log_discipline(log)]
    assert codes == [("log-subject", "warning")]

def test_check_log_discipline_warns_on_oversized_log():
    entries = "".join(f"## [2026-06-12] query | q{i}\n" for i in range(201))
    log = "# Log\n\n" + entries
    codes = [(i.code, i.severity) for i in wl.check_log_discipline(log)]
    assert codes == [("log-size", "warning")]

def test_check_memory_thinness_flags_over_threshold():
    body = "\n".join(f"- [m{i}](m{i}.md) — hook" for i in range(30))
    issues = wl.check_memory_thinness(body, max_entries=25)
    assert [(i.code, i.severity) for i in issues] == [("memory-bloat", "warning")]

def test_check_memory_thinness_ok_under_threshold():
    body = "\n".join(f"- [m{i}](m{i}.md) — hook" for i in range(5))
    assert wl.check_memory_thinness(body, max_entries=25) == []

CLEAN = os.path.join(os.path.dirname(__file__), "fixtures", "clean")
CLEAN_WIKI = os.path.join(CLEAN, ".claude", "wiki")

def test_lint_clean_wiki_has_no_issues():
    assert wl.lint(CLEAN_WIKI, CLEAN) == []

def test_lint_detects_undeclared_page(tmp_path):
    wiki = tmp_path / ".claude" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Index\n")
    (wiki / "log.md").write_text("# Log\n")
    (wiki / "stray.md").write_text("undeclared")
    codes = {i.code for i in wl.lint(str(wiki), str(tmp_path))}
    assert "undeclared-page" in codes

def test_main_exits_zero_on_clean():
    rc = wl.main(["--wiki", CLEAN_WIKI, "--repo", CLEAN])
    assert rc == 0

def test_main_exits_one_on_error(tmp_path):
    wiki = tmp_path / ".claude" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Index\n")
    (wiki / "log.md").write_text("# Log\n")
    (wiki / "stray.md").write_text("undeclared")
    rc = wl.main(["--wiki", str(wiki), "--repo", str(tmp_path)])
    assert rc == 1

def test_main_strict_exits_one_on_warning_only(tmp_path):
    # No errors, exactly one warning (a dead code-ref): --strict must exit 1.
    wiki = tmp_path / ".claude" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "log.md").write_text("# Log\n\n## [2026-06-12] ingest | seed\n")
    (wiki / "arch.md").write_text("links [Index](index.md); ref `nope/missing.py`")
    (wiki / "index.md").write_text("# Index\n\n[Arch](arch.md)\n")
    issues = wl.lint(str(wiki), str(tmp_path))
    assert [(i.severity, i.code) for i in issues] == [("warning", "dead-code-ref")]
    rc = wl.main(["--wiki", str(wiki), "--repo", str(tmp_path), "--strict"])
    assert rc == 1

def test_md_links_strip_title_attribute():
    # A link destination with a title must resolve to the bare target.
    assert wl.extract_md_links('[Arch](arch.md "Architecture")') == ["arch.md"]

def test_broken_link_detected_even_with_title_attribute(tmp_path):
    (tmp_path / "arch.md").write_text('[gone](gone.md "Title")')
    issues = wl.check_broken_links(str(tmp_path), {"arch.md"})
    assert [(i.code, i.severity) for i in issues] == [("broken-wiki-link", "error")]

def test_lint_flags_missing_wiki_dir(tmp_path):
    missing = tmp_path / "nope" / ".claude" / "wiki"
    issues = wl.lint(str(missing), str(tmp_path))
    assert [(i.code, i.severity) for i in issues] == [("missing-wiki", "error")]

def test_dead_code_ref_deduped_per_page(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "arch.md").write_text("see `nope/gone.py` and again `nope/gone.py`")
    issues = wl.check_code_refs(str(wiki), {"arch.md"}, str(tmp_path))
    assert len(issues) == 1

def test_extract_code_refs_skips_placeholder_absolute_home():
    # Only repo-relative paths are checkable. Placeholders (<RUN>), absolute /
    # container paths, and ~ home paths are inherently not repo-local.
    text = ("real `core/v2/views.py`, placeholder `configs/<RUN>.yaml`, "
            "absolute `/usr/src/datasets/data.yaml`, home `~/Downloads/x.onnx`")
    assert wl.extract_code_refs(text) == ["core/v2/views.py"]

def test_extract_code_refs_skips_inline_commands_with_spaces():
    # An inline code span containing whitespace is a command, not a single path.
    text = "run `cp configs/a.yaml configs/b.yaml` to copy"
    assert wl.extract_code_refs(text) == []

def test_extract_code_refs_ignores_fenced_code_block():
    # A triple-backtick fenced block whose content ends in a path-like token used
    # to be captured as one giant cross-newline "code span" -> spurious dead-code-ref.
    # An inline code span must not cross newlines, so the fence yields no ref.
    text = "```\nlisting:\nclrnet/models/nets/clrnet.py\n```\n"
    assert wl.extract_code_refs(text) == []

def test_check_log_discipline_skips_html_comment_lines():
    log = ("# Wiki Operation Log\n\n"
           "<!-- guidance line one\n"
           "     guidance line two -->\n\n"
           "## [2026-06-12] ingest | seed\n")
    assert wl.check_log_discipline(log) == []

def test_shipped_log_template_passes_discipline():
    import os
    tmpl = os.path.join(os.path.dirname(__file__), "..", "templates", "log.md")
    with open(tmpl) as f:
        assert wl.check_log_discipline(f.read()) == []

def test_check_log_discipline_subject_exactly_80_is_clean():
    log = "# Log\n\n## [2026-06-12] ingest | " + "x" * 80 + "\n"
    assert wl.check_log_discipline(log) == []

def test_check_log_discipline_exactly_200_entries_is_clean():
    entries = "".join(f"## [2026-06-12] query | q{i}\n" for i in range(200))
    assert wl.check_log_discipline("# Log\n\n" + entries) == []

def test_check_log_discipline_compact_op_allowed():
    log = "# Log\n\n## [2026-06-12] compact | rolled 100 entries to archive\n"
    assert wl.check_log_discipline(log) == []

def test_check_log_discipline_archive_exempt_from_size():
    entries = "".join(f"## [2026-06-12] query | q{i}\n" for i in range(250))
    log = "# Wiki Operation Log (archive)\n\n" + entries
    assert any(i.code == "log-size"
               for i in wl.check_log_discipline(log, label="log.md", check_size=True))
    assert wl.check_log_discipline(log, label="log-archive.md", check_size=False) == []

def test_check_log_discipline_archive_still_flags_structure():
    log = "# arch\n\n## [2026-06-13] ingest | a\nstray body\n## [2026-06-12] query | b\n"
    codes = sorted((i.code, i.severity)
                   for i in wl.check_log_discipline(log, label="log-archive.md", check_size=False))
    assert codes == [("log-body", "error"), ("log-order", "error")]

def test_check_log_discipline_message_uses_label():
    log = "# Log\n\n## [2026-06-12] scribble | x\n"
    issues = wl.check_log_discipline(log, label="log-archive.md")
    assert issues[0].code == "log-op"
    assert "log-archive.md" in issues[0].message

def test_find_pages_excludes_log_archive(tmp_path):
    (tmp_path / "index.md").write_text("i")
    (tmp_path / "log.md").write_text("l")
    (tmp_path / "log-archive.md").write_text("a")
    (tmp_path / "arch.md").write_text("p")
    assert wl.find_pages(str(tmp_path)) == {"arch.md"}

def test_lint_checks_log_archive(tmp_path):
    wiki = tmp_path / ".claude" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# I\n")
    (wiki / "log.md").write_text("# Log\n\n## [2026-06-12] ingest | seed\n")
    (wiki / "log-archive.md").write_text("# Archive\n\nstray body line\n")
    codes = {i.code for i in wl.lint(str(wiki), str(tmp_path))}
    assert "log-body" in codes


# --- CONFORMANCE.md rulings (2026-08-18) ---

def test_log_entry_rejects_unicode_digit_date():
    # Ruling 2: ISO dates are ASCII. Python's \d used to accept Arabic-Indic digits,
    # silently PASSING a log that conforming ports reject.
    log = "# Log\n\n## [٢٠٢٦-٠٦-١٢] ingest | unicode date\n"
    codes = [(i.code, i.severity) for i in wl.check_log_discipline(log)]
    assert codes == [("log-body", "error")]


def test_form_feed_inside_line_is_subject_content():
    # Ruling 1: control chars other than the LF terminator have no structural
    # meaning. splitlines() used to split here and flag the fragment as log-body.
    log = "# Log\n\n## [2026-06-12] ingest | part one\fpart two\n"
    assert wl.check_log_discipline(log) == []


def test_crlf_line_endings_accepted():
    log = "# Log\r\n\r\n## [2026-06-12] ingest | a\r\n## [2026-06-13] query | b\r\n"
    assert wl.check_log_discipline(log) == []


def test_exotic_separators_do_not_break_lines():
    for sep in ("\v", "\x1c", "\x1d", "\x1e", "\u0085", "\u2028", "\u2029"):
        log = f"# Log\n\n## [2026-06-12] ingest | a{sep}b\n"
        assert wl.check_log_discipline(log) == [], repr(sep)


def test_subject_length_counts_code_points():
    # Ruling 3: 80 multibyte runes is exactly at the limit — code points, not bytes.
    log = "# Log\n\n## [2026-06-12] ingest | " + "é" * 80 + "\n"
    assert wl.check_log_discipline(log) == []


def test_link_to_log_archive_is_valid(tmp_path):
    # Ruling 4: special files are always valid link targets.
    (tmp_path / "arch.md").write_text("see [archive](log-archive.md)")
    assert wl.check_broken_links(str(tmp_path), {"arch.md"}) == []


def test_index_linking_special_files_not_dangling(tmp_path):
    # Ruling 4: an index link to log.md / log-archive.md is navigation, not a
    # page declaration — must not produce dangling-index-entry.
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text(
        "| [Arch](arch.md) | x |\n[log](log.md) [archive](log-archive.md)\n")
    (wiki / "log.md").write_text("# Log\n")
    (wiki / "log-archive.md").write_text("# Wiki Operation Log (archive)\n")
    (wiki / "arch.md").write_text("see [Index](index.md)")
    assert wl.lint(str(wiki), str(tmp_path)) == []


def test_nested_pages_flagged(tmp_path):
    # Ruling 5: a nested wiki must be diagnosed, not silently half-inspected.
    wiki = tmp_path / "wiki"
    (wiki / "bugs").mkdir(parents=True)
    (wiki / "index.md").write_text("# I\n")
    (wiki / "log.md").write_text("# Log\n")
    (wiki / "bugs" / "b1.md").write_text("nested page")
    issues = wl.lint(str(wiki), str(tmp_path))
    assert ("nested-pages", "error") in {(i.code, i.severity) for i in issues}
    assert any("bugs/b1.md" in i.message for i in issues)


def test_index_target_not_bare_flagged():
    # Ruling 6: a slash-bearing local .md index target used to be silently
    # discarded and checked by nothing.
    issues = wl.check_index_targets("| [B](bugs/b1.md) | x |\n| [A](arch.md) | y |")
    assert [(i.code, i.severity) for i in issues] == [("index-target-not-bare", "error")]
    assert "bugs/b1.md" in issues[0].message
