"""
Package a scrollytelling story as a Tableau packaged extension (Data App) and publish it.

The story HTML (from build_standalone.py --packaged) is embedded in a .twbx as a worksheet
(viz) extension. Tableau Cloud hosts it, and it reads a published datasource live with
queryAsync, so there is no external host, no feeder sheet, and no Publish dialog.

    python3 package_extension.py configure --server https://<pod>.online.tableau.com --site <site> --pat-name <name>
    python3 package_extension.py store-secret            # prompts; the secret never appears in argv or chat
    python3 package_extension.py check                   # config, secret, sign-in, Packages enabled?
    python3 package_extension.py datasources --search 3PL
    python3 package_extension.py query --datasource "<DS name>" --query q.json     # validate via VDS
    python3 package_extension.py build --html story.html --name "CFO Brief" --datasource "<DS name>" --out-dir <dir>
    python3 package_extension.py publish --twbx "<dir>/CFO Brief.twbx" --project "<project>" --image check.png

Secret lookup: env TABLEAU_PAT_SECRET, else the macOS Keychain. If this skill has no profile
yet, an existing pulse-metric-builder profile (and its Keychain item) is reused.
Output is JSON on stdout; exit 2 means setup is incomplete.
"""
import argparse, json, os, platform, re, shutil, subprocess, sys, uuid, zipfile
import urllib.error, urllib.parse, urllib.request
from xml.sax.saxutils import escape, quoteattr

APP = "tableau-scrollytelling-demo-builder"
FALLBACK_APP = "tableau-pulse-metric-builder"
CFG_ROOT = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
SECRET_ENV = "TABLEAU_PAT_SECRET"
SOURCE_BUILD = "0.0.0 (0000.26.1026.0859)"   # Cloud accepts VizExtension workbooks tagged with this
ICON = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


class Fail(Exception):
    def __init__(self, msg, hint=None, code=1, **extra):
        super().__init__(msg)
        self.msg, self.hint, self.code, self.extra = msg, hint, code, extra


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# ---------- config + secret ----------

def cfg_path(app):
    return os.path.join(CFG_ROOT, app, "config.json")


def load_config(app=APP):
    p = cfg_path(app)
    if not os.path.exists(p):
        return {"active": "default", "profiles": {}}
    with open(p) as f:
        return json.load(f)


def profile(args):
    """(service, name, profile): this skill's profile, else a pulse-metric-builder one."""
    for app in (APP, FALLBACK_APP):
        cfg = load_config(app)
        name = args.profile or cfg.get("active") or "default"
        p = cfg.get("profiles", {}).get(name)
        if p:
            return app, name, p
    return APP, args.profile or "default", {}


def keychain_account(p):
    return f"{p['pat_name']}@{urllib.parse.urlparse(p['server']).netloc}/{p['site']}"


def get_secret(app, p):
    if os.environ.get(SECRET_ENV):
        return os.environ[SECRET_ENV], "env"
    if platform.system() == "Darwin" and shutil.which("security") and p.get("pat_name"):
        r = subprocess.run(["security", "find-generic-password", "-s", app, "-a", keychain_account(p), "-w"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip(), "keychain"
    return None, None


# ---------- HTTP ----------

class Session:
    def __init__(self, app, p):
        missing = [k for k in ("server", "site", "pat_name") if not p.get(k)]
        if not missing and not get_secret(app, p)[0]:
            missing.append("pat_secret")
        if missing:
            raise Fail("Setup incomplete", "Run `configure` / `store-secret`, then `check`.", 2, missing=missing)
        self.server = p["server"].rstrip("/")
        self.host = urllib.parse.urlparse(self.server).netloc
        self.site_url = p["site"]
        ver = self._req("GET", f"{self.server}/api/2.4/serverinfo")["serverInfo"]["restApiVersion"]
        self.api = f"{self.server}/api/{ver}"
        body = {"credentials": {"personalAccessTokenName": p["pat_name"],
                                "personalAccessTokenSecret": get_secret(app, p)[0],
                                "site": {"contentUrl": p["site"]}}}
        try:
            cred = self._req("POST", f"{self.api}/auth/signin", body)["credentials"]
        except Fail as e:
            if e.extra.get("status") == 401:
                raise Fail("Sign-in rejected (401)", "Check the PAT name, re-run store-secret, and confirm the site "
                           "content URL. PATs also expire after 15 days unused.", 2)
            raise
        self.token, self.site_id = cred["token"], cred["site"]["id"]

    def _req(self, method, url, body=None, raw=False, params=None, headers=None, data=None, timeout=120):
        if params:
            url += "?" + urllib.parse.urlencode(params)
        h = {"Accept": "application/json"}
        if getattr(self, "token", None):
            h["X-Tableau-Auth"] = self.token
        if body is not None:
            data = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                content = r.read()
        except urllib.error.HTTPError as e:
            raise Fail(f"{method} {url.split('?')[0]} -> {e.code}", None, 1, status=e.code,
                       response=e.read().decode(errors="replace")[:1500])
        except (urllib.error.URLError, TimeoutError) as e:
            raise Fail(f"Can't reach {url.split('?')[0]}: {getattr(e, 'reason', e)}",
                       "Network problem or timeout. Check the connection and the server URL, then re-run.")
        if raw:
            return content
        return json.loads(content) if content.strip() else {}

    def rest(self, method, path, body=None, **kw):
        return self._req(method, f"{self.api}/sites/{self.site_id}{path}", body, **kw)

    def vds(self, op, body):
        return self._req("POST", f"{self.server}/api/v1/vizql-data-service/{op}", body, timeout=300)

    def sign_out(self):
        try:
            self._req("POST", f"{self.api}/auth/signout")
        except Fail:
            pass


def session(args):
    app, _, p = profile(args)
    return Session(app, p)


def find_datasource(s, name):
    hits = s.rest("GET", "/datasources", params={"filter": f"name:eq:{name}", "pageSize": 100})
    lst = hits.get("datasources", {}).get("datasource", [])
    if not lst:
        raise Fail(f"Published datasource {name!r} not found",
                   "Names are exact; run `datasources --search <word>` to list candidates.")
    if len(lst) > 1:
        raise Fail(f"{len(lst)} published datasources are named {name!r}",
                   "Rename one, or publish the story against a uniquely named datasource.",
                   projects=[d.get("project", {}).get("name") for d in lst])
    return lst[0]


# ---------- commands ----------

def cmd_configure(args):
    cfg = load_config(APP)
    name = args.profile or "default"
    cfg.setdefault("profiles", {})[name] = {"server": args.server.rstrip("/"), "site": args.site,
                                            "pat_name": args.pat_name}
    cfg["active"] = name
    os.makedirs(os.path.dirname(cfg_path(APP)), exist_ok=True)
    with open(cfg_path(APP), "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(cfg_path(APP), 0o600)
    out({"ok": True, "profile": name, "config": cfg_path(APP),
         "next": "run `store-secret` (macOS) or export TABLEAU_PAT_SECRET, then `check`"})


def cmd_store_secret(args):
    app, name, p = profile(args)
    if not p:
        raise Fail("No profile yet", "Run `configure` first.", 2)
    if platform.system() != "Darwin" or not shutil.which("security"):
        raise Fail("Keychain is macOS-only", f"Export {SECRET_ENV} in your shell instead (never paste it in chat).", 2)
    # bare -w makes `security` prompt for the secret, so it never lands in argv or shell history
    r = subprocess.run(["security", "add-generic-password", "-U", "-s", app, "-a", keychain_account(p),
                        "-l", f"{app} ({name})", "-w"])
    if r.returncode:
        raise Fail("Keychain write failed", "Re-run and enter the PAT secret at the prompt.")
    out({"ok": True, "service": app, "account": keychain_account(p)})


def cmd_check(args):
    app, name, p = profile(args)
    res = {"profile": name, "config_from": app,
           "server": p.get("server"), "site": p.get("site"), "pat_name": p.get("pat_name"),
           "secret": get_secret(app, p)[1] if p else None}
    s = Session(app, p)
    try:
        res["signin"] = "ok"
        try:
            s._req("GET", f"{s.server}/api/exp/sites/{s.site_id}/packages")
            res["packages"] = "enabled"
        except Fail as e:
            res["packages"] = f"unavailable ({e.extra.get('status')})"
            res["hint"] = ("A site admin must turn on Settings > Packages > 'Allow Packages on this Site'. "
                           "Packaged extensions will not run until then; use hosted mode meanwhile.")
    finally:
        s.sign_out()
    out(res)


def cmd_datasources(args):
    s = session(args)
    try:
        params = {"pageSize": 1000, "fields": "id,name,contentUrl,project.name"}
        lst = s.rest("GET", "/datasources", params=params).get("datasources", {}).get("datasource", [])
        q = (args.search or "").lower()
        out([{"name": d["name"], "project": d.get("project", {}).get("name"), "contentUrl": d.get("contentUrl")}
             for d in lst if q in d["name"].lower()])
    finally:
        s.sign_out()


def cmd_query(args):
    q = json.load(open(args.query, encoding="utf-8"))
    s = session(args)
    try:
        ds = find_datasource(s, args.datasource or q.get("datasource"))
        body = {"datasource": {"datasourceLuid": ds["id"]},
                "query": {k: v for k, v in q.items() if k in ("fields", "filters")}}
        rows = s.vds("query-datasource", body).get("data", [])
        out({"datasource": ds["name"], "rows": len(rows), "keys": list(rows[0]) if rows else [],
             "sample": rows[:3]})
    finally:
        s.sign_out()


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not s:
        raise Fail("Name needs at least one letter or digit")
    return s


def twb_xml(name, pkg_id, version, ds_name, content_url, host, site):
    a = quoteattr
    ds_ref = f"sqlproxy.{uuid.uuid4().hex[:28]}"
    url = f"tableaulocalext:///{pkg_id}/content/index.html"
    guid = lambda: "{" + str(uuid.uuid4()).upper() + "}"
    return f"""<?xml version='1.0' encoding='utf-8' ?>

<workbook original-version='18.1' source-build={a(SOURCE_BUILD)} source-platform='mac' version='18.1' xml:base='https://localhost' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <AnimationOnByDefault />
    <MarkAnimation />
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences />
  <datasources>
    <datasource caption={a(ds_name)} inline='true' name={a(ds_ref)} version='18.1'>
      <repository-location derived-from={a(f"https://{host}/t/{site}/datasources/{content_url}?rev=1.0")} id={a(content_url)} path={a(f"/t/{site}/datasources")} revision='1.0' site={a(site)} />
      <connection channel='https' class='sqlproxy' dbname={a(content_url)} directory='/dataserver' port='443' server={a(host)} server-ds-friendly-name={a(ds_name)} username=''>
        <relation name='sqlproxy' table='[sqlproxy]' type='table' />
      </connection>
      <aliases enabled='yes' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name={a(name)}>
      <table>
        <view>
          <datasources>
            <datasource caption={a(ds_name)} name={a(ds_ref)} />
          </datasources>
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='VizExtension' />
            <add-in add-in-id={a(pkg_id)} extension-url={a(url)} extension-version={a(version)} instance-id={a(uuid.uuid4().hex.upper())}>
              <instance-settings />
              <type-settings>
                <worksheet />
              </type-settings>
            </add-in>
          </pane>
        </panes>
        <rows />
        <cols />
      </table>
      <simple-id uuid={a(guid())} />
    </worksheet>
  </worksheets>
  <windows>
    <window class='worksheet' maximized='true' name={a(name)}>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
      </cards>
      <simple-id uuid={a(guid())} />
    </window>
  </windows>
  <referenced-extensions>
    <referenced-extension>
      <manifest manifest-version='0.1'>
        <worksheet-extension extension-version={a(version)} id={a(pkg_id)}>
          <default-locale>en_US</default-locale>
          <name>{escape(name)}</name>
          <description>Scrollytelling story (packaged extension).</description>
          <author email='noreply@tableau.com' name='scrollytelling-demo-builder' organization='Tableau' website='https://www.tableau.com' />
          <min-api-version>1.11</min-api-version>
          <source-location>
            <url>{escape(url)}</url>
          </source-location>
          <icon>{ICON}</icon>
          <permissions>
            <permission>full data</permission>
          </permissions>
          {ENCODING}
        </worksheet-extension>
      </manifest>
      <referenced-views>
        <referenced-view instances='1' viewId={a(name)} />
      </referenced-views>
    </referenced-extension>
  </referenced-extensions>
</workbook>
"""


ENCODING = """<encoding id='field'>
            <display-name>Data</display-name>
            <role-spec>
              <role-type>discrete-dimension</role-type>
              <role-type>discrete-measure</role-type>
              <role-type>continuous-dimension</role-type>
              <role-type>continuous-measure</role-type>
            </role-spec>
            <fields max-count='50' />
            <encoding-icon token='level' />
          </encoding>"""


def trex_xml(name, pkg_id, version):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<manifest manifest-version="0.1" xmlns="http://www.tableau.com/xml/extension_manifest">
  <worksheet-extension id={quoteattr(pkg_id)} extension-version={quoteattr(version)}>
    <default-locale>en_US</default-locale>
    <name resource-id="name" />
    <description>Scrollytelling story: reads its published datasource live via the Extensions API.</description>
    <author name="scrollytelling-demo-builder" email="noreply@tableau.com" website="https://www.tableau.com" />
    <min-api-version>1.11</min-api-version>
    <source-location>
      <url>index.html</url>
    </source-location>
    <icon>{ICON}</icon>
    <permissions>
      <permission>full data</permission>
    </permissions>
    {ENCODING.replace("'", '"')}
  </worksheet-extension>
  <resources>
    <resource id="name">
      <text locale="en_US">{escape(name)}</text>
    </resource>
  </resources>
</manifest>
"""


def cmd_build(args):
    html = open(args.html, encoding="utf-8").read()
    if "__PKG_QUERY__" not in html or "queryAsync" not in html:
        raise Fail("HTML is not a packaged build",
                   "Build it with build_standalone.py --packaged --query <q.json> first.")
    pkg_id = f"com.tableau.mcp.{slug(args.name)}"
    s = session(args)
    try:
        ds = find_datasource(s, args.datasource)
        host, site = s.host, s.site_url
    finally:
        s.sign_out()
    ws = os.path.join(os.path.abspath(args.out_dir), slug(args.name))
    pkg = os.path.join(ws, "Packages", pkg_id)
    if os.path.isdir(ws):
        shutil.rmtree(ws)
    os.makedirs(os.path.join(pkg, "extensions"))
    os.makedirs(os.path.join(pkg, "content"))
    with open(os.path.join(pkg, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"id": pkg_id, "version": args.version, "name": args.name,
                   "author": "scrollytelling-demo-builder", "requestedOrigins": ""}, f, indent=2)
    with open(os.path.join(pkg, "extensions", "data-app.trex"), "w", encoding="utf-8") as f:
        f.write(trex_xml(args.name, pkg_id, args.version))
    shutil.copyfile(args.html, os.path.join(pkg, "content", "index.html"))
    twb = os.path.join(ws, f"{args.name}.twb")
    with open(twb, "w", encoding="utf-8") as f:
        f.write(twb_xml(args.name, pkg_id, args.version, ds["name"], ds["contentUrl"], host, site))
    # zip from inside the workspace: entries are "<name>.twb" and "Packages/...", never a parent dir
    twbx = os.path.join(os.path.abspath(args.out_dir), f"{args.name}.twbx")
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(ws):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, ws))
    out({"twbx": twbx, "package_id": pkg_id, "datasource": ds["name"],
         "size_kb": round(os.path.getsize(twbx) / 1024), "workspace": ws})


def find_project(s, spec):
    """Resolve a project by name, or by path ("/Parent/Child") when names repeat across the tree."""
    parts = [p for p in spec.strip("/").split("/") if p]
    if not parts:
        raise Fail("Empty project name")
    hits = s.rest("GET", "/projects", params={"filter": f"name:eq:{parts[-1]}", "pageSize": 1000})
    hits = hits.get("projects", {}).get("project", [])
    if len(parts) > 1 or len(hits) > 1:
        allp = s.rest("GET", "/projects", params={"pageSize": 1000}).get("projects", {}).get("project", [])
        by_id = {p["id"]: p for p in allp}

        def path(p):
            names = []
            while p:
                names.append(p["name"])
                p = by_id.get(p.get("parentProjectId"))
            return "/" + "/".join(reversed(names))
        if len(parts) > 1:
            hits = [p for p in hits if path(p) == "/" + "/".join(parts)]
        elif len(hits) > 1:
            raise Fail(f"Project name {spec!r} is ambiguous",
                       "Pass the full path instead, e.g. --project \"/Parent/Child\".",
                       matches=sorted(path(p) for p in hits))
    if not hits:
        raise Fail(f"Project {spec!r} not found",
                   "Project names are exact and case-sensitive; nested projects take a path like \"/Parent/Child\".")
    return hits[0]


def cmd_publish(args):
    name = args.name or os.path.splitext(os.path.basename(args.twbx))[0]
    s = session(args)
    try:
        project = find_project(s, args.project)
        payload = json.dumps({"workbook": {"name": name, "showTabs": "false", "project": {"id": project["id"]}}})
        b = uuid.uuid4().hex
        with open(args.twbx, "rb") as f:
            blob = f.read()
        body = (f"--{b}\r\nContent-Disposition: name=\"request_payload\"\r\nContent-Type: application/json\r\n\r\n"
                f"{payload}\r\n--{b}\r\nContent-Disposition: name=\"tableau_workbook\"; "
                f"filename=\"{os.path.basename(args.twbx)}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
                ).encode() + blob + f"\r\n--{b}--\r\n".encode()
        wb = s.rest("POST", "/workbooks", params={"workbookType": "twbx", "overwrite": "true"}, data=body,
                    headers={"Content-Type": f"multipart/mixed; boundary={b}"}, timeout=600)["workbook"]
        conns = s.rest("GET", f"/workbooks/{wb['id']}/connections").get("connections", {}).get("connection", [])
        views = s.rest("GET", f"/workbooks/{wb['id']}/views").get("views", {}).get("view", [])
        base = f"{s.server}/#/site/{s.site_url}"
        res = {"workbook": wb["name"], "id": wb["id"], "webpage": wb.get("webpageUrl"),
               "connections": [{"type": c.get("type"), "datasource": c.get("datasource", {}).get("name")}
                               for c in conns],
               "views": [f"{base}/views/{v['contentUrl'].replace('/sheets/', '/')}" for v in views]}
        if args.image and views:
            # server-side render of the extension: the proof that the package ran and queried live
            png = s.rest("GET", f"/views/{views[0]['id']}/image", params={"resolution": "high", "maxAge": 1},
                         raw=True, headers={"Accept": "*/*"}, timeout=300)   # image/png gets a 406
            with open(args.image, "wb") as f:
                f.write(png)
            res["image"] = os.path.abspath(args.image)
        out(res)
    finally:
        s.sign_out()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("configure"); c.add_argument("--server", required=True)
    c.add_argument("--site", required=True); c.add_argument("--pat-name", required=True)
    sub.add_parser("store-secret")
    sub.add_parser("check")
    c = sub.add_parser("datasources"); c.add_argument("--search")
    c = sub.add_parser("query"); c.add_argument("--query", required=True); c.add_argument("--datasource")
    c = sub.add_parser("build"); c.add_argument("--html", required=True); c.add_argument("--name", required=True)
    c.add_argument("--datasource", required=True, help="exact published datasource name")
    c.add_argument("--out-dir", required=True); c.add_argument("--version", default="1.0.0")
    c = sub.add_parser("publish"); c.add_argument("--twbx", required=True); c.add_argument("--project", required=True, help="project name, or a path like \"/Parent/Child\" for nested projects")
    c.add_argument("--name"); c.add_argument("--image", help="save a server-side render of the view here (PNG)")
    args = ap.parse_args()
    try:
        {"configure": cmd_configure, "store-secret": cmd_store_secret, "check": cmd_check,
         "datasources": cmd_datasources, "query": cmd_query, "build": cmd_build,
         "publish": cmd_publish}[args.cmd](args)
    except Fail as e:
        out({"error": e.msg, "hint": e.hint, **e.extra})
        sys.exit(e.code)


if __name__ == "__main__":
    main()
