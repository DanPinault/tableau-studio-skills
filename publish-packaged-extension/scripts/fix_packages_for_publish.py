#!/usr/bin/env python3
"""Make a workbook with a packaged extension survive publishing to Tableau Cloud.

Tableau Studio wraps packaged-extension zones in a `_.fcp.Packages` feature switch. Sites that
don't support the switch resolve it to "false" on publish and swap each extension for a
"removed when workbook was downgraded" text box. `fix` resolves the switch to "true" in a
copy of the .twbx (workbooks without the switch are copied as-is); `verify` checks any .twbx (for example the server's copy) for extension
zones and the fallback text. `fix` also runs the checks Tableau applies at publish time
(.twb at the archive root, a .trex per package, requestedOrigins as one string, referenced
Data/ files present) and warns about runtime risks. Standard library only; prints JSON.

  fix_packages_for_publish.py fix --in WORKBOOK.twbx|FOLDER [--out FIXED-FOR-PUBLISH.twbx]

FOLDER is an unzipped workbook: one .twb next to a Packages/ folder (a data-app workspace).
  fix_packages_for_publish.py verify --in WORKBOOK.twbx
"""
import argparse, json, re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

P = r"_\.fcp\.Packages\."
FALLBACK = "Embedded extension removed"
ORIGIN = re.compile(r"https?://[A-Za-z0-9.-]+(?::\d+)?")
NON_NETWORK = {"http://www.w3.org", "https://www.w3.org", "http://www.tableausoftware.com", "http://www.tableau.com"}
SECRET = re.compile(r"""[\w-]*(?:secret|token|api[_-]?key|password|private[_-]?key)['"]?\s*[:=]\s*['"]([^'"\s]{8,})['"]""", re.I)
PLACEHOLDER = re.compile(r"placeholder|example|changeme|replace|dummy|sample|your[_-]|xxxx", re.I)


def resolve_fcp(xml):
    """Resolve every _.fcp.Packages switch in the workbook XML to its 'true' branch."""
    xml = re.sub(r"<(" + P + r"false\.\.\.[\w:-]+)\b[^>]*?/>", "", xml)
    xml = re.sub(r"<(" + P + r"false\.\.\.[\w:-]+)\b[^>]*>.*?</\1>", "", xml, flags=re.S)
    xml = re.sub(r"\s" + P + r"false\.\.\.[\w:-]+='[^']*'", "", xml)
    xml = re.sub(r"\s*<" + P + r"true\.\.\.Packages\s*/>", "", xml)
    return re.sub(P + r"true\.\.\.", "", xml)


def load(src):
    """Return (entries, twb name) for a .twbx file or an unzipped workbook folder."""
    if src.is_dir():
        twbs = sorted(src.glob("*.twb"))
        if len(twbs) != 1:
            fail(f"Expected exactly one .twb directly in {src}, found {len(twbs)}.")
        files = [f for f in sorted(src.rglob("*")) if f.is_file()
                 and not any(part.startswith(".") and part != ".agents" for part in f.relative_to(src).parts)
                 and f.suffix.lower() != ".twbx"]
        # Resources/.agents/ (agent docs) travels with the workbook, per Tableau's data-app layout.
        files = [f for f in files if ".agents" not in f.relative_to(src).parts
                 or f.relative_to(src).as_posix().startswith("Resources/.agents/")]
        return {f.relative_to(src).as_posix(): f.read_bytes() for f in files}, twbs[0].name
    with zipfile.ZipFile(src) as z:
        entries = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    twb = next((n for n in entries if n.endswith(".twb")), None)
    if not twb:
        fail("No .twb inside the file; is it a .twbx?")
    return entries, twb


def inspect(names, xml):
    return {
        "packages": sorted({n.split("/")[1] for n in names if n.startswith("Packages/") and n.count("/") > 1}),
        # Other FCP switches (e.g. _.fcp.VizExtensions in Tableau's own samples) are left as-is.
        "extension_zones": len(re.findall(r"<(?:_\.fcp\.\w+\.true\.\.\.)?add-in ", xml)),
        "switch_markers": len(re.findall(P, xml)),
        "fallback_text": FALLBACK in xml,
    }


def check_package(entries, twb, xml):
    """Return (problems, warnings). Problems make publish fail or leave the app without data."""
    problems, warnings = [], []
    if "/" in twb:
        problems.append(f"{twb} is nested in a folder; the .twb and Packages/ must be at the archive root.")
    pkgs = sorted({n.split("/")[1] for n in entries if n.startswith("Packages/") and n.count("/") > 1})
    trex_versions = {}
    for pkg in pkgs:
        base = f"Packages/{pkg}/"
        trexes = [n for n in entries if n.startswith(base + "extensions/") and n.endswith(".trex")]
        if not trexes:
            problems.append(f"{pkg}: no .trex under extensions/; publish fails with PackageValidationException.")
        for t in trexes:
            m = re.search(r"<(?:dashboard|worksheet)-extension\b[^>]*\bid=['\"]([^'\"]+)['\"][^>]*\bextension-version=['\"]([^'\"]+)",
                          entries[t].decode("utf-8", "replace"))
            if m:
                trex_versions[m.group(1)] = m.group(2)
        declared = set()
        if base + "manifest.json" in entries:
            try:
                origins = json.loads(entries[base + "manifest.json"]).get("requestedOrigins")
            except (ValueError, AttributeError):
                origins = None
                problems.append(f"{pkg}: manifest.json isn't valid JSON.")
            if origins is not None and not isinstance(origins, str):
                problems.append(f"{pkg}: requestedOrigins must be one space-separated string; Tableau ignores "
                                f"a {type(origins).__name__} and blocks every external origin.")
            elif origins:
                declared = {o.lower().rstrip("/") for o in origins.split()}
        undeclared, secrets = set(), []
        for n, data in entries.items():
            name = n.rsplit("/", 1)[-1]
            if not n.startswith(base) or name.startswith("tableau.extensions.") or b"\0" in data[:8192]:
                continue
            text = data.decode("utf-8", "replace")
            if any(not PLACEHOLDER.search(v) for v in SECRET.findall(text)):
                secrets.append(n[len(base):])
            if n.startswith(base + "content/") and name.endswith((".js", ".mjs", ".html", ".htm", ".css")) \
                    and ".min." not in name:
                undeclared |= {o.lower() for o in ORIGIN.findall(text)} - declared - NON_NETWORK
        if undeclared:
            warnings.append(f"{pkg}: content references origins not in requestedOrigins ({', '.join(sorted(undeclared))}); "
                            "the browser blocks requests to them unless declared and allowed by the site.")
        if secrets:
            warnings.append(f"{pkg}: secret-looking values in {', '.join(secrets)}; anyone who can download the workbook can read them.")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        problems.append(f"{twb} isn't valid XML after the fix: {e}")
        return problems, warnings
    for c in root.iter("connection"):
        d = c.get("directory", "").replace("\\", "/").rstrip("/")
        for attr in ("filename", "dbname"):
            path = c.get(attr, "").replace("\\", "/")
            if attr == "filename" and d and path:
                path = f"{d}/{path}"
            if path.startswith("Data/") and path not in entries:
                problems.append(f"{twb} references {path}, which isn't in the workbook (no data at runtime).")
    for a in (e for e in root.iter() if e.tag.endswith("add-in")):
        want = trex_versions.get(a.get("add-in-id"))
        if want and a.get("extension-version") and a.get("extension-version") != want:
            warnings.append(f"{a.get('add-in-id')}: workbook uses extension-version {a.get('extension-version')} "
                            f"but the .trex says {want}; keep them in step.")
    return sorted(set(problems)), sorted(set(warnings))


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(1)


def cmd_fix(a):
    src = Path(a.inp).expanduser().resolve()
    entries, twb = load(src)
    stem = Path(twb).stem if src.is_dir() else src.stem
    out = Path(a.out).expanduser() if a.out else src.with_name(stem + ".fixed-for-publish.twbx")
    if out.suffix.lower() != ".twbx":
        fail("--out must end in .twbx.")
    if out.resolve() == src:
        fail("--out must differ from --in; the original is never modified.")
    xml = entries[twb].decode("utf-8")
    names = list(entries)
    before = inspect(names, xml)
    if not before["packages"]:
        fail("No Packages/ folder in the workbook, so there's no packaged extension to keep.")
    fixed = resolve_fcp(xml)
    entries[twb] = fixed.encode("utf-8")
    # Tableau expects the .twb at the root of the package, so write it first.
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as o:
        for n in [twb] + [n for n in names if n != twb]:
            o.writestr(n, entries[n])
    after = inspect(names, fixed)
    problems, warnings = check_package(entries, twb, fixed)
    ok = after["extension_zones"] > 0 and after["switch_markers"] == 0 and not after["fallback_text"] and not problems
    if not ok:
        out.unlink()  # don't leave a copy that would publish without its extension
    print(json.dumps({"ok": ok, "in": str(src), "out": str(out.resolve()) if ok else None,
                      "switch_markers_resolved": before["switch_markers"],
                      "already_clean": before["switch_markers"] == 0, **{k: after[k] for k in ("packages", "extension_zones", "fallback_text")},
                      "problems": problems, "warnings": warnings}, indent=2))
    sys.exit(0 if ok else 1)


def cmd_verify(a):
    src = Path(a.inp).expanduser()
    entries, twb = load(src)
    info = inspect(list(entries), entries[twb].decode("utf-8"))
    ok = info["extension_zones"] > 0 and not info["fallback_text"]
    print(json.dumps({"ok": ok, "file": str(src), **info}, indent=2))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fix", help="Write a copy with the Packages switch resolved to 'true'")
    f.add_argument("--in", dest="inp", required=True, help=".twbx, or a folder with one .twb and a Packages/ folder")
    f.add_argument("--out", help="Fixed-for-publish copy (default: <name>.fixed-for-publish.twbx next to the input)")
    v = sub.add_parser("verify", help="Check a .twbx for extension zones and the fallback text")
    v.add_argument("--in", dest="inp", required=True, help=".twbx to check")
    a = ap.parse_args()
    try:
        (cmd_fix if a.cmd == "fix" else cmd_verify)(a)
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
