"""
Build a SINGLE self-contained HTML for static hosting on any public,
framable host, which serves one HTML file with no backend.

Two vendored personas share the same D3/keynote skin and data contract:
  - coo : numbered-chapter operations brief (coo-brief.html.txt)
  - cfo : pinned/sticky margin brief (cfo-brief.html.txt)
A persona build renders from the template's own SEED; nothing is fetched or baked
at build time. Use --template to build your adapted copy instead.

Every build:
  - inlines D3 (skill-expertise/d3.min.js.txt) so the file has ZERO external <script src>
    (fully self-contained — one HTML file, no dependencies to fetch), and
  - for --extension, inlines the Tableau Extensions API so the same file also
    works as a .trex dashboard extension (initializeAsync resolves); otherwise
    the Extensions tag is stripped (initExtension() is guarded on window.tableau
    and no-ops without it).

Run it in place: vendored inputs are read from this script's folder. Output goes
to --out, or by default under the current working directory.

    python3 build_standalone.py                 # COO plain page   -> ./dist/index.html
    python3 build_standalone.py --extension      # COO .trex build  -> ./dist-ext/index.html
    python3 build_standalone.py --persona cfo --extension   # CFO .trex -> ./dist-ext/cfo-index.html
    python3 build_standalone.py --template my-brief.html --out story.html   # adapted copy, plain page

Packaged mode (Tableau Data App, the default delivery): the HTML runs on Tableau Cloud
inside the .twbx and reads the published datasource live with queryAsync, so nothing is
baked in. --query names the VDS query JSON you validated with query-datasource; it is
injected as window.__PKG_QUERY__ and the newer Extensions API (with queryAsync) is inlined.
package_extension.py then wraps the output into a .twbx.

    python3 build_standalone.py --persona cfo --packaged --query q.json --out story.html
    python3 build_standalone.py --template my-brief.html --packaged --query q.json --out story.html
"""
import os, sys, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
# Vendored files ship as .txt so the skill folder only holds .md/.py/.txt files.
D3 = os.path.join(HERE, "d3.min.js.txt")
EXT_LIB = os.path.join(HERE, "tableau.extensions.1.latest.js.txt")
# Data Apps build of the Extensions API: adds workbook.getAllDataSourcesAsync,
# datasource.readMetadataAsync and datasource.queryAsync (the 1.latest build above lacks them).
PKG_LIB = os.path.join(HERE, "tableau.extensions.data-apps.min.js.txt")

CDN_TAG = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'
# Inlined so the file is fully self-contained (zero external <script src>). The
# Extensions API is only needed when embedded as a Tableau .trex iframe; the standalone
# (full-screen page) build drops it — initExtension() is guarded on window.tableau,
# so it simply no-ops without it.
EXT_TAG = '<script src="https://tableau.github.io/extensions-api/lib/tableau.extensions.1.latest.js" async></script>'

# Default outputs are relative to the current working directory, never this folder.
PERSONAS = {
    "coo": {
        "template": os.path.join(HERE, "coo-brief.html.txt"),
        "out":      os.path.join("dist", "index.html"),
        "out_ext":  os.path.join("dist-ext", "index.html"),
    },
    "cfo": {
        "template": os.path.join(HERE, "cfo-brief.html.txt"),
        "out":      os.path.join("dist", "cfo.html"),
        "out_ext":  os.path.join("dist-ext", "cfo-index.html"),
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", choices=sorted(PERSONAS), default="coo",
                    help="which brief to build (default: coo)")
    ap.add_argument("--keep-cdn", action="store_true", help="reference D3 from CDN instead of inlining")
    ap.add_argument("--extension", action="store_true",
                    help="inline the Tableau Extensions API + emit the dist-ext build "
                         "so the file also works as a .trex dashboard extension")
    ap.add_argument("--packaged", action="store_true",
                    help="packaged extension (Data App): inline the Data Apps Extensions API, "
                         "inject --query as window.__PKG_QUERY__, bake no data")
    ap.add_argument("--query", help="VDS query JSON for --packaged "
                                    "({datasource, fields, filters}); validated with query-datasource")
    ap.add_argument("--template", help="build this HTML instead of the persona template "
                                       "(its SEED is the fallback data)")
    ap.add_argument("--out", help="output path (default: under the current working directory)")
    args = ap.parse_args()
    if args.packaged and args.extension:
        sys.exit("--packaged and --extension are separate delivery modes; pick one")
    if args.packaged and not args.query:
        sys.exit("--packaged needs --query <q.json> (the live VDS query the story reads)")
    cfg = dict(PERSONAS[args.persona])
    if args.template:
        cfg["template"] = os.path.abspath(args.template)
    out = os.path.abspath(args.out or os.path.join(
        os.getcwd(),
        os.path.join("dist-pkg", f"{args.persona}-index.html") if args.packaged
        else cfg["out_ext"] if args.extension else cfg["out"]))
    src = "packaged-live" if args.packaged else "template-seed"

    html = open(cfg["template"], encoding="utf-8").read()

    # 1) inline D3 (or keep the CDN tag if asked)
    if not args.keep_cdn:
        d3src = open(D3, encoding="utf-8").read()
        html = html.replace(CDN_TAG, f"<script>{d3src}</script>")

    # 2) Extensions API: inline it for the .trex build (so initializeAsync works AND
    #    the file stays fully self-contained); strip it otherwise.
    #    Packaged builds inline the Data Apps build instead and inject the live query.
    if args.packaged:
        if not os.path.exists(PKG_LIB):
            sys.exit(f"missing {PKG_LIB} (the Data Apps Extensions API ships with this skill)")
        query = json.load(open(args.query, encoding="utf-8"))
        if not query.get("fields"):
            sys.exit(f"{args.query} has no 'fields'; it must be a VDS query")
        pkgsrc = open(PKG_LIB, encoding="utf-8").read()
        if EXT_TAG not in html:
            sys.exit("template has no Extensions API tag to replace; see style-guide.md")
        html = html.replace(EXT_TAG, f"<script>{pkgsrc}</script>")
        # </ in a JSON string can't close the script tag once escaped
        qjs = json.dumps(query, separators=(",", ":")).replace("</", "<\\/")
        html = html.replace("<head>", f"<head>\n<script>window.__PKG_QUERY__ = {qjs};</script>", 1)
    elif args.extension:
        if not os.path.exists(EXT_LIB):
            sys.exit(f"missing {EXT_LIB}\n  fetch it once with:\n"
                     f"  curl -fsSL https://tableau.github.io/extensions-api/lib/"
                     f"tableau.extensions.1.latest.js -o {EXT_LIB}")
        extsrc = open(EXT_LIB, encoding="utf-8").read()
        html = html.replace(EXT_TAG, f"<script>{extsrc}</script>")
    else:
        html = html.replace(EXT_TAG, "")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)

    size = os.path.getsize(out)
    mode = ("packaged extension (Data App)" if args.packaged
            else "extension (.trex)" if args.extension else "plain page")
    print(f"wrote {out}  [{args.persona} · {mode}]")
    print(f"  source={src}  size={size/1024:.0f} KB  self-contained={'no (CDN)' if args.keep_cdn else 'yes'}")


if __name__ == "__main__":
    main()
