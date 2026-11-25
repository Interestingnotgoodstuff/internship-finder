"""Daily run: fetch every configured board, classify, track new/closed, write outputs.

Usage:
    python -m finder.main              # real run (needs internet)
    python -m finder.main --demo       # fill the dashboard with sample data
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import classify as C
from . import sources as S

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "companies.yaml"
STATE = ROOT / "data" / "state.json"
OUT = ROOT / "docs" / "jobs.json"
NEW_TODAY = ROOT / "data" / "new_today.json"
KEEP_CLOSED_DAYS = 14

NON_US = re.compile(
    r"london|toronto|montreal|calgary|vancouver|hong kong|singapore|tokyo|sydney|melbourne|"
    r"paris|frankfurt|zurich|geneva|dublin|luxembourg|madrid|milan|amsterdam|mumbai|"
    r"bangalore|bengaluru|dubai|sao paulo|mexico city|canada|united kingdom|\buk\b|india|"
    r"germany|france|spain|switzerland|japan|australia|ireland|brazil|mexico|monterrey|guadalajara", re.I)


def is_us(location: str) -> bool:
    return not NON_US.search(location or "")


def wants_title(title: str) -> bool:
    """Cheap first pass before downloading a full description."""
    t = title or ""
    if re.search(r"employee access|internal only", t, re.I):
        return False
    return C.is_internship_title(t) or bool(re.search(r"class of 2028|2028 analyst", t, re.I))


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text())


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"jobs": {}}


RAW_DIR = ROOT / "data" / "raw"


def ordered_for_fetch(companies: list[dict]) -> list[dict]:
    """Spread Workday boards out between the others to avoid rate limits."""
    wd = [c for c in companies if c.get("ats") == "workday"]
    other = [c for c in companies if c.get("ats") != "workday"]
    out = []
    while wd or other:
        if wd:
            out.append(wd.pop(0))
        if other:
            out.append(other.pop(0))
    return out


def shard_of(companies: list[dict], k: int, n: int) -> list[dict]:
    """Round-robin by board type so each shard gets an even share of Workday boards."""
    wd = [c for c in companies if c.get("ats") == "workday"]
    other = [c for c in companies if c.get("ats") != "workday"]
    return [c for i, c in enumerate(wd) if i % n == k] + [c for i, c in enumerate(other) if i % n == k]


def fetch_results(companies: list[dict], state: dict, retry_wait: int = 90) -> list:
    """Fetch every board; boards that were rate-limited get one more try after a pause."""
    cache = state.get("jobs", {})
    results = list(S.iter_safe(ordered_for_fetch(companies), title_prefilter=wants_title, cache=cache))
    limited = [c for c, _, err in results if err and ("429" in err or "503" in err or "Timeout" in err)]
    if limited:
        print(f"Rate-limited on {len(limited)} boards; retrying after {retry_wait}s", flush=True)
        time.sleep(retry_wait)
        again = {c["name"]: (c, j, e) for c, j, e in S.iter_safe(limited, title_prefilter=wants_title, cache=cache)}
        results = [again.get(c["name"], (c, j, e)) if e else (c, j, e) for c, j, e in results]
    return results


def fetch_shard(k: int, n: int) -> None:
    cfg = load_config()
    part = shard_of(cfg.get("companies") or [], k, n)
    print(f"Shard {k + 1}/{n}: {len(part)} boards", flush=True)
    results = fetch_results(part, load_state())
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = [{"company": c["name"], "jobs": jobs, "error": err} for c, jobs, err in results]
    (RAW_DIR / f"shard_{k}.json").write_text(json.dumps(out))
    bad = sum(1 for r in out if r["error"])
    print(f"Shard {k + 1}/{n} done: {len(out) - bad} ok, {bad} errors", flush=True)


def load_raw(companies: list[dict]) -> list:
    by_name = {c["name"]: c for c in companies}
    got = {}
    for f in sorted(RAW_DIR.glob("shard_*.json")):
        for r in json.loads(f.read_text()):
            got[r["company"]] = r
    out = []
    for name, c in by_name.items():
        r = got.get(name)
        if r is None:
            out.append((c, [], "Not fetched (scan job failed)"))
        else:
            out.append((c, r["jobs"], r["error"]))
    return out


def run(demo: bool = False, from_raw: bool = False) -> dict:
    cfg = load_config()
    companies = cfg.get("companies") or []
    state = load_state()
    today = date.today().isoformat()

    found: dict[str, dict] = {}
    health = []
    if demo:
        from .demo import demo_results
        results = demo_results(companies)
    elif from_raw:
        results = load_raw(companies)
    else:
        results = fetch_results(companies, state)

    for c, jobs, err in results:
        kept = 0
        for j in jobs:
            if not wants_title(j["title"]):
                continue
            C.classify(j)
            j["us"] = is_us(j.get("location", ""))
            found[j["id"]] = j
            kept += 1
        health.append({"company": c["name"], "ats": c.get("ats"), "ok": err is None,
                       "internships": kept, "error": err or ""})
        print(f"{'OK ' if err is None else 'ERR'} {c['name']:<32} {kept:>3} internships"
              + (f"  ({err})" if err else ""), flush=True)

    # Merge with history so we know what's new and what disappeared.
    prev = state.get("jobs", {})
    merged = {}
    new_ids = []
    for jid, j in found.items():
        old = prev.get(jid, {})
        j["first_seen"] = old.get("first_seen", today)
        j["last_seen"] = today
        j["status"] = "Open"
        if jid not in prev:
            new_ids.append(jid)
        merged[jid] = j
    cutoff = (date.today() - timedelta(days=KEEP_CLOSED_DAYS)).isoformat()
    failed = {h["company"] for h in health if not h["ok"]}
    for jid, old in prev.items():
        if jid in merged:
            continue
        if old.get("company") in failed:          # board was down; don't call it closed
            merged[jid] = old
            continue
        if old.get("last_seen", today) >= cutoff:
            old["status"] = "Closed / removed"
            merged[jid] = old

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"jobs": merged}, indent=1, sort_keys=True))

    jobs_out = sorted(merged.values(), key=lambda j: (j["status"] != "Open",
                                                      j.get("first_seen", ""),), reverse=False)
    jobs_out.sort(key=lambda j: j.get("first_seen", ""), reverse=True)
    for j in jobs_out:
        j["description_snippet"] = (j.get("description") or "")[:600]
    slim = [{k: v for k, v in j.items() if k != "description"} for j in jobs_out]

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "grad": "May 2028",
        "jobs": slim,
        "sources": sorted(health, key=lambda h: (h["ok"], h["company"])),
        "demo": demo,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1))

    new_jobs = [merged[i] for i in new_ids]
    NEW_TODAY.write_text(json.dumps(new_jobs, indent=1))
    ok = sum(1 for h in health if h["ok"])
    print(f"\nBoards OK: {ok}/{len(health)}  |  internships: {len(found)}  |  new today: {len(new_ids)}")
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="use sample data instead of the internet")
    ap.add_argument("--shard", type=int, help="fetch only shard K (0-based) and save raw results")
    ap.add_argument("--shards", type=int, default=1, help="number of shards")
    ap.add_argument("--merge", action="store_true", help="build outputs from saved shard results")
    args = ap.parse_args(argv)
    if args.shard is not None:
        fetch_shard(args.shard, args.shards)
        return 0
    run(demo=args.demo, from_raw=args.merge)
    return 0


if __name__ == "__main__":
    sys.exit(main())
