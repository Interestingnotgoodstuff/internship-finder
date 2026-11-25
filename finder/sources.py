"""Fetch job postings from the public job-board APIs that companies use.

Each fetcher returns a list of dicts with the same shape:
    {id, company, category, title, location, url, posted, description, source}
Descriptions are plain text (HTML stripped).
"""
from __future__ import annotations

import html
import re
import time
from typing import Iterable

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 25
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "application/json",
                        "Accept-Language": "en-US"})

# Words used to search large Workday boards. Each term is searched separately
# and results are merged, so a posting only needs to match one of them.
WORKDAY_SEARCH_TERMS = ["summer", "intern"]
WORKDAY_PAGE = 20          # Workday's maximum page size
WORKDAY_MAX_PER_TERM = 200 # safety cap per search term

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")


def html_to_text(raw: str | None) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)          # Greenhouse double-escapes its HTML
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</div>|</h\d>", "\n", text)
    text = _TAG.sub(" ", text)
    text = html.unescape(text)
    text = _WS.sub(" ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


_last_call = {"t": 0.0}
MIN_GAP = 1.2          # seconds between requests (Workday rate-limits fast callers)


def _throttle():
    wait = MIN_GAP - (time.time() - _last_call["t"])
    if wait > 0:
        time.sleep(wait)
    _last_call["t"] = time.time()


def _request(method: str, url: str, headers=None, **kw):
    delays = [20, 60, 120]
    for attempt in range(len(delays) + 1):
        _throttle()
        r = SESSION.request(method, url, timeout=TIMEOUT, headers=headers, **kw)
        if r.status_code not in (429, 503) or attempt == len(delays):
            r.raise_for_status()
            return r.json()
        retry = r.headers.get("Retry-After", "")
        time.sleep(int(retry) if retry.isdigit() else delays[attempt])
    raise RuntimeError("unreachable")


def _wd_headers(url: str) -> dict:
    host = url.split("/wday/")[0]
    return {"Content-Type": "application/json", "Origin": host, "Referer": host + "/"}


def _get(url: str, **kw):
    headers = _wd_headers(url) if "myworkdayjobs.com" in url else None
    return _request("GET", url, headers=headers, **kw)


def _post(url: str, payload: dict):
    return _request("POST", url, headers=_wd_headers(url), json=payload)


# ----------------------------------------------------------------- Workday
def workday_base(tenant: str, wd: str, site: str) -> str:
    return f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"


def parse_workday_list(data: dict) -> list[dict]:
    return data.get("jobPostings") or []


def parse_workday_detail(data: dict) -> dict:
    return data.get("jobPostingInfo") or {}


def fetch_workday(c: dict, title_prefilter=None, cache=None, **_) -> list[dict]:
    """cache: {job_id: previous job dict}. Known postings reuse their stored
    description instead of downloading it again (saves most requests)."""
    cache = cache or {}
    base = workday_base(c["tenant"], c["wd"], c["site"])
    seen_paths: dict[str, dict] = {}
    for term in WORKDAY_SEARCH_TERMS:
        offset = 0
        while offset < WORKDAY_MAX_PER_TERM:
            try:
                data = _post(f"{base}/jobs", {"appliedFacets": {}, "limit": WORKDAY_PAGE,
                                              "offset": offset, "searchText": term})
            except requests.HTTPError as e:
                # Some boards reject keyword search (HTTP 422); list everything instead.
                if e.response is None or e.response.status_code != 422 or term == "":
                    raise
                term = ""
                data = _post(f"{base}/jobs", {"appliedFacets": {}, "limit": WORKDAY_PAGE,
                                              "offset": offset, "searchText": ""})
            posts = parse_workday_list(data)
            for p in posts:
                path = p.get("externalPath")
                if path and path not in seen_paths:
                    seen_paths[path] = p
            total = data.get("total") or 0
            offset += WORKDAY_PAGE
            if not posts or offset >= total:
                break

    out = []
    for path, p in seen_paths.items():
        title = p.get("title", "")
        if title_prefilter and not title_prefilter(title):
            continue
        jid = f"workday:{c['tenant']}:{path}"
        old = cache.get(jid)
        if old and old.get("description"):
            info = {"title": old.get("title"), "location": old.get("location"),
                    "externalUrl": old.get("url"), "postedOn": old.get("posted")}
            desc = old["description"]
        else:
            try:
                info = parse_workday_detail(_get(f"{base}{path}"))
            except requests.RequestException:
                info = {}
            desc = html_to_text(info.get("jobDescription"))
        public = info.get("externalUrl") or (
            f"https://{c['tenant']}.{c['wd']}.myworkdayjobs.com/en-US/{c['site']}{path}")
        out.append({
            "id": jid,
            "company": c["name"],
            "category": c.get("category", ""),
            "title": info.get("title") or title,
            "location": info.get("location") or p.get("locationsText", ""),
            "url": public,
            "posted": p.get("postedOn") or info.get("postedOn", ""),
            "description": desc,
            "source": "Workday",
        })
    return out


# -------------------------------------------------------------- Greenhouse
def parse_greenhouse(c: dict, data: dict) -> list[dict]:
    out = []
    for j in data.get("jobs", []):
        out.append({
            "id": f"greenhouse:{c['token']}:{j.get('id')}",
            "company": c["name"],
            "category": c.get("category", ""),
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "posted": j.get("first_published") or j.get("updated_at", ""),
            "description": html_to_text(j.get("content")),
            "source": "Greenhouse",
        })
    return out


def fetch_greenhouse(c: dict, **_) -> list[dict]:
    data = _get(f"https://boards-api.greenhouse.io/v1/boards/{c['token']}/jobs",
                params={"content": "true"})
    return parse_greenhouse(c, data)


# ------------------------------------------------------------------- Lever
def parse_lever(c: dict, data: list) -> list[dict]:
    out = []
    for j in data or []:
        cats = j.get("categories") or {}
        parts = [j.get("descriptionPlain") or ""]
        for lst in j.get("lists") or []:
            parts.append(lst.get("text", ""))
            parts.append(html_to_text(lst.get("content")))
        parts.append(j.get("additionalPlain") or "")
        created = j.get("createdAt")
        out.append({
            "id": f"lever:{c['slug']}:{j.get('id')}",
            "company": c["name"],
            "category": c.get("category", ""),
            "title": j.get("text", ""),
            "location": cats.get("location", "") or ", ".join(cats.get("allLocations") or []),
            "url": j.get("hostedUrl", ""),
            "posted": time.strftime("%Y-%m-%d", time.gmtime(created / 1000)) if created else "",
            "description": "\n".join(p for p in parts if p).strip(),
            "source": "Lever",
        })
    return out


def fetch_lever(c: dict, **_) -> list[dict]:
    return parse_lever(c, _get(f"https://api.lever.co/v0/postings/{c['slug']}",
                               params={"mode": "json"}))


# ------------------------------------------------------------------- Ashby
def parse_ashby(c: dict, data: dict) -> list[dict]:
    out = []
    for j in data.get("jobs", []):
        out.append({
            "id": f"ashby:{c['org']}:{j.get('id')}",
            "company": c["name"],
            "category": c.get("category", ""),
            "title": j.get("title", ""),
            "location": j.get("location", ""),
            "url": j.get("jobUrl", ""),
            "posted": (j.get("publishedAt") or "")[:10],
            "description": j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml")),
            "source": "Ashby",
        })
    return out


def fetch_ashby(c: dict, **_) -> list[dict]:
    return parse_ashby(c, _get(f"https://api.ashbyhq.com/posting-api/job-board/{c['org']}"))


# -------------------------------------------------------------- Phenom
# Career sites at careers.<bank>.com/us/en (Truist, Frost, Regions, US Bank).
# Their keyword search is unreliable, so page through every listing and
# filter titles locally; only matching postings get a detail request.
def _phenom_page(host: str, frm: int, size: int = 100) -> dict:
    body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results",
            "ddoKey": "refineSearch", "sortBy": "", "subsearch": "", "from": frm, "jobs": True,
            "counts": False, "all_fields": [], "size": size, "clearAll": False, "jdsource": "facets",
            "isSliderEnable": False, "pageId": "page20", "siteType": "external", "keywords": "",
            "global": True, "selected_fields": {}, "locationData": {}}
    return _request("POST", f"https://{host}/widgets", json=body,
                    headers={"Content-Type": "application/json", "Origin": f"https://{host}",
                             "Referer": f"https://{host}/us/en/search-results"}).get("refineSearch") or {}


_JSON_DESC = re.compile(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"')


def _phenom_description(host: str, job_id: str) -> str:
    try:
        _throttle()
        r = SESSION.get(f"https://{host}/us/en/job/{job_id}", timeout=TIMEOUT)
        m = _JSON_DESC.search(r.text)
        if not m:
            return ""
        import json as _json
        return html_to_text(_json.loads('"' + m.group(1) + '"'))
    except Exception:  # noqa: BLE001
        return ""


def fetch_phenom(c: dict, title_prefilter=None, cache=None, **_) -> list[dict]:
    cache = cache or {}
    host, size, frm, total, posts = c["host"], 100, 0, None, []
    while total is None or frm < min(total, 3000):
        rs = _phenom_page(host, frm, size)
        jobs = (rs.get("data") or {}).get("jobs") or []
        total = rs.get("totalHits") or 0
        posts.extend(jobs)
        if not jobs:
            break
        frm += size
    out = []
    for j in posts:
        title = j.get("title", "")
        if title_prefilter and not title_prefilter(title):
            continue
        jid = f"phenom:{host}:{j.get('jobId') or j.get('reqId')}"
        old = cache.get(jid)
        desc = old["description"] if old and old.get("description") else _phenom_description(host, j.get("jobId"))
        out.append({
            "id": jid, "company": c["name"], "category": c.get("category", ""),
            "title": title, "location": j.get("cityStateCountry") or j.get("location", ""),
            "url": f"https://{host}/us/en/job/{j.get('jobId')}",
            "posted": (j.get("postedDate") or j.get("dateCreated") or "")[:10],
            "description": desc or html_to_text(j.get("descriptionTeaser")), "source": "Phenom",
        })
    return out


# ------------------------------------------------------ Radancy (Citi)
_RADANCY_ITEM = re.compile(
    r'<a[^>]+href="(/job/[^"]+)"[^>]*>\s*(.*?)\s*</a>.*?(?:sr-job-location|job-location)[^>]*>(.*?)<', re.S)


def fetch_radancy(c: dict, title_prefilter=None, cache=None, **_) -> list[dict]:
    cache = cache or {}
    host, seen = c["host"], {}
    for kw in c.get("keywords", ["2027", "intern"]):
        for page in range(1, 11):
            url = (f"https://{host}/search-jobs/results?ActiveFacetID=0&CurrentPage={page}&RecordsPerPage=100"
                   f"&Distance=50&RadiusUnitType=0&Keywords={requests.utils.quote(kw)}&Location=&ShowRadius=False"
                   f"&IsPagination=True&FacetType=0&SearchResultsModuleName=Search+Results"
                   f"&SearchFiltersModuleName=Search+Filters&SortCriteria=0&SortDirection=0&SearchType=5&ResultsType=0")
            d = _request("GET", url, headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
            items = _RADANCY_ITEM.findall(d.get("results", ""))
            for link, title, loc in items:
                seen.setdefault(link, (html.unescape(re.sub(r"<[^>]+>", "", title)).strip(), html.unescape(loc).strip()))
            if len(items) < 100:
                break
    out = []
    for link, (title, loc) in seen.items():
        if title_prefilter and not title_prefilter(title):
            continue
        jid = f"radancy:{host}:{link.rsplit('/', 1)[-1]}"
        old = cache.get(jid)
        desc, posted = (old.get("description"), old.get("posted", "")) if old and old.get("description") else ("", "")
        if not desc:
            try:
                _throttle()
                page = SESSION.get(f"https://{host}{link}", timeout=TIMEOUT).text
                m = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
                if m:
                    import json as _json
                    ld = _json.loads(m.group(1))
                    desc, posted = html_to_text(ld.get("description")), ld.get("datePosted", "")
            except Exception:  # noqa: BLE001
                pass
        out.append({"id": jid, "company": c["name"], "category": c.get("category", ""), "title": title,
                    "location": loc, "url": f"https://{host}{link}", "posted": posted,
                    "description": desc, "source": "Radancy"})
    return out


# ------------------------------------------------- Oracle HCM (J.P. Morgan)
def fetch_oracle(c: dict, title_prefilter=None, cache=None, **_) -> list[dict]:
    cache = cache or {}
    host, site, seen = c["host"], c["site"], {}
    api = f"https://{host}/hcmRestApi/resources/latest"
    for kw in c.get("keywords", ["2027", "intern", "summer"]):
        offset = 0
        while offset < 1000:
            url = (f"{api}/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations"
                   f"&finder=findReqs;siteNumber={site},keyword=%22{requests.utils.quote(kw)}%22,"
                   f"limit=100,offset={offset},sortBy=POSTING_DATES_DESC")
            items = (_request("GET", url).get("items") or [{}])
            reqs = items[0].get("requisitionList") or []
            for r in reqs:
                seen.setdefault(str(r.get("Id")), r)
            total = items[0].get("TotalJobsCount") or 0
            offset += 100
            if not reqs or offset >= total:
                break
    out = []
    for rid, r in seen.items():
        title = r.get("Title", "")
        if title_prefilter and not title_prefilter(title):
            continue
        jid = f"oracle:{host}:{rid}"
        old = cache.get(jid)
        desc = old.get("description") if old else ""
        if not desc:
            try:
                d = _request("GET", f'{api}/recruitingCEJobRequisitionDetails?expand=all&onlyData=true'
                                    f'&finder=ById;Id=%22{rid}%22,siteNumber={site}')
                it = (d.get("items") or [{}])[0]
                desc = html_to_text(" ".join(str(it.get(k) or "") for k in
                                             ("ExternalDescriptionStr", "ExternalQualificationsStr",
                                              "ExternalResponsibilitiesStr", "ShortDescriptionStr")))
            except Exception:  # noqa: BLE001
                desc = html_to_text(r.get("ShortDescriptionStr"))
        locs = [r.get("PrimaryLocation", "")] + [x.get("Name", "") for x in (r.get("secondaryLocations") or [])]
        out.append({"id": jid, "company": c["name"], "category": c.get("category", ""), "title": title,
                    "location": "; ".join(l for l in locs if l),
                    "url": f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{rid}",
                    "posted": (r.get("PostedDate") or "")[:10], "description": desc, "source": "Oracle"})
    return out


# ----------------------------------------------------------- Goldman Sachs
GS_QUERY = """query GetCampusRoles($searchQueryInput: RoleSearchQueryInput!) {
  roleSearch(searchQueryInput: $searchQueryInput) { totalCount items {
    roleId corporateTitle jobTitle jobFunction locations { primary state country city }
    status division educationLevel startDate gradDegreeStartDate gradDegreeEndDate
    externalSource { sourceId } } } }"""


def fetch_goldman(c: dict, title_prefilter=None, **_) -> list[dict]:
    out, page, size = [], 0, 100
    while True:
        payload = {"operationName": "GetCampusRoles", "query": GS_QUERY, "variables": {"searchQueryInput": {
            "page": {"pageSize": size, "pageNumber": page},
            "sort": {"sortStrategy": "POSTED_DATE", "sortOrder": "DESC"},
            "filters": [], "experiences": ["CAMPUS"], "searchTerm": ""}}}
        d = _request("POST", "https://api-higher.gs.com/gateway/api/v1/graphql", json=payload,
                     headers={"Content-Type": "application/json", "Origin": "https://higher.gs.com",
                              "Referer": "https://higher.gs.com/"})
        if d.get("errors"):
            raise RuntimeError(str(d["errors"])[:200])
        rs = (d.get("data") or {}).get("roleSearch") or {}
        items = rs.get("items") or []
        for r in items:
            title = r.get("jobTitle") or ""
            if title_prefilter and not title_prefilter(title):
                continue
            locs = r.get("locations") or []
            loc = "; ".join(", ".join(x for x in (l.get("city"), l.get("state"), l.get("country")) if x) for l in locs)
            g1, g2 = (r.get("gradDegreeStartDate") or "")[:7], (r.get("gradDegreeEndDate") or "")[:7]
            desc = (f"Division: {r.get('division') or ''}. Function: {r.get('jobFunction') or ''}. "
                    + (f"Candidates graduating between {_ym(g1)} and {_ym(g2)}. " if g1 and g2 else ""))
            out.append({"id": f"goldman:{r.get('roleId')}", "company": c["name"], "category": c.get("category", ""),
                        "title": title, "location": loc, "url": f"https://higher.gs.com/roles/{r.get('roleId')}",
                        "posted": (r.get("startDate") or "")[:10], "description": desc, "source": "Goldman"})
        if not items or (page + 1) * size >= (rs.get("totalCount") or 0):
            break
        page += 1
    return out


def _ym(s: str) -> str:
    try:
        y, m = s.split("-")[:2]
        return ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                "October", "November", "December"][int(m) - 1] + " " + y
    except Exception:  # noqa: BLE001
        return s


FETCHERS = {
    "workday": fetch_workday,
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "phenom": fetch_phenom,
    "radancy": fetch_radancy,
    "oracle": fetch_oracle,
    "goldman": fetch_goldman,
}


def fetch_company(c: dict, title_prefilter=None, cache=None) -> list[dict]:
    fn = FETCHERS.get(c.get("ats", ""))
    if not fn:
        raise ValueError(f"unknown ats '{c.get('ats')}'")
    return fn(c, title_prefilter=title_prefilter, cache=cache)


def iter_safe(companies: Iterable[dict], title_prefilter=None, cache=None):
    """Yield (company, jobs, error) so one broken board never stops the run."""
    for c in companies:
        try:
            yield c, fetch_company(c, title_prefilter=title_prefilter, cache=cache), None
        except Exception as e:  # noqa: BLE001 - report and keep going
            yield c, [], f"{type(e).__name__}: {e}"[:300]
