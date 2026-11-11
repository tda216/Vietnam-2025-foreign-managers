"""Step 3 – SET factsheet page per stock: foreign shareholding, foreign limit, NVDR holding, One Report 2025 file.

Usage: python -I thailand/pipeline/03_factsheet.py [TICKER ...]   (default: all; a ticker list writes nothing, prints rows)
       python -I thailand/pipeline/03_factsheet.py update TICKER ...   (re-reads those stocks, replaces their rows in factsheet.csv)

Bloomberg drops "&" and "-" from SET symbols (S&J -> SNJ, SE-ED -> SEED, M-CHAI -> MCHAI) and keeps old lines
(BANPU -> BANPUU): data/manual/set_symbol_manual.csv maps Ticker_Local to the SET symbol used in the factsheet URL.
The public factsheet page (robots.txt allows it) is fetched once per stock and language and kept in the web cache;
the English page links the English One Report (…E.zip) when there is one, otherwise the Thai page is read for the Thai
file (…T.zip). Requests are throttled (config.MIN_SECONDS_BETWEEN_REQUESTS) with an honest User-Agent; a 403 or 429
stops the run (no retries under another identity). SET's API and weblink.set.or.th are never called.
SET's terms allow personal, non-commercial use; the figures are kept as observations with their "as of" date.
Output: data/factsheet.csv
"""
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

import requests

from common import fetch_text, read_csv, write_csv
from config import DATA, SET_FACTSHEET

LINK_RE = re.compile(r"https?://weblink\.set\.or\.th/dat/(f56/[A-Za-z0-9_\-]+\.zip)")
FIELD_RE = {
    "Foreign_Shareholders": re.compile(r"Foreign Shareholders\s*([\d.,\-]+)\s*%?\s*\(as of\s*([^)]+)\)", re.I),
    "Foreign_Limit": re.compile(r"Foreign Limit\s*([\d.,\-]+)\s*%?\s*\(as of\s*([^)]+)\)", re.I),
    "NVDR_Shareholders": re.compile(r"NVDR Shareholders\s*([\d.,\-]+)\s*%?\s*\(as of\s*([^)]+)\)", re.I),
}


def tickers() -> list[str]:
    """Every SET company, plus the hand-classified funds (their factsheet confirms the security type)."""
    manual = {m["Ticker_Local"] for m in read_csv(DATA / "manual" / "security_class_manual.csv")}
    return [u["Ticker_Local"] for u in read_csv(DATA / "universe.csv")
            if u["Security_Class"] == "COMPANY_TH" or u["Ticker_Local"] in manual]


_SYMBOLS: dict[str, str] | None = None


def set_symbol(ticker: str) -> str:
    """SET symbol of a Bloomberg Ticker_Local (hand list for the codes Bloomberg spells differently)."""
    global _SYMBOLS
    if _SYMBOLS is None:
        p = DATA / "manual" / "set_symbol_manual.csv"
        _SYMBOLS = {r["Ticker_Local"]: r["SET_Symbol"] for r in read_csv(p)} if p.exists() else {}
    return _SYMBOLS.get(ticker, ticker)


def factsheet_url(ticker: str, lang: str) -> str:
    return SET_FACTSHEET.format(lang=lang, ticker=quote(set_symbol(ticker), safe=""))


def get(ticker: str, lang: str) -> tuple[str, dict] | tuple[None, dict]:
    url = factsheet_url(ticker, lang)
    try:
        return fetch_text(url)
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 0
        if code in (403, 429):
            raise SystemExit(f"{code} from {url} – stopping (no workaround)")
        return None, {"url": url, "status": code}


def visible(html: str) -> str:
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def as_of(s: str) -> str:
    s = s.strip()
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def parse(ticker: str) -> dict:
    row = {"Ticker_Local": ticker}
    for lang in ("en", "th"):
        html, meta = get(ticker, lang)
        row[f"URL_{lang}"], row[f"Status_{lang}"] = meta.get("url", ""), meta.get("status", "")
        row[f"Fetched_{lang}"] = meta.get("fetched_at", "")
        if html is None:
            continue
        if lang == "en":
            text = visible(html)
            m = re.search(r"As of (\d{1,2} \w{3} \d{4})", text)
            row["Page_As_Of"] = as_of(m.group(1)) if m else ""
            for k, rx in FIELD_RE.items():
                m = rx.search(text)
                row[f"{k}_Raw"] = m.group(1) if m else ""
                row[f"{k}_Pct"] = m.group(1).replace(",", "") if m and re.fullmatch(r"[\d.,]+", m.group(1)) else ""
                row[f"{k}_As_Of"] = as_of(m.group(2)) if m else ""
            m = re.search(r"(Annual Report|One Report)\s*(20\d\d)", text)
            row["Report_Label_Year"] = m.group(2) if m else ""
        elif not row.get("Report_Label_Year"):
            m = re.search(r"รายงานประจำปี\s*(25\d\d)", visible(html))  # Buddhist-era year
            row["Report_Label_Year"] = str(int(m.group(1)) - 543) if m else ""
        links = sorted(set(LINK_RE.findall(html)))
        if links and not row.get("Report_Path"):
            row["Report_Path"], row["Report_Lang"] = links[0], links[0][-5]
            break  # English page already links a report: the Thai page is not needed
    return row


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "update":
        new = {t: parse(t) for t in sys.argv[2:]}
        old = read_csv(DATA / "factsheet.csv")
        rows = [new.pop(r["Ticker_Local"], r) for r in old] + list(new.values())
        write_csv(DATA / "factsheet.csv", rows, list(dict.fromkeys(k for r in rows for k in r)))
        for t in sys.argv[2:]:
            r = next(x for x in rows if x["Ticker_Local"] == t)
            print(t, set_symbol(t), r.get("Foreign_Shareholders_Raw"), r.get("Foreign_Limit_Raw"), r.get("Report_Path"))
        return
    if len(sys.argv) > 1:
        for t in sys.argv[1:]:
            print(parse(t))
        return
    rows = []
    for i, t in enumerate(tickers(), 1):
        rows.append(parse(t))
        if i % 50 == 0:
            print(i, "done", flush=True)
    cols = list(dict.fromkeys(k for r in rows for k in r))
    write_csv(DATA / "factsheet.csv", rows, cols)
    print(len(rows), "stocks |", sum(1 for r in rows if r.get("Report_Path")), "with a One Report link |",
          sum(1 for r in rows if r.get("Foreign_Shareholders_Raw")), "with a foreign-shareholder figure")


if __name__ == "__main__":
    main()
