"""Second probe: response shapes for Goldman, Citi, Phenom, Oracle detail."""
import json, re, requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA, "Accept-Language": "en-US"})
def p(*a): print(*a, flush=True)

p("=== GOLDMAN query text")
home = S.get("https://higher.gs.com/results?query=2027&type=students", timeout=25).text
for s in re.findall(r'<script[^>]+src="([^"]+)"', home):
    js = S.get("https://higher.gs.com" + s if s.startswith("/") else s, timeout=25).text
    for name in ["GetRoles", "GetCampusRoles"]:
        for m in re.finditer(r'(query|mutation)\s+' + name + r'\b', js):
            p(f"--- {name} in {s[-40:]}:\n", js[max(0, m.start()-200): m.start()+2500].replace("\\n", "\n"))
            break

p("\n=== CITI result html sample")
u = ("https://jobs.citi.com/search-jobs/results?ActiveFacetID=0&CurrentPage=1&RecordsPerPage=15&Distance=50"
     "&RadiusUnitType=0&Keywords=2027&Location=&ShowRadius=False&IsPagination=False&FacetType=0"
     "&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=0"
     "&SortDirection=0&SearchType=5&ResultsType=0")
d = S.get(u, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=25).json()
h = d["results"]; i = h.find('/job/')
p(h[max(0, i-600): i+1800])
link = re.search(r'href="(/job/[^"]+)"', h).group(1)
dp = S.get("https://jobs.citi.com" + link, timeout=25).text
p("\n--- detail page", link, len(dp))
for cls in ["ats-description", "job-description", "jd-description", "description"]:
    j = dp.find(cls); p(cls, j, dp[j:j+300].replace("\n", " ") if j > 0 else "")
m = re.search(r'<script type="application/ld\+json">(.*?)</script>', dp, re.S)
p("ld+json:", (m.group(1)[:800] if m else None))

p("\n=== PHENOM keyword behavior")
def phen(host, kw, frm=0):
    body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results", "ddoKey": "refineSearch",
            "sortBy": "", "subsearch": "", "from": frm, "jobs": True, "counts": True, "all_fields": ["category", "city", "state"],
            "size": 50, "clearAll": False, "jdsource": "facets", "isSliderEnable": False, "pageId": "page20",
            "siteType": "external", "keywords": kw, "global": True, "selected_fields": {}, "locationData": {}}
    r = S.post(f"https://{host}/widgets", json=body, timeout=25, headers={"Origin": f"https://{host}", "Referer": f"https://{host}/us/en/search-results"})
    return r.json().get("refineSearch", {})
for host in ["careers.truist.com", "careers.frostbank.com", "careers.regions.com", "careers.usbank.com"]:
    for kw in ["", "intern", "summer", "2027", "internship"]:
        rs = phen(host, kw); jobs = (rs.get("data") or {}).get("jobs") or []
        p(f"{host} kw={kw!r}: totalHits={rs.get('totalHits')} got={len(jobs)} intern-ish={[j['title'] for j in jobs if re.search('intern|summer', j.get('title',''), re.I)][:6]}")
    rs = phen(host, ""); jobs = (rs.get("data") or {}).get("jobs") or []
    if jobs:
        p("  keys:", sorted(jobs[0].keys()))
        j0 = jobs[0]; jp = S.get(f"https://{host}/us/en/job/{j0.get('jobId')}", timeout=25).text
        m = re.search(r'"description"\s*:\s*"(.{0,300})', jp); p("  detail desc:", m.group(1) if m else None, "len", len(jp))

p("\n=== ORACLE detail")
r = S.get("https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&finder=findReqs;siteNumber=CX_1001,keyword=%222027%22,limit=5,offset=0", timeout=25).json()
rl = r["items"][0]["requisitionList"]; p("total", r["items"][0].get("TotalJobsCount"), [x["Title"] for x in rl])
jid = rl[0]["Id"]; p("list keys", sorted(rl[0].keys()))
d = S.get(f'https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ById;Id=%22{jid}%22,siteNumber=CX_1001', timeout=25).json()
it = d["items"][0]; p("detail keys", sorted(it.keys())[:40]); p("desc:", str(it.get("ExternalDescriptionStr"))[:400])
