"""Step 2 – BoardEx roles and individuals (Thailand extract) -> tidy CSVs with an FY2025 period status.

BoardEx date conventions seen in the extract (checked against the flag columns):
  start 1900-01-02 (flag 75) = start date unknown; flags 10/20/30 = exact day / month (day 1) / year only (1 Jan)
  end   9000-01-01 (flag 40) = current role;  9999-12-31 (flag 80) = ended at an unknown date
        flags 10/15/25 = exact day / month only (day 28) / year only (28 Dec)
FY2025_Valid: YES = held in 2025 (known start <= 2025-12-31 and current or ended on/after 2025-01-01);
              UNCERTAIN = start unknown; NO = ended at an unknown date (not evidence for 2025).
Role_Group: board seat -> Board; executive (leadership) team -> Executive; any other role -> Other_Manager.
Date of birth and LinkedIn links are not carried over (not needed).
Outputs: data/boardex_roles.csv, data/boardex_people.csv
"""
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from openpyxl import load_workbook

from common import read_csv, write_csv
from config import BOARDEX_PEOPLE_FILE, BOARDEX_ROLES_FILE, DATA, NATIONALITY_EN


def table(path: Path) -> list[dict]:
    rows = load_workbook(path, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True)
    head = next(rows)
    return [dict(zip(head, r)) for r in rows]


def d(x) -> str:
    return x.strftime("%Y-%m-%d") if isinstance(x, datetime) else ("" if x is None else str(x))


def period(start: datetime, end: datetime) -> tuple[str, str]:
    if end.year == 9999:
        return "ENDED_DATE_UNKNOWN", "NO"
    if start.year == 1900:
        return ("CURRENT_START_UNKNOWN" if end.year == 9000 else "ENDED_START_UNKNOWN"), "UNCERTAIN"
    if start > datetime(2025, 12, 31):
        return "STARTED_AFTER_2025", "NO"
    if end.year == 9000:
        return "CURRENT", "YES"
    return ("ENDED_2025_OR_LATER", "YES") if end >= datetime(2025, 1, 1) else ("ENDED_BEFORE_2025", "NO")


def main():
    isin_ticker = {u["ISIN"]: u["Ticker_Local"] for u in read_csv(DATA / "universe.csv") if u["ISIN"]}
    people = []
    for p in table(BOARDEX_PEOPLE_FILE):
        raw = p["(nationality) Nationality"] or ""
        people.append({"Director_ID": p["(directorid) Individual ID"], "Director_Name": p["(directorname) Individual Name"],
                       "Title": p["(title) Title"] or "", "Forename1": p["(forename1) First Name"] or "",
                       "Forename2": p["(forename2) Second Forename"] or "", "Forename3": p["(forename3) Third Forename"] or "",
                       "Forename4": p["(forename4) Fourth Forename"] or "", "Usual_Name": p["(usualname) Preferred Name"] or "",
                       "Surname": p["(surname) Last Name"] or "", "Gender": p["(gender) Gender"] or "",
                       "Nationality_Raw": raw, "Nationality": NATIONALITY_EN.get(raw.lower(), "UNMAPPED" if raw else "")})
    unmapped = Counter(p["Nationality_Raw"] for p in people if p["Nationality"] == "UNMAPPED")
    if unmapped:
        raise SystemExit(f"add to config.NATIONALITY_EN: {dict(unmapped)}")
    roles = []
    for r in table(BOARDEX_ROLES_FILE):
        status, valid = period(r["datestartrole"], r["dateendrole"])
        board, lead = r["brdposition"] == "Yes", r["(leadershipteam) Flag indicating executive team membership"] == "Yes"
        roles.append({"Role_Record_ID": r["(primarykeyid) Unique record identifier"], "ISIN": r["isin"],
                      "Ticker_Local": isin_ticker.get(r["isin"], ""), "Director_ID": r["directorid"],
                      "Director_Name": r["directorname"], "Company_Name_BoardEx": r["companyname"],
                      "Role_Name": r["rolename"], "Board_Position": r["brdposition"], "NED": r["ned"],
                      "Leadership_Team": r["(leadershipteam) Flag indicating executive team membership"],
                      "Role_Group": "Board" if board else ("Executive" if lead else "Other_Manager"),
                      "Date_Start": d(r["datestartrole"]), "Date_Start_Flag": r["(datestartroleflag) Flag denoting disclosed date"],
                      "Date_End": d(r["dateendrole"]), "Date_End_Flag": r["(dateendroleflag) Flag denoting disclosed date"],
                      "Period_Status": status, "FY2025_Valid": valid, "Description": r["fulltextdescription"] or "",
                      "Row_Type": r["(rowtype) Row Type"], "Org_Type": r["orgtype"]})
    write_csv(DATA / "boardex_people.csv", people, list(people[0].keys()))
    write_csv(DATA / "boardex_roles.csv", roles, list(roles[0].keys()))
    nat = {p["Director_ID"]: p["Nationality"] for p in people}
    print(len(people), "people |", len(roles), "roles |", dict(Counter(r["FY2025_Valid"] for r in roles)),
          "| no ticker", sum(1 for r in roles if not r["Ticker_Local"]),
          "| foreign people", sum(1 for p in people if p["Nationality"] not in ("", "Thailand")),
          "| foreign valid roles", sum(1 for r in roles if r["FY2025_Valid"] == "YES" and nat[r["Director_ID"]] not in ("", "Thailand")))


if __name__ == "__main__":
    main()
