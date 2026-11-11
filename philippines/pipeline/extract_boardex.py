"""Extract supplied BoardEx data without web research or changing source files.

Run from the repository root with python -I. The output uses the Vietnam workbook
schema, with spreadsheet row locators and BoardEx-specific supplementary sheets.
This is an extraction checkpoint, not a completed ownership/manager assessment.
"""
import argparse
import csv
import hashlib
import json
import posixpath
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile, ZIP_DEFLATED

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


PROJECT = Path(__file__).resolve().parents[1]
NATIONALITIES = {
    "Filipino": "Philippines", "American": "United States",
    "British": "United Kingdom", "Singaporean": "Singapore",
    "Chinese": "China", "Japanese": "Japan", "Australian": "Australia",
    "Malaysian": "Malaysia", "Chinese (Taiwan)": "Taiwan", "Indian": "India",
    "Indonesian": "Indonesia", "French": "France", "South Korean": "South Korea",
    "Danish": "Denmark", "South African": "South Africa", "Swiss": "Switzerland",
    "German": "Germany", "Spanish": "Spain", "Belgian": "Belgium",
    "Saudi": "Saudi Arabia", "Peruvian": "Peru", "Czech": "Czech Republic",
    "Sri Lankan": "Sri Lanka", "Bermudian": "Bermuda", "Russian": "Russia",
    "Fijian": "Fiji", "New Zealander": "New Zealand", "Thai": "Thailand",
    "Mexican": "Mexico", "Kosovar": "Kosovo", "Greek": "Greece",
}
PERSON_ID = "directorid"
RECORD_ID = "(primarykeyid) Unique record identifier"
TEAM = "(leadershipteam) Flag indicating executive team membership"
START_FLAG = "(datestartroleflag) Flag denoting disclosed date"
END_FLAG = "(dateendroleflag) Flag denoting disclosed date"
ROLE_EXTRA = [
    "Source_Sheet", "Source_Row", "Nationality_Source_Cell", "Nationality_Status",
    "BoardEx_Company_ID", "BoardEx_Director_ID", "BoardEx_Record_ID", "ISIN",
    "BoardEx_Board_Position", "BoardEx_Nonexecutive", "BoardEx_Leadership_Team",
    "BoardEx_Row_Type", "BoardEx_Headquarters_Country", "BoardEx_Organization_Type",
    "Role_Description_Raw", "Nationality_Disclosure_Status_Raw", "Start_Date_Raw",
    "End_Date_Raw", "Start_Date_Flag_Raw", "End_Date_Flag_Raw", "FY2025_Date_Check",
    "Role_Review_Status",
]


def clean(value):
    return "" if value is None else str(value).strip()


def serializable(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def checksum(path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_write(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows({k: serializable(v) for k, v in row.items()} for row in rows)


def table_sheet(wb, title, rows, fields):
    sheet = wb.create_sheet(title)
    sheet.append(fields)
    for row in rows:
        sheet.append([row.get(field, "") for field in fields])
    # All text is data, including a source value beginning with '='.
    for row in sheet:
        for cell in row:
            if isinstance(cell.value, str):
                cell.data_type = "s"
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="17365D")
    sheet.freeze_panes = "A2"
    if rows:
        table = Table(displayName="tbl_" + title, ref=sheet.dimensions)
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        sheet.add_table(table)
    for column, field in enumerate(fields, 1):
        width = 19
        if field in {"Company", "Manager_Name", "Raw_Position", "BoardEx_Company"}:
            width = 38
        elif any(word in field for word in ("Note", "Summary", "Description", "Source_File")):
            width = 60
        elif field in {"Evidence_Quote", "Local_File"}:
            width = 45
        sheet.column_dimensions[get_column_letter(column)].width = width
    return sheet


def copy_values(wb, source, title):
    sheet = wb.create_sheet(title)
    for source_row in source:
        sheet.append([cell.value for cell in source_row])
        for src, dest in zip(source_row, sheet[sheet.max_row]):
            dest.number_format = src.number_format or "General"
            if isinstance(dest.value, str):
                dest.data_type = "s"
    sheet.freeze_panes = "A2"


def preserve_raw_numeric_values(path, sources):
    """Restore original OOXML numeric text instead of rounding through serialization.

    openpyxl writes floats with 16 significant digits; Bloomberg can contain more.
    Raw-sheet values are restored at their original coordinates before exact QA.
    """
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    def sheet_path(archive, title):
        relationships = {r.attrib["Id"]: r.attrib["Target"] for r in
                         ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        for sheet in ElementTree.fromstring(archive.read("xl/workbook.xml")).find("s:sheets", ns):
            if sheet.attrib["name"] == title:
                target = relationships[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
                return target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
        raise ValueError(f"Missing sheet: {title}")
    replacements = {}
    with ZipFile(path) as generated:
        for raw_title, input_path, input_title in sources:
            with ZipFile(input_path) as original:
                original_tree = ElementTree.fromstring(original.read(sheet_path(original, input_title)))
                numbers = {c.attrib["r"]: c.find("s:v", ns).text
                           for c in original_tree.findall("s:sheetData/s:row/s:c", ns)
                           if c.attrib.get("t", "n") == "n" and c.find("s:v", ns) is not None}
            target = sheet_path(generated, raw_title)
            tree = ElementTree.fromstring(generated.read(target))
            for cell in tree.findall("s:sheetData/s:row/s:c", ns):
                if cell.attrib["r"] in numbers:
                    value = cell.find("s:v", ns)
                    if value is None:
                        raise ValueError(f"Missing raw numeric cell: {cell.attrib['r']}")
                    value.text = numbers[cell.attrib["r"]]
            replacements[target] = ElementTree.tostring(tree, encoding="utf-8")
        replacement_path = path.with_suffix(".precision.xlsx")
        with ZipFile(replacement_path, "w", ZIP_DEFLATED) as restored:
            for item in generated.infolist():
                restored.writestr(item, replacements.get(item.filename, generated.read(item.filename)))
    replacement_path.replace(path)


def normalized_date(value):
    """Do not expose BoardEx's 1900/9000/9999 placeholders as real role dates."""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date) and 1901 <= value.year < 2100:
        return value.isoformat()
    return ""


def run(args):
    boardex_path, bloomberg_path = args.boardex.resolve(), args.bloomberg.resolve()
    template_path = args.template.resolve()
    before = {str(p): checksum(p) for p in (boardex_path, bloomberg_path)}
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = output.parent / "data"
    data.mkdir(parents=True, exist_ok=True)

    source_book = load_workbook(boardex_path, read_only=True, data_only=True)
    source = source_book["Results"]
    source_headers = list(next(source.iter_rows(values_only=True)))
    required = {"isin", "companyid", "companyname", "directorname", PERSON_ID,
                RECORD_ID, "rolename", "BoardEx Nationality", "datestartrole", "dateendrole"}
    if not required.issubset(source_headers):
        raise ValueError(f"Missing BoardEx fields: {required - set(source_headers)}")
    source_rows = [(number, dict(zip(source_headers, values)))
                   for number, values in enumerate(source.iter_rows(min_row=2, values_only=True), 2)
                   if any(value is not None for value in values)]

    bb_book = load_workbook(bloomberg_path, read_only=True, data_only=True)
    bb_sheet = bb_book.worksheets[0]
    bb_headers, securities = None, []
    for number, values in enumerate(bb_sheet.iter_rows(values_only=True), 1):
        if values[0] == "Ticker":
            bb_headers = list(values)
        elif bb_headers and isinstance(values[0], str) and values[0].endswith(" Equity"):
            securities.append({"Source_Row": number, **dict(zip(bb_headers, values))})
    if not securities:
        raise ValueError("No Bloomberg securities found")
    bb_isin = defaultdict(list)
    for security in securities:
        if clean(security.get("ISIN")):
            bb_isin[clean(security["ISIN"])].append(security)

    template = load_workbook(template_path, read_only=True, data_only=True)
    company_fields = ["Company_Name_Local" if f == "Company_Name_VN" else f
                      for f in next(template["Companies"].iter_rows(values_only=True))]
    manager_fields = list(next(template["Foreign_Managers"].iter_rows(values_only=True)))

    person_nats, person_nat_rows = defaultdict(set), defaultdict(list)
    for number, raw in source_rows:
        pid, nat = clean(raw[PERSON_ID]), clean(raw.get("BoardEx Nationality"))
        if not pid or not clean(raw[RECORD_ID]) or not clean(raw["companyid"]):
            raise ValueError(f"Missing stable ID in source row {number}")
        if nat:
            if nat not in NATIONALITIES:
                raise ValueError(f"Unmapped nationality in source row {number}: {nat}")
            person_nats[pid].add(nat)
            person_nat_rows[pid].append(number)

    all_roles, company_records = [], defaultdict(list)
    company_match = {}
    for number, raw in source_rows:
        cid, pid = clean(raw["companyid"]), clean(raw[PERSON_ID])
        matches = bb_isin.get(clean(raw["isin"]), [])
        if len(matches) != 1:
            raise ValueError(f"Source row {number} has {len(matches)} Bloomberg ISIN matches; manual review required")
        security = matches[0]
        previous = company_match.setdefault(cid, security)
        if previous["Ticker"] != security["Ticker"]:
            raise ValueError(f"Company {cid} maps to multiple securities; review before grouping")
        ticker = security["Ticker"].removesuffix(" Equity")
        # Match the Vietnam join convention: local exchange tickers omit the market suffix.
        if ticker.endswith(" PM"):
            ticker = ticker[:-3]
        nat_raw = clean(raw.get("BoardEx Nationality"))
        options = person_nats[pid]
        nat_status = "SOURCE_DISCLOSED" if nat_raw else "NOT_DISCLOSED"
        if len(options) > 1:
            nat_status = "PERSON_NATIONALITY_CONFLICT"
        elif not nat_raw and len(options) == 1:
            nat_raw = next(iter(options))
            nat_status = "OTHER_ROW_SAME_BOARDEX_DIRECTOR_ID"
        nationality = NATIONALITIES.get(nat_raw, "UNKNOWN")
        is_foreign = "" if not nat_raw or len(options) > 1 else int(nationality != "Philippines")
        start, end = normalized_date(raw.get("datestartrole")), normalized_date(raw.get("dateendrole"))
        if start and start > "2025-12-31" or end and end < "2025-01-01":
            date_check = "OUTSIDE_2025_RECORDED_DATES"
        elif not start:
            date_check = "START_DATE_SPECIAL_REVIEW"
        elif not end:
            date_check = "START_BY_2025_END_DATE_SPECIAL_REVIEW"
        else:
            date_check = "OVERLAPS_2025_RECORDED_DATES"
        # These flags are reading aids; final eligibility and combined roles need review.
        group = ("Board" if raw.get("brdposition") == "Yes" else
                 "Executive" if raw.get(TEAM) == "Yes" else "")
        notes = ["BoardEx-only extraction; listed-issuer attribution, role eligibility, and FY2025 service not independently verified.",
                 "Role_Group is provisional, based on BoardEx board/executive-team flags; combined roles remain unsplit.",
                 "Page is blank because the source is an Excel worksheet; use Source_Sheet and Source_Row."]
        if not start or not end:
            notes.append("Special source date retained in raw fields; not interpreted as an actual appointment/resignation date.")
        if nat_status == "OTHER_ROW_SAME_BOARDEX_DIRECTOR_ID":
            notes.append("Nationality transferred by identical BoardEx director ID from source row(s): "
                         + ", ".join(map(str, person_nat_rows[pid])))
        row = {field: "" for field in manager_fields + ROLE_EXTRA}
        row.update({
            "Company": clean(raw["companyname"]), "Ticker": ticker, "Year": 2025,
            "Manager_Name": clean(raw["directorname"]), "Raw_Position": clean(raw["rolename"]),
            "Nationality": nationality, "Source": "BoardEx", "Manager_ID": ticker + "-BX-" + pid,
            "Nationality_Raw": nat_raw, "Is_Foreign": is_foreign, "Role_Group": group,
            "Appointed_Date": start, "Resigned_Date": end,
            "Evidence_Type": "DOC_FIELD" if nat_raw and len(options) == 1 else "",
            "Evidence_Quote": nat_raw, "Local_File": str(boardex_path),
            "Note": " ".join(notes), "Source_Sheet": "Results", "Source_Row": number,
            "Nationality_Source_Cell": (f"T{number}" if nat_status == "SOURCE_DISCLOSED" else
                                        "; ".join(f"T{n}" for n in person_nat_rows[pid]) if nat_raw else ""),
            "Nationality_Status": nat_status, "BoardEx_Company_ID": cid,
            "BoardEx_Director_ID": pid, "BoardEx_Record_ID": clean(raw[RECORD_ID]),
            "ISIN": clean(raw["isin"]), "BoardEx_Board_Position": clean(raw.get("brdposition")),
            "BoardEx_Nonexecutive": clean(raw.get("ned")), "BoardEx_Leadership_Team": clean(raw.get(TEAM)),
            "BoardEx_Row_Type": clean(raw.get("(rowtype) Row Type")),
            "BoardEx_Headquarters_Country": clean(raw.get("hocountryname")),
            "BoardEx_Organization_Type": clean(raw.get("orgtype")),
            "Role_Description_Raw": clean(raw.get("fulltextdescription")),
            "Nationality_Disclosure_Status_Raw": clean(raw.get("Nationality Disclosure Status")),
            "Start_Date_Raw": serializable(raw.get("datestartrole")),
            "End_Date_Raw": serializable(raw.get("dateendrole")),
            "Start_Date_Flag_Raw": raw.get(START_FLAG, ""), "End_Date_Flag_Raw": raw.get(END_FLAG, ""),
            "FY2025_Date_Check": date_check, "Role_Review_Status": "PENDING_REVIEW",
        })
        all_roles.append(row)
        company_records[security["Ticker"]].append(row)

    foreign_managers = [row for row in all_roles if row["Is_Foreign"] != 0]
    reported_foreign = [row for row in all_roles if row["Is_Foreign"] == 1]
    missing = [row for row in all_roles if row["Is_Foreign"] == ""]
    company_extra = ["Source", "BoardEx_Coverage", "N_BoardEx_Role_Records", "N_BoardEx_People",
                     "N_BoardEx_Known_Nationality", "N_BoardEx_Missing_Nationality",
                     "N_BoardEx_Foreign_Nationality", "BoardEx_Nationalities_Reported", "Research_Note"]
    companies, coverage = [], []
    for security in securities:
        ticker = security["Ticker"]
        rows = company_records.get(ticker, [])
        def unique_people(predicate):
            return len({r["Manager_ID"] for r in rows if predicate(r)})
        row = {field: "" for field in company_fields + company_extra}
        row.update({
            "Country": "PH", "Ticker": ticker, "Ticker_Local": ticker.removesuffix(" Equity").removesuffix(" PM"),
            "Company": rows[0]["Company"] if rows else security.get("Short Name", ""),
            "ISIN": security.get("ISIN") or "", "Industry_Group": security.get("Ind Group") or "",
            "Ownership_Type": "REVIEW", "Flag_Status": "NOT_SEARCHED",
            "Source": "BoardEx" if rows else "", "BoardEx_Coverage": "MATCHED_BY_ISIN" if rows else "NO_BOARDEX_MATCH",
            "Research_Note": "Ownership and final manager flags pending. " +
                ("BoardEx extraction available; role eligibility, date precision, and nationality gaps need review."
                 if rows else "No matching ISIN in the supplied BoardEx file; not evidence of no foreign managers."),
        })
        if rows:
            row.update({
                "N_BoardEx_Role_Records": len(rows), "N_BoardEx_People": unique_people(lambda r: True),
                "N_BoardEx_Known_Nationality": unique_people(lambda r: r["Is_Foreign"] != ""),
                "N_BoardEx_Missing_Nationality": unique_people(lambda r: r["Is_Foreign"] == ""),
                "N_BoardEx_Foreign_Nationality": unique_people(lambda r: r["Is_Foreign"] == 1),
                "BoardEx_Nationalities_Reported": "; ".join(sorted({r["Nationality"] for r in rows if r["Nationality"] != "UNKNOWN"})),
                "Foreign_Manager_Summary": "; ".join(dict.fromkeys(
                    f"{r['Manager_Name']} — {r['Raw_Position']} ({r['Nationality']}; BoardEx, eligibility pending)"
                    for r in rows if r["Is_Foreign"] == 1)),
            })
        companies.append(row)
        coverage.append({
            "Ticker_Local": row["Ticker_Local"], "Company": row["Company"], "ISIN": row["ISIN"],
            "Source": row["Source"], "Source_Basis": "BOARDEX_ONLY" if rows else "",
            "Source_File": str(boardex_path) if rows else "", "Source_Sheet": "Results" if rows else "",
            "Source_Rows": "; ".join(str(r["Source_Row"]) for r in rows),
            "BoardEx_Coverage": row["BoardEx_Coverage"], "Records": len(rows) if rows else "",
            "Flag_Status": "NOT_SEARCHED", "Source_Basis_Note": row["Research_Note"],
        })

    people_groups = defaultdict(list)
    for row in all_roles:
        people_groups[(row["Ticker"], row["Manager_ID"])].append(row)
    people = []
    for (ticker, pid), rows in people_groups.items():
        people.append({
            "Company": rows[0]["Company"], "Ticker": ticker, "Year": 2025, "Manager_ID": pid,
            "Manager_Name": "; ".join(dict.fromkeys(r["Manager_Name"] for r in rows)),
            "Positions": "; ".join(dict.fromkeys(r["Raw_Position"] for r in rows)),
            "Nationality": rows[0]["Nationality"], "Nationality_Raw": rows[0]["Nationality_Raw"],
            "Is_Foreign": rows[0]["Is_Foreign"], "Source": "BoardEx", "N_Role_Records": len(rows),
            "Source_Sheet": "Results", "Source_Rows": "; ".join(str(r["Source_Row"]) for r in rows),
            "BoardEx_Director_ID": rows[0]["BoardEx_Director_ID"], "BoardEx_Company_ID": rows[0]["BoardEx_Company_ID"],
        })

    summary = {
        "bloomberg_securities": len(securities), "boardex_companies": len(company_match),
        "matched_bloomberg_securities": len(company_records),
        "bloomberg_without_boardex": len(securities) - len(company_records),
        "boardex_role_records": len(all_roles), "unique_people_global": len({r["BoardEx_Director_ID"] for r in all_roles}),
        "company_person_pairs": len(people), "nationality_disclosed_role_records": sum(r["Is_Foreign"] != "" for r in all_roles),
        "nationality_disclosed_unique_people": len({r["BoardEx_Director_ID"] for r in all_roles if r["Is_Foreign"] != ""}),
        "filipino_role_records": sum(r["Is_Foreign"] == 0 for r in all_roles),
        "foreign_nationality_role_records": len(reported_foreign),
        "foreign_nationality_unique_people": len({r["BoardEx_Director_ID"] for r in reported_foreign}),
        "companies_with_foreign_nationality_reported": len({r["Ticker"] for r in reported_foreign}),
        "missing_nationality_role_records": len(missing),
        "missing_nationality_unique_people": len({r["BoardEx_Director_ID"] for r in missing}),
        "nationality_conflicts": sum(len(nats) > 1 for nats in person_nats.values()),
        "nationality_rows_filled_by_director_id": sum(r["Nationality_Status"] == "OTHER_ROW_SAME_BOARDEX_DIRECTOR_ID" for r in all_roles),
        "foreign_managers_sheet_rows": len(foreign_managers),
        "date_checks": dict(Counter(r["FY2025_Date_Check"] for r in all_roles)),
        "source_hashes_sha256": before, "extracted_at_utc": stamp,
    }

    workbook = Workbook()
    readme = workbook.active
    readme.title = "README"
    notes = [
        ("Philippines FY2025 — BoardEx extraction checkpoint", ""),
        ("Status", "DRAFT. BoardEx and Bloomberg files only; no external research performed."),
        ("Companies", "All Bloomberg securities, including those without a BoardEx match; Source = BoardEx where matched."),
        ("Foreign_Managers", "Reported foreign-national and UNKNOWN role records. Filipino records are retained in BoardEx_All_Managers."),
        ("BoardEx_All_Managers", "Every input BoardEx role record; one source row per output row. Combined titles remain unsplit."),
        ("BoardEx_People", "One person per company; the same director ID identifies a person across roles and companies."),
        ("Foreign_Nationals", "Records with a disclosed non-Filipino nationality; role eligibility and FY2025 service still need review."),
        ("Missing_Nationality", "Rows with no usable disclosed nationality. Missing is never coded as Filipino or zero."),
        ("Source", "BoardEx; nationality is transcribed from the supplied file, not independently verified against issuer filings."),
        ("Source locators", "Source_Sheet, Source_Row, and Nationality_Source_Cell locate evidence in the input Excel. Page is blank; no PDF page exists."),
        ("Evidence_Quote", "Verbatim nationality cell value. Person, position, and dates are in the same source row."),
        ("Nationality", "English country name translated from BoardEx Nationality. Original wording is preserved in Nationality_Raw and BoardEx_Raw."),
        ("Is_Foreign", "1 = source reports non-Filipino nationality; 0 = source reports Filipino; blank = unknown. This is a person-level field."),
        ("Company flags", "Foreign_Manager, Foreign_Manager_Core, and final manager counts are blank pending review. BoardEx counts are supplied separately."),
        ("Ownership", "Ownership_Type = REVIEW; no ownership measure has been collected. In_Scope and Manager_Search await the ownership/universe checkpoint."),
        ("Flag_Status", "NOT_SEARCHED means the full research workflow is pending, including for companies with BoardEx extraction."),
        ("Role_Group", "Provisional: Board if BoardEx brdposition=Yes; otherwise Executive if leadershipteam=Yes. Other roles remain unclassified pending review."),
        ("Dates", "1900-01-02, 9000-01-01 and 9999-12-31 are special source values, kept in raw fields and left blank in normalized dates."),
        ("Date flags", "Original BoardEx codes are retained. Their precision meanings have not been verified; source dates are not asserted to be exact."),
        ("FY2025", "The input filename labels the export 2025. Date checks flag issues; they do not independently establish service in 2025."),
        ("FY2025 and listed entities", "Count eligible positions held at any time in 2025, including roles that ended during the year. Record the resignation/departure time when the source provides it, preserving stated precision; leave it blank when undisclosed. Attribute each role to the sampled listed issuer where it was actually held. A listed subsidiary in the sample is counted separately from its listed parent."),
        ("Unlisted subsidiaries", "Positions held only at unlisted subsidiaries are out of scope regardless of country. Record UNLISTED_SUBSIDIARY_ONLY with entity, reason, and PDF page or BoardEx row; preserve the source record. Unclear entity/listing status remains unresolved."),
        ("Management_Include", "Blank pending manual eligibility review. BoardEx companyname and headquarters country do not prove the employer for every described role. Confirm listed issuer attribution, role level, combined positions, and committee-only roles."),
        ("Reviewed_On", "Blank: extraction is not a manual source verification. Extraction timestamp is recorded below."),
        ("Schema", "Vietnam main-sheet columns retained in order; Company_Name_VN renamed Company_Name_Local. BoardEx audit columns appended."),
        ("Raw sheets", "BoardEx_Raw and Bloomberg_Raw retain original cell values, row order, and number formats."),
        ("No inference", "No nationality inferred from names, photos, headquarters, or company ownership."),
        ("Extracted at UTC", stamp),
    ] + [(key, value) for key, value in summary.items() if isinstance(value, int)]
    for row in notes:
        readme.append(row)
    readme.column_dimensions["A"].width = 43
    readme.column_dimensions["B"].width = 110
    for row in readme:
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    table_sheet(workbook, "Companies", companies, company_fields + company_extra)
    table_sheet(workbook, "Foreign_Managers", foreign_managers, manager_fields + ROLE_EXTRA)
    table_sheet(workbook, "Coverage_Log", coverage, list(coverage[0]))
    table_sheet(workbook, "BoardEx_All_Managers", all_roles, manager_fields + ROLE_EXTRA)
    table_sheet(workbook, "BoardEx_People", people, list(people[0]))
    table_sheet(workbook, "Foreign_Nationals", reported_foreign, manager_fields + ROLE_EXTRA)
    table_sheet(workbook, "Missing_Nationality", missing, manager_fields + ROLE_EXTRA)
    copy_values(workbook, source, "BoardEx_Raw")
    copy_values(workbook, bb_sheet, "Bloomberg_Raw")
    workbook_path = output / "Philippines_2025_Foreign_Managers_BoardEx_Extract.xlsx"
    pending_path = workbook_path.with_name(workbook_path.stem + ".pending.xlsx")
    workbook.save(pending_path)
    preserve_raw_numeric_values(pending_path, [
        ("BoardEx_Raw", boardex_path, source.title),
        ("Bloomberg_Raw", bloomberg_path, bb_sheet.title),
    ])

    # Validate the saved artifact, including complete source value preservation.
    saved = load_workbook(pending_path, read_only=True, data_only=True)
    checks = []
    def check(name, ok, detail=""):
        checks.append({"Check": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})
    for title, original in (("BoardEx_Raw", source), ("Bloomberg_Raw", bb_sheet)):
        check(title + "_values", list(saved[title].values) == list(original.values))
    check("all_role_rows_preserved", saved["BoardEx_All_Managers"].max_row - 1 == len(source_rows))
    check("unique_record_ids", len({r["BoardEx_Record_ID"] for r in all_roles}) == len(source_rows))
    check("all_bloomberg_rows_preserved", saved["Companies"].max_row - 1 == len(securities))
    check("every_boardex_company_matched_once", len(company_match) == len({clean(r["companyid"]) for _, r in source_rows}))
    check("nationality_partition", len(missing) + len(reported_foreign) + summary["filipino_role_records"] == len(source_rows))
    check("unknown_is_never_zero", all(r["Is_Foreign"] == "" for r in all_roles if r["Nationality"] == "UNKNOWN"))
    check("no_placeholder_normalized_dates", all(not r[k] or 1901 <= int(r[k][:4]) < 2100 for r in all_roles for k in ("Appointed_Date", "Resigned_Date")))
    check("company_flags_remain_pending", all(r["Foreign_Manager"] == "" and r["Foreign_Manager_Core"] == "" for r in companies))
    check("nationality_matches_source", all(r["Nationality_Raw"] == clean(source_rows[i][1].get("BoardEx Nationality")) for i, r in enumerate(all_roles) if r["Nationality_Status"] == "SOURCE_DISCLOSED"))
    check("input_files_unchanged", before == {str(p): checksum(p) for p in (boardex_path, bloomberg_path)})
    csv_write(data / "boardex_roles.csv", all_roles, manager_fields + ROLE_EXTRA)
    csv_write(data / "companies_boardex.csv", companies, company_fields + company_extra)
    csv_write(data / "boardex_people.csv", people, list(people[0]))
    csv_write(data / "extraction_qa.csv", checks, ["Check", "Result", "Detail"])
    summary["qa_checks"] = len(checks)
    summary["qa_violations"] = sum(c["Result"] == "FAIL" for c in checks)
    (data / "extraction_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if summary["qa_violations"]:
        raise RuntimeError(f"Extraction validation failed: {checks}")
    saved.close()
    pending_path.replace(workbook_path)
    print(json.dumps({"workbook": str(workbook_path), **summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boardex", type=Path, required=True)
    parser.add_argument("--bloomberg", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=PROJECT.parent / "vietnam/output/1_Vietnam_2025_Foreign_Managers.xlsx")
    parser.add_argument("--output", type=Path, default=PROJECT / "output")
    run(parser.parse_args())
