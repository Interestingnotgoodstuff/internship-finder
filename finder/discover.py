"""Test guesses for firms listed under `candidates` in config/companies.yaml.

For Workday it also tries common "site" names, because each company names
its careers site differently. Prints a table of what worked, which can be
pasted into the `companies` list. Also writes docs/discovery.json.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
import yaml

from . import sources as S

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "companies.yaml"
OUT = ROOT / "docs" / "discovery.json"

WORKDAY_SITES = [
    "External", "Careers", "Campus", "Students", "External_Career_Site", "ExternalCareers",
    "careers", "campus", "Early_Careers", "EarlyCareers", "University", "Search",
    "Jobs", "jobs", "External_Careers", "CampusCareers", "{tenant}", "{tenant}careers",
    "{tenant}_careers", "{Tenant}Careers", "{Tenant}_Careers",
]


def try_workday(tenant: str, wd: str):
    hits = []
    for pat in WORKDAY_SITES:
        site = pat.format(tenant=tenant, Tenant=tenant.capitalize())
        try:
            data = S._post(f"{S.workday_base(tenant, wd, site)}/jobs",
                           {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
            hits.append({"ats": "workday", "tenant": tenant, "wd": wd, "site": site,
                         "total_jobs": data.get("total", 0)})
        except requests.RequestException:
            continue
    return hits


def try_simple(ats: str, ident: str):
    try:
        if ats == "greenhouse":
            data = S._get(f"https://boards-api.greenhouse.io/v1/boards/{ident}/jobs")
            return [{"ats": ats, "token": ident, "total_jobs": len(data.get("jobs", []))}]
        if ats == "lever":
            data = S._get(f"https://api.lever.co/v0/postings/{ident}", params={"mode": "json"})
            return [{"ats": ats, "slug": ident, "total_jobs": len(data)}] if isinstance(data, list) else []
        if ats == "ashby":
            data = S._get(f"https://api.ashbyhq.com/posting-api/job-board/{ident}")
            return [{"ats": ats, "org": ident, "total_jobs": len(data.get("jobs", []))}]
    except requests.RequestException:
        return []
    return []


def main() -> int:
    cfg = yaml.safe_load(CONFIG.read_text())
    report = []
    lines = ["| Firm | Result | Config line to copy |", "|---|---|---|"]
    for cand in cfg.get("candidates") or []:
        name, guesses = cand["name"], cand.get("guesses") or {}
        hits = []
        for tenant, wd in guesses.get("workday", []):
            hits += try_workday(str(tenant), wd)
        for ats in ("greenhouse", "lever", "ashby"):
            for ident in guesses.get(ats, []):
                hits += try_simple(ats, ident)
        hits.sort(key=lambda h: -h.get("total_jobs", 0))
        report.append({"name": name, "hits": hits})
        if hits:
            h = hits[0]
            fields = ", ".join(f"{k}: {v}" for k, v in h.items() if k not in ("total_jobs",))
            lines.append(f"| {name} | found ({h.get('total_jobs', 0)} jobs) | "
                         f"`- {{name: \"{name}\", category: TBD, {fields}}}` |")
        else:
            lines.append(f"| {name} | not found | check the firm's careers URL manually |")
        print(f"{name:<32} {'FOUND ' + str(hits[0]) if hits else 'not found'}", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("## Job-board discovery\n\n" + "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
