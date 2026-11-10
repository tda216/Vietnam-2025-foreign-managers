"""Logged-in session for malaysiastock.biz (copies of Bursa annual-report PDFs).

The login (two lines: user, password) is read from malaysia/.malaysiastock_login, which is
git-ignored. Never print or log the password.

    from ms_session import login, search_announcements
    s = login()
    rows = search_announcements(s, "1155", category="3")   # 3 = Annual Report
"""
import html, re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
LOGIN_FILE = ROOT / ".malaysiastock_login"
BASE = "https://www.malaysiastock.biz"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def hidden_fields(page):
    return {k: html.unescape(v) for k, v in
            re.findall(r'<input type="hidden" name="(__[A-Z]+)" id="[^"]*" value="([^"]*)"', page)}


def login():
    user, pwd = [x.strip() for x in LOGIN_FILE.read_text(encoding="utf-8").splitlines()[:2]]
    s = requests.Session(); s.headers["User-Agent"] = UA
    page = s.get(f"{BASE}/Login.aspx", timeout=60).text
    form = hidden_fields(page)
    form.update({"ctl00$MainContent$User_Login$tbUserName": user,
                 "ctl00$MainContent$User_Login$tbPassword": pwd,
                 "ctl00$MainContent$User_Login$btnLogin": "Login"})
    r = s.post(f"{BASE}/Login.aspx", data=form, timeout=60)
    ok = "Login required to unlock" not in s.get(f"{BASE}/Bursa-Announcement.aspx", timeout=60).text
    if not ok:
        raise RuntimeError(f"malaysiastock.biz login failed (HTTP {r.status_code}, landed on {r.url})")
    return s


def search_announcements(s, code, category="3"):
    """Return the result page of the announcement search for one stock code and category."""
    url = f"{BASE}/Bursa-Announcement.aspx"
    form = hidden_fields(s.get(url, timeout=60).text)
    form.update({"ctl00$MainContent2$ddlCompany": code, "ctl00$MainContent2$ddlCategory": category,
                 "ctl00$MainContent2$btnSearch.x": "10", "ctl00$MainContent2$btnSearch.y": "10"})
    return s.post(url, data=form, timeout=90).text
