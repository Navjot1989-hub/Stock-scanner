#!/usr/bin/env python3
"""Scheduled order-intelligence scan + email digest.

Run by GitHub Actions on alternate days at 11:00 IST. Aggregates recent order
wins from the live feeds (NSE/BSE/Moneycontrol/Mint/Bloomberg/Google) and emails
a ranked HTML digest. No LLM, no paid API.

Email is sent via Gmail SMTP when SMTP_USER / SMTP_PASS / EMAIL_TO are set as
repo secrets; otherwise it just prints the digest. Set SCAN_QUERY to change the
default command.
"""

import os
import sys
import smtplib
import datetime
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(__file__))
from app.scanner import scan  # noqa: E402


def build_html(hits, today):
    head = (
        '<div style="font-family:Arial,sans-serif;color:#111;max-width:820px">'
        f'<h2>StockScan India — Order Intelligence ({today})</h2>'
        '<p style="font-size:13px;color:#555">Recent order / contract wins from '
        'NSE, BSE, Moneycontrol, Mint, Bloomberg &amp; Google News. '
        'Research only — not investment advice.</p>'
        '<table cellpadding="6" cellspacing="0" border="1" '
        'style="border-collapse:collapse;font-size:13px">'
        '<tr style="background:#0f3d5e;color:#fff"><th>#</th><th>Company</th>'
        '<th>Ticker</th><th>Order</th><th>Cap bracket</th><th>Sector</th><th>Source</th></tr>'
    )
    rows = ""
    for i, h in enumerate(hits, 1):
        rows += (
            f"<tr><td>{i}</td><td>{h.company}</td><td>{h.ticker or '-'}</td>"
            f"<td>{h.order_size or '-'}</td><td>{h.market_cap_bracket or '-'}</td>"
            f"<td>{h.client_sector or '-'}</td>"
            f"<td><a href='{h.source_url}'>{h.source_title}</a></td></tr>"
        )
    return head + rows + "</table></div>"


def send_email(subject, html):
    user, pw, to = (os.environ.get(k) for k in ("SMTP_USER", "SMTP_PASS", "EMAIL_TO"))
    if not (user and pw and to):
        print("Email not configured (SMTP_USER/SMTP_PASS/EMAIL_TO) — printing digest:\n")
        print(html)
        return
    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.sendmail(user, [a.strip() for a in to.split(",")], msg.as_string())
    print(f"Email sent to {to}")


def main():
    today = datetime.date.today().isoformat()
    query = os.environ.get("SCAN_QUERY", "recent large order wins")
    hits = scan(query=query, limit=40)
    print(f"Found {len(hits)} order hits for query: {query!r}")
    subject = f"StockScan India ({today}): {len(hits)} order wins"
    if hits:
        subject = f"StockScan India ({today}): {hits[0].company} +{len(hits)-1} more"
    send_email(subject, build_html(hits, today))


if __name__ == "__main__":
    main()
