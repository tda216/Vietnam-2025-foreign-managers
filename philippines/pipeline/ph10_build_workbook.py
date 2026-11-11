"""Step ph10: final Philippines FY2025 workbook -> philippines/output/Philippines_2025_Foreign_Managers.xlsx (+ QA).
(Until 2026-11-07 it was written to output/New_Philippines_2025_Foreign_Managers.xlsx; the owner asked for the Philippines folder.)

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph10_build_workbook.py
(run ph07 and ph08 first). The earlier BoardEx checkpoint workbooks are left untouched; their BoardEx_Raw and
Bloomberg_Raw sheets are copied cell by cell.

Inputs
  philippines/data/companies_boardex.csv      Bloomberg list (289 securities) + BoardEx coverage columns
  philippines/data/fo_final.csv               foreign-ownership classification (ph08)
  philippines/data/boardex_roles.csv          BoardEx roles, used AS-IS (owner, 2026-11-06: not re-checked)
  philippines/data/manual/*.csv               hand-reviewed records, decisions, ownership and holder evidence
  philippines/data/manager_search_set_133.csv, fallback_download_list.csv, holder_nationality.csv, top100_form.csv

Company flags (same rules as Vietnam, never turning missing into 0)
  1 + FOUND         at least one eligible foreign-national manager (any level); Foreign_Manager_Core counts Board/Supervisory/Executive
  0 + NONE_FOUND    source read and no foreign manager; for BoardEx companies every eligible person's nationality is disclosed
  blank + UNRESOLVED   no foreign manager found, but eligible BoardEx people have undisclosed nationality
  blank + NO_SOURCE    no FY2025 17-A, no 2026 Information Statement and no FY2024 17-A on PSE Edge
  blank + OUT_OF_SCOPE not in scope, or FOREIGN_MAJORITY with FO above 55% (manager search not required)
BoardEx rows without a board/leadership flag get a Role_Group from their title (see TITLE RULE below); advisers and similar
roles are not managers; roles at BoardEx 'Unlisted/Other Organisations' are excluded (Philippines rule of 5 Nov 2026).
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PH = ROOT / "philippines"
DATA = PH / "data"
RAW = PH / "raw" / "pse"
OUT = PH / "output" / "Philippines_2025_Foreign_Managers.xlsx"
OLD = PH / "output" / "Philippines_2025_Foreign_Managers_BoardEx_Extract.xlsx"  # byte-identical to output/Philippines_2025_Foreign_Managers.xlsx (5 Nov checkpoint)
sys.path.insert(0, str(HERE))
from ph_add_records import NATIONALITIES  # noqa: E402

CORE = {"Board", "Supervisory", "Executive"}
YEAR = 2025

# TITLE RULE for BoardEx rows that carry neither the board flag nor the leadership-team flag (applies the shared
# 'who counts' rule: Executive = CEO/President, deputy-CEO level, CFO, chief accountant/treasurer, C-suite;
# Other_Manager = director/head level; advisers are not managers).
NOT_MANAGER_RE = re.compile(r"(?i)advis|geologist|consultant|scientist|ambassador")
DIVISION_RE = re.compile(r"(?i)\b(division|regional|country|deputy|assistant|associate)\b")
EXEC_RE = re.compile(r"(?i)^(ceo|cfo|coo|cto|cio|cro|cco|president|treasurer|(senior )?executive vp\b.*|chief [a-z ,&/-]*officer)$")
MANAGER_RE = re.compile(r"(?i)\b(head|director|vp|vice president|president|officer|manager|general manager|md|treasurer|controller|"
                        r"secretary|chairman|ceo|cfo|coo|executive|partner)\b")


def rd(path, **kw):
    return list(csv.DictReader(open(path, encoding=kw.get("enc", "utf-8"))))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def norm_tokens(name):
    return set(re.sub(r"[^a-z ]", " ", name.lower()).split()) - {"jr", "sr", "ii", "iii", "dr", "atty", "mr", "ms"}


def boardex_eligibility(r):
    """(Role_Group_Final, Role_Group_Basis, Eligible) for a BoardEx role row."""
    if r["BoardEx_Row_Type"] != "Listed Organisations":
        return "", "EXCLUDED_ROLE_AT_" + r["BoardEx_Row_Type"].upper().replace(" ", "_"), False
    if r["Role_Group"] in CORE:
        return r["Role_Group"], "BOARDEX_FLAG", True
    t = r["Raw_Position"].strip()
    if NOT_MANAGER_RE.search(t):
        return "", "TITLE_RULE_NOT_A_MANAGER", False
    if EXEC_RE.match(t) and not DIVISION_RE.search(t):
        return "Executive", "TITLE_RULE", True
    if MANAGER_RE.search(t):
        return "Other_Manager", "TITLE_RULE", True
    return "", "TITLE_RULE_UNCLASSIFIED", False


def latest_17a(sym):
    best = None
    for mp in (RAW / sym).glob("*/meta.json") if (RAW / sym).exists() else []:
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m["form"] == "17-1" and "2026" in m["announced"]:
            if best is None or datetime.strptime(m["announced"][:12], "%b %d, %Y") > datetime.strptime(best["announced"][:12], "%b %d, %Y"):
                best = m
    return best


def main():
    comps = rd(DATA / "companies_boardex.csv", enc="utf-8-sig")
    fo = {r["Ticker"]: r for r in rd(DATA / "fo_final.csv")}
    bx = rd(DATA / "boardex_roles.csv", enc="utf-8-sig")
    recs = rd(DATA / "manual" / "manager_records.csv")
    decisions = rd(DATA / "manual" / "candidate_decisions.csv")
    own_manual = rd(DATA / "manual" / "ownership_manual.csv")
    holders_manual = rd(DATA / "manual" / "holder_nationality_review.csv")
    holders = rd(DATA / "holder_nationality.csv")
    top100 = rd(DATA / "top100_form.csv")
    s133 = {r["Ticker"]: r for r in rd(DATA / "manager_search_set_133.csv")}
    fallback = {}
    for r in rd(DATA / "fallback_download_list.csv"):
        fallback.setdefault(r["Symbol"], r)

    # ---------- manager rows ----------
    name_of = {c["Ticker"].split()[0]: c["Company"] for c in comps}
    tk_of = {c["Ticker"].split()[0]: c["Ticker"] for c in comps}
    ids, per = {}, Counter()
    fm_rows = []
    for r in recs:
        k = (r["Symbol"], " ".join(sorted(norm_tokens(r["Manager_Name"]))))
        if k not in ids:
            per[r["Symbol"]] += 1
            ids[k] = f"{r['Symbol']}-F{per[r['Symbol']]:02d}"
        fm_rows.append({**r, "Company": r["Company"] or name_of.get(r["Symbol"], ""), "Ticker": r["Ticker"] or tk_of.get(r["Symbol"], ""),
                        "Manager_ID": ids[k], "Record_Source": "FILING_REVIEW", "Role_Group_Basis": "REVIEWED",
                        "Verification": "Read in the filing: quote and PDF page recorded"})
    ours_by = defaultdict(list)
    for r in fm_rows:
        ours_by[r["Symbol"]].append(r)
    fill_path = DATA / "manual" / "boardex_nationality_fill.csv"
    fills = {(f["Symbol"], f["BoardEx_Director_ID"]): f for f in (rd(fill_path) if fill_path.exists() else [])}
    bx_rows, unknown_rows = [], []
    latest_dec = {}
    for d in decisions:  # a later decision for the same person supersedes an earlier one (earlier rows stay as the audit trail)
        latest_dec[(d["Symbol"], d["Name"])] = d
    excluded = {k: d for k, d in latest_dec.items() if d["Decision"] in
                ("NOT_A_MANAGER", "NOT_FY2025", "UNLISTED_SUBSIDIARY_ONLY", "LISTED_SUBSIDIARY_ROLE", "SAME_AS_RECORD",
                 "OWNER_DECISION_NOT_COUNTED", "NOT_FOREIGN_STATED")}
    open_elig = {k: d for k, d in latest_dec.items() if d["Decision"] == "NEEDS_REVIEW"}
    for r in bx:
        sym = r["Ticker"].split()[0]
        rg, basis, ok = boardex_eligibility(r)
        if (sym, r["Manager_Name"]) in excluded:  # hand decision (e.g. research-owner exclusion), see Candidate_Decisions
            rg, basis, ok = "", "DECISION_" + excluded[(sym, r["Manager_Name"])]["Decision"], False
        if (sym, r["Manager_Name"]) in open_elig and r["Is_Foreign"] == "1":
            # foreign national, but the role's employer/eligibility could not be verified: not counted, keeps the company open
            row = {**r, "Symbol": sym, "Role_Group_BoardEx": r["Role_Group"], "Role_Group": rg, "Role_Group_Basis": "DECISION_NEEDS_REVIEW",
                   "Eligible": "0", "Management_Include": "0", "Record_Source": "BOARDEX",
                   "Verification": "BoardEx-reported foreign national; role eligibility unresolved (see Candidate_Decisions)"}
            bx_rows.append(row)
            unknown_rows.append({**row, "Nationality_Status": "FOREIGN_ROLE_ELIGIBILITY_UNRESOLVED", "Resolved_By": ""})
            continue
        row = {**r, "Symbol": sym, "Role_Group_BoardEx": r["Role_Group"], "Role_Group": rg, "Role_Group_Basis": basis,
               "Eligible": "1" if ok else "0", "Record_Source": "BOARDEX",
               "Verification": "BoardEx-reported, not independently verified (owner decision 2026-11-06)"}
        if not ok:
            row["Management_Include"] = "0"
        if basis == "DECISION_NOT_FOREIGN_STATED":  # the company's filing states local nationality (owner decision); row kept, not counted
            row["Verification"] = "BoardEx nationality contradicted by the company's filing (local nationality stated); not counted - see Candidate_Decisions"
        fl0 = fills.get((sym, r["BoardEx_Director_ID"]))
        if r["Is_Foreign"] == "" and fl0 and fl0["Is_Foreign"] == "1":
            # undisclosed in BoardEx, foreign nationality read in the company's filing (ph11, reviewed)
            row.update(Nationality=fl0["Nationality"], Nationality_Raw=fl0["Nationality_Raw"], Is_Foreign="1",
                       Dual_Nationality=fl0["Dual_Nationality"],
                       Evidence_Type="INFERRED" if fl0["Nationality_Raw"] == "INFERRED" else "DOC_FIELD", Evidence_Quote=fl0["Evidence_Quote"],
                       Source=fl0["Source"], Source_URL=fl0["Source_URL"], Local_File=fl0["Local_File"], Page=fl0["Page"],
                       Note=(r.get("Note", "") + " | Nationality: " + fl0["Method"]).strip(" |"),
                       Record_Source="BOARDEX_ROLE + " + ("NAME_INFERENCE" if fl0["Nationality_Raw"] == "INFERRED" else "FILING_NATIONALITY"),
                       Verification=("BoardEx role not independently verified; nationality INFERRED from the name (owner decision)"
                                     if fl0["Nationality_Raw"] == "INFERRED" else
                                     "BoardEx role not independently verified; nationality read in the company's filing (quote, page)"))
            bx_rows.append(row)
            continue
        if r["Is_Foreign"] == "1":
            bx_rows.append(row)
        elif r["Is_Foreign"] == "" and ok:
            # an undisclosed BoardEx nationality resolved by a filing record for the same person (e.g. GLO Singtel directors)
            hit = [o for o in ours_by.get(sym, []) if norm_tokens(r["Manager_Name"]) and norm_tokens(r["Manager_Name"]) <= norm_tokens(o["Manager_Name"])]
            fl = fills.get((sym, r["BoardEx_Director_ID"]))
            row["Resolved_By"] = (f"{hit[0]['Manager_Name']} ({hit[0]['Nationality']}, filing p{hit[0]['Page']})" if hit else
                                  f"{fl['Name_In_Text']} ({fl['Nationality_Raw']}, {fl['Source'][:40]} p{fl['Page']}; {fl['Method']})"
                                  if fl and fl["Is_Foreign"] == "0" else "")
            unknown_rows.append(row)

    # Owner rule (2026-11-07): an undisclosed person counts as 'open' only when there is a foreign indication (review list:
    # BoardEx foreign national with unverified role, or a foreign-looking name kept for review). Other undisclosed people are
    # treated as not foreign, so a company with no foreign person identified is concluded NONE_FOUND.
    review_names = {k for k, d in latest_dec.items() if d["Decision"] == "NEEDS_REVIEW"
                    and not any(f["Symbol"] == d["Symbol"] and f["Manager_Name"] == d["Name"] for f in fills.values())}
    for u in unknown_rows:
        u["Treated_As"] = ("RESOLVED" if u["Resolved_By"] else
                           "OPEN_REVIEW" if u.get("Nationality_Status") == "FOREIGN_ROLE_ELIGIBILITY_UNRESOLVED" or (u["Symbol"], u["Manager_Name"]) in review_names
                           else "NOT_FOREIGN_NO_INDICATION (owner rule 2026-11-07)")

    # ---------- company rows ----------
    out, cov = [], []
    for c in comps:
        tk, sym = c["Ticker"], c["Ticker"].split()[0]
        f = fo[tk]
        lo, hi = num(f["FO_Lower"]), num(f["FO_Upper"])
        in_scope = f["In_Scope"] or "1"
        ms = "1" if f["Manager_Search"] == "Y" else "0"
        ms_reason = ("NOT_IN_SCOPE: " + f["Exclusion_Reason"] if in_scope != "1" else
                     "LOCAL" if f["Ownership_Type"] == "LOCAL" else
                     "BORDERLINE_FOREIGN_MAJORITY_FO_LE_55" if ms == "1" else "FOREIGN_MAJORITY_FO_ABOVE_55")
        matched = c["BoardEx_Coverage"].startswith("MATCHED")
        eligible_bx = [r for r in bx_rows if r["Symbol"] == sym and r["Eligible"] == "1"] if matched else []
        foreign = eligible_bx + ours_by.get(sym, [])
        unk_all = [r for r in unknown_rows if r["Symbol"] == sym and not r["Resolved_By"]] if matched else []
        unk = [r for r in unk_all if r["Treated_As"] == "OPEN_REVIEW"]
        unk_people = {r["Manager_ID"] for r in unk}
        n_undisclosed = len({r["Manager_ID"] for r in unk_all} - unk_people)
        doc17a = latest_17a(sym)
        if matched:
            src = "BOARDEX" + (" + FILING_REVIEW" if ours_by.get(sym) else "")
            basis_doc = "BoardEx extract (Results sheet)" + (f"; FY2025 17-A {doc17a['report_no']}" if ours_by.get(sym) and doc17a else "")
        else:
            src = "FILING_REVIEW"
            fb = fallback.get(sym)
            if doc17a:
                basis_doc = f"FY2025 SEC 17-A ({doc17a['report_no']}, announced {doc17a['announced'][:12]})"
            elif fb:
                basis_doc = f"{fb['Template']} ({fb['Form']} {fb['Report_No']}, announced {fb['Announced'][:12]}) - last-resort basis"
            else:
                basis_doc = ""
        if in_scope != "1" or ms != "1":
            flag, status = "", "OUT_OF_SCOPE"
        elif foreign:
            flag, status = 1, "FOUND"
        elif not matched and not basis_doc:
            flag, status = "", "NO_SOURCE"
        elif unk_people:
            flag, status = "", "UNRESOLVED"
        else:
            flag, status = 0, "NONE_FOUND"
        people = lambda rows: len({r["Manager_ID"] for r in rows})
        core = [r for r in foreign if r["Role_Group"] in CORE]
        core_flag = (1 if core else (0 if flag == 0 or (flag == 1 and not unk_people) else "")) if flag != "" else ""
        basis = ("PERSON_RECORD (" + "; ".join(sorted({r["Record_Source"] for r in foreign})) + ")" if status == "FOUND" else
                 (("NO_FOREIGN_IDENTIFIED_OWNER_RULE" if n_undisclosed else "BOARDEX_ALL_NATIONALITIES_DISCLOSED") if matched
                  else ("AR2024_OR_IS_FALLBACK" if "last-resort" in basis_doc else "AR2025"))
                 if status == "NONE_FOUND" else "")
        out.append({
            **{k: c.get(k, "") for k in ["Country", "Ticker", "Ticker_Local", "Company", "Company_Name_Local", "Exchange_At_FO_Date", "Exchange",
                                        "ISIN", "Industry_Group", "Security_Class"]},
            "In_Scope": in_scope, "Exclusion_Reason": f["Exclusion_Reason"],
            "Foreign_Ownership_Pct": f["Foreign_Ownership_Pct"] or (f["FO_Lower"] if f["FO_Bound"] == "EXACT" else ""),
            "FO_Bound": f["FO_Bound"], "FO_Lower": f["FO_Lower"], "FO_Upper": f["FO_Upper"], "FO_As_Of_Date": f["FO_As_Of_Date"],
            "Ownership_Type": f["Ownership_Type"], "FO_Method": f["FO_Method"], "FO_Source": f["FO_Source"], "FO_Source_URL": f["FO_Source_URL"],
            "FO_Page": f["FO_Page"], "FO_Evidence": f["FO_Evidence"], "FO_Note": f["FO_Note"], "FO_Basis": f["Basis"],
            "Manager_Search": ms, "Manager_Search_Reason": ms_reason,
            **{k: c.get(k, "") for k in ["Mcap_Rank", "Deep_Prelim", "Deep_Reason_Prelim"]},
            "Foreign_Manager": flag, "Foreign_Manager_Core": core_flag, "Flag_Status": status, "Flag_Basis": basis,
            "N_Foreign_Managers": people(foreign), "N_Foreign_Unnamed": 0,
            "N_Foreign_Board": people([r for r in foreign if r["Role_Group"] == "Board"]),
            "N_Foreign_Supervisory": people([r for r in foreign if r["Role_Group"] == "Supervisory"]),
            "N_Foreign_Executive": people([r for r in foreign if r["Role_Group"] == "Executive"]),
            "N_Foreign_Other": people([r for r in foreign if r["Role_Group"] not in CORE]),
            "N_Unknown_Candidates": len(unk_people), "N_Undisclosed_Treated_Not_Foreign": n_undisclosed,
            "Foreign_Manager_Summary": "; ".join(dict.fromkeys(f"{r['Manager_Name']} – {r['Raw_Position']} ({r['Nationality']})" for r in foreign)),
            "Manager_Source": src,
            **{k: c.get(k, "") for k in ["BoardEx_Coverage", "N_BoardEx_Role_Records", "N_BoardEx_People", "N_BoardEx_Known_Nationality",
                                        "N_BoardEx_Missing_Nationality", "N_BoardEx_Foreign_Nationality", "BoardEx_Nationalities_Reported"]},
        })
        cov.append({"Ticker": tk, "Symbol": sym, "Company": c["Company"], "In_Scope": in_scope, "Ownership_Type": f["Ownership_Type"],
                    "Manager_Search": ms, "Manager_Source": src, "Source_Basis": basis_doc,
                    "Source_URL": (doc17a or {}).get("viewer_url", "") if not matched or ours_by.get(sym) else "",
                    "In_Search_Set_133": "1" if tk in s133 else "0", "PSE_Map": s133.get(tk, {}).get("Map", ""),
                    "BoardEx_Eligible_Foreign_Rows": len(eligible_bx), "Filing_Records": len(ours_by.get(sym, [])),
                    "Unknown_Nationality_People": len(unk_people), "Flag_Status": status})

    # ---------- QA ----------
    qa = []
    def check(name, bad, detail=""):
        qa.append({"Check": name, "Violations": len(bad), "Examples": "; ".join(map(str, bad[:8])), "Detail": detail})
    by_t = {r["Ticker"]: r for r in out}
    check("In-scope securities without a final ownership class",
          [r["Ticker"] for r in out if r["In_Scope"] == "1" and r["Ownership_Type"] not in ("LOCAL", "FOREIGN_MAJORITY")])
    check("LOCAL with FO_Upper > 50 or FOREIGN_MAJORITY with FO_Lower <= 50",
          [r["Ticker"] for r in out if (r["Ownership_Type"] == "LOCAL" and num(r["FO_Upper"]) is not None and num(r["FO_Upper"]) > 50)
           or (r["Ownership_Type"] == "FOREIGN_MAJORITY" and num(r["FO_Lower"]) is not None and num(r["FO_Lower"]) <= 50)])
    check("Classified rows without FO bounds (except owner-rule rows)",
          [r["Ticker"] for r in out if r["Ownership_Type"] in ("LOCAL", "FOREIGN_MAJORITY") and r["FO_Lower"] == "" and not r["FO_Method"].startswith("OWNER_RULE")])
    check("FO_Lower > FO_Upper", [r["Ticker"] for r in out if num(r["FO_Lower"]) is not None and num(r["FO_Upper"]) is not None
                                   and num(r["FO_Lower"]) > num(r["FO_Upper"]) + 1e-9])
    check("Manual ownership rows without Evidence_Quote or Source",
          [o["Symbol"] for o in own_manual if not o["Evidence_Quote"]
           or not (o["Source"] or o["Local_File"] or (o["FO_Method"].startswith("OWNER_RULE") and "owner" in o["Evidence_Quote"].lower()))],
          "Owner-rule rows cite the research owner's instruction in Evidence_Quote instead of a document.")
    check("Flag/status mismatch",
          [r["Ticker"] for r in out if (r["Flag_Status"] == "FOUND") != (r["Foreign_Manager"] == 1)
           or (r["Flag_Status"] == "NONE_FOUND") != (r["Foreign_Manager"] == 0)])
    check("FOUND without a foreign record, or NONE_FOUND with open unknown people",
          [r["Ticker"] for r in out if (r["Flag_Status"] == "FOUND" and r["N_Foreign_Managers"] == 0)
           or (r["Flag_Status"] == "NONE_FOUND" and r["N_Unknown_Candidates"])])
    check("Manager search required but no flag status",
          [r["Ticker"] for r in out if r["Manager_Search"] == "1" and r["Flag_Status"] in ("", "OUT_OF_SCOPE")])
    check("Missing nationality coded as 0 (core flag 0 while people unresolved)",
          [r["Ticker"] for r in out if r["Foreign_Manager_Core"] == 0 and r["N_Unknown_Candidates"]])
    check("Filing records: nationality not in the standard list",
          [f"{r['Symbol']} {r['Manager_Name']} {r['Nationality']}" for r in fm_rows if r["Nationality"] not in NATIONALITIES])
    check("Filing records without quote, page or source URL",
          [f"{r['Symbol']} {r['Manager_Name']}" for r in fm_rows if not r["Evidence_Quote"] or not r["Page"] or not r["Source_URL"]])
    check("Filing records with Role_Group outside Board/Supervisory/Executive/Other_Manager",
          [f"{r['Symbol']} {r['Manager_Name']}" for r in fm_rows if r["Role_Group"] not in CORE | {"Other_Manager"}])
    check("Filing records for symbols not in the Bloomberg list", [r["Symbol"] for r in fm_rows if r["Symbol"] not in name_of])
    check("BoardEx foreign rows dropped by the extraction (count check)",
          [] if sum(1 for r in bx if r["Is_Foreign"] == "1" or (r["Is_Foreign"] == "" and fills.get((r["Ticker"].split()[0], r["BoardEx_Director_ID"]), {}).get("Is_Foreign") == "1"))
          == len(bx_rows) else ["mismatch"])
    check("BoardEx nationality fills without quote, page or source",
          [f"{f['Symbol']} {f['Manager_Name']}" for f in fills.values() if not f["Evidence_Quote"]
           or (f["Nationality_Raw"] != "INFERRED" and (not f["Page"] or not f["Source_URL"]))],
          "INFERRED rows (owner rule: Filipino name) carry the basis in Evidence_Quote instead of a page.")
    check("Holder review rows (Is_Foreign 0/1) without Evidence_Quote",
          [f"{h['Symbol']} {h['Holder_Name']}" for h in holders_manual if h["Is_Foreign"] in ("0", "1") and not h["Evidence_Quote"]])

    # ---------- workbook ----------
    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    st = Counter(r["Flag_Status"] for r in out)
    insc = [r for r in out if r["In_Scope"] == "1"]
    srch = [r for r in out if r["Manager_Search"] == "1"]
    readme = [
        ("Listed Companies & Foreign Managers – Philippines FY2025", True),
        (f"Built {datetime.now(timezone.utc).isoformat(timespec='seconds')} by philippines/pipeline/ph10_build_workbook.py. "
         "Earlier checkpoint workbooks are not modified.", False),
        ("", False),
        ("SCOPE", True),
        (f"{len(out)} Bloomberg securities; {len(insc)} in scope. Out of scope: securities listed only outside the Philippines "
         "(owner rule: recorded FOREIGN_MAJORITY), DELM (SGX+PSE, owner rule), and AR, PORT, LAND, DMPI (owner decision 6 Nov 2026: no usable "
         "filing / not PSE-listed). Rows are kept with In_Scope = 0 and Exclusion_Reason.", False),
        ("", False),
        ("FOREIGN OWNERSHIP (sheet Companies, Ownership_*)", True),
        ("FO = share of VOTING POWER held by holders whose legal nationality is not Philippine (IMF BPM6 §6.12/§6.19; general rule in "
         "philippines/AGENTS.md). Single voting class: foreign % of outstanding common shares. Companies with voting preferred shares: "
         "common + voting preferred (owner decision 6 Nov 2026). FO > 50 = FOREIGN_MAJORITY, FO <= 50 = LOCAL. Unknown holders are kept as "
         "bounds: FO_Lower treats them as local, FO_Upper as foreign; a class is assigned only when the bounds settle it.", False),
        ("Sources: PSE Top 100 Stockholders (17-12-A) at 31 Dec 2025 (PCD Nominee Filipino/Non-Filipino + named holders) with holder "
         "nationality from the FY2025 SEC 17-A; issuer statements of foreign ownership (17-A, PSE Public Ownership Report, PSE Form 17-13); "
         "the 2025 General Information Sheet where the 17-A does not settle the class (owner approval 6 Nov 2026). Corporate holders take the "
         "legal nationality written in the filing (place of incorporation), not the ultimate owner. FO may be measured at any date in 2025 "
         "(FO_As_Of_Date records it). FO_Basis: AUTO_BOUNDS = computed by ph07 from the Top 100 and 17-A labels; MANUAL = read by hand "
         "(sheet Ownership_Manual).", False),
        (f"Result: in scope {Counter(r['Ownership_Type'] for r in insc)}.", False),
        ("", False),
        ("FOREIGN MANAGERS (sheets Foreign_Managers, Unknown_Nationality)", True),
        ("FY2025 = held an eligible position at any time in 2025. Board, Executive (CEO/President, deputy-CEO level, CFO, treasurer, C-suite) and "
         "Other_Manager (director/head level) at the sampled listed company itself; roles only at unlisted subsidiaries do not count. "
         "Two sources: (1) BoardEx (156 securities matched by ISIN) used AS-IS and labelled 'BoardEx-reported, not independently verified' "
         "(owner decision 6 Nov 2026); BoardEx rows without board/leadership flags get a Role_Group from the title (Role_Group_Basis = "
         "TITLE_RULE; advisers etc. are not managers; roles at BoardEx 'Unlisted/Other Organisations' are excluded). (2) Filing review for "
         "the 133 securities without a BoardEx match: FY2025 SEC 17-A (Items 9-10 directors and officers with citizenship), OCR for scanned "
         "pages, FY2024 17-A or 2026 Information Statement as last resort; every record has a verbatim quote and PDF page.", False),
        ("BoardEx people with undisclosed nationality were looked up in the company's own FY2025 17-A / Information Statement "
         "(ph11): a nationality written directly after the person's name ('Name, Filipino, 58' / 'Name, 58, Filipino' / the first "
         "'Citizenship:' field of the person's bio) settles a Filipino person automatically (sheet BoardEx_Nationality_Fill, with quote "
         "and page); foreign, dual or conflicting labels were read by hand. People still undisclosed after that search whose name is "
         "Filipino were given Philippine nationality by the research owner's rule of 6 Nov 2026 (Nationality_Raw = INFERRED, Method = "
         "INFERRED_WEAK). Name test: the surname occurs among people stated Filipino and among no one stated foreign (shared surnames "
         "such as Tan, Lim, Lee, Go, Ng are not inferred). These people count as Filipino for the flags.", False),
        ("Nationality rules: stated citizenship is used ('Filipino/Chinese' or 'Spanish / Filipino' = dual nationality, Is_Foreign = 1, "
         "Dual_Nationality = 1). Titles are recorded as written. Undisclosed nationality is never treated as Filipino.", False),
        ("", False),
        ("COMPANY FLAGS", True),
        ("Same flag rules as the Vietnam workbook, for cross-country comparability (owner decision 6 Nov 2026); Foreign_Manager_Core is "
         "blank whenever Foreign_Manager is blank. Owner rule 7 Nov 2026: a person whose nationality stays undisclosed keeps a company open "
         "only when there is a foreign indication (sheet Review_Open); otherwise the company is concluded NONE_FOUND (Flag_Basis = "
         "NO_FOREIGN_IDENTIFIED_OWNER_RULE; count in N_Undisclosed_Treated_Not_Foreign) - as in Vietnam, where only foreign-looking names "
         "were candidates. Foreign_Manager = 1 (FOUND): at least one eligible foreign national (any level). Foreign_Manager_Core uses Board/Supervisory/Executive "
         "only and is the comparable variable. 0 (NONE_FOUND): source read and none found; for BoardEx companies only when every eligible "
         "person's nationality is disclosed. Blank: UNRESOLVED (no foreign found but eligible BoardEx people with undisclosed nationality), "
         "NO_SOURCE (no FY2025/FY2024 17-A or Information Statement on PSE Edge), OUT_OF_SCOPE (not in scope, or FOREIGN_MAJORITY with FO > 55%). "
         "Manager search covers LOCAL and FOREIGN_MAJORITY with FO_Lower <= 55%.", False),
        (f"Result (manager search = {len(srch)}): {dict(Counter(r['Flag_Status'] for r in srch))}; "
         f"Foreign_Manager = 1: {sum(r['Foreign_Manager'] == 1 for r in srch)}; Foreign_Manager_Core = 1: {sum(r['Foreign_Manager_Core'] == 1 for r in srch)}.", False),
        ("", False),
        ("SHEETS", True),
        ("Companies (1 row per Bloomberg security) | Foreign_Managers (1 row per person x position, Record_Source = FILING_REVIEW or BOARDEX) | "
         "Unknown_Nationality (eligible BoardEx people with undisclosed nationality; they keep companies UNRESOLVED) | Candidate_Decisions | "
         "Coverage_Log | Ownership_Manual (hand-read FO evidence and owner rules) | Holder_Nationality (Top 100 holders with nationality evidence) | "
         "Holder_Review (hand-read holder evidence) | Top100_Form (PSE form figures) | QA | BoardEx_Raw, Bloomberg_Raw (verbatim copies).", False),
        ("", False),
        ("OPEN ITEMS", True),
        (f"{st.get('UNRESOLVED', 0)} companies are UNRESOLVED only because BoardEx does not disclose some people's nationality; they could be "
         "settled by reading the citizenship column of each company's FY2025 17-A (Items 9-10). BoardEx roles are not checked against filings "
         "(owner decision). FY2025 date checks on BoardEx rows are as supplied (special dates kept in the raw columns). The manual QA sample has "
         "not been drawn yet.", False),
    ]
    for text, bold in readme:
        ws.append([text])
        ws.cell(ws.max_row, 1).font = Font(bold=bold, size=13 if bold else 11)
        ws.cell(ws.max_row, 1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 160

    def sheet(title, rows, cols=None):
        w = wb.create_sheet(title)
        cols = cols or (list(rows[0].keys()) if rows else ["(empty)"])
        w.append(cols)
        for r in rows:
            w.append([r.get(c, "") for c in cols])
        for cell in w[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E78")
        w.freeze_panes = "A2"
        return w

    sheet("Companies", out)
    fm_cols = ["Company", "Ticker", "Symbol", "Year", "Manager_ID", "Manager_Name", "Raw_Position", "Role_Group", "Role_Group_Basis",
               "Nationality", "Nationality_Raw", "Is_Foreign", "Dual_Nationality", "Appointed_Date", "Resigned_Date", "Source", "Source_URL",
               "Local_File", "Page", "Evidence_Type", "Evidence_Quote", "Other_Sources", "Note", "Reviewed_On", "Management_Include",
               "Record_Source", "Verification", "Eligible", "Role_Group_BoardEx", "Source_Sheet", "Source_Row", "BoardEx_Director_ID",
               "BoardEx_Record_ID", "BoardEx_Row_Type", "Start_Date_Raw", "End_Date_Raw", "FY2025_Date_Check"]
    for r in fm_rows:
        r.setdefault("Year", YEAR)
        r["Eligible"] = "1"
    sheet("Foreign_Managers", fm_rows + bx_rows, fm_cols)
    sheet("Unknown_Nationality", unknown_rows, ["Company", "Ticker", "Symbol", "Manager_ID", "Manager_Name", "Raw_Position", "Role_Group",
                                                "Role_Group_Basis", "Nationality_Status", "Resolved_By", "Treated_As", "Source_Sheet", "Source_Row",
                                                "BoardEx_Director_ID", "FY2025_Date_Check"])
    if fills:
        sheet("BoardEx_Nationality_Fill", list(fills.values()))
    sheet("Candidate_Decisions", decisions)
    flag_of = {r["Ticker"].split()[0]: r["Flag_Status"] for r in out}
    sheet("Review_Open", [{"Symbol": d["Symbol"], "Company": name_of.get(d["Symbol"], ""), "Company_Flag_Status": flag_of.get(d["Symbol"], ""),
                           "Name": d["Name"], "Reason": d["Reason"], "Reviewed_On": d["Reviewed_On"],
                           "Next_Step": "Check the FY2024 / FY2023 17-A or Information Statement (owner, 2026-11-07)"}
                          for (s_, n_), d in latest_dec.items() if (s_, n_) in review_names])
    sheet("Coverage_Log", cov)
    sheet("Ownership_Manual", own_manual)
    sheet("Holder_Nationality", holders)
    sheet("Holder_Review", holders_manual)
    sheet("Top100_Form", top100)
    sheet("QA", qa)
    if OLD.exists():
        old = load_workbook(OLD, read_only=True)
        for name in ("BoardEx_Raw", "Bloomberg_Raw"):
            if name in old.sheetnames:
                w = wb.create_sheet(name)
                for row in old[name].iter_rows(values_only=True):
                    w.append(list(row))
    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    print("wrote", OUT.relative_to(ROOT))
    print("ownership (in scope):", Counter(r["Ownership_Type"] for r in insc))
    print("flag status (manager search):", Counter(r["Flag_Status"] for r in srch))
    print("Foreign_Manager=1:", sum(r["Foreign_Manager"] == 1 for r in srch), "| Core=1:", sum(r["Foreign_Manager_Core"] == 1 for r in srch),
          "| Core=0:", sum(r["Foreign_Manager_Core"] == 0 for r in srch))
    print("Foreign_Managers rows:", len(fm_rows) + len(bx_rows), f"(filing {len(fm_rows)}, BoardEx {len(bx_rows)}, BoardEx eligible "
          f"{sum(r['Eligible'] == '1' for r in bx_rows)})", "| Unknown_Nationality rows:", len(unknown_rows))
    print("QA violations:", sum(q["Violations"] for q in qa))
    for q in qa:
        if q["Violations"]:
            print("  ", q["Check"], q["Violations"], q["Examples"])


if __name__ == "__main__":
    main()
