"""Step 2a – find and download the exchanges' foreign-ownership notices for FO_AS_OF.

HOSE and HNX publish a daily notice "Số liệu quản lý sở hữu của nhà đầu tư nước ngoài"
(data from VSDC) with the figures as an attachment. hnx.vn is not reachable from this
machine, so the notices are located through CafeF's republication feed and the
attachments are downloaded from CafeF's media CDN. The notice page URL is kept as the source.

Outputs: data/fo_notices.csv (all notices seen around the as-of date),
         data/fo_files.csv (downloaded attachments), files in raw/ownership/<EXCHANGE>/.
"""
import re
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import fetch, fetch_text, now_iso, strip_accents, write_csv
from config import DATA, FO_AS_OF, RAW_OWNERSHIP

FEED = ("https://cafef.vn/du-lieu/Ajax/Events_RelatedNews_New.aspx?symbol={sym}"
        "&floorID=0&configID=0&PageIndex={page}&PageSize=30&Type=2")
AS_OF = date.fromisoformat(FO_AS_OF)
STOP_BEFORE = date(AS_OF.year, AS_OF.month, 15)   # page back until the feed is older than this
MAX_PAGES = 400


def notice_date(title: str):
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", title)
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def scan_feed(sym: str) -> list[dict]:
    found = []
    for page in range(1, MAX_PAGES + 1):
        html, _ = fetch_text(FEED.format(sym=sym, page=page))
        items = BeautifulSoup(html, "lxml").select("li")
        if not items:
            break
        oldest = None
        for li in items:
            a, t = li.select_one("a"), li.select_one(".timeTitle")
            if not a or not t:
                continue
            published = datetime.strptime(t.get_text(strip=True), "%d/%m/%Y %H:%M")
            oldest = published.date() if oldest is None else min(oldest, published.date())
            title = a.get("title") or a.get_text(strip=True)
            folded = strip_accents(title)
            if "so lieu" in folded and "so huu" in folded and "nuoc ngoai" in folded:
                d = notice_date(title)
                if d and STOP_BEFORE <= d <= date(AS_OF.year + 1, 1, 15):
                    found.append({
                        "Exchange": sym, "Notice_Date": d.isoformat(), "Published_At": published.isoformat(),
                        "Title": title, "Notice_URL": urljoin("https://cafef.vn", a["href"].split("?")[0]),
                    })
        print(f"{sym} page {page}: oldest {oldest}, matches so far {len(found)}")
        if oldest and oldest < STOP_BEFORE:
            break
    return found


def attachments(notice_url: str) -> list[tuple[str, str]]:
    html, _ = fetch_text(notice_url)
    out = []
    for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
        h = a["href"]
        if "/download/" in h or re.search(r"\.(pdf|xlsx?|zip)(\?|$)", h, re.I):
            out.append((a.get_text(strip=True), h))
    return out


def main():
    notices = []
    for sym in ("HNX", "HOSE"):
        notices += scan_feed(sym)
    notices.sort(key=lambda x: (x["Exchange"], x["Notice_Date"], x["Notice_URL"]))
    write_csv(DATA / "fo_notices.csv", notices, ["Exchange", "Notice_Date", "Published_At", "Title", "Notice_URL"])

    # Use the notice dated exactly FO_AS_OF; otherwise the latest one before it.
    files = []
    for ex in ("HNX", "HOSE"):
        cands = [n for n in notices if n["Exchange"] == ex and n["Notice_Date"] <= FO_AS_OF]
        if not cands:
            print(f"!! no {ex} notice on/before {FO_AS_OF}")
            continue
        best = max(n["Notice_Date"] for n in cands)
        for n in (x for x in cands if x["Notice_Date"] == best):
            for label, href in attachments(n["Notice_URL"]):
                body, meta = fetch(href)
                name = label or unquote(Path(urlparse(href).path).name)
                dest = RAW_OWNERSHIP / ex / re.sub(r"[^\w.\- ]", "_", name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(body)
                files.append({
                    "Exchange": ex, "Notice_Date": best, "Notice_URL": n["Notice_URL"], "Attachment_Label": label,
                    "Attachment_URL": href, "Local_File": str(dest.relative_to(RAW_OWNERSHIP.parent.parent)),
                    "SHA256": meta["sha256"], "Bytes": meta["bytes"], "Downloaded_At": now_iso(),
                })
                print(f"{ex} {best}: {label} -> {dest} ({meta['bytes']} B)")
    write_csv(DATA / "fo_files.csv", files, ["Exchange", "Notice_Date", "Notice_URL", "Attachment_Label",
                                            "Attachment_URL", "Local_File", "SHA256", "Bytes", "Downloaded_At"])


if __name__ == "__main__":
    main()
