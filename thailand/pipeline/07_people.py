"""Step 7 – FY2025 people, foreign records, BoardEx cross-check, open candidates (Thailand).

One Report decides who is foreign (user decision 2026-11-07); BoardEx adds the country and managers below the
executive list. Outputs (data/):
  roster.csv            every One Report person with FY2025 status, Role_Group and the matched BoardEx person
  records_auto.csv      foreign people: One Report "Thai nationality: No" (Evidence_Type ONE_REPORT_FIELD), and BoardEx
                        people labelled non-Thai with an FY2025 role who are not in the One Report lists (Evidence BOARDEX)
  source_conflicts.csv  One Report and BoardEx disagree (Yes vs non-Thai label, No vs Thai label)
  candidates.csv        to check by hand: One Report executives without the field whose name looks non-Thai (character
                        trigram model trained on the One Report Yes/No names, Latin and Thai script); BoardEx board/executive
                        roles missing from the report lists; BoardEx non-Thai labels on Thai-looking names
FY2025: a current director or executive appointed after 31/12/2025 and a director who left before 1/1/2025 are not
counted (Include_FY2025 = NO with the reason).
"""
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from rapidfuzz import fuzz

from common import read_csv, write_csv
from config import DATA, SEC_DOWNLOAD

FY_START, FY_END = "2025-01-01", "2025-12-31"
SCREEN_CUT = 0.0     # candidate when the trigram log-odds (non-Thai vs Thai) is above this
MATCH_CUT = 88       # rapidfuzz token_set_ratio for One Report <-> BoardEx names within one company
THAI_LOOKING = -0.5  # a BoardEx non-Thai label on a name scoring below this is checked by hand
# BoardEx people without a nationality label are not opened as candidates (user 2026-11-07: "accurate and fast"):
# below the executive list only BoardEx-labelled non-Thai people are recorded (Evidence_Type BOARDEX).


def norm(s: str) -> str:
    s = re.sub(r"\(.*?\)|\[.*?\]|\*", " ", s or "")
    s = re.sub(r"(?i)\b(mr|mrs|ms|miss|dr|doctor|professor|prof|assoc|asst|assistant|associate|general|gen|lt|pol|adm|air|chief|"
               r"marshal|admiral|captain|major|police|colonel|the|hon|dato|datuk|tan sri|sri|seri|m\.?l|m\.?r)\b\.?", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z฀-๿ ]", " ", s)).strip().lower()


def name_score(a: str, b: str) -> float:
    """Token-set similarity only when the names share >= 2 words (a bare surname must not match a relative)."""
    shared = set(a.split()) & set(b.split())
    return fuzz.token_set_ratio(a, b) if len(shared) >= 2 else fuzz.token_sort_ratio(a, b)


def name_words(name: str) -> list[str]:
    return [w for w in norm(name).split() if len(w) >= 4]


class Screen:
    """Character trigram log-odds: non-Thai vs Thai, trained on labelled names."""
    def __init__(self, thai: list[str], foreign: list[str]):
        self.cT = Counter(g for n in thai for g in self.grams(n))
        self.cF = Counter(g for n in foreign for g in self.grams(n))
        self.nT, self.nF, self.V = sum(self.cT.values()), sum(self.cF.values()), len(set(self.cT) | set(self.cF)) or 1

    @staticmethod
    def grams(name: str) -> list[str]:
        return [w[i:i + 3] for w in (f"^{x}$" for x in norm(name).split()) for i in range(len(w) - 2)]

    def score(self, name: str) -> float:
        g = self.grams(name)
        if not g:
            return 0.0
        return sum(math.log((self.cF[x] + .5) / (self.nF + .5 * self.V)) - math.log((self.cT[x] + .5) / (self.nT + .5 * self.V))
                   for x in g) / len(g)


def bx_variants(p: dict) -> list[str]:
    """Name forms of a BoardEx person. Never the bare surname: with an empty Usual_Name/forename it would score 100
    against every relative with a two-word surname (ALUCON Vrinporn vs Vibool Uer-Anant)."""
    fore = [p[k] for k in ("Forename1", "Forename2", "Forename3", "Forename4") if p[k]]
    v = {p["Director_Name"], " ".join(fore + [p["Surname"]]), f"{p['Surname']} {' '.join(fore)}"}
    if p["Usual_Name"]:
        v.add(f"{p['Usual_Name']} {p['Surname']}")
    if fore:
        v.add(f"{fore[0]} {p['Surname']}")
    return sorted(x for x in v if x.strip())


def main():
    uni = {u["Ticker_Local"]: u for u in read_csv(DATA / "companies_step2.csv")}
    people = read_csv(DATA / "people_onereport.csv")
    stats = {s["Ticker_Local"]: s for s in read_csv(DATA / "report_stats.csv")}
    docs = {(d["Ticker_Local"], d["Local_File"]): d for d in read_csv(DATA / "docs.csv") if d["Status"] == "OK"}
    bxp = {p["Director_ID"]: p for p in read_csv(DATA / "boardex_people.csv")}
    bxr = read_csv(DATA / "boardex_roles.csv")
    roles_t = defaultdict(list)
    for r in bxr:
        roles_t[r["Ticker_Local"]].append(r)

    # FY2025 status and role group of One Report people
    for p in people:
        why = ""
        if p["Section"] in ("BOARD", "EXECUTIVE") and p["Date_Assumed"] > FY_END:
            why = "appointed after 31/12/2025"
        if "(***)" in p["Name_Raw"]:
            why = "marked (***): appointed after the fiscal year end"
        if p["Section"] == "LEFT" and p["Date_Ended"] and p["Date_Ended"] < FY_START:
            why = "left before 1/1/2025"
        p["Include_FY2025"], p["FY_Note"] = ("NO", why) if why else ("YES", "")
        p["Role_Group"] = "Executive" if p["Section"] == "EXECUTIVE" else "Board"

    # trigram screen trained on stated names (both scripts)
    screen = Screen([p["Name_Clean"] for p in people if p["Thai_Nationality"] == "Yes"],
                    [p["Name_Clean"] for p in people if p["Thai_Nationality"] == "No"]
                    + [b["Director_Name"] for b in bxp.values() if b["Nationality"] not in ("", "Thailand")])

    # nationality stated anywhere in the company's One Report lists (an executive who also sits on the board)
    stated, stated_src = {}, {}
    for p in people:
        if p["Thai_Nationality"]:
            stated[(p["Ticker_Local"], norm(p["Name_Clean"]))] = p["Thai_Nationality"]
            if p["Thai_Nationality"] == "No":
                stated_src.setdefault((p["Ticker_Local"], norm(p["Name_Clean"])), p)

    # One Report <-> BoardEx match within the company (Latin names only)
    for p in people:
        p["BoardEx_Director_ID"], p["BoardEx_Nationality"], p["Match_Score"] = "", "", ""
        p["Stated_In_Report"] = stated.get((p["Ticker_Local"], norm(p["Name_Clean"])), "")
        if not re.search(r"[A-Za-z]{2}", p["Name_Clean"]):
            continue
        sc = {did: max(name_score(norm(p["Name_Clean"]), norm(v)) for v in bx_variants(bxp[did]))
              for did in {r["Director_ID"] for r in roles_t.get(p["Ticker_Local"], [])}}
        top = max(sc.values(), default=0)
        tied = sorted((d for d, s in sc.items() if s == top), key=lambda d: (len(d), d))
        # a tie between BoardEx ids (duplicate profiles of one person, e.g. ANI Nichol Yeo) keeps the lowest id, so every
        # run gives the same result; a tie between ids with different BoardEx nationalities is ambiguous -> no match
        if top >= MATCH_CUT and len({bxp[d]["Nationality"] for d in tied}) == 1:
            p["BoardEx_Director_ID"], p["Match_Score"] = tied[0], round(top)
            p["BoardEx_Nationality"] = bxp[tied[0]]["Nationality"]
    # one BoardEx person per report person: two different names in one company matched to the same id (e.g. SIS siblings
    # Lim Hwee Hai / Lim Hwee Noi) -> only the best-scoring name keeps it (a tie keeps none)
    by_id = defaultdict(list)
    for p in people:
        if p["BoardEx_Director_ID"]:
            by_id[(p["Ticker_Local"], p["BoardEx_Director_ID"])].append(p)
    for ps in by_id.values():
        names = {norm(p["Name_Clean"]) for p in ps}
        if len(names) < 2:
            continue
        top = max(p["Match_Score"] for p in ps)
        keep = {norm(p["Name_Clean"]) for p in ps if p["Match_Score"] == top}
        for p in ps:
            if len(keep) > 1 or norm(p["Name_Clean"]) not in keep:
                p["BoardEx_Director_ID"], p["BoardEx_Nationality"], p["Match_Score"] = "", "", ""

    surnames = defaultdict(set)
    for p in people:
        surnames[p["Ticker_Local"]] |= set(name_words(p["Name_Clean"]))
    records, conflicts, cands = [], [], []
    exec_seen = set()
    for p in people:
        t = p["Ticker_Local"]
        d = docs.get((t, p["Local_File"]), {})
        nat_bx = p["BoardEx_Nationality"]
        if p["Thai_Nationality"] == "Yes" and nat_bx not in ("", "Thailand"):
            conflicts.append({"Ticker_Local": t, "Name": p["Name_Raw"], "Page": p["Page"], "One_Report": "Thai nationality: Yes",
                              "BoardEx": nat_bx, "BoardEx_Director_ID": p["BoardEx_Director_ID"], "Default": "Is_Foreign = 0 (One Report)"})
        if p["Thai_Nationality"] == "No" and nat_bx == "Thailand":
            conflicts.append({"Ticker_Local": t, "Name": p["Name_Raw"], "Page": p["Page"], "One_Report": "Thai nationality: No",
                              "BoardEx": nat_bx, "BoardEx_Director_ID": p["BoardEx_Director_ID"], "Default": "Is_Foreign = 1 (One Report)"})
        if p["Include_FY2025"] != "YES":
            continue
        if p["Thai_Nationality"] == "No":
            quote = (f"{p['Name_Raw']} – {p['Position_Raw']} – Thai nationality: No; Residing in Thailand: "
                     f"{p['Residing_In_Thailand'] or 'not stated'}")
            records.append({"Ticker_Local": t, "Manager_Name": p["Name_Clean"], "Name_Raw": p["Name_Raw"],
                            "Raw_Position": p["Position_Raw"], "Role_Group": p["Role_Group"], "Section": p["Section"],
                            "Nationality": nat_bx if nat_bx not in ("", "Thailand") else "UNKNOWN",
                            "Nationality_Raw": "Thai nationality: No", "Is_Foreign": 1,
                            "Country_Evidence_Type": "BOARDEX" if nat_bx not in ("", "Thailand") else "",
                            "Thai_Nationality_Stated": "No", "Residing_In_Thailand": p["Residing_In_Thailand"],
                            "Appointed_Date": p["Date_Assumed"], "Resigned_Date": p["Date_Ended"],
                            "Evidence_Type": "ONE_REPORT_FIELD", "Evidence_Quote": quote,
                            "Source": f"Form 56-1 One Report 2025 ({t})", "Source_URL": d.get("Source_URL", ""),
                            "Local_File": p["Local_File"], "Page": p["Page"],
                            "BoardEx_Director_ID": p["BoardEx_Director_ID"], "BoardEx_Nationality": nat_bx,
                            "Note": "NATIONALITY_CONFLICT: BoardEx says Thai" if nat_bx == "Thailand" else ""})
        elif not p["Thai_Nationality"] and p["Stated_In_Report"] == "No":
            # an executive-list entry without the field whose own director entry says "No": one row per position, the
            # evidence page is the director entry (so the QA check finds the name and "No" there). Some reports print the
            # executive list twice (CPR, TR) -> one row per person x position.
            k_exec = (t, norm(p["Name_Clean"]), norm(p["Position_Raw"]))
            if k_exec in exec_seen:
                continue
            exec_seen.add(k_exec)
            s = stated_src[(t, norm(p["Name_Clean"]))]
            nat = s["BoardEx_Nationality"] or nat_bx
            records.append({"Ticker_Local": t, "Manager_Name": s["Name_Clean"], "Name_Raw": s["Name_Raw"],
                            "Raw_Position": p["Position_Raw"], "Role_Group": p["Role_Group"], "Section": p["Section"],
                            "Nationality": nat if nat not in ("", "Thailand") else "UNKNOWN",
                            "Nationality_Raw": "Thai nationality: No", "Is_Foreign": 1,
                            "Country_Evidence_Type": "BOARDEX" if nat not in ("", "Thailand") else "",
                            "Thai_Nationality_Stated": "No", "Residing_In_Thailand": s["Residing_In_Thailand"],
                            "Appointed_Date": p["Date_Assumed"], "Resigned_Date": p["Date_Ended"],
                            "Evidence_Type": "ONE_REPORT_FIELD",
                            "Evidence_Quote": (f"{s['Name_Raw']} – {s['Position_Raw']} – Thai nationality: No; Residing in Thailand: "
                                               f"{s['Residing_In_Thailand'] or 'not stated'}"),
                            "Source": f"Form 56-1 One Report 2025 ({t})", "Source_URL": d.get("Source_URL", ""),
                            "Local_File": s["Local_File"], "Page": s["Page"],
                            "BoardEx_Director_ID": s["BoardEx_Director_ID"] or p["BoardEx_Director_ID"], "BoardEx_Nationality": nat,
                            "Note": f"position from the executive list p{p['Page']} (no nationality field there); nationality from the "
                                    f"same person's director entry p{s['Page']}"})
        elif not p["Thai_Nationality"] and not p["Stated_In_Report"]:
            if nat_bx not in ("", "Thailand"):
                records.append({"Ticker_Local": t, "Manager_Name": p["Name_Clean"], "Name_Raw": p["Name_Raw"],
                                "Raw_Position": p["Position_Raw"], "Role_Group": p["Role_Group"], "Section": p["Section"],
                                "Nationality": nat_bx, "Nationality_Raw": f"BoardEx: {bxp[p['BoardEx_Director_ID']]['Nationality_Raw']}",
                                "Is_Foreign": 1, "Country_Evidence_Type": "BOARDEX", "Thai_Nationality_Stated": "",
                                "Residing_In_Thailand": "", "Appointed_Date": p["Date_Assumed"], "Resigned_Date": "",
                                "Evidence_Type": "BOARDEX",
                                "Evidence_Quote": f"BoardEx individual {p['BoardEx_Director_ID']}: nationality "
                                                  f"{bxp[p['BoardEx_Director_ID']]['Nationality_Raw']}; One Report lists {p['Name_Raw']} – {p['Position_Raw']} (no nationality field)",
                                "Source": f"BoardEx (individual {p['BoardEx_Director_ID']}); Form 56-1 One Report 2025 ({t})",
                                "Source_URL": d.get("Source_URL", ""), "Local_File": p["Local_File"], "Page": p["Page"],
                                "BoardEx_Director_ID": p["BoardEx_Director_ID"], "BoardEx_Nationality": nat_bx, "Note": ""})
            elif nat_bx != "Thailand" and screen.score(p["Name_Clean"]) > SCREEN_CUT:
                cands.append({"Ticker_Local": t, "Name": p["Name_Raw"], "Name_Clean": p["Name_Clean"], "Origin": "ONE_REPORT_NO_FIELD",
                              "Role_Group": p["Role_Group"], "Raw_Position": p["Position_Raw"], "Page": p["Page"],
                              "Local_File": p["Local_File"], "Score": round(screen.score(p["Name_Clean"]), 2),
                              "BoardEx_Director_ID": p["BoardEx_Director_ID"]})

    # BoardEx people with an FY2025 role who are not in the company's One Report lists
    matched = {(p["Ticker_Local"], p["BoardEx_Director_ID"]) for p in people if p["BoardEx_Director_ID"]}
    by_person = defaultdict(list)
    for r in bxr:
        if r["FY2025_Valid"] == "YES" and (r["Ticker_Local"], r["Director_ID"]) not in matched:
            by_person[(r["Ticker_Local"], r["Director_ID"])].append(r)
    for (t, did), rs in by_person.items():
        b = bxp[did]
        has_report = stats.get(t, {}).get("Status") == "OK"
        for r in rs:
            note = "" if r["Role_Group"] == "Other_Manager" else ("BoardEx board/executive role not found in the One Report lists"
                                                                  if has_report else "company has no parsed One Report")
            shares_surname = any(w in surnames.get(t, set()) for w in name_words(b["Director_Name"]))
            if b["Nationality"] not in ("", "Thailand") and has_report and r["Role_Group"] != "Other_Manager" and shares_surname:
                # One Report decides for directors and executives: a BoardEx board/executive role whose surname occurs in
                # the report's lists is most likely a name variant of a listed person – checked by hand
                cands.append({"Ticker_Local": t, "Name": b["Director_Name"], "Name_Clean": b["Director_Name"],
                              "Origin": "BOARDEX_CORE_NOT_IN_REPORT", "Role_Group": r["Role_Group"], "Raw_Position": r["Role_Name"],
                              "Page": "", "Local_File": "", "Score": "", "BoardEx_Director_ID": did,
                              "BoardEx_Role_Record_ID": r["Role_Record_ID"], "Note": f"BoardEx nationality {b['Nationality_Raw']}; {note}; surname in report"})
            elif b["Nationality"] not in ("", "Thailand") and has_report and r["Role_Group"] == "Board":
                # not in the One Report board lists (complete per the count checks): not counted (One Report decides)
                cands.append({"Ticker_Local": t, "Name": b["Director_Name"], "Name_Clean": b["Director_Name"],
                              "Origin": "BOARDEX_CORE_NOT_IN_REPORT", "Role_Group": r["Role_Group"], "Raw_Position": r["Role_Name"],
                              "Page": "", "Local_File": "", "Score": "", "BoardEx_Director_ID": did,
                              "BoardEx_Role_Record_ID": r["Role_Record_ID"], "Auto_Decision": "NOT_IN_REPORT_BOARD",
                              "Note": f"BoardEx nationality {b['Nationality_Raw']}; not in the One Report board lists – not counted"})
            elif b["Nationality"] not in ("", "Thailand") and screen.score(b["Director_Name"]) < THAI_LOOKING:
                # labelled non-Thai but the name reads as Thai (BoardEx label errors seen): checked by hand
                cands.append({"Ticker_Local": t, "Name": b["Director_Name"], "Name_Clean": b["Director_Name"],
                              "Origin": "BOARDEX_LABEL_CHECK", "Role_Group": r["Role_Group"], "Raw_Position": r["Role_Name"],
                              "Page": "", "Local_File": "", "Score": round(screen.score(b["Director_Name"]), 2),
                              "BoardEx_Director_ID": did, "BoardEx_Role_Record_ID": r["Role_Record_ID"],
                              "Note": f"BoardEx nationality {b['Nationality_Raw']}; name reads as Thai"})
            elif b["Nationality"] not in ("", "Thailand"):
                below = has_report and r["Role_Group"] == "Executive"  # executive team below the report's top-executive list
                records.append({"Ticker_Local": t, "Manager_Name": b["Director_Name"], "Name_Raw": b["Director_Name"],
                                "Raw_Position": r["Role_Name"], "Role_Group": "Other_Manager" if below else r["Role_Group"], "Section": "BOARDEX",
                                "Nationality": b["Nationality"], "Nationality_Raw": f"BoardEx: {b['Nationality_Raw']}", "Is_Foreign": 1,
                                "Country_Evidence_Type": "BOARDEX", "Thai_Nationality_Stated": "", "Residing_In_Thailand": "",
                                "Appointed_Date": r["Date_Start"] if r["Date_Start_Flag"] != "75" else "",
                                "Resigned_Date": r["Date_End"] if r["Date_End"][:4] not in ("9000", "9999") else "",
                                "Evidence_Type": "BOARDEX",
                                "Evidence_Quote": f"BoardEx individual {did} ({b['Director_Name']}): nationality {b['Nationality_Raw']}; "
                                                  f"role record {r['Role_Record_ID']}: {r['Role_Name']} at {r['Company_Name_BoardEx']}, "
                                                  f"{r['Date_Start']} – {r['Date_End']} ({r['Period_Status']})",
                                "Source": f"BoardEx (individual {did}, role record {r['Role_Record_ID']})", "Source_URL": "",
                                "Local_File": "", "Page": "", "BoardEx_Director_ID": did, "BoardEx_Nationality": b["Nationality"],
                                "Note": ("BoardEx executive-team role below the One Report executive list: counted as Other_Manager"
                                         if below else note)})

    # a director in both the current board list and the "left during the year" list with the same position is one
    # person x position: keep the BOARD row, take the end date from the LEFT row
    merged, idx = [], {}
    for r in records:
        k = (r["Ticker_Local"], norm(r["Manager_Name"]), r["Raw_Position"])
        if k in idx and {merged[idx[k]]["Section"], r["Section"]} == {"BOARD", "LEFT"}:
            keep, other = (merged[idx[k]], r) if merged[idx[k]]["Section"] == "BOARD" else (r, merged[idx[k]])
            keep["Resigned_Date"] = keep["Resigned_Date"] or other["Resigned_Date"]
            keep["Note"] = "; ".join(x for x in (keep["Note"], f"also listed among directors who left in the year (p{other['Page']}, "
                                                 f"appointed {other['Appointed_Date'] or '?'}, ended {other['Resigned_Date'] or '?'})") if x)
            merged[idx[k]] = keep
            continue
        idx.setdefault(k, len(merged))
        merged.append(r)
    records = merged

    rcols = ["Ticker_Local", "Local_File", "Report_Lang", "Section", "Seq", "Page", "Name_Raw", "Name_Clean", "Role_Group",
             "Thai_Nationality", "Residing_In_Thailand", "Position_Raw", "Director_Type", "Date_Assumed", "Date_Ended",
             "Include_FY2025", "FY_Note", "Stated_In_Report", "BoardEx_Director_ID", "BoardEx_Nationality", "Match_Score"]
    write_csv(DATA / "roster.csv", [{k: p.get(k, "") for k in rcols} for p in people], rcols)
    write_csv(DATA / "records_auto.csv", records, list(dict.fromkeys(k for r in records for k in r)) if records else ["Ticker_Local"])
    write_csv(DATA / "source_conflicts.csv", conflicts, list(conflicts[0].keys()) if conflicts else ["Ticker_Local"])
    write_csv(DATA / "candidates.csv", cands, list(dict.fromkeys(k for c in cands for k in c)) if cands else ["Ticker_Local"])
    print("people", len(people), "| FY2025", sum(p["Include_FY2025"] == "YES" for p in people), "| matched to BoardEx",
          sum(1 for p in people if p["BoardEx_Director_ID"]), "| records", dict(Counter(r["Evidence_Type"] for r in records)),
          "| conflicts", len(conflicts), "| candidates", dict(Counter(c["Origin"] for c in cands)))


if __name__ == "__main__":
    main()
