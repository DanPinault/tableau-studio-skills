#!/usr/bin/env python3
"""Create Tableau Pulse metric definitions and metrics through the Pulse REST API.

Standard library only. Every command prints JSON to stdout; errors print
{"error": ..., "hint": ...} and exit non-zero.

Nothing site-specific lives in the skill folder:
  - server, site and PAT name go in ~/.config/tableau-pulse-metric-builder/config.json
  - the PAT secret goes in the macOS Keychain (fallback: env var TABLEAU_PAT_SECRET)

Commands:
  check                          what's configured, what's missing, and whether sign-in works
  configure --server --site --pat-name [--profile]
  store-secret                   prompts for the PAT secret (hidden) and saves it to the Keychain
  datasources [--search TEXT]    published data sources: name, LUID, project, content URL
  fields --datasource LUID       columns from the .tds: caption -> internal name, role, type
  definitions [--datasource LUID] [--search TEXT]
  create --spec FILE [--dry-run] create definitions + one metric each, print Studio card settings
  metric --definition ID --period P   get or create the metric for a period
  rename --definition ID --name NEW
  delete --definition ID --yes

Exit codes: 0 ok, 1 API/other error, 2 setup missing, 3 spec incomplete or invalid.
"""

import argparse
import io
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

APP = "tableau-pulse-metric-builder"
CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), APP, "config.json")
SECRET_ENV = "TABLEAU_PAT_SECRET"

AGGS = ["SUM", "AVERAGE", "COUNT", "COUNT_DISTINCT", "MIN", "MAX", "USER"]  # USER = the UI's "Calculated"
FORMATS = ["NUMBER", "PERCENT", "CURRENCY"]
SENTIMENTS = ["UP", "DOWN", "NONE"]
GRANS = ["GRANULARITY_BY_DAY", "GRANULARITY_BY_WEEK", "GRANULARITY_BY_MONTH",
         "GRANULARITY_BY_QUARTER", "GRANULARITY_BY_YEAR"]
INSIGHTS = ["RISKY_MONOPOLY", "TOP_DRIVERS", "CURRENT_TREND", "BOTTOM_CONTRIBUTORS", "TOP_DETRACTORS",
            "NEW_TREND", "UNUSUAL_CHANGE", "RECORD_LEVEL_OUTLIERS", "CORRELATED_METRIC",
            "METRIC_FORECAST", "PACE_TO_GOAL"]
# period key -> (granularity, range, card tooltip)
PERIODS = {
    "today": ("DAY", "RANGE_CURRENT_PARTIAL", "Today"),
    "yesterday": ("DAY", "RANGE_LAST_COMPLETE", "Yesterday"),
    "wtd": ("WEEK", "RANGE_CURRENT_PARTIAL", "Week to Date"),
    "last-week": ("WEEK", "RANGE_LAST_COMPLETE", "Last Week"),
    "mtd": ("MONTH", "RANGE_CURRENT_PARTIAL", "Month to Date"),
    "last-month": ("MONTH", "RANGE_LAST_COMPLETE", "Last Month"),
    "qtd": ("QUARTER", "RANGE_CURRENT_PARTIAL", "Quarter to Date"),
    "last-quarter": ("QUARTER", "RANGE_LAST_COMPLETE", "Last Quarter"),
    "ytd": ("YEAR", "RANGE_CURRENT_PARTIAL", "Year to Date"),
    "last-year": ("YEAR", "RANGE_LAST_COMPLETE", "Last Year"),
}
COMPARISONS = {"previous-period": "TIME_COMPARISON_PREVIOUS_PERIOD",
               "year-ago": "TIME_COMPARISON_YEAR_AGO_PERIOD"}
REQUIRED = ["name", "datasource", "measure", "aggregation", "time_dimension", "dimensions",
            "sentiment", "format", "period"]
AGG_CALC = re.compile(r"\b(SUM|AVG|COUNT|COUNTD|MIN|MAX|MEDIAN|ATTR|STDEV|VAR|PERCENTILE|WINDOW_\w+|RUNNING_\w+)\s*\(", re.I)


class Fail(Exception):
    def __init__(self, msg, hint=None, code=1, **extra):
        super().__init__(msg)
        self.msg, self.hint, self.code, self.extra = msg, hint, code, extra


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# ---------- config + secret ----------

def load_config():
    if not os.path.exists(CONFIG):
        return {"active": "default", "profiles": {}}
    with open(CONFIG) as f:
        return json.load(f)


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG, 0o600)


def profile(args):
    cfg = load_config()
    name = args.profile or cfg.get("active") or "default"
    return name, cfg.get("profiles", {}).get(name, {})


def keychain_account(p):
    return f"{p['pat_name']}@{urllib.parse.urlparse(p['server']).netloc}/{p['site']}"


def get_secret(p):
    if os.environ.get(SECRET_ENV):
        return os.environ[SECRET_ENV], "env"
    if platform.system() == "Darwin" and shutil.which("security") and p.get("pat_name"):
        r = subprocess.run(["security", "find-generic-password", "-s", APP, "-a", keychain_account(p), "-w"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip(), "keychain"
    return None, None


def missing_setup(p):
    missing = [k for k in ("server", "site", "pat_name") if not p.get(k)]
    if not missing and not get_secret(p)[0]:
        missing.append("pat_secret")
    return missing


# ---------- HTTP ----------

class Session:
    def __init__(self, p):
        missing = missing_setup(p)
        if missing:
            raise Fail("Setup incomplete", "Run `check` and fill in what's missing.", 2, missing=missing)
        self.server = p["server"].rstrip("/")
        self.site_url = p["site"]
        ver = self._req("GET", f"{self.server}/api/2.4/serverinfo")["serverInfo"]["restApiVersion"]
        self.api = f"{self.server}/api/{ver}"
        body = {"credentials": {"personalAccessTokenName": p["pat_name"],
                                "personalAccessTokenSecret": get_secret(p)[0],
                                "site": {"contentUrl": p["site"]}}}
        try:
            cred = self._req("POST", f"{self.api}/auth/signin", body)["credentials"]
        except Fail as e:
            if e.extra.get("status") == 401:
                raise Fail("Sign-in rejected (401)", "Check the PAT name, re-run store-secret, and confirm the site "
                           "content URL (the part after /site/ in the browser URL). PATs also expire after 15 days "
                           "unused.", 2)
            raise
        self.token, self.site_id, self.user_id = cred["token"], cred["site"]["id"], cred["user"]["id"]
        self.pulse = f"{self.server}/api/-/pulse"

    def _req(self, method, url, body=None, raw=False, params=None):
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json"}
        if getattr(self, "token", None):
            headers["X-Tableau-Auth"] = self.token
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                content = r.read()
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:1500]
            raise Fail(f"{method} {url.split('?')[0]} -> {e.code}", pulse_hint(e.code) if "/api/-/pulse" in url else None, 1,
                       status=e.code, response=text)
        except (urllib.error.URLError, TimeoutError) as e:
            raise Fail(f"Can't reach {url.split('?')[0]}: {getattr(e, 'reason', e)}",
                       "Network problem or timeout (120s). Check the connection and the server URL in config, then "
                       "re-run; `create` is safe to re-run because it reuses definitions that already exist.")
        if raw:
            return content
        return json.loads(content) if content.strip() else {}

    def rest(self, method, path, body=None, **kw):
        return self._req(method, f"{self.api}/sites/{self.site_id}{path}", body, **kw)

    def pulse_call(self, method, path, body=None, params=None):
        return self._req(method, self.pulse + path, body, params=params)

    def sign_out(self):
        try:
            self._req("POST", f"{self.api}/auth/signout")
        except Fail:
            pass


def pulse_hint(status):
    if status == 400:
        return ("Usual causes: (1) on some data sources, no metric has ever been saved in the Pulse UI — create one "
                "there first, then retry; (2) no categorical filter dimension in `dimensions` (bins don't count); "
                "(3) a field type mismatch, e.g. a non-date time_dimension.")
    if status == 403:
        return ("The signed-in user can't author Pulse here. Use a PAT for a user with Creator/Explorer (can publish) "
                "on a site with Pulse turned on. Connected App JWTs have been seen to get 403 here.")
    if status == 404:
        return ("A field wasn't found. Calculated fields must use the internal name (Calculation_...), not the "
                "caption — run `fields` to look it up. Or the definition/data source ID is wrong.")
    if status == 409:
        return ("Duplicate: a definition with this name already exists, or one with the same data source, measure, "
                "aggregation and filters. Run `definitions --datasource ...` to find it.")
    if status == 429:
        return "Rate limited. Wait a minute, then re-run; `create` reuses anything already created."
    if status >= 500:
        return "Tableau returned a server error. Wait a minute and re-run; if it repeats, check the site's status."
    return None


# ---------- data sources + fields ----------

def all_datasources(s, search=None):
    rows, page = [], 1
    while True:
        d = s.rest("GET", "/datasources", params={"pageSize": 1000, "pageNumber": page})
        for ds in d.get("datasources", {}).get("datasource", []):
            rows.append({"name": ds["name"], "id": ds["id"], "content_url": ds.get("contentUrl"),
                         "project": ds.get("project", {}).get("name"), "type": ds.get("type")})
        total = int(d.get("pagination", {}).get("totalAvailable", 0))
        if page * 1000 >= total:  # REST has no substring filter on name, so search here
            return [r for r in rows if not search or search.lower() in r["name"].lower()]
        page += 1


def tds_fields(s, ds_id):
    content = s.rest("GET", f"/datasources/{ds_id}/content", params={"includeExtract": "false"}, raw=True)
    if content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".tds"))
            content = z.read(name)
    root = ET.fromstring(content)
    fields = {}
    # Physical columns (no metadata edits) only appear as metadata-records.
    for rec in root.iter("metadata-record"):
        if rec.get("class") != "column":
            continue
        local = (rec.findtext("local-name") or "").strip("[]")
        if local:
            fields[local] = {"name": local, "caption": local, "datatype": rec.findtext("local-type"),
                             "role": None, "type": None, "is_calc": False}
    for col in root.iter("column"):
        name = (col.get("name") or "").strip("[]")
        if not name or name.startswith(":"):
            continue
        f = fields.setdefault(name, {"name": name, "caption": name, "is_calc": False})
        f.update({k: v for k, v in {"caption": col.get("caption"), "datatype": col.get("datatype"),
                                    "role": col.get("role"), "type": col.get("type")}.items() if v})
        calc = col.find("calculation")
        if calc is not None and calc.get("formula"):
            f["is_calc"] = True
            f["formula"] = calc.get("formula")
            if AGG_CALC.search(calc.get("formula")):
                f["aggregate_calc"] = True
        if col.get("hidden") == "true":
            f["hidden"] = True
    fields = {k: f for k, f in fields.items() if f.get("datatype") != "table"}
    for f in fields.values():
        if not f.get("role"):
            f["role"] = "measure" if f.get("datatype") in ("integer", "real") else "dimension"
    return sorted(fields.values(), key=lambda f: (f["role"], f["caption"].lower()))


def resolver(fields):
    by = {}
    for f in fields:
        by.setdefault(f["name"].lower(), f)
    for f in fields:
        by.setdefault(f["caption"].lower(), f)
    return by


# ---------- definitions ----------

def all_definitions(s):
    defs, params = [], {"page_size": 100}
    while True:
        page = s.pulse_call("GET", "/definitions", params=params)
        defs.extend(page.get("definitions", []))
        if not page.get("next_page_token"):
            return defs
        params["page_token"] = page["next_page_token"]


def summarize(d):
    spec = d.get("specification", {})
    basic = spec.get("basic_specification", {})
    return {"name": d["metadata"]["name"], "id": d["metadata"]["id"],
            "datasource": spec.get("datasource", {}).get("id"),
            "measure": basic.get("measure", {}).get("field"),
            "aggregation": basic.get("measure", {}).get("aggregation", "").replace("AGGREGATION_", ""),
            "time_dimension": basic.get("time_dimension", {}).get("field"),
            "dimensions": d.get("extension_options", {}).get("allowed_dimensions", [])}


def definition_body(m):
    sentiment = m["sentiment"].upper()
    fmt = m["format"].upper()
    units = m.get("units") or ["", ""]
    filters = [{"field": f["field"], "operator": "OPERATOR_EQUAL",
                "categorical_values": [{"string_value": str(v)} for v in f["values"]]}
               for f in m.get("filters", [])]
    comps = m.get("comparisons") or ["previous-period", "year-ago"]
    # Full body, shaped like the one the Pulse UI sends: trimmed bodies return 400 on many data sources.
    return {
        "name": m["name"],
        "description": m.get("description", ""),
        "specification": {
            "datasource": {"id": m["datasource"], "id_type": "DATASOURCE_ID_TYPE_UNSPECIFIED", "vizql_session_id": ""},
            "basic_specification": {"measure": {"field": m["measure"], "aggregation": f"AGGREGATION_{m['aggregation'].upper()}"},
                                    "time_dimension": {"field": m["time_dimension"]}, "filters": filters},
            "is_running_total": bool(m.get("running_total", False)),
            "temporality": "TEMPORALITY_OVER_TIME",
        },
        "extension_options": {"allowed_dimensions": m["dimensions"], "allowed_granularities": GRANS,
                              "offset_from_today": 0, "correlation_candidate_definition_ids": [],
                              # anchor periods on the latest date in the data, not today
                              "use_dynamic_offset": bool(m.get("use_latest_data", True)),
                              "dimension_links": []},
        "representation_options": {
            "type": f"NUMBER_FORMAT_TYPE_{fmt}",
            "number_units": {"singular_noun": units[0], "plural_noun": units[1]},
            "sentiment_type": "SENTIMENT_TYPE_NONE" if sentiment == "NONE" else f"SENTIMENT_TYPE_{sentiment}_IS_GOOD",
            "row_level_id_field": {"identifier_col": "", "identifier_label": ""},
            "row_level_entity_names": {"entity_name_singular": "", "entity_name_plural": ""},
            "row_level_name_field": {"name_col": ""},
            "currency_code": f"CURRENCY_CODE_{m.get('currency', 'USD').upper()}" if fmt == "CURRENCY" else "CURRENCY_CODE_UNSPECIFIED",
            "positive_only": False,
        },
        "insights_options": {"show_insights": True, "settings": [
            {"type": f"INSIGHT_TYPE_{t}", "disabled": t == "RECORD_LEVEL_OUTLIERS"} for t in INSIGHTS]},
        "comparisons": {"comparisons": [
            {"compare_config": {"comparison": COMPARISONS[c], "comparison_period_override": []}, "index": str(i)}
            for i, c in enumerate(comps)]},
    }


def metric_body(def_id, period, comparison="previous-period"):
    gran, rng, _ = PERIODS[period]
    return {"definition_id": def_id,
            "specification": {"filters": [],
                              "measurement_period": {"granularity": f"GRANULARITY_BY_{gran}", "range": rng},
                              "comparison": {"comparison": COMPARISONS[comparison]}}}


def card_settings(s, m, def_id, metric_id, ds_content_url):
    return {"DATASOURCE_NAME": ds_content_url, "MEASURE_FIELD": m["measure"],
            "TIME_DIMENSION_FIELD": m["time_dimension"], "METRIC_DEFINITION_ID": def_id, "METRIC_ID": metric_id,
            "PULSE_ROOT": f"{s.server}/pulse/site/{s.site_url}/", "SYSTEM_TOOLTIP_TEXT": PERIODS[m["period"]][2],
            "ENABLE_LINK": "true", "USE_FULL_CARD": "false", "USE_DASHBOARD_FILTERS": "true",
            "SQUARE_CORNERS": "true", "has_been_configured": "true", "has_been_initialized": "true"}


def load_spec(path):
    with open(path) as f:
        spec = json.load(f)
    if isinstance(spec, list):
        spec = {"metrics": spec}
    if "metrics" not in spec:
        spec = {"metrics": [spec]}
    defaults = spec.get("defaults", {})
    return [{**defaults, **m} for m in spec["metrics"]]


def validate(m, fields_by, problems):
    label = m.get("name") or "(unnamed metric)"
    miss = [k for k in REQUIRED if m.get(k) in (None, "", [])]
    if miss:
        problems.append({"metric": label, "missing": miss})
        return
    bad = []
    if m["aggregation"].upper() not in AGGS:
        bad.append(f"aggregation must be one of {AGGS}")
    if m["format"].upper() not in FORMATS:
        bad.append(f"format must be one of {FORMATS}")
    if m["sentiment"].upper() not in SENTIMENTS:
        bad.append(f"sentiment must be one of {SENTIMENTS}")
    if m["period"] not in PERIODS:
        bad.append(f"period must be one of {list(PERIODS)}")
    for c in m.get("comparisons") or []:
        if c not in COMPARISONS:
            bad.append(f"comparison '{c}' must be one of {list(COMPARISONS)}")
    if isinstance(m["dimensions"], str):
        m["dimensions"] = [m["dimensions"]]
    notes = []
    if fields_by is not None:
        def res(cap, want=None):
            f = fields_by.get(str(cap).lower())
            if not f:
                bad.append(f"field '{cap}' not in the data source (run `fields`)")
                return cap
            if f["name"] != f["caption"] and str(cap) != f["name"]:
                notes.append(f"'{cap}' -> internal name '{f['name']}'")
            if want == "date" and f.get("datatype") not in ("date", "datetime"):
                bad.append(f"time_dimension '{cap}' is {f.get('datatype')}, needs date or datetime")
            if want == "dimension" and f.get("role") != "dimension":
                bad.append(f"filter dimension '{cap}' is a {f.get('role')}; Pulse needs a categorical dimension")
            if want == "measure" and f.get("aggregate_calc"):
                if m["aggregation"].upper() != "USER":
                    # SUM/AVERAGE on an already-aggregated calc is accepted but returns no value (tested)
                    notes.append(f"measure '{cap}' is an aggregate calc ({f.get('formula')}); aggregation set to "
                                 f"USER (the UI's 'Calculated') instead of {m['aggregation'].upper()}")
                    m["aggregation"] = "USER"
            elif want == "measure" and m["aggregation"].upper() == "USER":
                bad.append(f"aggregation USER is only for aggregate calcs like SUM([A])/SUM([B]); '{cap}' is not one. "
                           "Use SUM, AVERAGE, etc.")
            return f["name"]
        m["measure"] = res(m["measure"], "measure")
        m["time_dimension"] = res(m["time_dimension"], "date")
        m["dimensions"] = [res(d, "dimension") for d in m["dimensions"]]
        for flt in m.get("filters", []):
            flt["field"] = res(flt["field"])
    for flt in m.get("filters", []):
        if not flt.get("field") or not flt.get("values"):
            bad.append("each filter needs `field` and a non-empty `values` list")
    if bad:
        problems.append({"metric": label, "invalid": bad})
    if notes:
        m["_resolved"] = notes


# ---------- commands ----------

def cmd_check(args):
    pname, p = profile(args)
    secret, source = get_secret(p)
    res = {"config_file": CONFIG, "profile": pname,
           "server": p.get("server"), "site": p.get("site"), "pat_name": p.get("pat_name"),
           "pat_secret": f"found ({source})" if secret else "missing",
           "missing": missing_setup(p)}
    if res["missing"]:
        res["next"] = ("Ask the user for any missing server/site/pat_name and run `configure`. For pat_secret, have "
                       "the user run `store-secret` in Terminal themselves — never collect it in chat.")
        out(res)
        return 2
    s = Session(p)
    res.update(signed_in=True, site_id=s.site_id, user_id=s.user_id, rest_api=s.api.rsplit("/", 1)[1])
    s.sign_out()
    out(res)
    return 0


def cmd_configure(args):
    cfg = load_config()
    pname = args.profile or cfg.get("active") or "default"
    p = cfg.setdefault("profiles", {}).setdefault(pname, {})
    if args.server:
        u = args.server.strip().rstrip("/")
        if not u.startswith("http"):
            u = "https://" + u
        parsed = urllib.parse.urlparse(u)
        p["server"] = f"{parsed.scheme}://{parsed.netloc}"
        m = re.search(r"/site/([^/]+)", u)  # a pasted browser URL carries the site too
        if m and not args.site:
            p["site"] = m.group(1)
    if args.site is not None:
        p["site"] = args.site
    if args.pat_name:
        p["pat_name"] = args.pat_name
    cfg["active"] = pname
    save_config(cfg)
    out({"saved": CONFIG, "profile": pname, **p, "missing": missing_setup(p)})
    return 0


def cmd_store_secret(args):
    pname, p = profile(args)
    if not p.get("pat_name"):
        raise Fail("Run `configure` first (server, site, PAT name).", code=2)
    if platform.system() != "Darwin" or not shutil.which("security"):
        out({"keychain": "unavailable",
             "next": f"Set the secret in your shell instead:  read -s {SECRET_ENV} && export {SECRET_ENV}"})
        return 2
    if not sys.stdin.isatty():
        raise Fail("store-secret needs an interactive Terminal",
                   f"Have the user run this in Terminal:  python3 {shlex.quote(os.path.abspath(__file__))} store-secret", 2)
    # A bare trailing -w makes security(1) prompt for the secret itself, so it never appears in argv.
    print(f"Paste the PAT secret for '{p['pat_name']}' (input hidden, asked twice):", file=sys.stderr)
    r = subprocess.run(["security", "add-generic-password", "-U", "-s", APP, "-a", keychain_account(p),
                        "-l", f"Tableau PAT ({p['site']})", "-w"])
    if r.returncode:
        raise Fail("Keychain write failed", "Re-run store-secret and paste the same secret both times.")
    print(f"Saved to the macOS Keychain as '{APP}' / {keychain_account(p)}.", file=sys.stderr)
    out({"stored": True, "keychain_service": APP, "account": keychain_account(p)})
    return 0


def with_session(args, fn):
    _, p = profile(args)
    s = Session(p)
    try:
        return fn(s)
    finally:
        s.sign_out()


def cmd_datasources(args):
    def run(s):
        out({"datasources": all_datasources(s, args.search)})
        return 0
    return with_session(args, run)


def cmd_fields(args):
    def run(s):
        fields = tds_fields(s, args.datasource)
        if not args.all:
            fields = [f for f in fields if not f.get("hidden")]
        out({"datasource": args.datasource, "fields": fields,
             "note": "Use `name` in specs (captions are resolved automatically). Calcs need their internal name."})
        return 0
    return with_session(args, run)


def cmd_definitions(args):
    def run(s):
        defs = [summarize(d) for d in all_definitions(s)]
        if args.datasource:  # the API has no datasource filter (400), so filter here
            defs = [d for d in defs if d["datasource"] == args.datasource]
        if args.search:
            defs = [d for d in defs if args.search.lower() in d["name"].lower()]
        out({"definitions": defs})
        return 0
    return with_session(args, run)


def cmd_create(args):
    metrics = load_spec(args.spec)

    def run(s):
        problems, field_cache = [], {}
        for m in metrics:
            ds = m.get("datasource")
            if ds and ds not in field_cache:
                try:
                    field_cache[ds] = resolver(tds_fields(s, ds))
                except Fail as e:
                    problems.append({"metric": m.get("name"), "invalid": [f"can't read data source {ds}: {e.msg}"]})
                    field_cache[ds] = None
            validate(m, field_cache.get(ds), problems)
        if problems:
            out({"error": "Spec incomplete or invalid", "problems": problems,
                 "next": "Ask the user for the missing/invalid values, update the spec, and re-run."})
            return 3
        existing = all_definitions(s)
        by_name = {d["metadata"]["name"]: d["metadata"]["id"] for d in existing}
        ds_with_defs = {d["specification"]["datasource"]["id"] for d in existing}

        def shape(ds, field, agg, filters):  # Pulse rejects a second definition with the same shape (409)
            return (ds, field, agg.upper().replace("AGGREGATION_", ""),
                    json.dumps(sorted((f["field"], sorted(map(str, f["values"]))) for f in filters)))
        by_shape = {}
        for d in existing:
            b = d["specification"].get("basic_specification", {})
            flt = [{"field": f["field"], "values": [v.get("string_value") for v in f.get("categorical_values", [])]}
                   for f in b.get("filters", [])]
            by_shape[shape(d["specification"]["datasource"]["id"], b.get("measure", {}).get("field"),
                           b.get("measure", {}).get("aggregation", ""), flt)] = d["metadata"]["name"]
        content_urls = {d["id"]: d["content_url"] for d in all_datasources(s)}
        plan, results = [], []
        for m in metrics:
            step = {"name": m["name"], "datasource": m["datasource"],
                    "action": "reuse existing definition" if m["name"] in by_name else "create definition",
                    "measure": f"{m['aggregation'].upper()}({m['measure']})", "time_dimension": m["time_dimension"],
                    "dimensions": m["dimensions"], "filters": m.get("filters", []),
                    "format": m["format"].upper(), "sentiment": m["sentiment"].upper(), "period": m["period"]}
            if m.get("_resolved"):
                step["resolved_fields"] = m["_resolved"]
            twin = by_shape.get(shape(m["datasource"], m["measure"], m["aggregation"], m.get("filters", [])))
            if m["name"] not in by_name and twin:
                step["action"] = "blocked"
                step["conflict"] = (f"'{twin}' already uses this data source, measure, aggregation and filters; Pulse "
                                    "returns 409. Reuse it (use its name), or change the aggregation or filters.")
            if m["datasource"] not in ds_with_defs:
                step["warning"] = ("No Pulse definition exists on this data source yet. Some data sources reject the "
                                   "first definition with a 400 until one metric is saved in the Pulse UI; others "
                                   "accept it. Try it.")
            plan.append(step)
        blocked = [st for st in plan if st["action"] == "blocked"]
        if args.dry_run or blocked:
            out({"dry_run": args.dry_run, "plan": plan, "next": "Resolve the conflicts, then dry-run again." if blocked else
                 "Show this plan to the user; re-run without --dry-run once they confirm."})
            return 3 if blocked else 0
        rc = 0
        for m, step in zip(metrics, plan):
            r = {"name": m["name"]}
            try:
                did = by_name.get(m["name"])
                if did:
                    r["definition"] = "existing"
                else:
                    did = s.pulse_call("POST", "/definitions", definition_body(m))["definition"]["metadata"]["id"]
                    r["definition"] = "created"
                    by_name[m["name"]] = did
                r["definition_id"] = did
                met = s.pulse_call("POST", "/metrics:getOrCreate", metric_body(did, m["period"]))
                r["metric_id"] = met["metric"]["id"]
                r["metric"] = "created" if met.get("is_metric_created") else "existing"
                r["pulse_url"] = f"{s.server}/pulse/site/{s.site_url}/metrics/{r['metric_id']}"
                r["studio_card_settings"] = card_settings(s, m, did, r["metric_id"],
                                                          content_urls.get(m["datasource"]))
            except Fail as e:
                rc = 1
                r.update(error=e.msg, hint=e.hint, response=e.extra.get("response"))
                if step.get("warning") and e.extra.get("status") == 400:
                    r["hint"] = step["warning"] + " " + (e.hint or "")
            results.append(r)
        out({"results": results})
        return rc
    return with_session(args, run)


def cmd_metric(args):
    if args.period not in PERIODS:
        raise Fail(f"period must be one of {list(PERIODS)}", code=3)

    def run(s):
        met = s.pulse_call("POST", "/metrics:getOrCreate", metric_body(args.definition, args.period, args.comparison))
        mid = met["metric"]["id"]
        out({"definition_id": args.definition, "metric_id": mid, "period": args.period,
             "metric": "created" if met.get("is_metric_created") else "existing",
             "pulse_url": f"{s.server}/pulse/site/{s.site_url}/metrics/{mid}",
             "SYSTEM_TOOLTIP_TEXT": PERIODS[args.period][2]})
        return 0
    return with_session(args, run)


def bundle_request(d, met):
    """Insight-bundle request for one metric, built from its definition `d` and metric `met`."""
    spec = d["specification"]
    return {"bundle_request": {"version": 1,
            "options": {"output_format": "OUTPUT_FORMAT_TEXT", "time_zone": "UTC",
                        "language": "LANGUAGE_EN_US", "locale": "LOCALE_EN_US"},
            "input": {"metadata": {"name": d["metadata"]["name"], "metric_id": met["id"],
                                   "definition_id": d["metadata"]["id"]},
                      "metric": {"definition": {"datasource": {"id": spec["datasource"]["id"]},
                                                "basic_specification": spec["basic_specification"],
                                                "is_running_total": spec.get("is_running_total", False)},
                                 "metric_specification": met["specification"],
                                 "extension_options": d.get("extension_options", {}),
                                 "representation_options": d.get("representation_options", {}),
                                 "insights_options": d.get("insights_options", {})}}}}


def find_markup(resp):
    """The headline sentence of the bundle, e.g. 'X was $217.33 (2026 year to date), down 4.1% ...'.
    (Other numbers in the response are chart styling, not the metric's value.)"""
    groups = resp.get("bundle_response", {}).get("result", {}).get("insight_groups", [])
    for g in groups:
        for i in g.get("insights", []):
            text = i.get("result", {}).get("markup")
            if text:
                return text
    return None


def cmd_value(args):
    def run(s):
        met = s.pulse_call("GET", f"/metrics/{args.metric}")["metric"]
        d = s.pulse_call("GET", f"/definitions/{met['definition_id']}")["definition"]
        resp = s.pulse_call("POST", "/insights/ban", bundle_request(d, met))
        text = find_markup(resp)
        out({"metric_id": met["id"], "name": d["metadata"]["name"], "has_value": bool(text), "summary": text,
             "next": "Read the summary: it should state a figure for the period. If so, the metric works." if text else
                     "No value came back. Ask the user to open the metric's link before calling it done."})
        return 0 if text else 4
    return with_session(args, run)


def cmd_rename(args):
    def run(s):
        d = s.pulse_call("GET", f"/definitions/{args.definition}")["definition"]
        body = {k: d[k] for k in ("specification", "extension_options", "representation_options",
                                  "insights_options", "comparisons") if k in d}
        body.update(name=args.name, description=d["metadata"].get("description", ""))
        s.pulse_call("PATCH", f"/definitions/{args.definition}", body)
        out({"renamed": args.definition, "from": d["metadata"]["name"], "to": args.name})
        return 0
    return with_session(args, run)


def cmd_delete(args):
    if not args.yes:
        raise Fail("Deleting a definition also deletes its metrics and followers' subscriptions.",
                   "Confirm with the user, then re-run with --yes.", 3)

    def run(s):
        name = s.pulse_call("GET", f"/definitions/{args.definition}")["definition"]["metadata"]["name"]
        s.pulse_call("DELETE", f"/definitions/{args.definition}")
        out({"deleted": args.definition, "name": name})
        return 0
    return with_session(args, run)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="config profile (default: the active one)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    c = sub.add_parser("configure")
    c.add_argument("--server", help="e.g. https://prod-useast-a.online.tableau.com, or paste any URL from the site")
    c.add_argument("--site", help="site content URL (after /site/ in the browser URL)")
    c.add_argument("--pat-name")
    sub.add_parser("store-secret")
    c = sub.add_parser("datasources")
    c.add_argument("--search")
    c = sub.add_parser("fields")
    c.add_argument("--datasource", required=True)
    c.add_argument("--all", action="store_true", help="include hidden fields")
    c = sub.add_parser("definitions")
    c.add_argument("--datasource")
    c.add_argument("--search")
    c = sub.add_parser("create")
    c.add_argument("--spec", required=True)
    c.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("metric")
    c.add_argument("--definition", required=True)
    c.add_argument("--period", required=True, help=", ".join(PERIODS))
    c.add_argument("--comparison", default="previous-period", choices=list(COMPARISONS))
    c = sub.add_parser("value")
    c.add_argument("--metric", required=True)
    c = sub.add_parser("rename")
    c.add_argument("--definition", required=True)
    c.add_argument("--name", required=True)
    c = sub.add_parser("delete")
    c.add_argument("--definition", required=True)
    c.add_argument("--yes", action="store_true")
    args = ap.parse_args()
    fn = globals()["cmd_" + args.cmd.replace("-", "_")]
    try:
        sys.exit(fn(args))
    except Fail as e:
        err = {"error": e.msg}
        if e.hint:
            err["hint"] = e.hint
        err.update(e.extra)
        out(err)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
