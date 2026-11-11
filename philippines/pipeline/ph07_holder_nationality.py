"""Step ph07: assign a nationality to the direct stockholders of each company and compute the foreign-ownership (FO) bounds.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph07_holder_nationality.py

Inputs  philippines/data/top100_form.csv, top100_holders.csv   (31 Dec 2025 Top 100 list, ph03/ph04)
        philippines/raw/pse/<symbol>/*/att_*.pdf               (FY2025 17-A, untrusted input; text only)
Outputs philippines/data/holder_nationality.csv   one row per direct holder >= 1% (non-PCD) with the nationality found
        philippines/data/fo_bounds.csv            one row per company: FO_Lower, FO_Upper, basis counts, review class

Method (a SCREENING aid; every classification that matters is checked on the page):
  PCD Nominee Non-Filipino  -> foreign shares counted in the lower bound (Top 100 form, 31 Dec 2025).
  Direct holder >= 1%       -> its name is searched in the company's 17-A text; the nationality word found right next to the
                               name (Filipino / a demonym / a country) gives FILIPINO, FOREIGN:<country> or UNKNOWN.
  FO_Lower = PCD non-Filipino + holders found FOREIGN.
  FO_Upper = FO_Lower + holders UNKNOWN + all shares not covered by the Top 100 rows and not lodged with PCD (the tail).
Dates: Top 100 is as of 31 Dec 2025; 17-A nationality labels are as of the 17-A date (usually March-April 2026). Not the same date:
this is recorded in the output (Nationality_Date_Basis). An unlabelled holder is never assumed Filipino.
"""
import csv
import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "philippines" / "data"
RAW = ROOT / "philippines" / "raw" / "pse"

spec = importlib.util.spec_from_file_location("ph05", Path(__file__).resolve().parent / "ph05_scan_17a_nationality.py")
ph05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph05)

COUNTRY_WORDS = {  # country / region names accepted in a 'citizenship' column
    "singapore": "Singapore", "japan": "Japan", "china": "China", "hong kong": "Hong Kong", "hongkong": "Hong Kong",
    "taiwan": "Taiwan", "malaysia": "Malaysia", "korea": "South Korea", "india": "India", "usa": "United States",
    "u.s.a.": "United States", "united states": "United States", "uk": "United Kingdom", "united kingdom": "United Kingdom",
    "australia": "Australia", "canada": "Canada", "germany": "Germany", "france": "France", "switzerland": "Switzerland",
    "netherlands": "Netherlands", "thailand": "Thailand", "indonesia": "Indonesia", "bvi": "British Virgin Islands",
    "british virgin islands": "British Virgin Islands", "cayman": "Cayman Islands", "bermuda": "Bermuda", "panama": "Panama",
    "samoa": "Samoa", "labuan": "Malaysia", "vietnam": "Vietnam",
}
DEM_TO_COUNTRY = {k.lower(): v for k, v in ph05.DEMONYMS.items()}
LABEL_RE = re.compile(r"\b(Filipino|Philippines|Non-?Filipino|Foreign|Alien|" + ph05.DEM_ALT + r"|" +
                      "|".join(re.escape(c) for c in sorted(COUNTRY_WORDS, key=len, reverse=True)) + r")\b", re.I)
# Brokers and custodian banks: their accounts are PDTC participants, i.e. shares already lodged and already counted in the
# 'PCD Nominee Filipino / Non-Filipino' totals. They are listed apart (Class PDTC_PARTICIPANT_ASSUMED) and not counted twice.
PARTICIPANT_RE = re.compile(r"(?i)SECURIT|STOCKBROKER|BROKERAGE|CLIENTS|CITIBANK|HONGKONG AND SHANGHAI|HSBC|DEUTSCHE BANK|"
                            r"STANDARD CHARTERED|CUSTOD|\bA/C\b|PDTC|PCD|NOMINEE")
CORP_STOP = re.compile(r"(?i)\b(inc|incorporated|corp|corporation|co|company|ltd|limited|holdings?|the|of|and|&|ph|phils?|philippines?)\b\.?")


def norm(s):
    s = re.sub(r"[^A-Za-z0-9 ]", " ", s.upper())
    return re.sub(r"\s+", " ", CORP_STOP.sub(" ", s)).strip()


def pdf_texts(symbol):
    """Flatten text of all FY2025 17-A PDFs of a company (2026 filings first). Returns [(file, page, text, normalized text)]"""
    out = []
    for mp in sorted((RAW / symbol).glob("*/meta.json")):
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m["form"] != "17-1" or "2026" not in m["announced"]:
            continue
        for f in m["files"]:
            n = f.get("saved_as", "")
            if not n.lower().endswith(".pdf"):
                continue
            try:
                doc = fitz.open(mp.parent / n)
            except Exception:
                continue
            for i, p in enumerate(doc, 1):
                t = p.get_text()
                if len(t) > 80:
                    flat = re.sub(r"\s+", " ", t)
                    out.append((n, i, flat, norm(flat)))
    return out


def label_after(name, texts):
    """Find the nationality word next to a holder name in the 17-A text. Returns (label, file, page, snippet)."""
    key = norm(name)
    toks = key.split()
    if len(toks) < 1 or len(key) < 4:
        return None
    probe = " ".join(toks[:3])
    best = None
    for n, pno, t, nt in texts:
        if probe not in nt:
            continue
        # locate by the first two significant tokens in the original text. Case-insensitive search on the text itself
        # (str.upper() can change the length of some characters and shift positions) and whole words only (a one-word
        # name such as 'CISCO' must not match inside 'Francisco'). Fixed 2026-11-06.
        first = re.search(r"\b" + (r"[^A-Z0-9]+(?:\w+[^A-Z0-9]+){0,2}".join(re.escape(x) for x in toks[:2]) if len(toks) >= 2
                                   else re.escape(toks[0])) + r"\b", t, re.I)
        if not first:
            continue
        win = t[first.start(): first.start() + 330]
        # Row-level rule (strict): the label must sit between the holder name and that row's own share count
        # (a comma-formatted number within 60 characters after the label), and must not belong to a
        # "PCD Nominee ... (Non-Filipino)" line. Labels found in narrative text or in the next row are ignored.
        num = re.search(r"\d{1,3}(?:,\d{3})+", win[first.end() - first.start():])
        if num:
            row_end = first.end() - first.start() + num.start()
            seg = win[first.end() - first.start(): row_end]
            for m in LABEL_RE.finditer(seg):
                before = seg[max(0, m.start() - 30): m.start()].upper()
                if "PCD" in before or "NOMINEE" in before:
                    continue
                if len(seg) - m.end() > 60:
                    continue
                return (m.group(1), n, pno, win[:260])
        if best is None:
            best = (None, n, pno, win[:260])
    return best


RANK_RE = re.compile(r"^\s*(\d{1,3})[.)]?\s")
SUMMARY_RE = re.compile(r"(?i)number of|previous|lodged|certificated|outstanding|issued|listed|treasury|^filipino$|^non-filipino$|"
                        r"^total|sub-?total|grand total")
INT_TOKEN = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{4,}\b")


def pick_pct(row_text, outstanding, pct_rep):
    """Percent of outstanding for one parsed row. The share count is the integer whose percent matches the reported
    percent; without a reported percent, the first comma-formatted integer (account numbers are usually unformatted)."""
    ints = [(t, int(t.replace(",", ""))) for t in INT_TOKEN.findall(row_text)]
    ints = [(t, v) for t, v in ints if v >= 1000]
    if pct_rep is not None:
        for t, v in ints:
            if abs(100 * v / outstanding - pct_rep) <= max(0.02, 0.05 * pct_rep):
                return 100 * v / outstanding
        return pct_rep  # trust the issuer's own percentage
    for t, v in ints:
        if "," in t:
            return 100 * v / outstanding
    return None


def clean_rows(rows, outstanding):
    """Main stockholder table only. Returns ([(name, pct)], basis)."""
    def rep(h):
        try:
            return float(h["Pct_Reported"]) if h["Pct_Reported"] != "" else None
        except ValueError:
            return None
    rows = [h for h in rows if not SUMMARY_RE.search(h["Holder_Name"])]
    ranked = [h for h in rows if RANK_RE.match(h["Row_Text"]) and rep(h) is not None]
    if len(ranked) >= 5:
        basis, use, last = "RANKED_TABLE", [], 0
        for h in ranked:  # stop at the second table (ranks restart at 1)
            k = int(RANK_RE.match(h["Row_Text"]).group(1))
            if k < last and k <= 2:
                break
            last = max(last, k)
            use.append(h)
    elif sum(rep(h) is not None for h in rows) >= 5:
        basis, use = "PCT_ROWS", [h for h in rows if rep(h) is not None]
    else:
        basis, use = "ALL_ROWS", rows
    out, seen = [], set()
    for h in use:
        p = pick_pct(h["Row_Text"], outstanding, rep(h))
        if p is None:
            continue
        key = (h["Holder_Name"].upper(), round(p, 3))
        if key in seen:
            continue
        seen.add(key)
        out.append((h["Holder_Name"], p))
    return out, basis


def to_class(label):
    if label is None:
        return "UNKNOWN", ""
    l = label.lower()
    if l in ("filipino", "philippines"):
        return "FILIPINO", "Philippines"
    if l in ("non-filipino", "nonfilipino", "foreign", "alien"):
        return "FOREIGN", "UNKNOWN"
    if l in DEM_TO_COUNTRY:
        return "FOREIGN", DEM_TO_COUNTRY[l]
    if l in COUNTRY_WORDS:
        return "FOREIGN", COUNTRY_WORDS[l]
    return "UNKNOWN", ""


def main():
    form = {r["Symbol"]: r for r in csv.DictReader(open(DATA / "top100_form.csv", encoding="utf-8"))}
    holders = defaultdict(list)
    for r in csv.DictReader(open(DATA / "top100_holders.csv", encoding="utf-8")):
        holders[r["Symbol"]].append(r)
    hold_rows, bounds = [], []
    manual = {}  # (Symbol, HOLDER NAME) -> latest reviewed row
    mpath = DATA / "manual" / "holder_nationality_review.csv"
    if mpath.exists():
        for r in csv.DictReader(open(mpath, encoding="utf-8")):
            manual[(r["Symbol"], r["Holder_Name"].strip().upper())] = r
    for sym, f in sorted(form.items()):
        try:
            out, nf, fil = float(f["Outstanding_Shares"]), float(f["PCD_NonFilipino"]), float(f["PCD_Filipino"])
        except (ValueError, TypeError):
            bounds.append({"Symbol": sym, "Review_Class": "FORM_INCOMPLETE"})
            continue
        lb_pcd = 100 * nf / out
        pcd_total = 100 * (nf + fil) / out
        clean, basis = clean_rows(holders[sym], out)
        direct = [(n, p) for n, p in clean if not PARTICIPANT_RE.search(n)]
        for n, p in clean:
            if PARTICIPANT_RE.search(n) and "PCD" not in n.upper() and p >= 1:
                hold_rows.append({"Symbol": sym, "Holder_Name": n, "Pct_Of_Outstanding": round(p, 4),
                                  "Class": "PDTC_PARTICIPANT_ASSUMED", "Country": "", "Label_Found": "", "File": "", "Page": "",
                                  "Snippet": "broker/custodian name: assumed inside PCD lodged totals (not counted twice)",
                                  "Nationality_Date_Basis": ""})
        named = sorted({(n, p) for n, p in direct if p >= 1}, key=lambda x: -x[1])
        texts = pdf_texts(sym)
        foreign = fil_pct = 0.0
        unknown = sum(p for _, p in named[40:])  # holders beyond the first 40 are not looked up: counted as unknown
        for name, pct in named[:40]:
            mr = manual.get((sym, name.strip().upper()))
            if mr is not None:  # reviewed evidence wins over the automatic label
                cls = {"1": "FOREIGN", "0": "FILIPINO"}.get(mr["Is_Foreign"], "UNKNOWN")
                ctry = mr["Country"]
                hold_rows.append({"Symbol": sym, "Holder_Name": name, "Pct_Of_Outstanding": round(pct, 4), "Class": cls,
                                  "Country": ctry, "Label_Found": mr["Nationality_Raw"], "File": mr["Local_File"], "Page": mr["Page"],
                                  "Snippet": mr["Evidence_Quote"][:260], "Nationality_Date_Basis": "MANUAL_REVIEW " + mr["Reviewed_On"]})
            else:
                hit = label_after(name, texts) if texts else None
                cls, ctry = to_class(hit[0] if hit else None)
                hold_rows.append({"Symbol": sym, "Holder_Name": name, "Pct_Of_Outstanding": round(pct, 4), "Class": cls, "Country": ctry,
                                  "Label_Found": hit[0] if hit and hit[0] else "", "File": hit[1] if hit else "",
                                  "Page": hit[2] if hit else "", "Snippet": hit[3] if hit else "",
                                  "Nationality_Date_Basis": "AUTO: 17-A date (Mar-Apr 2026); shares as of 31 Dec 2025"})
            if cls == "FOREIGN":
                foreign += pct
            elif cls == "UNKNOWN":
                unknown += pct
            else:
                fil_pct += pct
        listed_direct = sum(p for _, p in named)
        tail = max(0.0, 100 - pcd_total - listed_direct)
        lower = lb_pcd + foreign
        upper = min(100.0, lower + unknown + tail)
        over = pcd_total + listed_direct > 102  # parsed rows add up to more than the company: do not classify automatically
        cls = ("PARSE_CHECK" if over else "FOREIGN_MAJORITY_CERTAIN" if lower > 50 else "LOCAL_CERTAIN" if upper <= 50
               else "NEEDS_REVIEW")
        bounds.append({"Symbol": sym, "PCD_NonFilipino_Pct": round(lb_pcd, 3), "Foreign_Direct_Pct": round(foreign, 3),
                       "Unknown_Direct_Pct": round(unknown, 3), "Filipino_Direct_Pct": round(fil_pct, 3), "Tail_Pct": round(tail, 3),
                       "FO_Lower": round(lower, 3), "FO_Upper": round(upper, 3), "Has_17A_Text": "Y" if texts else "N",
                       "Row_Basis": basis, "Parsed_Total_Pct": round(pcd_total + listed_direct, 2), "Review_Class": cls})
    for name, rows in (("holder_nationality.csv", hold_rows), ("fo_bounds.csv", bounds)):
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(DATA / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    from collections import Counter
    print("companies:", len(bounds), Counter(b["Review_Class"] for b in bounds))
    print("holder rows:", len(hold_rows), Counter(h["Class"] for h in hold_rows))


if __name__ == "__main__":
    main()
