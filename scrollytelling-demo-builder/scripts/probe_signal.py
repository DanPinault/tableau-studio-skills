#!/usr/bin/env python3
"""Locked signal probe: trend verdicts, lead signal, move start, window, divergence.

Implements the "Locked window rule" and the locked thresholds of
references/build-procedure.md so two runs on the same rows give the same
numbers. Usage:

  python3 -I probe_signal.py ROWS.json --date Date \
      --measure "Cost Per Stop|AVG" --measure "Stops|SUM" \
      --measure "Profit Ratio|RATIO|Profit|Sales" [--today 2026-11-04]

ROWS.json is a list of row objects, or {"data": [...]}, from a datasource query
at the finest date grain (one or more rows per date). Prints one JSON object.
"""
import argparse
import json
import statistics
import sys

THRESHOLD = 0.10      # trend: relative change over 10%
DIVERGE = 0.05        # divergence: one over +5% while the other under -5%
BASE = 14             # periods in the first and last blocks
TRAIL = 7             # trailing average length for the move start
SD_MULT = 3.0         # move start: trailing average beyond 3 baseline SD


def load(path):
    rows = json.load(open(path))
    return rows["data"] if isinstance(rows, dict) else rows


def parse_measure(spec):
    p = spec.split("|")
    if len(p) == 2 and p[1] in ("SUM", "AVG"):
        return {"name": p[0], "rule": p[1]}
    if len(p) == 4 and p[1] == "RATIO":
        return {"name": p[0], "rule": "RATIO", "num": p[2], "den": p[3]}
    sys.exit("bad --measure %r: use Name|SUM, Name|AVG or Name|RATIO|Num|Den" % spec)


def period_values(rows, dates, m):
    """Per-period (sum, count, num, den) so blocks can aggregate by rule."""
    out = []
    for d in dates:
        g = [r for r in rows if r["_d"] == d]
        if m["rule"] == "RATIO":
            n = [r[m["num"]] for r in g if r.get(m["num"]) is not None]
            dn = [r[m["den"]] for r in g if r.get(m["den"]) is not None]
            out.append(None if not n or not dn else {"num": sum(n), "den": sum(dn)})
        else:
            v = [r[m["name"]] for r in g if r.get(m["name"]) is not None]
            out.append(None if not v else {"sum": sum(v), "n": len(v)})
    return out


def block(vals, m):
    """Aggregate a list of per-period values by the measure's rule."""
    v = [x for x in vals if x is not None]
    if not v:
        return None
    if m["rule"] == "RATIO":
        den = sum(x["den"] for x in v)
        return sum(x["num"] for x in v) / den if den else None
    if m["rule"] == "SUM":
        return sum(x["sum"] for x in v) / len(v)  # per-period total
    return statistics.mean(x["sum"] / x["n"] for x in v)  # mean of per-period AVG


def series(vals, m):
    out = []
    for x in vals:
        out.append(None if x is None else block([x], m))
    return out


def rel(first, last):
    if first is None or last is None or first == 0:
        return None
    return (last - first) / abs(first)


def first_last(vals, m, lo, hi):
    seg = vals[lo:hi]
    return block(seg[:BASE], m), block(seg[-BASE:], m)


def move_start(s):
    """Index of the move start in series s, or None. Sample SD, trailing mean."""
    pts = [x for x in s if x is not None]
    if len(pts) < BASE + TRAIL:
        return None
    base = pts[:BASE]
    bm, bs = statistics.mean(base), statistics.stdev(base)
    change = rel(statistics.mean(pts[:BASE]), statistics.mean(pts[-BASE:]))
    if change is None or change == 0:
        return None
    d = 1 if change > 0 else -1
    q = [False] * len(s)
    for i in range(TRAIL - 1, len(s)):
        w = s[i - TRAIL + 1:i + 1]
        if any(x is None for x in w):
            continue
        q[i] = d * (statistics.mean(w) - bm) > SD_MULT * bs
    if not q[-1]:
        return None
    i = len(s) - 1
    while i > 0 and q[i - 1]:
        i -= 1
    return i


def yearly(rows, dates, vals, m):
    """First full calendar year vs last full calendar year, per period."""
    by = {}
    for d, x in zip(dates, vals):
        by.setdefault(d[:4], []).append((d[5:7], x))
    full = [y for y in sorted(by)
            if {"01"} <= {mo for mo, _ in by[y]} and {"12"} <= {mo for mo, _ in by[y]}]
    if len(full) < 2:
        return None
    f, l = full[0], full[-1]
    fv, lv = block([x for _, x in by[f]], m), block([x for _, x in by[l]], m)
    return {"first_year": f, "last_year": l, "change": rel(fv, lv)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rows")
    ap.add_argument("--date", required=True)
    ap.add_argument("--measure", action="append", required=True)
    ap.add_argument("--today", help="YYYY-MM-DD; flags data past this date")
    a = ap.parse_args()

    rows = load(a.rows)
    for r in rows:
        r["_d"] = str(r[a.date])[:10]
    dates = sorted({r["_d"] for r in rows})
    ms = [parse_measure(s) for s in a.measure]
    vals = {m["name"]: period_values(rows, dates, m) for m in ms}
    ser = {m["name"]: series(vals[m["name"]], m) for m in ms}
    out = {"grain_periods": len(dates), "first_date": dates[0], "last_date": dates[-1],
           "measures_probed": len(ms), "thresholds": {"trend": THRESHOLD, "diverge": DIVERGE}}
    if a.today:
        out["data_past_today"] = dates[-1] > a.today

    nulls = {}
    for m in ms:
        s = ser[m["name"]]
        nulls[m["name"]] = round(sum(1 for x in s if x is None) / len(s), 4)
    out["null_rate"] = nulls

    tiny = len(dates) < 2 * BASE
    full = {}
    for m in ms:
        f, l = first_last(vals[m["name"]], m, 0, len(dates))
        full[m["name"]] = rel(f, l)
    out["full_history_change"] = full

    ranked = sorted((n for n in full if full[n] is not None),
                    key=lambda n: -abs(full[n]))
    lead_full = next((n for n in ranked if abs(full[n]) > THRESHOLD), None)

    ms_idx = None
    if not tiny and lead_full:
        ms_idx = move_start(ser[lead_full])
    out["lead_for_move_start"] = lead_full
    out["move_start"] = dates[ms_idx] if ms_idx is not None else None

    if tiny:
        lo, mode = 0, "full_history_tiny"
    elif ms_idx is not None:
        lo, mode = max(0, ms_idx - BASE), "move_start"
    else:
        lo, mode = 0, "full_history_no_move_start"
    out["window"] = {"start": dates[lo], "end": dates[-1], "mode": mode,
                     "periods": len(dates) - lo}

    rows_out = []
    for m in ms:
        n = m["name"]
        f, l = first_last(vals[n], m, lo, len(dates))
        r = {"measure": n, "rule": m["rule"] if m["rule"] != "RATIO" else
             "SUM(%s) / SUM(%s)" % (m["num"], m["den"]),
             "first14_vs_last14": rel(f, l)}
        if mode != "move_start" and not tiny:
            y = yearly(rows, dates, vals[n], m)
            r["yearly"] = y
        decider = r["first14_vs_last14"]
        if r.get("yearly") and r["yearly"]["change"] is not None:
            decider = r["yearly"]["change"]
        r["deciding_change"] = decider
        r["verdict"] = "qualifies" if decider is not None and abs(decider) > THRESHOLD else "noise"
        rows_out.append(r)
    rows_out.sort(key=lambda r: -abs(r["deciding_change"] or 0))
    out["table"] = rows_out
    out["lead_signal"] = ({"measure": rows_out[0]["measure"],
                           "change": rows_out[0]["deciding_change"]}
                          if rows_out and rows_out[0]["verdict"] == "qualifies" else None)
    out["qualifying"] = sum(1 for r in rows_out if r["verdict"] == "qualifies")

    div = []
    ch = {r["measure"]: r["deciding_change"] for r in rows_out}
    names = [n for n in ch if ch[n] is not None]
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            if (ch[x] > DIVERGE and ch[y] < -DIVERGE) or (ch[y] > DIVERGE and ch[x] < -DIVERGE):
                div.append({"pair": [x, y], "changes": [ch[x], ch[y]]})
    out["divergent_pairs"] = div
    def pct(x):
        return "n/a" if x is None else "%+.1f%%" % (x * 100)

    q = out["qualifying"]
    if q == 0:
        chapters = "none (no qualifying measure)"
    elif q <= 4:
        chapters = "%d (%d qualifying measures + opening and closing)" % (q + 2, q)
    else:
        chapters = ("6 (%d qualifying measures, the 4 strongest get chapters "
                    "+ opening and closing)" % q)
    ls = out["lead_signal"]
    out["proposal_lines"] = {
        "measures_probed": "%d of %d (%s)" % (len(ms), len(ms), ", ".join(m["name"] for m in ms)),
        "lead_signal": ("%s, %s" % (ls["measure"], pct(ls["change"]))) if ls else "none",
        "move_start": out["move_start"] or "none",
        "window": "%s to %s" % (out["window"]["start"], out["window"]["end"]),
        "chapters": chapters,
        "table": [[r["measure"], r["rule"], pct(r["deciding_change"]), r["verdict"]]
                  for r in rows_out],
    }
    out["not_covered"] = "concentration and anomaly checks are separate queries"
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
