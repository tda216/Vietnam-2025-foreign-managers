"""Vietstock Finance document lists (company page tab "Tải tài liệu"), via POST /data/getdocument.

The endpoint returns 20 documents per page, filtered by document type and report year, and needs the
anti-forgery token from the company's document page (same session cookies). Every response page is kept
verbatim under raw/web/vietstock_docs/ and reused on later runs.
"""
import json
import re
from datetime import datetime, timezone

from common import now_iso, session, throttle
from config import RAW

BASE = "https://finance.vietstock.vn"
CACHE = RAW / "web" / "vietstock_docs"
DOC_TYPES = {1: "FINANCIAL_STATEMENT", 2: "ANNUAL_REPORT", 3: "PROSPECTUS", 4: "AGM_RESOLUTION", 5: "AGM_DOCUMENTS",
             6: "OTHER", 8: "FS_EXPLANATION", 9: "GOVERNANCE_REPORT", 10: "LIQUIDITY_RATIO", 23: "BOARD_RESOLUTION",
             31: "CAPITAL_ADEQUACY"}
_token = None


def _get_token() -> str:
    global _token
    if _token is None:
        throttle("finance.vietstock.vn")
        r = session().get(f"{BASE}/FPT/tai-tai-lieu.htm", timeout=60)
        r.raise_for_status()
        _token = re.search(r'name=__RequestVerificationToken type=hidden value=([^ >]+)', r.text).group(1)
    return _token


def _page(code: str, doc_type: int, year: int, page: int) -> list[dict]:
    path = CACHE / code / f"t{doc_type}_y{year}_p{page}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["data"]
    throttle("finance.vietstock.vn")
    r = session().post(f"{BASE}/data/getdocument",
                       data={"code": code, "page": page, "type": doc_type, "year": year,
                             "__RequestVerificationToken": _get_token()},
                       headers={"X-Requested-With": "XMLHttpRequest"}, timeout=60)
    r.raise_for_status()
    data = r.json() if r.text.strip() else []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"code": code, "type": doc_type, "year": year, "page": page,
                                "fetched_at": now_iso(), "data": data}, ensure_ascii=False), encoding="utf-8")
    return data


def list_documents(code: str, doc_type: int, year: int) -> list[dict]:
    """All documents of one type and report year for a ticker, as returned by Vietstock (all pages)."""
    out, page = [], 1
    while True:
        rows = _page(code, doc_type, year, page)
        out.extend(rows)
        total = rows[0]["TotalRow"] if rows else 0
        if not rows or len(out) >= total or page >= 50:
            return out
        page += 1


def parse_ms_date(s: str) -> str:
    """'/Date(1793066192833)/' -> ISO UTC timestamp (Vietstock upload time)."""
    m = re.search(r"\d+", s or "")
    return datetime.fromtimestamp(int(m.group(0)) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if m else ""
