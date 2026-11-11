"""Step 6 – foreign ownership observations and the ownership classification (Thailand).

Sources, in order of preference for FO at 31/12/2025 (user decision 2026-11-07: public sources now, licensed later):
  1. LICENSED  data/manual/fo_licensed.csv – a licensed extract (Bloomberg / SETSMART) at 31/12/2025, when the team has it
  2. MANUAL    data/manual/ownership_manual.csv – issuers listed abroad / special cases, read from their own filings
  3. REPORT    the One Report 2025 table of shareholders by nationality (foreign shares / Thai + foreign shares);
               taken only when both rows parse and their share counts add up (else listed for review)
  4. FACTSHEET SET factsheet "Foreign Shareholders" (as of the crawl date, Nov 2026)
FO is registered foreign shareholding; NVDR holdings are not added (user decision 2026-11-07) but kept: NVDR_Pct,
FO_Plus_NVDR (factsheet foreign + NVDR on the same date) and NVDR_Sensitive (FO <= 50 < FO + NVDR).
A factsheet value "-" is missing, not 0: the foreign limit then bounds FO (FO_Bound "<= limit").
Outputs: data/ownership_observations.csv, data/fo_report_proposals.csv, data/companies_step2.csv
"""
import re
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

import pymupdf

from common import read_csv, write_csv
from config import DATA, FO_AS_OF, FO_BORDERLINE_UPPER, FO_THRESHOLD, ROOT, SEC_DOWNLOAD

HEAD = re.compile(r"(?i)(shareholding structure by nationality|shareholders? by nationality|distribution of shareholders by nationality"
                  r"|การกระจายการถือหุ้นตามสัญชาติ|ผู้ถือหุ้นแยกตามสัญชาติ|การถือหุ้นแยกตามสัญชาติ|สัดส่วนการถือหุ้นของผู้ถือหุ้นไทยและต่างด้าว)")
THAI_LABEL = re.compile(r"(?i)(?<![A-Za-z])Thai(?! NVDR)|สัญชาติไทย|ผู้ถือหุ้นไทย|(?<!ต่าง)ไทย")
FOREIGN_LABEL = re.compile(r"(?i)foreign|non-thai|ต่างด้าว|ต่างชาติ|ต่างประเทศ")
STOP_LABEL = re.compile(r"(?i)\btotal\b|รวม|free float|การกระจายการถือหุ้นตามอัตราส่วน")
SHARES = re.compile(r"\d{1,3}(?:,\d{3})+")
SHARE_PCT = re.compile(r"(\d{1,3}(?:,\d{3})+)\s+(?=\d{1,3}\.\d{1,4}(?![\d,])|[-–](?:\s|$))")
TH_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
EN_MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]


def row_shares(text: str) -> int | None:
    """Share count of one table row: the row total when one number is the sum of the others, else the sum.
    A share count is followed by its percentage (holder counts such as "43,920" are followed by a share count)."""
    n = [int(x.replace(",", "")) for x in SHARE_PCT.findall(text)] or \
        [int(x.replace(",", "")) for x in SHARES.findall(text) if int(x.replace(",", "")) >= 1000]
    if not n:
        return None
    m = max(n)
    return m if len(n) > 1 and abs(sum(n) - 2 * m) <= 2 else sum(n)


def as_of(text: str) -> str:
    m = re.search(r"(?i)as of\s+(\d{1,2})\s+([a-z]+)\s+(\d{4})|as of\s+([a-z]+)\s+(\d{1,2}),?\s+(\d{4})|ณ วันที่\s*(\d{1,2})\s*(\S+?)\s*(\d{4})", text)
    try:
        if m and m.group(1):
            return date(int(m.group(3)), EN_MONTHS.index(m.group(2).lower()) + 1, int(m.group(1))).isoformat()
        if m and m.group(4):
            return date(int(m.group(6)), EN_MONTHS.index(m.group(4).lower()) + 1, int(m.group(5))).isoformat()
        if m and m.group(7):
            y = int(m.group(9))
            return date(y - 543 if y > 2400 else y, TH_MONTHS.index(m.group(8)) + 1, int(m.group(7))).isoformat()
    except ValueError:
        pass
    return ""


def report_fo(path: Path) -> dict | None:
    doc = pymupdf.open(path)
    for i, page in enumerate(doc, 1):
        text = re.sub(r"\s+", " ", page.get_text())
        for m in HEAD.finditer(text):
            if re.search(r"(?i)employee|พนักงาน|แรงงาน", text[max(0, m.start() - 80):m.end() + 60]):
                continue
            win = text[m.start():m.start() + 900]
            th, fo = THAI_LABEL.search(win, m.end() - m.start()), FOREIGN_LABEL.search(win, m.end() - m.start())
            if not th or not fo:
                continue
            def seg(label):  # from this row label to the next row label
                nxt = [x.start() for x in (THAI_LABEL.search(win, label.end()), FOREIGN_LABEL.search(win, label.end()),
                                           STOP_LABEL.search(win, label.end())) if x]
                return win[label.start():min(nxt) if nxt else len(win)]
            t_seg, f_seg = seg(th), seg(fo)
            t_sh, f_sh = row_shares(t_seg), row_shares(f_seg)
            if f_sh is None and re.search(r"(^|\s)[-–](\s|$)", f_seg):
                f_sh = 0  # foreign row printed as "-"
            if not t_sh or f_sh is None:
                continue
            fo_pct = 100 * f_sh / (t_sh + f_sh)
            printed = [float(x) for x in re.findall(r"(?<![\d,.])\d{1,3}\.\d{1,4}(?![\d,])", f_seg)]
            check = "AUTO" if any(abs(fo_pct - x) <= 0.05 for x in printed + [sum(printed)]) else "CHECK"
            return {"Page": i, "Thai_Shares": t_sh, "Foreign_Shares": f_sh, "FO_Pct": round(fo_pct, 4),
                    "Printed_Pct": "; ".join(map(str, printed)), "Check": check, "As_Of": as_of(win), "Snippet": win[:500]}
    return None


HOLDERS_HEAD = re.compile(r"(?i)list of major shareholders|top\s*10\s*(major\s*)?shareholders|10 major shareholders|major shareholders"
                          r"|รายชื่อผู้ถือหุ้นรายใหญ่|ผู้ถือหุ้นรายใหญ่\s*10")
HOLDER_ROW = re.compile(r"(?<![\d,.])(\d{1,2})[.)]?\s+([^\d][^\n]{2,120}?)\s+(\d{1,3}(?:,\d{3})+)\s+(\d{1,3}\.\d{1,4})")
FOREIGN_MARK = re.compile(r"(?i)\bpte\b|\bgmbh\b|\bag\b|\binc\b|\bcorporation\b|\bcorp\b|\bn\.?v\b|\bb\.?v\b|\bs\.a\b|\bplc\b(?!.*public)"
                          r"|bank,? ltd|holdings? limited|\(singapore\)|\(hong kong\)|japan|singapore|hong kong|malaysia|korea|"
                          r"taiwan|china|netherlands|\bsdn\b|\bbhd\b|kabushiki|kaisha|co\., ltd\.\s*\(japan\)")
THAI_MARK = re.compile(r"(?i)thai nvdr|\(thailand\)|thailand|public company limited|social security|vayupak|fund\b")
HEADER_ROW = re.compile(r"(?i)shareholders|as follows|\bas (of|at)\b|^(january|february|march|april|may|june|july|august|september"
                        r"|october|november|december) \d{4}")  # a table heading read as the first holder row


def major_holders(path: Path) -> tuple[int, list[tuple[str, float]]]:
    """(page, [(holder, pct)]) of the first major-shareholder table (rank, name, shares, %); a reading aid for review."""
    for i, page in enumerate(pymupdf.open(path), 1):
        text = re.sub(r"\s+", " ", page.get_text())
        for m in HOLDERS_HEAD.finditer(text):
            win = text[m.end():m.end() + 2500]
            rows = [(r.group(2).strip(" -•"), float(r.group(4))) for r in HOLDER_ROW.finditer(win)]
            if len(rows) >= 3 and all(p <= 100 for _, p in rows):
                return i, rows[:15]
    return 0, []


def num(s: str) -> float | None:
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def main():
    uni = read_csv(DATA / "universe.csv")
    fs = {r["Ticker_Local"]: r for r in read_csv(DATA / "factsheet.csv")} if (DATA / "factsheet.csv").exists() else {}
    docs = read_csv(DATA / "docs.csv") if (DATA / "docs.csv").exists() else []
    lic = {r["Ticker_Local"]: r for r in read_csv(DATA / "manual" / "fo_licensed.csv")} if (DATA / "manual" / "fo_licensed.csv").exists() else {}
    man = {r["Ticker_Local"]: r for r in read_csv(DATA / "manual" / "ownership_manual.csv")} if (DATA / "manual" / "ownership_manual.csv").exists() else {}
    review = {r["Ticker_Local"]: r for r in read_csv(DATA / "manual" / "fo_report_review.csv")} if (DATA / "manual" / "fo_report_review.csv").exists() else {}
    # hand review of flagged companies (KEEP_FACTSHEET / USE_FILING …) – shown in the workbook, does not change the figure
    fo_rev = {r["Ticker_Local"]: r for r in read_csv(DATA / "manual" / "fo_review.csv")} if (DATA / "manual" / "fo_review.csv").exists() else {}
    main_docs = {}
    for d in docs:
        if d["Status"] == "OK" and d["Member_Role"] in ("MAIN", "E_FORM"):
            main_docs.setdefault(d["Ticker_Local"], []).append(d)
    obs, props, out, holders = [], [], [], []
    for u in uni:
        t = u["Ticker_Local"]
        f = fs.get(t, {})
        if f.get("Foreign_Shareholders_Raw"):
            obs.append({"Ticker_Local": t, "Source_Type": "FACTSHEET", "FO_Pct": f["Foreign_Shareholders_Pct"],
                        "FO_Raw": f["Foreign_Shareholders_Raw"], "As_Of": f["Foreign_Shareholders_As_Of"],
                        "Foreign_Limit_Pct": f.get("Foreign_Limit_Pct", ""), "NVDR_Pct": f.get("NVDR_Shareholders_Pct", ""),
                        "Source": "SET factsheet (Foreign Shareholders, Foreign Limit, NVDR Shareholders)", "Source_URL": f.get("URL_en", ""),
                        "Page": "", "Status": "OK" if f["Foreign_Shareholders_Pct"] else "MISSING (" + f["Foreign_Shareholders_Raw"] + ")"})
        for d in main_docs.get(t, [])[:2]:
            r = report_fo(ROOT / d["Local_File"])
            if r:
                rv = review.get(t, {})
                status = rv.get("Decision") or r["Check"]  # CHECK rows wait for data/manual/fo_report_review.csv
                props.append({"Ticker_Local": t, "Local_File": d["Local_File"], **r, "Decision": status})
                if status in ("AUTO", "ACCEPT"):
                    obs.append({"Ticker_Local": t, "Source_Type": "REPORT", "FO_Pct": rv.get("FO_Pct") or r["FO_Pct"],
                                "FO_Raw": f"foreign {r['Foreign_Shares']:,} / Thai {r['Thai_Shares']:,} shares",
                                "As_Of": rv.get("As_Of") or r["As_Of"], "Source": "Form 56-1 One Report 2025 – shareholders by nationality",
                                "Source_URL": SEC_DOWNLOAD.format(path=d["Report_Path"]), "Local_File": d["Local_File"],
                                "Page": r["Page"], "Status": "OK"})
                break
        for d in sorted(main_docs.get(t, []), key=lambda d: d["Member_Role"] != "E_FORM")[:2]:
            pg, rows = major_holders(ROOT / d["Local_File"])
            if rows:
                for k, (name, pct) in enumerate(rows, 1):
                    holders.append({"Ticker_Local": t, "Rank": k, "Holder": name, "Pct": pct,
                                    "Foreign_Mark": int(bool(FOREIGN_MARK.search(name)) and not THAI_MARK.search(name)
                                                        and not HEADER_ROW.search(name)),
                                    "Local_File": d["Local_File"], "Page": pg})
                break
        for src, rows in (("LICENSED", lic), ("MANUAL", man)):
            if t in rows:
                m = rows[t]
                obs.append({"Ticker_Local": t, "Source_Type": src, "FO_Pct": m.get("FO_Pct", ""), "FO_Raw": m.get("FO_Raw", ""),
                            "FO_Bound": m.get("FO_Bound", ""), "As_Of": m.get("FO_As_Of_Date", FO_AS_OF), "Source": m.get("Source", ""),
                            "Source_URL": m.get("Source_URL", ""), "Page": m.get("Page", ""), "FO_Method": m.get("FO_Method", ""),
                            "Status": "OK"})
        # choose
        mine = [o for o in obs if o["Ticker_Local"] == t and o["Status"] == "OK"]
        # a report table without a printed date stays an observation only (its date would be a guess)
        pick = next((o for src in ("LICENSED", "MANUAL", "REPORT", "FACTSHEET") for o in mine
                     if o["Source_Type"] == src and (src != "REPORT" or o["As_Of"])), None)
        fo = num(pick["FO_Pct"]) if pick else None
        limit, nvdr, fs_fo = num(f.get("Foreign_Limit_Pct")), num(f.get("NVDR_Shareholders_Pct")), num(f.get("Foreign_Shareholders_Pct"))
        bound = (pick or {}).get("FO_Bound", "")
        if fo is None and not bound and limit is not None and limit <= FO_THRESHOLD and f.get("Foreign_Shareholders_Raw"):
            bound = f"<= {limit:g}"  # factsheet shows "-": no figure, but the legal foreign limit caps it
        if fo is not None:
            otype = "FOREIGN_MAJORITY" if fo > FO_THRESHOLD else "LOCAL"
        elif bound:
            op, x = bound.split()
            otype = "FOREIGN_MAJORITY" if op == ">=" and float(x) > FO_THRESHOLD else ("LOCAL" if op == "<=" and float(x) <= FO_THRESHOLD else "REVIEW")
        else:
            otype = "REVIEW"
        if u["Security_Class"] == "FUND":
            otype = ""
        gap = (date.fromisoformat(pick["As_Of"]) - date.fromisoformat(FO_AS_OF)).days if pick and pick.get("As_Of") else ""
        flags = []
        if fo is not None and 40 <= fo <= 60:
            flags.append("FO_NEAR_THRESHOLD")
        if limit is not None and limit > FO_THRESHOLD:
            flags.append("LIMIT_ABOVE_50")
        rep = next((o for o in mine if o["Source_Type"] == "REPORT"), None)
        if rep and fs_fo is not None and abs(num(rep["FO_Pct"]) - fs_fo) > 15:
            flags.append("REPORT_VS_FACTSHEET_GAP")
        if fs_fo is not None and limit is not None and limit - fs_fo <= 1.0 and limit <= FO_THRESHOLD:
            flags.append("AT_FOREIGN_LIMIT")  # the foreign register is full: strategic holders with a waiver are not in it
        big = [h for h in holders if h["Ticker_Local"] == t and h["Foreign_Mark"] and h["Pct"] >= 20]
        if big and (fo is None or fo <= FO_THRESHOLD):
            flags.append("FOREIGN_MAJOR_HOLDER")
        out.append({**u, "Foreign_Ownership_Pct": "" if fo is None else round(fo, 4), "FO_Bound": bound,
                    "FO_As_Of_Date": pick["As_Of"] if pick else "", "FO_Date_Gap_Days": gap, "Ownership_Type": otype,
                    "FO_Method": (pick or {}).get("FO_Method") or (pick["Source_Type"] if pick else ("LIMIT_BOUND" if bound else "")),
                    "FO_Source": pick["Source"] if pick else ("SET factsheet (Foreign Limit)" if bound else ""),
                    "FO_Source_URL": (pick or {}).get("Source_URL", "") or f.get("URL_en", ""), "FO_Page": (pick or {}).get("Page", ""),
                    "Foreign_Limit_Pct": "" if limit is None else limit, "NVDR_Pct": "" if nvdr is None else nvdr,
                    "FO_Plus_NVDR": "" if fs_fo is None or nvdr is None else round(fs_fo + nvdr, 2),
                    "NVDR_Sensitive": int(fs_fo is not None and nvdr is not None and fs_fo <= FO_THRESHOLD < fs_fo + nvdr),
                    "FO_Review_Flags": "; ".join(flags),
                    "FO_Review_Decision": fo_rev.get(t, {}).get("Decision", "") or ("SOURCE_MANUAL" if t in man else ""),
                    "FO_Review_Basis": fo_rev.get(t, {}).get("Basis", ""),
                    "Manager_Search": 1 if u["In_Scope"] == "1" else 0,
                    "Manager_Search_Reason": "ALL_IN_SCOPE" if u["In_Scope"] == "1" else "FUND",
                    "Borderline": int(fo is not None and FO_THRESHOLD < fo <= FO_BORDERLINE_UPPER)})
    write_csv(DATA / "ownership_observations.csv", obs, list(dict.fromkeys(k for o in obs for k in o)))
    write_csv(DATA / "fo_report_proposals.csv", props, ["Ticker_Local", "Local_File", "Page", "Thai_Shares", "Foreign_Shares",
                                                         "FO_Pct", "Printed_Pct", "Check", "As_Of", "Decision", "Snippet"])
    write_csv(DATA / "companies_step2.csv", out, list(out[0].keys()))
    write_csv(DATA / "major_holders.csv", holders, ["Ticker_Local", "Rank", "Holder", "Pct", "Foreign_Mark", "Local_File", "Page"])
    from collections import Counter
    print(dict(Counter(o["Ownership_Type"] for o in out)), "| FO from", dict(Counter(o["FO_Method"] for o in out)),
          "| report tables", len(props), "| flags", dict(Counter(f for o in out for f in o["FO_Review_Flags"].split("; ") if f)))


if __name__ == "__main__":
    main()
