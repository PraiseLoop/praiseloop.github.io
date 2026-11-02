#!/usr/bin/env python3
"""Check the PraiseLoop static site before publishing.

Usage:
    python3 check_site.py            # checks the site, lists TODO(owner) markers
    python3 check_site.py --strict   # also fails while TODO(owner) markers remain

Uses only the Python standard library and makes no network requests.
Exit code 0 means every check passed.
"""

from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
SHELL_LINKS = ("/privacy/", "/terms/", "mailto:hello@praiseloop.ca")
CANONICAL_PREFIX = "https://praiseloop.ca/"
TODO_MARKER = "TODO(owner)"


class PageParser(HTMLParser):
    """Collect the handful of facts the checks need from one HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.h1_count = 0
        self.title_parts: list[str] = []
        self.description: str | None = None
        self.refs: list[tuple[str, str, str, bool]] = []
        self.anchor_hrefs: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        rels = values.get("rel", "").lower().split()
        is_canonical = tag == "link" and "canonical" in rels

        if tag == "html":
            self.lang = values.get("lang")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and values.get("name", "").lower() == "description":
            self.description = values.get("content", "").strip()

        for attr in ("href", "src"):
            value = values.get(attr)
            if value:
                self.refs.append((tag, attr, value, is_canonical))

        if tag == "a" and values.get("href"):
            self.anchor_hrefs.append(values["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def html_pages() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if ".git" not in path.relative_to(ROOT).parts
    )


def resolve_root_relative(reference: str) -> Path | None:
    """Return the file a root-relative reference should serve, or None if broken."""
    path = urlsplit(reference).path
    if not path.startswith("/"):
        return None

    target = ROOT / path.lstrip("/")
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def check_reference(
    rel: str, tag: str, attr: str, value: str, is_canonical: bool, problems: list[str]
) -> None:
    if is_canonical:
        if not value.startswith(CANONICAL_PREFIX):
            problems.append(
                f"{rel}: canonical URL should start with {CANONICAL_PREFIX!r} "
                f"(found {value!r})"
            )
        return

    if value.startswith("//"):
        problems.append(f"{rel}: external {attr} {value!r} is not allowed")
        return

    parts = urlsplit(value)
    scheme = parts.scheme.lower()

    # A visitor-clicked https link (<a href>) loads nothing when the page opens, so the privacy
    # promise "no third-party requests" still holds. Scripts, styles, images, frames and
    # insecure http links stay forbidden.
    if scheme == "https" and tag == "a" and attr == "href":
        return

    if scheme in ("http", "https"):
        problems.append(
            f"{rel}: external {attr} {value!r} is not allowed "
            '(only <link rel="canonical"> may be an absolute URL)'
        )
        return

    if scheme:
        if scheme != "mailto":
            problems.append(
                f"{rel}: unsupported {attr} scheme in {value!r} (only mailto: is allowed)"
            )
        return

    # A fragment-only link such as "#main" stays on the page.
    if not parts.path:
        return

    if not parts.path.startswith("/"):
        problems.append(
            f"{rel}: {attr} {value!r} should be root-relative and start with '/'"
        )
        return

    target = resolve_root_relative(value)
    if target is None or not target.is_file():
        shown = (
            target.relative_to(ROOT).as_posix()
            if target is not None and target.is_relative_to(ROOT)
            else "an unknown path"
        )
        problems.append(
            f"{rel}: {attr} {value!r} does not resolve to a file "
            f"(looked for {shown})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the PraiseLoop static site.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if any TODO(owner) marker remains in a published HTML file",
    )
    args = parser.parse_args()

    problems: list[str] = []
    pages = html_pages()

    print("PraiseLoop site check")
    print(f"Root: {ROOT}")
    print(f"Pages: {len(pages)}")
    print()

    if not pages:
        problems.append("no HTML pages were found")

    todo_markers: list[tuple[str, int, str]] = []

    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text(encoding="utf-8")
        parsed = PageParser()
        parsed.feed(text)
        parsed.close()

        if parsed.lang != "en-CA":
            problems.append(
                f'{rel}: <html> must have lang="en-CA" (found {parsed.lang!r})'
            )
        if parsed.h1_count != 1:
            problems.append(f"{rel}: expected exactly one <h1>, found {parsed.h1_count}")
        if not parsed.title:
            problems.append(f"{rel}: missing or empty <title>")
        if not parsed.description:
            problems.append(f"{rel}: missing or empty meta description")

        for tag, attr, value, is_canonical in parsed.refs:
            check_reference(rel, tag, attr, value, is_canonical, problems)

        anchor_hrefs = set(parsed.anchor_hrefs)
        for link in SHELL_LINKS:
            if link not in anchor_hrefs:
                problems.append(f"{rel}: shared shell link {link!r} is missing")

        for number, line in enumerate(text.splitlines(), start=1):
            if TODO_MARKER in line:
                todo_markers.append((rel, number, line.strip()))

        print(f"checked {rel}")

    print()

    cname_path = ROOT / "CNAME"
    if not cname_path.is_file():
        problems.append("CNAME: file is missing")
    else:
        cname = cname_path.read_text(encoding="utf-8").strip()
        if cname != "praiseloop.ca":
            problems.append(f"CNAME: must contain exactly 'praiseloop.ca' (found {cname!r})")

    if todo_markers:
        print(f"{TODO_MARKER} markers ({len(todo_markers)}):")
        for rel, number, line in todo_markers:
            print(f"  {rel}:{number}: {line}")
        print()
        if args.strict:
            problems.append(
                f"{len(todo_markers)} {TODO_MARKER} marker(s) remain "
                "(resolved before publishing)"
            )
    else:
        print(f"{TODO_MARKER} markers: none")
        print()

    if problems:
        unique_problems = list(dict.fromkeys(problems))
        print(f"FAILED with {len(unique_problems)} problem(s):")
        for problem in unique_problems:
            print(f"  - {problem}")
        return 1

    print(f"OK: {len(pages)} page(s) checked, all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
