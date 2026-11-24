"""Email Josh when new, relevant internships appear.

Reads data/new_today.json written by main.py. Sends nothing (and exits 0)
if there is nothing new or if email isn't configured.

Environment variables (set as GitHub Actions secrets):
    SMTP_USER   e.g. yourname@gmail.com
    SMTP_PASS   a Gmail *app password* (not your normal password)
    ALERT_TO    where to send alerts (defaults to SMTP_USER)
    SMTP_HOST   optional, default smtp.gmail.com
    SMTP_PORT   optional, default 465
    DASHBOARD_URL optional link included in the email
"""
from __future__ import annotations

import html
import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_TODAY = ROOT / "data" / "new_today.json"

ALERT_STATUSES = {"Eligible", "Unclear"}
QUIET_TRACKS = {"Non-finance"}


def pick(jobs: list[dict]) -> list[dict]:
    keep = [j for j in jobs if j.get("eligibility") in ALERT_STATUSES
            and j.get("track") not in QUIET_TRACKS and j.get("us", True)]
    order = {"Eligible": 0, "Unclear": 1}
    return sorted(keep, key=lambda j: (order.get(j["eligibility"], 9), j["company"]))


def build(jobs: list[dict], dashboard: str = "") -> tuple[str, str, str]:
    n_el = sum(1 for j in jobs if j["eligibility"] == "Eligible")
    subject = f"{len(jobs)} new internship{'s' if len(jobs) != 1 else ''} ({n_el} eligible)"
    lines, rows = [], []
    for j in jobs:
        dl = f" | deadline {j['deadline']}" if j.get("deadline") else ""
        lines.append(f"[{j['eligibility']}] {j['company']} - {j['title']} ({j.get('location','')}){dl}\n"
                     f"   {j['reason']}\n   {j['url']}\n")
        color = "#1a7f37" if j["eligibility"] == "Eligible" else "#9a6700"
        rows.append(
            f"<tr><td style='padding:6px 8px;color:{color};font-weight:600'>{html.escape(j['eligibility'])}</td>"
            f"<td style='padding:6px 8px'><b>{html.escape(j['company'])}</b><br>"
            f"<a href='{html.escape(j['url'])}'>{html.escape(j['title'])}</a><br>"
            f"<span style='color:#555'>{html.escape(j.get('location',''))} &middot; {html.escape(j.get('track',''))}"
            f"{' &middot; deadline ' + html.escape(j['deadline']) if j.get('deadline') else ''}</span><br>"
            f"<span style='color:#777;font-size:12px'>{html.escape(j['reason'])}</span></td></tr>")
    footer = (f"\nDashboard: {dashboard}\n" if dashboard else "")
    footer += "\nProcess: apply first, then message a contact at that firm within 24 hours."
    text = "New internships found today:\n\n" + "\n".join(lines) + footer
    html_body = (
        "<div style='font-family:Arial,sans-serif;font-size:14px'>"
        f"<p>New internships found today:</p><table>{''.join(rows)}</table>"
        + (f"<p><a href='{html.escape(dashboard)}'>Open the dashboard</a></p>" if dashboard else "")
        + "<p style='color:#555'>Process: apply first, then message a contact at that firm within 24 hours.</p></div>")
    return subject, text, html_body


def send(subject: str, text: str, html_body: str) -> None:
    user, pw = os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS")
    to = os.environ.get("ALERT_TO") or user
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL(host, port, timeout=30) as s:
        s.login(user, pw)
        s.sendmail(user, [a.strip() for a in to.split(",")], msg.as_string())


def main() -> int:
    if not NEW_TODAY.exists():
        print("No new_today.json; nothing to send.")
        return 0
    jobs = pick(json.loads(NEW_TODAY.read_text()))
    if not jobs:
        print("Nothing new worth emailing today.")
        return 0
    if not (os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS")):
        print(f"{len(jobs)} new postings, but email isn't set up (SMTP_USER/SMTP_PASS missing).")
        return 0
    subject, text, html_body = build(jobs, os.environ.get("DASHBOARD_URL", ""))
    send(subject, text, html_body)
    print(f"Emailed {len(jobs)} postings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
