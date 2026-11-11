"""Step 9 – proposals for a person's nationality from the profile pages of the company's own One Report.

Many One Reports print, in the director / executive profiles (attachment 1), a line such as "Nationality: Malaysian",
"Age 59 Years / Malaysian" or a table with a Nationality column ("Head of … 51 years Thai"); Thai reports print
"สัญชาติ …". For two kinds of people this step looks for such a statement in the window that follows the person's name
and ends before the next person's honorific:
  NO_RECORD   "Thai nationality: No" people whose country is still UNKNOWN  -> the country
  CANDIDATE   executives listed without the nationality field (open candidates) -> foreign or Thai
Proposals are a reading aid: each one is checked by a person before it goes to data/manual/country_records.csv or
candidate_decisions.csv.
Output: data/country_proposals.csv
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

import pymupdf

from common import read_csv, write_csv
from config import DATA, NATIONALITY_EN, ROOT

NEXT_PERSON = re.compile(r"(?<!^)\b(Mr|Mrs|Ms|Miss|Dr)\.?\s+[A-Z]|(?<!^)(นาย|นางสาว|นาง)\s*[฀-๿]")
PATTERNS = [
    ("LABEL", re.compile(r"(?i)nationality\s*[:：]?\s*([A-Za-z]+(?:\s*\(Taiwan\))?)")),
    ("AGE_SLASH", re.compile(r"(?i)\d{2}\s*(?:years?(?:\s*old)?)?\s*/\s*([A-Za-z]+)")),
    ("AGE_THEN", re.compile(r"(?i)\b\d{2}\s*years?\s+(Thai|[A-Z][a-z]+(?:an|ese|ish|ch|ian|ean|i))\b")),
    ("LABEL_TH", re.compile(r"สัญชาติ\s*[:：]?\s*([฀-๿]+)")),
]


def tokens(name: str) -> list[str]:
    name = re.sub(r"\(.*?\)|\[.*?\]|\*", " ", name)
    name = re.sub(r"(?i)^\s*(mr|mrs|ms|miss|dr|ph\.d)\.?\s+|^\s*(นาย|นางสาว|นาง)\s*", "", name.strip())
    return sorted((w for w in re.split(r"[\s,\-]+", name) if len(w) >= 3), key=len, reverse=True)


def main():
    recs = [r for r in read_csv(DATA / "records_auto.csv") if r["Evidence_Type"] == "ONE_REPORT_FIELD" and r["Nationality"] == "UNKNOWN"]
    cands = [c for c in read_csv(DATA / "candidates.csv") if c["Origin"] == "ONE_REPORT_NO_FIELD"]
    targets = defaultdict(dict)
    for r in recs:
        targets[r["Ticker_Local"]][r["Manager_Name"]] = ("NO_RECORD", r["Name_Raw"])
    for c in cands:
        targets[c["Ticker_Local"]].setdefault(c["Name_Clean"] or c["Name"], ("CANDIDATE", c["Name"]))
    docs = defaultdict(list)
    for d in read_csv(DATA / "docs.csv"):
        if d["Status"] == "OK":
            docs[d["Ticker_Local"]].append(d["Local_File"])
    out = []
    for t, people in sorted(targets.items()):
        pages = [(f, i, re.sub(r"\s+", " ", p.get_text())) for f in docs[t] for i, p in enumerate(pymupdf.open(ROOT / f), 1)]
        for name, (kind, raw) in people.items():
            toks = tokens(raw)
            found = None
            for f, i, x in pages:
                for m in re.finditer(re.escape(toks[0]), x, flags=re.I) if toks else []:
                    win = x[m.start():m.start() + 700]
                    if len(toks) > 1 and not re.search(re.escape(toks[1]), x[max(0, m.start() - 60):m.start() + 80], flags=re.I):
                        continue  # the other name part must be next to it
                    nxt = NEXT_PERSON.search(win, 40)
                    win = win[:nxt.start()] if nxt else win
                    if re.search(r"(?i)thai nationality|สัญชาติไทย\s*:", win):
                        continue  # the template row itself, not a profile
                    for pat, rx in PATTERNS:
                        v = rx.search(win)
                        if v and NATIONALITY_EN.get(v.group(1).strip().lower()):
                            found = {"Pattern": pat, "Value_Raw": v.group(1).strip(), "Nationality": NATIONALITY_EN[v.group(1).strip().lower()],
                                     "Local_File": f, "Page": i, "Snippet": win[:500]}
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                out.append({"Ticker_Local": t, "Name": name, "Name_Raw": raw, "Target": kind, **found})
    write_csv(DATA / "country_proposals.csv", out, ["Ticker_Local", "Name", "Name_Raw", "Target", "Pattern", "Value_Raw",
                                                   "Nationality", "Local_File", "Page", "Snippet"])
    from collections import Counter
    print("targets", sum(len(v) for v in targets.values()), "| proposals", len(out), dict(Counter((o["Target"], o["Nationality"] == "Thailand") for o in out)))


if __name__ == "__main__":
    main()
