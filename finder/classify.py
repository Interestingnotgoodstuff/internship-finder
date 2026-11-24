"""Decide whether a posting is relevant and whether Josh (class of May 2028) can apply.

Everything here is plain rules on the title and description, so it can be
tuned by editing the lists below. Every decision comes with a short reason
that is shown on the dashboard.
"""
from __future__ import annotations

import re
from datetime import date

# ---------------------------------------------------------------- settings
GRAD_YEAR = 2028          # Josh graduates May 2028
SUMMER_YEAR = 2027        # the internship summer he is recruiting for

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
MONTHS.update({"sept": 9, "spring": 5, "summer": 7, "fall": 12, "autumn": 12, "winter": 12})

INTERN_TITLE = re.compile(
    r"\b(intern|internship|summer|co-?op|off[- ]cycle|placement|externship)\b", re.I)

# Title words that mean the role is not a finance seat. These are hidden by
# default on the dashboard (track "Non-finance") rather than deleted.
# STRONG words win even if the title also mentions a finance word
# ("Ratings Multimedia Intern"); WEAK words only count when no finance word
# is present ("Technology Investment Banking" stays Investment Banking).
NON_FINANCE_STRONG = re.compile(
    r"\b(software|engineer(ing)?|developer|data scien\w*|machine learning|cyber\w*|"
    r"multimedia|graphic|human resources|marketing|communications|ux|nurs\w*|pharmac\w*)\b", re.I)
NON_FINANCE_WEAK = re.compile(
    r"\b(technology|tech|data|legal|design|facilities|operations|it|ai|sales|product)\b", re.I)

TRACKS = [
    ("Ratings", r"\bratings?\b|rating agency|credit ratings"),
    ("Private Credit / Lending", r"private credit|direct lending|private debt|leveraged (finance|lending)|lev ?fin|credit portfolio|private financing"),
    ("Commercial / Corporate Banking & Credit", r"corporate banking|commercial bank|commercial credit|credit analyst|credit risk|underwrit|middle market|enterprise credit|\bcredit\b"),
    ("Investment Banking", r"investment banking|\bm&a\b|mergers|restructuring|capital markets|advisory|\bkbcm\b|\bib\b"),
    ("Equity Research", r"equity research|research analyst|investment research"),
    ("Private Equity / Investing", r"private equity|investment analyst|portfolio|asset management|investing|secondaries|infrastructure"),
    ("Markets / Trading", r"sales (and|&) trading|trading|global markets|commodit"),
]

CITY_PATTERNS = [
    ("New York", r"new york|nyc|manhattan|\bny\b"),
    ("Chicago", r"chicago|\bil\b"),
    ("Dallas", r"dallas|fort worth|irving|plano|richardson"),
    ("Houston", r"houston"),
    ("Charlotte", r"charlotte"),
]

DEADLINE_RE = re.compile(
    r"(deadline|apply by|applications? (are |is )?due|applications? (will )?close|closing date|"
    r"submit (your )?application by)[^.\n]{0,60}?"
    r"(?P<date>(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\.?\s+\d{1,2}(st|nd|rd|th)?,?\s*(20\d\d)?|"
    r"\d{1,2}/\d{1,2}/(20)?\d\d)", re.I)

# Phrases that introduce a graduation date. Deliberately narrow so that
# "undergraduate degree" or "graduate students" don't pull in internship dates.
GRAD_CONTEXT = re.compile(
    r"(\bgraduating\b|\bgraduation\b|\bgraduate (in|by|between|from|no later than)\b|"
    r"\bclass of\b|degree (completion|conferral)|expected to (complete|finish|graduate)|"
    r"complet(e|ion of) (your|their) (degree|studies))", re.I)
MONTH_YEAR = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|spring|summer|fall|autumn|winter)?"
    r"\.?\s*,?\s*(20\d\d)\b", re.I)


def is_internship_title(title: str) -> bool:
    return bool(INTERN_TITLE.search(title or ""))


def track_of(title: str, text: str) -> str:
    t = (title or "").lower()
    if NON_FINANCE_STRONG.search(t):
        return "Non-finance"
    for name, pat in TRACKS:          # title first: it is the strongest signal
        if re.search(pat, t, re.I):
            return name
    if NON_FINANCE_WEAK.search(t):
        return "Non-finance"
    body = (text or "")[:3000].lower()
    for name, pat in TRACKS:
        if re.search(pat, body, re.I):
            return name
    return "Other finance"


def city_of(location: str) -> str:
    loc = (location or "").lower()
    for name, pat in CITY_PATTERNS:
        if re.search(pat, loc):
            return name
    return "Other"


def find_deadline(text: str) -> str:
    m = DEADLINE_RE.search(text or "")
    return m.group("date").strip() if m else ""


def grad_dates(text: str) -> list[tuple[int, int]]:
    """(year, month) pairs that appear near graduation language (month 0 = unknown)."""
    found = []
    for m in GRAD_CONTEXT.finditer(text or ""):
        # Stay inside the sentence that mentions graduation.
        start = max(text.rfind(". ", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
        start = max(start, m.start() - 80)
        stops = [i for i in (text.find(". ", m.end()), text.find("\n", m.end())) if i != -1]
        end = min(stops + [m.end() + 140])
        window = text[start:end]
        for mm in MONTH_YEAR.finditer(window):
            year = int(mm.group(2))
            word = (mm.group(1) or "").lower().rstrip(".")
            if word == "summer" and year == SUMMER_YEAR:
                continue                      # that's the internship itself
            month = MONTHS.get(word, 0)
            if 2024 <= year <= 2032 and (year, month) not in found:
                found.append((year, month))
    return found


TARGET = GRAD_YEAR * 12 + 5          # May 2028 as a month number


def _mn(year: int, month: int, end: bool = False) -> int:
    if month == 0:                   # year only: treat as the whole year
        month = 12 if end else 1
    return year * 12 + month


def window_verdict(dates: list[tuple[int, int]]) -> tuple[str, str] | None:
    """Compare a graduation window (or single date) with May 2028."""
    if not dates:
        return None
    shown = ", ".join(f"{m:02d}/{y}" if m else str(y) for y, m in dates[:4])
    if len(dates) == 1:
        y, m = dates[0]
        if (y == GRAD_YEAR and m in (0, 4, 5, 6)) or abs(_mn(y, m) - TARGET) <= 1:
            return "Eligible", f"Graduation date fits May {GRAD_YEAR} ({shown})"
        if (y, m) == (GRAD_YEAR - 1, 12):
            return "Unclear", f"Mentions December {GRAD_YEAR - 1} graduation; check if May {GRAD_YEAR} is included"
        if _mn(y, m, end=True) < TARGET:
            return "Not eligible", f"Wants graduates by {shown}"
        return "Not eligible", f"Wants graduates in {shown}"
    lo = min(_mn(y, m) for y, m in dates)
    hi = max(_mn(y, m, end=True) for y, m in dates)
    if lo <= TARGET <= hi:
        return "Eligible", f"Graduation window includes May {GRAD_YEAR} ({shown})"
    if lo > TARGET:
        return "Not eligible", f"Graduation window is after May {GRAD_YEAR} ({shown})"
    return "Not eligible", f"Graduation window ends before May {GRAD_YEAR} ({shown})"


def eligibility(title: str, text: str) -> tuple[str, str]:
    """Return (status, reason). status is Eligible, Not eligible, or Unclear."""
    t = (title or "").lower()
    body = (text or "").lower()
    both = f"{t}\n{body}"

    # Hard exclusions from the title.
    if re.search(r"summer associate|\bmba\b", t):
        return "Not eligible", "MBA / summer associate role"
    if re.search(rf"class of {GRAD_YEAR}\b", both):
        return "Eligible", f"Says class of {GRAD_YEAR}"
    if re.search(rf"\b{SUMMER_YEAR + 1}\b", t) and re.search(r"summer|intern", t):
        return "Not eligible", f"Summer {SUMMER_YEAR + 1} program (for the class of {GRAD_YEAR + 1})"
    if re.search(rf"class of {GRAD_YEAR - 1}\b", t):
        return "Not eligible", f"Class of {GRAD_YEAR - 1} (full-time for earlier grads)"
    if re.search(rf"class of {GRAD_YEAR}\b", both):
        return "Eligible", f"Says class of {GRAD_YEAR}"

    verdict = window_verdict(grad_dates(text or ""))
    if verdict:
        return verdict

    summer_2027 = re.search(rf"(summer|internship|intern)[^\n]{{0,40}}\b{SUMMER_YEAR}\b|"
                            rf"\b{SUMMER_YEAR}\b[^\n]{{0,40}}(summer|internship|intern)", both)
    if re.search(r"penultimate|junior year|rising senior|third[- ]year|entering (your|their) (final|senior) year", body):
        return "Eligible", "Asks for penultimate-year / junior students"
    if re.search(rf"summer {SUMMER_YEAR + 1}|{SUMMER_YEAR + 1} summer", both) and not summer_2027:
        return "Not eligible", f"Summer {SUMMER_YEAR + 1} program"
    if summer_2027:
        return "Unclear", f"Summer {SUMMER_YEAR} role, no graduation dates listed (likely OK)"
    return "Unclear", "No year or graduation info found; check the posting"


def classify(job: dict) -> dict:
    text = job.get("description", "")
    status, reason = eligibility(job.get("title", ""), text)
    job.update({
        "eligibility": status,
        "reason": reason,
        "track": track_of(job.get("title", ""), text),
        "city": city_of(job.get("location", "")),
        "deadline": find_deadline(text),
    })
    return job


def today() -> str:
    return date.today().isoformat()
