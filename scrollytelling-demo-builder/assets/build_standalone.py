"""
Build a SINGLE self-contained HTML for static hosting on any public,
framable host, which serves one HTML file with no backend.

Two personas share the same D3/keynote skin and data contract; each bakes a live
snapshot at build time (PAT never leaves this machine):
  - coo : "Running Hot" operations brief. pulse_values.fetch() returns a fully-
          computed COO contract; it is baked in as window.__LIVE__.
  - cfo : "The Quiet Erosion" margin brief. cfo_values.fetch() returns the RAW
          feeder rows (Date × Facility × Client Segment + 6 measures); the browser
          runs contractFromRows() over them — identical math to the live tile.
Each persona names its fetch module in PERSONAS[...]["module"]. If the fetch fails
(VDS/auth hiccup) the build degrades to the template's own SEED and skips injection.

Either way the build:
  - inlines D3 (vendor/d3.min.js) so the file has ZERO external <script src>
    (fully self-contained — one HTML file, no dependencies to fetch), and
  - for --extension, inlines the Tableau Extensions API so the same file also
    works as a .trex dashboard extension (initializeAsync resolves); otherwise
    the Extensions tag is stripped (initExtension() is guarded on window.tableau
    and no-ops without it).

    python3 build_standalone.py                 # COO live snapshot  -> dist/index.html
    python3 build_standalone.py --extension      # COO .trex build    -> dist-ext/index.html
    python3 build_standalone.py --persona cfo --extension   # CFO .trex -> dist-ext/cfo-index.html
    python3 build_standalone.py --seed           # COO, bundled seed (no Tableau call)

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
D3 = os.path.join(HERE, "vendor", "d3.min.js")
EXT_LIB = os.path.join(HERE, "vendor", "tableau.extensions.1.latest.js")
# Data Apps build of the Extensions API: adds workbook.getAllDataSourcesAsync,
# datasource.readMetadataAsync and datasource.queryAsync (the 1.latest build above lacks them).
PKG_LIB = os.path.join(HERE, "vendor", "tableau.extensions.data-apps.min.js")

CDN_TAG = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'
# Inlined so the file is fully self-contained (zero external <script src>). The
# Extensions API is only needed when embedded as a Tableau .trex iframe; the standalone
# (full-screen page) build drops it — initExtension() is guarded on window.tableau,
# so it simply no-ops without it.
EXT_TAG = '<script src="https://tableau.github.io/extensions-api/lib/tableau.extensions.1.latest.js" async></script>'

PERSONAS = {
    "coo": {
        "template": os.path.join(HERE, "public", "coo-brief.html"),
        "out":      os.path.join(HERE, "dist", "index.html"),
        "out_ext":  os.path.join(HERE, "dist-ext", "index.html"),
        "live": True,                        # bake a live snapshot
        "module": "pulse_values",            # fetch() returns a fully-computed COO contract
        "marker": "// ---------- seed data",  # window.__LIVE__ is injected before this
    },
    "cfo": {
        "template": os.path.join(HERE, "public", "cfo-brief.html"),
        "out":      os.path.join(HERE, "dist", "cfo.html"),
        "out_ext":  os.path.join(HERE, "dist-ext", "cfo-index.html"),
        "live": True,                        # bake raw feeder rows; browser computes contract
        "module": "cfo_values",              # fetch() returns {cols, rows} at Date×Facility×Segment
        "marker": "// __LIVE_INJECT__",       # window.__LIVE__ is injected before this anchor
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", choices=sorted(PERSONAS), default="coo",
                    help="which brief to build (default: coo)")
    ap.add_argument("--seed", action="store_true", help="skip live fetch, use server.SEED")
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
                                       "(no live bake; the template's SEED is the fallback)")
    ap.add_argument("--out", help="output path (overrides the persona default)")
    args = ap.parse_args()
    if args.packaged and args.extension:
        sys.exit("--packaged and --extension are separate delivery modes; pick one")
    if args.packaged and not args.query:
        sys.exit("--packaged needs --query <q.json> (the live VDS query the story reads)")
    cfg = dict(PERSONAS[args.persona])
    if args.template:
        cfg.update(template=os.path.abspath(args.template), live=False, marker=None)
    if args.packaged:
        cfg["live"] = False                  # live data comes from queryAsync at view time
    out = args.out or (os.path.join(HERE, "dist-pkg", f"{args.persona}-index.html") if args.packaged
                       else cfg["out_ext"] if args.extension else cfg["out"])

    # ---- resolve the data snapshot to bake (only when this persona bakes live) ----
    data, src = None, "packaged-live" if args.packaged else "none"
    if cfg["live"] and cfg["marker"]:
        if args.seed:
            # dev-only: bake the COO server.SEED (only meaningful for the coo persona;
            # other personas fall back to the template's own SEED, so skip injection)
            import server
            data = dict(server.SEED) if args.persona == "coo" else None
            src = "seed" if data is not None else "template-seed"
        else:
            import importlib
            try:
                data = importlib.import_module(cfg["module"]).fetch()
                src = data.get("source", "live")
            except Exception as e:
                # degrade gracefully: render from the template's SEED, skip injection so
                # a transient VDS/auth hiccup never produces a broken page.
                print(f"  WARN: {cfg['module']}.fetch() failed ({e}); "
                      f"rendering from template SEED", file=sys.stderr)
                data, src = None, "seed-fallback"

    html = open(cfg["template"], encoding="utf-8").read()

    # 1) inline D3 (or keep the CDN tag if asked)
    if not args.keep_cdn:
        d3src = open(D3, encoding="utf-8").read()
        html = html.replace(CDN_TAG, f"<script>{d3src}</script>")

    # 1b) Extensions API: inline it for the .trex build (so initializeAsync works AND
    #     the file stays fully self-contained); strip it otherwise.
    #     Packaged builds inline the Data Apps build instead and inject the live query.
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

    # 2) bake the real data in as window.__LIVE__ (boot() prefers it) — personas that
    #    ship a grounded SEED (e.g. cfo) skip this and render straight from SEED.
    if data is not None and cfg["marker"]:
        payload = "window.__LIVE__ = " + json.dumps(data, separators=(",", ":")) + ";\n"
        html = html.replace("<script>\n" + cfg["marker"],
                            "<script>\n" + payload + cfg["marker"], 1)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)

    size = os.path.getsize(out)
    mode = ("packaged extension (Data App)" if args.packaged
            else "extension (.trex)" if args.extension else "plain page")
    print(f"wrote {out}  [{args.persona} · {mode}]")
    print(f"  source={src}  size={size/1024:.0f} KB  self-contained={'no (CDN)' if args.keep_cdn else 'yes'}")
    if data is not None and "utilization" in data:            # coo contract
        npts = len(data.get("trend") or [])
        print(f"  util={data['utilization']['value']}%  peak={data['peak']['facility']} "
              f"{data['peak']['value']}%  trend_pts={npts}")
    elif data is not None and "rows" in data:                 # cfo raw feeder rows
        print(f"  rows={len(data['rows'])}  asof={data.get('asof')}  "
              f"cols={[c['fieldName'] for c in data.get('cols', [])]}")


if __name__ == "__main__":
    main()
