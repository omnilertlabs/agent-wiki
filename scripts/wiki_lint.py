"""Generic structural linter for an agent-wiki (.claude/wiki/).

Derives all checks from wiki content; no repo-specific configuration.
Behavior contract for ports (Go/Node): see CONFORMANCE.md at the repo root.
"""
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")  # inline code spans never cross newlines/fences
_LINE_SUFFIX_RE = re.compile(r":\d+(-\d+)?$")


@dataclass
class Issue:
    severity: str  # 'error' | 'warning'
    code: str
    message: str


def extract_md_links(text):
    # A Markdown destination may carry an optional title: (url "title").
    # Return only the destination (first whitespace-delimited token).
    out = []
    for m in _LINK_RE.finditer(text):
        parts = m.group(1).split()
        out.append(parts[0] if parts else m.group(1))
    return out


def extract_code_refs(text):
    refs = []
    for m in _BACKTICK_RE.finditer(text):
        tok = m.group(1).strip()
        path = _LINE_SUFFIX_RE.sub("", tok)
        # Only repo-relative file paths are checkable. Skip placeholders (<RUN>),
        # absolute / container paths (/usr/...), home paths (~/...), and inline
        # commands (anything containing whitespace is not a single file path).
        if path.startswith(("/", "~")) or "<" in path or ">" in path or " " in path:
            continue
        last = path.split("/")[-1]
        # A dotted symbol (`Type.Method`) also ends in ".Word" but has no "/", so the
        # "/" requirement below skips it. Deliberate: symbol resolution needs language
        # awareness this linter doesn't have (CONFORMANCE.md ruling 7).
        if "/" in path and re.search(r"\.[A-Za-z0-9]+$", last):
            refs.append(path)
    return refs


# Infrastructure files: not topic pages, never declared in the index as pages,
# but always valid link targets (CONFORMANCE.md ruling 4).
_SPECIAL_FILES = ("index.md", "log.md", "log-archive.md")


def parse_index(index_text):
    pages = set()
    for target in extract_md_links(index_text):
        target = target.split("#")[0]
        if (target.endswith(".md") and "/" not in target and "://" not in target
                and target not in _SPECIAL_FILES):
            pages.add(target)
    return pages


def check_index_targets(index_text):
    """Flag local .md index targets that are not bare filenames.

    In the flat standard every page target is bare; a slash-bearing target was
    previously discarded silently and checked by nothing (CONFORMANCE.md ruling 6).
    """
    issues = []
    targets = {t.split("#")[0] for t in extract_md_links(index_text)}
    for target in sorted(targets):
        if target.endswith(".md") and "://" not in target and "/" in target:
            issues.append(Issue("error", "index-target-not-bare",
                                f"index.md links to {target}; page targets must be "
                                f"bare filenames in the flat wiki dir"))
    return issues


def find_pages(wiki_dir):
    return {
        p.name
        for p in Path(wiki_dir).glob("*.md")
        if p.name not in ("index.md", "log.md", "log-archive.md")
    }


def check_index_disk(declared, on_disk):
    issues = []
    for d in sorted(declared - on_disk):
        issues.append(Issue("error", "dangling-index-entry",
                            f"index.md declares {d} but the file does not exist"))
    for f in sorted(on_disk - declared):
        issues.append(Issue("error", "undeclared-page",
                            f"{f} exists on disk but is not declared in index.md"))
    return issues


def _local_md_targets(text):
    out = set()
    for t in extract_md_links(text):
        t = t.split("#")[0]
        if t.endswith(".md") and "/" not in t and "://" not in t:
            out.add(t)
    return out


def check_broken_links(wiki_dir, on_disk):
    issues = []
    valid = on_disk | set(_SPECIAL_FILES)
    for name in sorted(on_disk):
        text = (Path(wiki_dir) / name).read_text()
        for t in sorted(_local_md_targets(text)):
            if t not in valid:
                issues.append(Issue("error", "broken-wiki-link",
                                    f"{name} links to {t} which does not exist"))
    return issues


def find_orphans(wiki_dir, on_disk, index_text):
    linked = set(_local_md_targets(index_text))
    for name in on_disk:
        linked |= _local_md_targets((Path(wiki_dir) / name).read_text())
    return [
        Issue("warning", "orphan-page",
              f"{f} is not linked from index.md or any page")
        for f in sorted(on_disk - linked)
    ]


def check_code_refs(wiki_dir, on_disk, repo_root):
    issues = []
    for name in sorted(on_disk):
        text = (Path(wiki_dir) / name).read_text()
        for ref in sorted(set(extract_code_refs(text))):
            if not (Path(repo_root) / ref).exists():
                issues.append(Issue("warning", "dead-code-ref",
                                    f"{name}: reference `{ref}` not found in repo"))
    return issues


# ASCII by design: dates are ISO-8601 ASCII digits, ops come from the fixed ASCII set
# below. Python's Unicode \d/\w previously (mis)accepted e.g. Arabic-Indic digit dates
# that conforming ports reject (CONFORMANCE.md ruling 2).
_LOG_ENTRY_RE = re.compile(r"^## \[([0-9]{4}-[0-9]{2}-[0-9]{2})\] ([a-z]+) \| (.+)$")
_LOG_OPS = {"ingest", "query", "supersede", "migrate", "compact"}
_LOG_SUBJECT_MAX = 80
_LOG_SIZE_MAX = 200


def check_log_discipline(log_text, label="log.md", check_size=True):
    """Enforce a log file as a thin, ordered, append-only operation index.

    ERROR: body content (`log-body`), out-of-order dates (`log-order`),
    unknown op (`log-op`). WARNING: over-length subject (`log-subject`),
    oversized log (`log-size`, only when check_size).

    `label` names the file in messages. `check_size=False` exempts the file
    from the size warning (used for log-archive.md, which is meant to grow).
    """
    issues = []
    prev_date = None
    entry_count = 0
    in_comment = False
    # Lines terminate at LF, with one immediately preceding CR stripped (CRLF).
    # Other control characters (FF, VT, NEL, LS, PS, ...) have no structural meaning
    # and may appear inside a subject — do NOT use splitlines(), which breaks on nine
    # separators and rejected in-spec input (CONFORMANCE.md ruling 1).
    for n, line in enumerate(log_text.split("\n"), 1):
        line = line.removesuffix("\r")
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if not stripped:
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        if n == 1 and line.startswith("# "):
            continue
        m = _LOG_ENTRY_RE.match(line)
        if not m:
            issues.append(Issue("error", "log-body",
                                f"{label} line {n}: not the title or a "
                                f"'## [date] op | subject' entry: {line!r}"))
            continue
        date, op, subject = m.group(1), m.group(2), m.group(3)
        entry_count += 1
        if op not in _LOG_OPS:
            issues.append(Issue("error", "log-op",
                                f"{label} line {n}: unknown op {op!r} "
                                f"(allowed: {', '.join(sorted(_LOG_OPS))})"))
        if prev_date is not None and date < prev_date:
            issues.append(Issue("error", "log-order",
                                f"{label} line {n}: date {date} precedes previous {prev_date}"))
        prev_date = date
        # Length in Unicode code points, not bytes (Go ports: RuneCountInString).
        if len(subject) > _LOG_SUBJECT_MAX:
            issues.append(Issue("warning", "log-subject",
                                f"{label} line {n}: subject exceeds {_LOG_SUBJECT_MAX} chars "
                                f"({len(subject)}); move detail into a page"))
    if check_size and entry_count > _LOG_SIZE_MAX:
        issues.append(Issue("warning", "log-size",
                            f"{label} has {entry_count} entries (>{_LOG_SIZE_MAX}); "
                            "run /wiki-compact to roll old entries into log-archive.md"))
    return issues


def check_memory_thinness(memory_text, max_entries=25):
    entries = [l for l in memory_text.splitlines() if l.strip().startswith("- [")]
    if len(entries) > max_entries:
        return [Issue("warning", "memory-bloat",
                      f"MEMORY.md has {len(entries)} entries (>{max_entries}); "
                      "domain facts likely belong in the wiki, not memory")]
    return []


def lint(wiki_dir, repo_root, memory_file=None):
    wiki = Path(wiki_dir)
    if not wiki.is_dir():
        return [Issue("error", "missing-wiki",
                      f"wiki directory not found: {wiki_dir}")]
    index_text = (wiki / "index.md").read_text() if (wiki / "index.md").exists() else ""
    log_text = (wiki / "log.md").read_text() if (wiki / "log.md").exists() else ""
    on_disk = find_pages(wiki_dir)
    declared = parse_index(index_text)

    issues = []
    nested = sorted(str(p.relative_to(wiki)) for p in wiki.rglob("*.md")
                    if p.parent != wiki)
    if nested:
        shown = ", ".join(nested[:5]) + (", ..." if len(nested) > 5 else "")
        issues.append(Issue("error", "nested-pages",
                            f"{len(nested)} .md file(s) in subdirectories ({shown}); "
                            "the wiki is flat by design — see PROTOCOL.md"))
    issues += check_index_disk(declared, on_disk)
    issues += check_index_targets(index_text)
    issues += check_broken_links(wiki_dir, on_disk)
    issues += find_orphans(wiki_dir, on_disk, index_text)
    issues += check_code_refs(wiki_dir, on_disk, repo_root)
    issues += check_log_discipline(log_text, label="log.md", check_size=True)
    archive = wiki / "log-archive.md"
    if archive.exists():
        issues += check_log_discipline(archive.read_text(),
                                       label="log-archive.md", check_size=False)
    if memory_file and Path(memory_file).exists():
        issues += check_memory_thinness(Path(memory_file).read_text())
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lint an agent-wiki.")
    parser.add_argument("--wiki", default=".claude/wiki",
                        help="path to the wiki dir (default: .claude/wiki)")
    parser.add_argument("--repo", default=".",
                        help="repo root for code-ref checks (default: .)")
    parser.add_argument("--memory-file", default=None,
                        help="optional MEMORY.md path for thinness check")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    args = parser.parse_args(argv)

    issues = lint(args.wiki, args.repo, args.memory_file)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    for i in issues:
        print(f"[{i.severity.upper()}] {i.code}: {i.message}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
