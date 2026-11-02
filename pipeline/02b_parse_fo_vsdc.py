"""Step 2b – parse the VSDC foreign-ownership file (as republished by HOSE/HNX) into observations.

The file is one table per market section. STO = HOSE, STX = HNX, UPX = UPCoM, DEPOX = registered
at VSDC but not trading. GBX/HCX are bonds and are ignored. Columns: issued shares, max foreign ratio (%),
max foreign-permitted qty, qty currently held by foreign investors, remaining room.

Foreign_Ownership_Pct = foreign-held qty / issued qty * 100 (the file has no % column; both raw quantities
are kept so the figure can be re-derived). Each row's PDF page is recorded for the Page column.
Output: data/fo_vsdc_20251231.csv
"""
import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv, write_csv
from config import DATA, FO_AS_OF, ROOT

SECTION_EXCHANGE = {"DEPOX": "DEPOX", "STO": "HOSE", "STX": "HNX", "UPX": "UPCoM"}
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
NUM_RE = re.compile(r"^-?[\d.]+(,\d+)?$")
SECTION_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII)\.\s+([A-Z]+)\s*$")
TOTAL_RE = re.compile(r"^Tổng\s*\(([A-Z]+)\)\s+(.*)$")

FIELDS = ["Exchange_Section", "Exchange", "STT", "Ticker_Local", "ISIN", "Qty_Issued", "Max_Foreign_Ratio_Pct",
          "Qty_Foreign_Permitted", "Qty_Foreign_Held", "Qty_Room_Remaining", "Foreign_Ownership_Pct",
          "FO_As_Of_Date", "Source", "Source_URL", "Local_File", "Page"]


def vn_number(s: str) -> float:
    """'65.000.000' -> 65000000 ; '49,0000000' -> 49.0 ; '-365.852' -> -365852."""
    return float(s.replace(".", "").replace(",", "."))


def visual_lines(page, tol: float = 4.0) -> list[list[str]]:
    """Group a page's words into rows by vertical centre (cells of one row sit at slightly different y)."""
    words = sorted(page.get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines, cur, cur_y = [], [], None
    for x0, y0, x1, y1, w, *_ in words:
        yc = (y0 + y1) / 2
        if cur and abs(yc - cur_y) > tol:
            lines.append(cur)
            cur = []
        cur.append((x0, w))
        cur_y = yc if len(cur) == 1 else (cur_y * (len(cur) - 1) + yc) / len(cur)
    if cur:
        lines.append(cur)
    return [[w for _, w in sorted(line)] for line in lines]


def main():
    files = read_csv(DATA / "fo_files.csv")
    f = files[0]  # HOSE and HNX attachments are byte-identical (same SHA256); one parse covers both
    assert len({x["SHA256"] for x in files}) == 1, "HOSE and HNX files differ – parse each separately"
    pdf_path = ROOT / f["Local_File"]
    source_urls = " | ".join(f"{x['Exchange']}: {x['Notice_URL']}" for x in files)

    doc = pymupdf.open(pdf_path)
    header_text = doc[0].get_text()
    assert "31 tháng 12 năm 2025" in header_text, "unexpected as-of date in file header"

    rows, totals, section = [], {}, None
    for pno, page in enumerate(doc, start=1):
        for toks in visual_lines(page):
            text = " ".join(toks)
            m = SECTION_RE.match(text)
            if m:
                section = m.group(2)
                continue
            m = TOTAL_RE.match(text)
            if m:
                totals[m.group(1)] = [vn_number(t) for t in m.group(2).split()]
                continue
            isin_idx = next((i for i, t in enumerate(toks) if ISIN_RE.match(t)), None)
            if isin_idx is None or section not in SECTION_EXCHANGE:
                continue
            before, after = toks[:isin_idx], toks[isin_idx + 1:]
            if not before or not before[0].isdigit() or len(after) != 5 or not all(NUM_RE.match(t) for t in after):
                print(f"!! unparsed p{pno}: {text}")
                continue
            issued, ratio, permitted, held, room = (vn_number(t) for t in after)
            rows.append({
                "Exchange_Section": section,
                "Exchange": SECTION_EXCHANGE[section],
                "STT": before[0],
                "Ticker_Local": before[1] if len(before) > 1 else "",
                "ISIN": toks[isin_idx],
                "Qty_Issued": int(issued),
                "Max_Foreign_Ratio_Pct": ratio,
                "Qty_Foreign_Permitted": int(permitted),
                "Qty_Foreign_Held": int(held),
                "Qty_Room_Remaining": int(room),
                "Foreign_Ownership_Pct": round(held / issued * 100, 6) if issued else "",
                "FO_As_Of_Date": FO_AS_OF,
                "Source": "VSDC foreign ownership data (FOL 31.12.2025), published by HOSE & HNX",
                "Source_URL": source_urls,
                "Local_File": f["Local_File"],
                "Page": pno,
            })

    # Reconcile each section against its printed total row (issued, permitted, held, room).
    for sec in SECTION_EXCHANGE:
        got = [r for r in rows if r["Exchange_Section"] == sec]
        sums = [sum(r[k] for r in got) for k in ("Qty_Issued", "Qty_Foreign_Permitted", "Qty_Foreign_Held", "Qty_Room_Remaining")]
        exp = totals.get(sec)
        ok = exp is not None and [int(x) for x in exp] == sums
        print(f"{sec:5s} rows={len(got):4d} totals_match={ok}" + ("" if ok else f" parsed={sums} printed={exp}"))

    write_csv(DATA / "fo_vsdc_20251231.csv", rows, FIELDS)
    print("written rows:", len(rows))


if __name__ == "__main__":
    main()
