"""One-off connectivity probe for new job-board types. Run in GitHub Actions:
    python -m finder.probe
Prints status, result counts and sample titles for each candidate endpoint.
"""
from __future__ import annotations

import json
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en-US"})
OUT = []


def log(*a):
    line = " ".join(str(x) for x in a)
    print(line, flush=True)
    OUT.append(line)


def try_req(label, method, url, **kw):
    try:
        r = S.request(method, url, timeout=25, **kw)
        return r
    except Exception as e:  # noqa: BLE001
        log(f"  {label}: EXC {type(e).__name__}: {str(e)[:120]}")
        return None


def titles_from(obj, keys=("title", "jobTitle", "Title", "name", "roleTitle")):
    found = []
    def walk(o):
        if isinstance(o, dict):
            for k in keys:
                if isinstance(o.get(k), str) and len(found) < 400:
                    found.append(o[k])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    return found


def show(label, r, parse="json"):
    if r is None:
        return None
    ct = r.headers.get("content-type", "")
    if parse == "json":
        try:
            d = r.json()
        except Exception:  # noqa: BLE001
            log(f"  {label}: HTTP {r.status_code} not-json ct={ct} body={r.text[:160]!r}")
            return None
        t = titles_from(d)
        intern = [x for x in t if re.search(r"intern|summer|analyst program", x, re.I)]
        keys = list(d.keys())[:8] if isinstance(d, dict) else f"list[{len(d)}]"
        log(f"  {label}: HTTP {r.status_code} keys={keys} titles={len(t)} intern-ish={len(intern)}")
        for x in intern[:6]:
            log(f"      - {x}")
        return d
    log(f"  {label}: HTTP {r.status_code} len={len(r.text)} ct={ct}")
    return r.text


# ------------------------------------------------------------------ Phenom
PHENOM = ["careers.frostbank.com", "careers.regions.com", "careers.comerica.com",
          "www.wellsfargojobs.com", "careers.truist.com", "jobs.citizensbank.com",
          "careers.53.com", "careers.usbank.com", "careers.bankofamerica.com",
          "careers.firsthorizon.com", "careers.cadencebank.com", "careers.huntington.com"]


def phenom(host, kw="intern"):
    body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results",
            "ddoKey": "refineSearch", "sortBy": "", "subsearch": "", "from": 0, "jobs": True,
            "counts": True, "all_fields": ["category", "city", "state", "type"], "size": 50,
            "clearAll": False, "jdsource": "facets", "isSliderEnable": False, "pageId": "page20",
            "siteType": "external", "keywords": kw, "global": True, "selected_fields": {},
            "locationData": {}}
    home = try_req("home", "GET", f"https://{host}/us/en/search-results?keywords={kw}")
    if home is not None:
        m = re.search(r'"refNum"\s*:\s*"([^"]+)"', home.text)
        log(f"  home: HTTP {home.status_code} len={len(home.text)} refNum={m.group(1) if m else None} "
            f"phenom={'phenom' in home.text.lower()} workday={sorted(set(re.findall(r'([a-z0-9-]+\.wd\d+\.myworkdayjobs\.com/[A-Za-z0-9_-]+)', home.text)))[:3]}")
        # Phenom embeds the first page of results in the HTML as phApp.ddo
        m2 = re.search(r'phApp\.ddo\s*=\s*(\{.*?\});\s*phApp', home.text, re.S)
        if m2:
            try:
                ddo = json.loads(m2.group(1))
                jobs = (((ddo.get("eagerLoadRefineSearch") or {}).get("data") or {}).get("jobs")) or []
                log(f"  embedded ddo jobs={len(jobs)} total={(ddo.get('eagerLoadRefineSearch') or {}).get('totalHits')}")
                for j in jobs[:5]:
                    log(f"      - {j.get('title')} | {j.get('location')} | applyUrl={str(j.get('applyUrl'))[:90]}")
            except Exception as e:  # noqa: BLE001
                log(f"  ddo parse error {e}")
    r = try_req("widgets", "POST", f"https://{host}/widgets", json=body,
                headers={"Content-Type": "application/json", "Origin": f"https://{host}",
                         "Referer": f"https://{host}/us/en/search-results"})
    d = show("widgets", r)
    if isinstance(d, dict):
        rs = d.get("refineSearch") or {}
        log(f"  refineSearch totalHits={rs.get('totalHits')} hits={len((rs.get('data') or {}).get('jobs') or [])}")


# ------------------------------------------------------------------ Radancy / TalentBrew
def radancy(host, kw="summer analyst"):
    url = (f"https://{host}/search-jobs/results?ActiveFacetID=0&CurrentPage=1&RecordsPerPage=100"
           f"&Distance=50&RadiusUnitType=0&Keywords={requests.utils.quote(kw)}&Location=&ShowRadius=False"
           f"&IsPagination=False&FacetType=0&SearchResultsModuleName=Search+Results"
           f"&SearchFiltersModuleName=Search+Filters&SortCriteria=0&SortDirection=0&SearchType=5"
           f"&ResultsType=0")
    r = try_req("radancy", "GET", url, headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
    if r is None:
        return
    try:
        d = r.json()
        html = d.get("results", "")
        links = re.findall(r'href="(/[^"]*?/job/[^"]+)"', html) or re.findall(r'href="(/job/[^"]+)"', html)
        titles = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.S)
        log(f"  radancy: HTTP {r.status_code} keys={list(d.keys())[:6]} links={len(links)} titles={len(titles)} hasJobs={d.get('hasJobs')}")
        for t, l in list(zip(titles, links))[:6]:
            log(f"      - {re.sub('<[^>]+>', '', t).strip()} | {l[:100]}")
    except Exception:  # noqa: BLE001
        log(f"  radancy: HTTP {r.status_code} not-json body={r.text[:160]!r}")


# ------------------------------------------------------------------ Jibe (iCIMS)
def jibe(host, kw="intern"):
    r = try_req("jibe", "GET", f"https://{host}/api/jobs?keywords={kw}&page=1&limit=100",
                headers={"Accept": "application/json"})
    d = show("jibe", r)
    if isinstance(d, dict):
        jobs = d.get("jobs") or []
        log(f"  jibe totalCount={d.get('totalCount')} count={d.get('count')} jobs={len(jobs)}")
        for j in jobs[:5]:
            dd = j.get("data", j)
            log(f"      - {dd.get('title')} | {dd.get('full_location') or dd.get('city')} | slug={dd.get('slug')} req={dd.get('req_id')} apply={str(dd.get('apply_url'))[:80]}")


# ------------------------------------------------------------------ Oracle HCM
def oracle(host, site, kw="summer analyst"):
    url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
           f"&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber={site},"
           f"keyword=%22{requests.utils.quote(kw)}%22,limit=50,offset=0,sortBy=POSTING_DATES_DESC")
    r = try_req("oracle", "GET", url, headers={"Accept": "application/json"})
    d = show(f"oracle {site}", r)
    if isinstance(d, dict):
        items = d.get("items") or []
        if items:
            rl = items[0].get("requisitionList") or []
            log(f"  TotalJobsCount={items[0].get('TotalJobsCount')} returned={len(rl)}")
            for j in rl[:6]:
                log(f"      - {j.get('Title')} | {j.get('PrimaryLocation')} | Id={j.get('Id')} posted={j.get('PostedDate')}")


# ------------------------------------------------------------------ Goldman
def goldman():
    r = try_req("gs home", "GET", "https://higher.gs.com/results?query=2027&type=students&page=1&sort=RELEVANCE")
    if r is None:
        return
    log(f"  gs home: HTTP {r.status_code} len={len(r.text)}")
    apis = sorted(set(re.findall(r'https://[a-z0-9.-]*gs\.com/[A-Za-z0-9/_.-]*(?:api|graphql)[A-Za-z0-9/_.-]*', r.text)))
    log(f"  api-like urls in html: {apis[:10]}")
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', r.text)
    log(f"  scripts: {scripts[:8]}")
    for s in scripts[:12]:
        u = s if s.startswith("http") else "https://higher.gs.com" + s
        js = try_req("js", "GET", u)
        if js is None:
            continue
        found = sorted(set(re.findall(r'https://[a-z0-9.-]+/[A-Za-z0-9/_.-]*(?:graphql|api)[A-Za-z0-9/_.-]*', js.text)))
        ops = sorted(set(re.findall(r'(?:query|mutation)\s+([A-Za-z]+)\s*\(', js.text)))[:20]
        if found or ops:
            log(f"  {u[-60:]}: urls={found[:8]} ops={ops}")
    for u in ["https://api-higher.gs.com/gateway/api/v1/graphql", "https://higher.gs.com/api/graphql"]:
        q = {"operationName": "GetRoles", "variables": {"searchQueryInput": {"page": {"pageSize": 20, "pageNumber": 0},
             "sort": {"sortStrategy": "RELEVANCE", "sortOrder": "DESC"}, "filters": [], "experiences": ["EARLY_CAREER"],
             "searchTerm": "2027"}},
             "query": "query GetRoles($searchQueryInput: RoleSearchQueryInput!) { roleSearch(searchQueryInput: $searchQueryInput) { totalCount items { roleId jobTitle locations { city state country } } } }"}
        rr = try_req("gs gql", "POST", u, json=q, headers={"Content-Type": "application/json",
                     "Origin": "https://higher.gs.com", "Referer": "https://higher.gs.com/"})
        if rr is not None:
            log(f"  POST {u}: HTTP {rr.status_code} body={rr.text[:300]!r}")


# ------------------------------------------------------------------ Workday guesses
WD = [("truist", "wd1", ["Careers", "Truist", "TruistCareers", "External"]),
      ("truist", "wd5", ["Careers", "Truist"]),
      ("frostbank", "wd5", ["Frost", "FrostBank", "External", "Careers"]),
      ("comerica", "wd5", ["Comerica", "External", "Careers"]),
      ("regions", "wd5", ["Regions_Careers", "Regions", "External"]),
      ("firsthorizon", "wd1", ["FirstHorizon", "External", "Careers"]),
      ("cadencebank", "wd5", ["External", "Careers", "CadenceBank"]),
      ("prosperitybank", "wd5", ["External", "Careers", "Prosperity"]),
      ("prosperity", "wd1", ["External", "Careers"]),
      ("fifththird", "wd5", ["53", "External", "Careers"]),
      ("huntington", "wd12", ["HNBcareers", "External", "Careers"]),
      ("usbank", "wd1", ["US_Bank_Careers", "External"]),
      ("jefferies", "wd5", ["Jefferies", "JefferiesCareers", "External"]),
      ("evercore", "wd1", ["Evercore", "EvercoreCareers", "External"]),
      ("moodys", "wd5", ["Moodys", "Careers", "External"]),
      ("ms", "wd5", ["External", "Careers"]),
      ("osv-cci", "wd1", ["CCICareers"]),
      ("pru", "wd5", ["Careers", "PGIM", "PGIM_Careers"])]


def workday():
    for tenant, wd, sites in WD:
        for site in sites:
            url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
            r = try_req("wd", "POST", url, json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "summer"},
                        headers={"Content-Type": "application/json", "Accept": "application/json",
                                 "Origin": f"https://{tenant}.{wd}.myworkdayjobs.com",
                                 "Referer": f"https://{tenant}.{wd}.myworkdayjobs.com/en-US/{site}"})
            if r is None:
                continue
            ok = r.status_code == 200
            extra = ""
            if ok:
                try:
                    d = r.json(); extra = f"total={d.get('total')} sample={[p.get('title') for p in (d.get('jobPostings') or [])[:4]]}"
                except Exception:  # noqa: BLE001
                    extra = "not-json"
            else:
                extra = r.text[:120].replace("\n", " ")
            log(f"  {'HIT ' if ok else 'miss'} {tenant}/{wd}/{site}: HTTP {r.status_code} {extra}")
            time.sleep(1.5)
            if ok:
                break


def main():
    which = set(sys.argv[1:]) or {"phenom", "radancy", "jibe", "oracle", "goldman", "workday"}
    if "phenom" in which:
        for h in PHENOM:
            log(f"\n=== Phenom {h}")
            phenom(h)
    if "radancy" in which:
        for h in ["jobs.citi.com", "jobs.citizensbank.com", "careers.bankofamerica.com", "www.wellsfargojobs.com", "jobs.jpmorganchase.com"]:
            log(f"\n=== Radancy {h}")
            radancy(h)
    if "jibe" in which:
        for h in ["careers.amegybank.com", "careers.zionsbancorp.com", "growwithzions.zionsbancorp.com",
                  "hilltop-holdings.jibeapply.com", "careers.prosperitybankusa.com"]:
            log(f"\n=== Jibe {h}")
            jibe(h)
    if "oracle" in which:
        for site in ["CX_1001", "CX_1002", "CX"]:
            log(f"\n=== Oracle jpmc {site}")
            oracle("jpmc.fa.oraclecloud.com", site)
    if "goldman" in which:
        log("\n=== Goldman")
        goldman()
    if "workday" in which:
        log("\n=== Workday guesses")
        workday()
    try:
        import os
        p = os.environ.get("GITHUB_STEP_SUMMARY")
        if p:
            with open(p, "a") as f:
                f.write("```\n" + "\n".join(OUT)[-60000:] + "\n```\n")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
