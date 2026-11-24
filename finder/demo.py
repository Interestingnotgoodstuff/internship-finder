"""Sample postings so the dashboard can be previewed without internet access.

These are made-up examples shaped like real postings. The dashboard shows a
"DEMO DATA" banner whenever they are in use.
"""
from __future__ import annotations

SAMPLES = [
    ("Raymond James", "2027 Investment Banking Summer Analyst Private Credit New York, NY", "New York, NY",
     "Summer 2027 internship. Candidates should be graduating between December 2027 and June 2028."),
    ("BMO", "Credit Analyst Internship - Chicago, IL (Summer 2027)", "Chicago, IL",
     "10-week program. Expected graduation date: May 2028. Applications close January 15, 2027."),
    ("TD Securities", "2027 Summer Analyst - Global Markets Credit (New York City)", "New York, NY",
     "Open to students in their penultimate year of undergraduate study."),
    ("Barclays", "International Corporate Banking Analyst Summer Internship Program 2027 New York City", "New York, NY",
     "Our summer 2027 internship runs 10 weeks."),
    ("S&P Global", "Ratings Analytical Intern - Americas", "New York, NY",
     "Current undergraduate students in their penultimate year of study. 10-week summer program starting June 2027."),
    ("Wintrust", "Wintrust 2027 Summer Internship: Commercial Banking", "Chicago, IL",
     "Must be graduating in Spring 2028."),
    ("PGIM", "PGIM: 2027 Private Credit, Summer Investment Analyst Program", "Chicago, IL",
     "Graduating between December 2027 and May 2028."),
    ("Piper Sandler", "2027 Campus Recruiting - Investment Banking Summer Associate - Houston", "Houston, TX",
     "For first-year MBA students."),
    ("Houlihan Lokey", "Financial Analyst (Class of 2027), GP Advisory - New York", "New York, NY",
     "Full-time analyst role for the Class of 2027."),
    ("Jefferies", "2028 Investment Banking Summer Analyst Program, Generalist", "New York, NY",
     "For students graduating December 2028 to June 2029."),
    ("CIBC", "2027 Summer Intern Equity Research (Buy Side) Chicago", "Chicago, IL",
     "Summer internship in our equity research group."),
    ("Castleton Commodities", "Commodities Trading Summer Analyst Internship Program (Summer 2027 Internship)", "Houston, TX",
     "Rising seniors preferred."),
    ("TD Securities", "2027 Summer Analyst - Software Engineering Rotational Program (New York City)", "New York, NY",
     "Software engineering rotation for summer 2027."),
    ("Barclays", "Capital Markets Summer Internship Programme 2027 London", "London, UK",
     "Penultimate year students."),
]


def demo_results(companies):
    by_name = {c["name"]: c for c in companies}
    grouped: dict[str, list] = {}
    for i, (co, title, loc, desc) in enumerate(SAMPLES):
        c = by_name.get(co, {"name": co, "category": ""})
        grouped.setdefault(co, []).append({
            "id": f"demo:{i}", "company": co, "category": c.get("category", ""),
            "title": title, "location": loc, "url": "https://example.com/demo-posting",
            "posted": "Posted 3 Days Ago", "description": desc, "source": "Demo",
        })
    for co, jobs in grouped.items():
        yield by_name.get(co, {"name": co, "ats": "demo"}), jobs, None
    yield {"name": "Example Broken Board", "ats": "workday"}, [], "HTTPError: 404 (example of a board that needs fixing)"
