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

UA = "Mozilla/5.0 (compatible; internship-finder/1.0; personal job search)"
TIMEOUT = 25
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "application/json",
                        "Accept-Language": "en-US"})

# Words used to search large Workday boards. Each term is searched separately
# and results are merged, so a posting only needs to match one of them.
WORKDAY_SEARCH_TERMS = ["summer", "intern", "2027"]
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


def _get(url: str, **kw):
    r = SESSION.get(url, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r.json()


def _post(url: str, payload: dict):
    r = SESSION.post(url, json=payload, timeout=TIMEOUT,
                     headers={"Content-Type": "application/json"})
    r.raise_for_status()
    return r.json()


# ----------------------------------------------------------------- Workday
def workday_base(tenant: str, wd: str, site: str) -> str:
    return f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"


def parse_workday_list(data: dict) -> list[dict]:
    return data.get("jobPostings") or []


def parse_workday_detail(data: dict) -> dict:
    return data.get("jobPostingInfo") or {}


def fetch_workday(c: dict, title_prefilter=None, delay: float = 0.3) -> list[dict]:
    base = workday_base(c["tenant"], c["wd"], c["site"])
    seen_paths: dict[str, dict] = {}
    for term in WORKDAY_SEARCH_TERMS:
        offset = 0
        while offset < WORKDAY_MAX_PER_TERM:
            data = _post(f"{base}/jobs", {"appliedFacets": {}, "limit": WORKDAY_PAGE,
                                          "offset": offset, "searchText": term})
            posts = parse_workday_list(data)
            for p in posts:
                path = p.get("externalPath")
                if path and path not in seen_paths:
                    seen_paths[path] = p
            total = data.get("total") or 0
            offset += WORKDAY_PAGE
            if not posts or offset >= total:
                break
            time.sleep(delay)

    out = []
    for path, p in seen_paths.items():
        title = p.get("title", "")
        # Skip detail calls for titles that clearly aren't internships.
        if title_prefilter and not title_prefilter(title):
            continue
        try:
            info = parse_workday_detail(_get(f"{base}{path}"))
        except requests.RequestException:
            info = {}
        time.sleep(delay)
        public = info.get("externalUrl") or (
            f"https://{c['tenant']}.{c['wd']}.myworkdayjobs.com/en-US/{c['site']}{path}")
        out.append({
            "id": f"workday:{c['tenant']}:{info.get('jobReqId') or path}",
            "company": c["name"],
            "category": c.get("category", ""),
            "title": info.get("title") or title,
            "location": info.get("location") or p.get("locationsText", ""),
            "url": public,
            "posted": info.get("postedOn") or p.get("postedOn", ""),
            "description": html_to_text(info.get("jobDescription")),
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


FETCHERS = {
    "workday": fetch_workday,
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}


def fetch_company(c: dict, title_prefilter=None) -> list[dict]:
    fn = FETCHERS.get(c.get("ats", ""))
    if not fn:
        raise ValueError(f"unknown ats '{c.get('ats')}'")
    return fn(c, title_prefilter=title_prefilter)


def iter_safe(companies: Iterable[dict], title_prefilter=None):
    """Yield (company, jobs, error) so one broken board never stops the run."""
    for c in companies:
        try:
            yield c, fetch_company(c, title_prefilter=title_prefilter), None
        except Exception as e:  # noqa: BLE001 - report and keep going
            yield c, [], f"{type(e).__name__}: {e}"[:300]
