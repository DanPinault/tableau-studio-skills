#!/usr/bin/env python3
"""Make a workbook with a packaged extension survive publishing to Tableau Cloud.

Tableau Studio wraps packaged-extension zones in a `_.fcp.Packages` feature switch. Sites that
don't support the switch resolve it to "false" on publish and swap each extension for a
"removed when workbook was downgraded" text box. `fix` resolves the switch to "true" in a
copy of the .twbx (workbooks without the switch are copied as-is); `verify` checks any .twbx (for example the server's copy) for extension
zones and the fallback text. `fix` also runs the checks Tableau applies at publish time
(.twb at the archive root, a .trex per package, requestedOrigins as one string, referenced
Data/ files present) and warns about runtime risks. Standard library only; prints JSON.

  fix_packages_for_publish.py fix --in WORKBOOK.twbx|FOLDER [--out FIXED-FOR-PUBLISH.twbx] [--force]

FOLDER is an unzipped workbook: one .twb next to a Packages/ folder (a data-app workspace).
More than one .twb fails with status "multiple_workbooks" and lists them.
  fix_packages_for_publish.py verify --in WORKBOOK.twbx
"""
import argparse, json, os, re, shutil, sys, tempfile, zipfile
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


class Source:
    """A .twbx file or an unzipped workbook folder. Members are read only when needed, so large
    Data/ files are streamed to the output instead of being held in memory."""

    def __init__(self, src):
        self.zip = None
        if src.is_dir():
            twbs = sorted(f.name for f in src.glob("*.twb"))
            files = [f for f in sorted(src.rglob("*")) if f.is_file()
                     and not any(part.startswith(".") and part != ".agents" for part in f.relative_to(src).parts)
                     and f.suffix.lower() != ".twbx"]
            # Resources/.agents/ (agent docs) travels with the workbook, per Tableau's data-app layout.
            files = [f for f in files if ".agents" not in f.relative_to(src).parts
                     or f.relative_to(src).as_posix().startswith("Resources/.agents/")]
            self.files = {f.relative_to(src).as_posix(): f for f in files}
            if not twbs:
                fail(f"Expected exactly one .twb directly in {src}, found 0.")
        else:
            self.zip = zipfile.ZipFile(src)
            self.files = {i.filename: i for i in self.zip.infolist() if not i.filename.endswith("/")}
            twbs = sorted(n for n in self.files if n.endswith(".twb"))
            if not twbs:
                self.close()
                fail("No .twb inside the file; is it a .twbx?")
        if len(twbs) > 1:
            self.close()
            fail(f"{src.name} holds {len(twbs)} workbooks; ask which one to publish.",
                 status="multiple_workbooks", multiple_workbooks=twbs)
        self.twb = twbs[0]
        self.names = list(self.files)

    def read(self, n):
        return self.zip.read(self.files[n]) if self.zip else self.files[n].read_bytes()

    def copy_into(self, out, n):
        """Stream one member into the output zip without loading it whole."""
        if not self.zip:
            out.write(self.files[n], n)
            return
        info = self.files[n]
        zi = zipfile.ZipInfo(n, date_time=info.date_time)
        zi.compress_type, zi.file_size, zi.external_attr = zipfile.ZIP_DEFLATED, info.file_size, info.external_attr
        with self.zip.open(info) as r, out.open(zi, "w") as w:
            shutil.copyfileobj(r, w, 1 << 20)

    def close(self):
        if self.zip:
            self.zip.close()


def inspect(names, xml):
    return {
        "packages": sorted({n.split("/")[1] for n in names if n.startswith("Packages/") and n.count("/") > 1}),
        # Other FCP switches (e.g. _.fcp.VizExtensions in Tableau's own samples) are left as-is.
        "extension_zones": len(re.findall(r"<(?:_\.fcp\.\w+\.true\.\.\.)?add-in ", xml)),
        "switch_markers": len(re.findall(P, xml)),
        "fallback_text": FALLBACK in xml,
    }


def check_package(src, twb, xml):
    """Return (problems, warnings). Problems make publish fail or leave the app without data."""
    problems, warnings = [], []
    entries = set(src.names)
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
                          src.read(t).decode("utf-8", "replace"))
            if m:
                trex_versions[m.group(1)] = m.group(2)
        declared = set()
        if base + "manifest.json" in entries:
            try:
                origins = json.loads(src.read(base + "manifest.json")).get("requestedOrigins")
            except (ValueError, AttributeError):
                origins = None
                problems.append(f"{pkg}: manifest.json isn't valid JSON.")
            if origins is not None and not isinstance(origins, str):
                problems.append(f"{pkg}: requestedOrigins must be one space-separated string; Tableau ignores "
                                f"a {type(origins).__name__} and blocks every external origin.")
            elif origins:
                declared = {o.lower().rstrip("/") for o in origins.split()}
        undeclared, secrets = set(), []
        for n in sorted(entries):
            name = n.rsplit("/", 1)[-1]
            if not n.startswith(base) or name.startswith("tableau.extensions."):
                continue
            data = src.read(n)
            if b"\0" in data[:8192]:
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


def fail(msg, **extra):
    print(json.dumps({"ok": False, **extra, "error": msg}, indent=2 if extra else None))
    sys.exit(1)


def cmd_fix(a):
    src = Path(a.inp).expanduser().resolve()
    source = Source(src)
    twb = source.twb
    stem = Path(twb).stem if src.is_dir() else src.stem
    out = (Path(a.out).expanduser() if a.out else src.with_name(stem + ".fixed-for-publish.twbx")).resolve()
    if out.suffix.lower() != ".twbx":
        fail("--out must end in .twbx.")
    if out == src:
        fail("--out must differ from --in; the original is never modified.")
    if out.exists() and not a.force:
        fail(f"{out} already exists. Choose another --out, or pass --force to replace it.")
    xml = source.read(twb).decode("utf-8")
    names = source.names
    before = inspect(names, xml)
    if not before["packages"]:
        # Not an error in the file: there is no packaged extension to fix. Zones here are URL/hosted extensions.
        print(json.dumps({"ok": False, "status": "no_packages", "no_packages": True, "in": str(src), "out": None,
                          "packages": [], "extension_zones": before["extension_zones"],
                          "error": "No Packages/ folder in the workbook, so there's no packaged extension to keep."},
                         indent=2))
        sys.exit(1)
    fixed = resolve_fcp(xml)
    after = inspect(names, fixed)
    problems, warnings = check_package(source, twb, fixed)
    ok = after["extension_zones"] > 0 and after["switch_markers"] == 0 and not after["fallback_text"] and not problems
    if ok:
        # Write to a temporary file beside --out and move it into place only when complete, so a failure
        # never leaves a partial copy and never removes a file this run didn't create.
        fd, tmp = tempfile.mkstemp(suffix=".partial", dir=out.parent)
        os.close(fd)
        try:
            # Tableau expects the .twb at the root of the package, so write it first.
            # Only the .twb is rewritten; every other member is streamed across unchanged.
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True, strict_timestamps=False) as o:
                o.writestr(twb, fixed.encode("utf-8"))
                for n in names:
                    if n != twb:
                        source.copy_into(o, n)
            os.replace(tmp, out)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
    source.close()
    st = None if src.is_dir() else src.stat()
    print(json.dumps({"ok": ok, "in": str(src), "out": str(out) if ok else None,
                      "in_size": st and st.st_size, "in_mtime": st and st.st_mtime,
                      "switch_markers_resolved": before["switch_markers"],
                      "already_clean": before["switch_markers"] == 0, **{k: after[k] for k in ("packages", "extension_zones", "fallback_text")},
                      "problems": problems, "warnings": warnings}, indent=2))
    sys.exit(0 if ok else 1)


def cmd_verify(a):
    src = Path(a.inp).expanduser()
    source = Source(src)
    info = inspect(source.names, source.read(source.twb).decode("utf-8"))
    source.close()
    ok = info["extension_zones"] > 0 and not info["fallback_text"]
    print(json.dumps({"ok": ok, "file": str(src), **info}, indent=2))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fix", help="Write a copy with the Packages switch resolved to 'true'")
    f.add_argument("--in", dest="inp", required=True, help=".twbx, or a folder with one .twb and a Packages/ folder")
    f.add_argument("--out", help="Fixed-for-publish copy (default: <name>.fixed-for-publish.twbx next to the input)")
    f.add_argument("--force", action="store_true", help="Replace --out if it already exists (default: refuse)")
    v = sub.add_parser("verify", help="Check a .twbx for extension zones and the fallback text")
    v.add_argument("--in", dest="inp", required=True, help=".twbx to check")
    a = ap.parse_args()
    try:
        (cmd_fix if a.cmd == "fix" else cmd_verify)(a)
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
