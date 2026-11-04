#!/usr/bin/env python3
"""Pre-delivery check for a built scrolly story page (no network, stdlib only).

usage: check_story.py <story.html> [--query q.json] [--probe probe.json] [--chrome <path>]

Static checks on the HTML, then (if Chrome or Edge is installed) renders the page
headless and checks the live DOM, so every chapter is looked at, not just the
first screen. Prints one JSON object; exit 0 = all checks pass, 1 = a check
failed, 2 = could not run. Does not replace the user's scroll/toggle/Explore check.
--probe takes the output of probe_signal.py and checks that the page shows the
proposal's lead figure and move start. Phrases and decimals copied from the vendored
templates (assets/public) fail the page.
"""
import glob
import html as htmllib
import json
import os
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
]
BAD_TEXT = re.compile(r"\bNaN\b|\bundefined\b|\[object Object\]|\{\{|\}\}|\bInfinity\b")


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ext = []
        self.chapters = 0
        self.dv = 0
        self.title = ""
        self._t = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("src", "href"):
            v = a.get(k) or ""
            if tag in ("script", "link", "img", "iframe") and re.match(r"(https?:)?//", v):
                self.ext.append(f"{tag} {k}={v[:80]}")
        if tag == "section" and "data-ch" in a:
            self.chapters += 1
        if "data-v" in a:
            self.dv += 1
        if tag == "title":
            self._t = True

    def handle_data(self, d):
        if self._t:
            self.title += d

    def handle_endtag(self, tag):
        if tag == "title":
            self._t = False


def visible_text(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", h))


def shingles(text, n=5):
    w = re.findall(r"[a-z0-9%.']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def template_leaks(page_text, skill_dir):
    """Phrases and decimals the story shares with exactly one vendored template."""
    paths = sorted(glob.glob(os.path.join(skill_dir, "assets", "public", "*.html")))
    texts = [visible_text(open(p, encoding="utf-8").read()) for p in paths]
    if len(texts) < 2:
        return [], []
    sh = [shingles(t) for t in texts]
    nums = [set(re.findall(r"\b\d+\.\d+\b", t)) for t in texts]
    shared_sh = set.intersection(*sh)      # interface wording both templates use
    shared_n = set.intersection(*nums)
    page_sh = shingles(page_text)
    page_n = set(re.findall(r"\b\d+\.\d+\b", page_text))
    phr = sorted((set.union(*sh) - shared_sh) & page_sh)
    num = sorted((set.union(*nums) - shared_n) & page_n)
    return phr, num


def date_forms(iso):
    import datetime
    d = datetime.date.fromisoformat(iso)
    return {iso, d.strftime("%b %d").replace(" 0", " "), d.strftime("%B %d").replace(" 0", " "),
            "%s %d" % (d.strftime("%b"), d.day), "%s %d" % (d.strftime("%B"), d.day),
            "%d %s" % (d.day, d.strftime("%b"))}


def find_chrome(arg):
    for c in ([arg] if arg else []) + CHROMES:
        if c and os.path.exists(c):
            return c
    return None


def render(chrome, path):
    with tempfile.TemporaryDirectory() as prof:
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
               f"--user-data-dir={prof}", "--virtual-time-budget=8000",
               "--window-size=1400,900", "--dump-dom", "file://" + os.path.abspath(path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.stdout


def main(argv):
    if len(argv) < 2 or argv[1].startswith("-"):
        print(__doc__)
        return 2
    path, query, chrome_arg = argv[1], None, None
    if "--query" in argv:
        query = argv[argv.index("--query") + 1]
    probe = None
    if "--probe" in argv:
        probe = json.load(open(argv[argv.index("--probe") + 1]))
    if "--chrome" in argv:
        chrome_arg = argv[argv.index("--chrome") + 1]
    html = open(path, encoding="utf-8").read()
    scan = Scan()
    scan.feed(html)
    checks = []

    def add(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    add("no external scripts, styles, images or frames", not scan.ext, "; ".join(scan.ext[:5]))
    # a real credential mixes letters and digits; the bundled Extensions library
    # has event names like ReadyToReceiveAuthToken="readytoreceiveauthtoken"
    secrets = [m for m in re.findall(
        r"(?i)(?:pat|token|secret|password)[\"']?\s*[:=]\s*[\"']([A-Za-z0-9+/=_-]{16,})", html)
        if re.search(r"\d", m) and re.search(r"[A-Za-z]", m)]
    add("no secrets in the page", not secrets, f"{len(secrets)} suspicious assignment(s)")
    add("chapter sections present (3 to 6 plus opening and closing)", 3 <= scan.chapters <= 8, f"{scan.chapters} sections with data-ch")
    add("prose spans present", scan.dv > 0, f"{scan.dv} data-v spans")
    # a sticky header that wraps covers the page in a short Cloud frame
    sticky = bool(re.search(r"position:\s*sticky", html))
    short_ok = bool(re.search(
        r"@media\s*\(\s*max-height:\s*\d+px\s*\)\s*\{[^}]*position:\s*static", html))
    add("a sticky header turns off in a short frame", (not sticky) or short_ok,
        "sticky header with no max-height rule" if sticky and not short_ok else "")
    if query:
        q = json.load(open(query))
        has_filter = bool(q.get("filters"))
        add("the query carries a window filter", has_filter, f"{len(q.get('filters', []))} filter(s)")
        add("every aggregated query field has an alias",
            all("fieldAlias" in f for f in q.get("fields", []) if f.get("function")),
            "")
    chrome = find_chrome(chrome_arg)
    rendered = False
    if chrome:
        try:
            dom = render(chrome, path)
            rendered = bool(dom.strip())
        except Exception as e:  # noqa: BLE001
            dom = ""
            add("page renders headless", False, str(e)[:120])
        if rendered:
            body = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", dom)
            text = re.sub(r"<[^>]+>", " ", body)
            bad = sorted(set(BAD_TEXT.findall(text)))
            add("no NaN/undefined/placeholder text after render", not bad, ", ".join(bad))
            empties = len(re.findall(r"<[^>]+data-v=\"[^\"]+\"[^>]*>\s*</", body))
            add("no empty prose spans after render", empties == 0, f"{empties} empty")
            secs = re.findall(r"(?is)<section\b[^>]*data-ch[^>]*>.*?</section>", body)
            thin = [i + 1 for i, s in enumerate(secs) if len(re.sub(r"<[^>]+>", " ", s).split()) < 12]
            add("every chapter has text after render", secs and not thin,
                f"{len(secs)} sections; thin: {thin}")
            nosvg = [i + 1 for i, s in enumerate(secs) if not re.search(r"<(svg|canvas)\b", s)]
            add("at least half the sections carry a chart (svg or canvas)",
                secs and len(nosvg) <= len(secs) / 2,
                f"sections without a chart: {nosvg} of {len(secs)}")
    else:
        add("page renders headless", False, "no Chrome or Edge found; render check skipped")
    page_text = re.sub(r"\s+", " ", visible_text(dom if rendered else html))
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    phr, num = template_leaks(page_text, skill_dir)
    add("no phrases copied from a vendored template", not phr,
        "; ".join(phr[:3]) + (" ..." if len(phr) > 3 else ""))
    add("no decimals left over from a vendored template", not num, ", ".join(num[:6]))
    if probe:
        ls = probe.get("lead_signal")
        if ls and ls.get("change") is not None:
            fig = "%.1f" % abs(ls["change"] * 100)
            add("the page shows the proposal's lead figure", fig in page_text, fig)
        ms = probe.get("move_start")
        if ms:
            add("the page shows the proposal's move start",
                any(f in page_text for f in date_forms(ms)), ms)
    ok = all(c["pass"] for c in checks if not c["check"].startswith("page renders") or chrome)
    print(json.dumps({"file": path, "rendered": rendered, "ok": ok, "checks": checks}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
