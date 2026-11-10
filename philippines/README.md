# Philippines FY2025

> **Final result (7 Nov 2026):** [output/Philippines_2025_Foreign_Managers.xlsx](output/Philippines_2025_Foreign_Managers.xlsx), built by `pipeline/ph10_build_workbook.py` (run from the top-level folder: `.venv/bin/python -I philippines/pipeline/ph10_build_workbook.py`).
> - 257 LOCAL firms: 91 with a foreign manager (88 at board or executive level), 166 none found (updated 9 Nov 2026: ABS corrected to NONE_FOUND).
> - Career before appointment of the foreign executives: `data/manager_background.csv`.
> - Methodology (sources, report types, steps, decisions, results, limitations): [output/methodology.md](output/methodology.md).
> - Rules and owner decisions: [AGENTS.md](AGENTS.md).
> - Lessons for the next countries: [../NEW_COUNTRY_PLAYBOOK.md](../NEW_COUNTRY_PLAYBOOK.md).
>
> The text below describes the **5 Nov 2026 BoardEx extraction checkpoint** and is kept as history. That checkpoint is `output/Philippines_2025_Foreign_Managers_BoardEx_Extract.xlsx`; an identical earlier copy is in `output/archive/`.

## BoardEx extraction checkpoint (5 Nov 2026)

Prepared on 5 November 2026 using only the two user-supplied workbooks. No web research was performed. This is the initial data extraction, before ownership classification and manual verification of role eligibility and FY2025 service.

## Workbook

Open [Philippines_2025_Foreign_Managers_BoardEx_Extract.xlsx](output/Philippines_2025_Foreign_Managers_BoardEx_Extract.xlsx).

The main sheets follow the Vietnam workbook's column order. The country-specific `Company_Name_VN` column is renamed `Company_Name_Local`; additional BoardEx audit columns follow the standard columns. The existing `Source` column is populated with **BoardEx** for extracted records.

- **Companies:** all 289 Bloomberg securities. There are 156 exact ISIN matches to BoardEx and 133 securities without a match in the supplied extract.
- **Foreign_Managers:** 2,768 source role records: 193 with a disclosed non-Filipino nationality and 2,575 with nationality unknown. This follows Vietnam's convention of retaining foreign and UNKNOWN records in this sheet.
- **BoardEx_All_Managers:** all 5,393 original role records, including the 2,625 records reporting Filipino nationality. Nothing is deleted from the extraction.
- **BoardEx_People:** 5,209 company–person pairs, covering 4,184 distinct BoardEx people. A person can appear at more than one company.
- **Foreign_Nationals:** the 193 reported non-Filipino nationality records, representing 176 distinct people at 77 companies. These are source-reported nationalities, not final findings that all roles qualify for the study.
- **Missing_Nationality:** the 2,575 unresolved role records, representing 2,322 distinct people.
- **Coverage_Log:** company coverage and the source worksheet rows used.
- **BoardEx_Raw / Bloomberg_Raw:** copies of original cell values, source row order, and number formats.
- **README:** field definitions, extraction limitations, and summary counts.

BoardEx supplies nationality for 1,862 distinct people. No missing nationality can be filled from another row with the same BoardEx director ID; no conflicting nationality values were found for an ID. Nationality is not inferred from names, photographs, headquarters, or ownership.

The role description for Maidy Quinto at source row 1720 contains the wording “Subsidiary Operations Filipino Since Jun 2020 and Regional Operations Group Director for Luzon. Corporate Project Management Until June 2020”. This is retained in `Role_Description_Raw`; its context is ambiguous and the dedicated nationality field is undisclosed, so it has not been converted into a nationality finding.

## How to use the fields

Filter `Is_Foreign = 1` to see source-reported foreign nationalities. A numeric 0 means the source explicitly reports Filipino nationality; blank means unknown. `Nationality_Raw` preserves the source wording, while `Nationality` translates it into an English country name. Dual nationality is left blank because it is not independently established by this extract.

`Source = BoardEx`, `Local_File`, `Source_Sheet`, `Source_Row`, and `Nationality_Source_Cell` locate the evidence. `Evidence_Quote` preserves the nationality cell value verbatim. `Page` is blank because this evidence comes from Excel rather than a PDF. `Reviewed_On` is blank because an automated extraction is not manual evidence review.

`Manager_ID` is company-specific, as in the Vietnam dataset. `BoardEx_Director_ID` is the original identifier for linking the same person across companies. Each source role record is retained separately, with its original record ID. Combined position titles have not yet been split into separate study positions.

`Role_Group` is a provisional reading aid: BoardEx `brdposition = Yes` maps to Board; otherwise `leadershipteam = Yes` maps to Executive. Other roles remain unclassified. FY2025 includes anyone who held an eligible position at any time during 2025, including someone who resigned during the year. Record the departure time when the source provides it, at the source's stated precision; an undisclosed time remains blank. **Count each position at the sampled listed company where it was actually held.** A listed subsidiary in the sample receives its own record; the listed parent receives a separate record only for a role actually held there. Positions held only at unlisted subsidiaries are outside the study regardless of country. Record `UNLISTED_SUBSIDIARY_ONLY` with source PDF page or BoardEx row, while retaining every source row. If entity identity or listing status is unclear, leave eligibility unresolved. BoardEx `companyname` and `hocountryname` identify the source organisation but may not establish the employer for every position described in a text field. Role level, committee-only roles, advisors, and combined positions also require review.

All company ownership classifications are `REVIEW`, and final company flags and counts are blank. Source-reported nationality counts are shown separately in the `N_BoardEx_*` columns. All company `Flag_Status` values are `NOT_SEARCHED`, meaning that the full research workflow is pending. Neither a missing BoardEx match nor an undisclosed nationality is coded as a negative finding.

## Dates

The source includes special dates and date flags whose full precision definitions have not been verified:

- 1,135 role records use 2 January 1900 for the start date.
- 4,593 role records use a far-future end date: 1 January 9000 or 31 December 9999.

These values are preserved in `Start_Date_Raw`, `End_Date_Raw`, the original flag columns, and `BoardEx_Raw`. They are blank in normalized appointment/resignation fields. No sentinel has been interpreted as an actual appointment, resignation, or proof of continuing service.

`FY2025_Date_Check` distinguishes recorded date overlap from cases needing start/end-date review. The file is labelled 2025 by its supplied filename; actual FY2025 service still requires the agreed review. No source rows were excluded on date grounds.

## Reproduction and validation

The original workbooks remain at their supplied locations. Their SHA256 hashes and extraction timestamp are recorded in `data/extraction_summary.json`. Generated data and workbooks are ignored by Git locally; the extraction code is separate from the Vietnam pipeline.

Install `openpyxl` in the local virtual environment and run from the repository root:

```bash
.venv/bin/python -I philippines/pipeline/extract_boardex.py \
  --boardex '/Users/thanh/Desktop/Researches/Broadex_Philippines_2025_with_Nationality.xlsx' \
  --bloomberg '/Users/thanh/Library/CloudStorage/OneDrive-Personal/Tien si - Thanh/Thanh data/Bloomberg-Philippines2025.xlsx'
```

The default schema template is `output/1_Vietnam_2025_Foreign_Managers.xlsx`; use `--template` to supply another Vietnam workbook with the same main sheets.

Extraction QA checks original cell-value preservation, complete record retention, unique source IDs, company matches, nationality partitions, missing-value handling, special dates, pending company flags, and unchanged input hashes. See `data/extraction_qa.csv`. These checks validate extraction only; they do not replace the final research QA or manual sample review.
