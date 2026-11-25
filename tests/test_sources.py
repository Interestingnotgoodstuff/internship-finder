"""Parsers are tested against payloads shaped like the real APIs."""
from finder import sources as S


def test_html_to_text_handles_greenhouse_escaping():
    raw = "&lt;p&gt;Graduating &lt;strong&gt;May 2028&lt;/strong&gt;&lt;/p&gt;&lt;ul&gt;&lt;li&gt;Excel&lt;/li&gt;&lt;/ul&gt;"
    assert "Graduating May 2028" in S.html_to_text(raw)
    assert "Excel" in S.html_to_text(raw)


def test_parse_greenhouse():
    c = {"name": "KBRA", "token": "krollbondratingagency", "category": "Ratings"}
    data = {"jobs": [{"id": 123, "title": "Summer Intern - Corporate Ratings",
                      "location": {"name": "New York, NY"},
                      "absolute_url": "https://job-boards.greenhouse.io/krollbondratingagency/jobs/123",
                      "updated_at": "2026-11-01T00:00:00-04:00",
                      "content": "&lt;p&gt;Class of 2028&lt;/p&gt;"}]}
    jobs = S.parse_greenhouse(c, data)
    assert jobs[0]["id"] == "greenhouse:krollbondratingagency:123"
    assert jobs[0]["location"] == "New York, NY"
    assert "Class of 2028" in jobs[0]["description"]


def test_parse_lever():
    c = {"name": "D.A. Davidson", "slug": "dadavidson"}
    data = [{"id": "abc", "text": "Investment Banking Summer Analyst",
             "hostedUrl": "https://jobs.lever.co/dadavidson/abc",
             "categories": {"location": "Chicago, IL", "commitment": "Intern"},
             "descriptionPlain": "Summer 2027.", "lists": [{"text": "Requirements", "content": "<li>Graduating May 2028</li>"}],
             "createdAt": 1767225600000}]
    j = S.parse_lever(c, data)[0]
    assert j["location"] == "Chicago, IL" and "Graduating May 2028" in j["description"]
    assert j["posted"].startswith("2026") or j["posted"].startswith("2025")


def test_parse_ashby():
    c = {"name": "Agentis", "org": "agentis-capital-advisors"}
    data = {"jobs": [{"id": "x1", "title": "IB Summer Analyst - Summer 2027", "location": "New York",
                      "jobUrl": "https://jobs.ashbyhq.com/agentis/x1", "descriptionPlain": "Penultimate year.",
                      "publishedAt": "2026-10-01T00:00:00Z"}]}
    j = S.parse_ashby(c, data)[0]
    assert j["posted"] == "2026-10-01" and j["url"].endswith("x1")


def test_workday_payload_shapes():
    listing = {"total": 1, "jobPostings": [{"title": "2027 Summer Analyst", "externalPath": "/job/NY/2027-Summer-Analyst_R1",
                                            "locationsText": "New York, NY", "postedOn": "Posted 5 Days Ago"}]}
    detail = {"jobPostingInfo": {"title": "2027 Summer Analyst", "jobDescription": "<p>Graduating May 2028</p>",
                                 "location": "New York, NY", "jobReqId": "R1",
                                 "externalUrl": "https://x.wd1.myworkdayjobs.com/en-US/Site/job/NY/2027-Summer-Analyst_R1"}}
    assert S.parse_workday_list(listing)[0]["externalPath"].startswith("/job/")
    assert S.parse_workday_detail(detail)["jobReqId"] == "R1"
    assert S.workday_base("bmo", "wd3", "Campus") == "https://bmo.wd3.myworkdayjobs.com/wday/cxs/bmo/Campus"


def test_shards_cover_every_board_once():
    from finder.main import load_config, shard_of
    cos = load_config()["companies"]
    names = [c["name"] for k in range(4) for c in shard_of(cos, k, 4)]
    assert sorted(names) == sorted(c["name"] for c in cos)


def test_radancy_item_regex():
    from finder.sources import _RADANCY_ITEM
    html = '''<h3 class="sr-job-item__title">
      <a class="sr-job-item__link" href="/job/houston/banking-corporate-banking-summer-analyst-houston-us-2027/287/89623966960" data-job-id="1">
          Banking - Corporate Banking Summer Analyst - Houston, US 2027
      </a></h3>
      <span class="sr-job-item__facet sr-job-item__facet-icon sr-job-location">Houston, Texas, United States</span></li>'''
    (link, title, loc), = _RADANCY_ITEM.findall(html)
    assert link.endswith("/89623966960") and title.startswith("Banking - Corporate") and loc.startswith("Houston")


def test_goldman_parse(monkeypatch):
    from finder import sources as S
    fake = {"data": {"roleSearch": {"totalCount": 1, "items": [{
        "roleId": "158147", "jobTitle": "2027 | Americas | Dallas | Transaction Banking (TxB), Coverage | Summer Analyst",
        "locations": [{"city": "Dallas", "state": "Texas", "country": "United States"}], "division": "Banking",
        "jobFunction": "Coverage", "gradDegreeStartDate": "2027-12-01", "gradDegreeEndDate": "2028-06-30"}]}}}
    monkeypatch.setattr(S, "_request", lambda *a, **k: fake)
    (j,) = S.fetch_goldman({"name": "Goldman Sachs"})
    from finder.classify import classify
    classify(j)
    assert j["eligibility"] == "Eligible" and "Dallas" in j["location"]


def test_is_us():
    from finder.main import is_us
    for loc in ["Dallas, TX", "Irving, Texas, United States", "New York, NY, United States", "DE, United States",
                "Tempe, AZ, United States; Columbus, OH", "Atlanta, Georgia, USA", "", "Remote - US"]:
        assert is_us(loc), loc
    for loc in ["Shanghai, Shanghai Municipality, China", "Metro Manila, National Capital Region, P", "Indonesia",
                "Warsaw, Mazovia, Poland", "Taipei, Taiwan, Taiwan", "Stockholm, Stockholm County, Sweden",
                "London", ", Finland", "Virtual, BR", "Seoul The Executive Centre", "Copenhagen, Capital Region, Denmark"]:
        assert not is_us(loc), loc
