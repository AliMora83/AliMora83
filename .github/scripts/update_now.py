"""Rewrite the "Now building" block of README.md from recently pushed repos.

Repos tagged with the SHOWCASE_TOPIC topic are listed. If none are tagged,
the most recently pushed public, non-fork, non-archived repos are used.
"""
import json
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_USER", "AliMora83")
TOPIC = os.environ.get("SHOWCASE_TOPIC", "showcase")
LIMIT = int(os.environ.get("NOW_LIMIT", "5"))
README = os.environ.get("README_PATH", "README.md")
START, END = "<!-- NOW:START -->", "<!-- NOW:END -->"


def fetch_repos():
    fixture = os.environ.get("REPOS_FIXTURE")
    if fixture:
        with open(fixture, encoding="utf-8") as f:
            return json.load(f)
    url = f"https://api.github.com/users/{USER}/repos?type=owner&sort=pushed&per_page=100"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def pick(repos):
    eligible = [
        r for r in repos
        if not r.get("fork") and not r.get("archived") and not r.get("private")
        and r["name"].lower() != USER.lower()
    ]
    eligible.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    tagged = [r for r in eligible if TOPIC in (r.get("topics") or [])]
    return (tagged or eligible)[:LIMIT]


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def render(repos):
    if not repos:
        return "_Nothing public right now._"
    rows = ["| Project | What it is | Language | Last push |", "|---|---|---|---|"]
    for r in repos:
        name = f"[**{cell(r['name'])}**]({r['html_url']})"
        if r.get("homepage"):
            name += f" · [live]({r['homepage']})"
        rows.append(
            f"| {name} | {cell(r.get('description')) or '–'} "
            f"| {cell(r.get('language')) or '–'} | {(r.get('pushed_at') or '')[:10]} |"
        )
    return "\n".join(rows)


def main():
    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit(f"Markers {START} / {END} not found in {README}")
    block = f"{START}\n{render(pick(fetch_repos()))}\n{END}"
    new = pattern.sub(lambda _: block, text)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README updated")
    else:
        print("No change")


if __name__ == "__main__":
    main()
