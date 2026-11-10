# Handover report – Listed companies and foreign-national managers, Indonesia FY2025

Updated: 10 November 2026 · Data file: `Indonesia_2025_Foreign_Managers.xlsx` (built by `id10_build_workbook.py`,
sheet `QA` = 0 violations on all 8 checks)

---

## 1. Conclusions

**Of the 805 LOCAL listed companies (foreign ownership ≤ 50 % at 31 December 2025), 155 (19.3 %) had at least one
foreign-national manager at some time in 2025 (`Foreign_Manager = 1`).** 148 of them have a foreign member of the
Board of Commissioners or the Board of Directors (`Foreign_Manager_Core = 1`).

| LOCAL companies (805) | Companies | Meaning |
|---|---:|---|
| `Foreign_Manager = 1` | 155 | at least one foreign manager, any level |
| `Foreign_Manager_Core = 1` | 148 | foreign Commissioner (Board) or Director (Executive) |
| Foreign member of the Board of Commissioners (Dewan Komisaris) | 94 | 29 of them have a foreign President Commissioner |
| Foreign member of the Board of Directors (Direksi) or C-suite | 97 | 21 of them have a foreign President Director |
| Foreign Executive or Other_Manager | 111 | 97 Executive + 24 Other_Manager, 10 firms in both; 50 of the 111 also have a foreign Commissioner |
| `Foreign_Manager = 0` | 564 | none found in the AR 2025 (see the limits in section 6) |
| `Foreign_Manager` blank | 86 | 69 `NO_SOURCE` (no AR 2025), 17 `UNRESOLVED` (AR profiles state no nationality) |

Main points:

1. **Indonesia has a two-tier board.** Commissioners (`Board`) supervise and Directors (`Executive`) run the company.
   Nobody can hold both seats, so there is no Board/Executive overlap at person level. In the 111 firms with a foreign
   executive or other manager, the foreign executives and the foreign Commissioners are always different people.
2. **The nationalities are mostly Asian: 29 groups.** Counting the 331 distinct foreign persons, the largest groups are
   Singapore (47), Japan (46), Malaysia (38), India (37), Australia (27), Thailand (23), South Korea (19),
   United Kingdom (18), United States (15), China (15) and the Philippines (13).
3. **Large firms have a much higher rate.** Of the 161 LOCAL firms among the 200 largest by market capitalisation, 58
   (36 %) have `Foreign_Manager = 1`, against 19 % for all LOCAL firms.
4. **The evidence is almost all direct.** 331 of the 333 rows cite a document field that states the nationality: an
   AR profile, a diversity table, or the foreign-worker (TKA) table. Two rows are `INFERRED_WEAK`: two members who
   left in 2025, a Japanese and a Korean name, for whom no source states the nationality (ACRO, SCCO).
5. **`Foreign_Manager = 0` means "none found", not "every member verified".** A firm is `NONE_FOUND` when its AR 2025
   was screened, its profiles carry nationality labels, and none of them is foreign.
6. **Foreign-majority firms were not searched (owner decision).** Unlike Vietnam, there is no 50–55 % borderline band:
   the 139 `FOREIGN_MAJORITY` firms have no manager data.

---

## 2. What is delivered

### 2.1 Main file: `Indonesia_2025_Foreign_Managers.xlsx`

| Sheet | One row per | Use |
|---|---|---|
| **Companies** | Bloomberg security (1,015 rows; 953 in scope) | **Main**: FO class, FO evidence and the company flags |
| **Foreign_Managers** | person × position (333 rows, 331 persons) | **Main**: names, positions, nationality, source, PDF page, verbatim quote |
| README | – | Column definitions and the rules applied; read once |
| FO_Classification | in-scope company | How FO was settled: KSEI bounds, AR table, named holders, or hand reading |
| Ownership_AR_Manual | hand-read FO value | Page, verbatim quote (or `[page image]` transcription of a scan) and reasoning for 89 firms |
| Company_Level_Evidence | 1 row | NCKL: a company-level statement on a foreign member |
| Candidate_Decisions | name | Why a screened name was not recorded (not FY2025, not foreign, not a manager, no nationality stated, …) |
| AR_File_Reviews | file | Files rejected or confirmed by hand: AR 2024 instead of 2025, a parent's report, a file damaged on IDX |
| Departures_AR2024 | departed name | Members who left in 2025: what the AR 2024 says about their nationality |
| Open_Items | item | What remains open (section 6) |
| QA | check | The automatic checks and their counts |

### 2.2 Other documents

- `HANDOVER_REPORT.md`: this report.
- `methodology.md`: the full methodology (sources, rules, owner decisions, results, limits).
- The repository, which holds the code (`indonesia/pipeline/`) and every hand-reviewed input and batch
  (`indonesia/data/manual/`). The downloaded PDFs (about 17 GB in `indonesia/raw/`) are not in the repository; the
  data team keeps them and provides them on request.

---

## 3. How to use the data

### 3.1 Choose the sample

In **Companies**, filter on `In_Scope = 1` and `FO_Class = LOCAL`. This gives 805 companies.

- `FO_Class` is based on foreign ownership at 31 December 2025: `LOCAL` (≤ 50 %), `FOREIGN_MAJORITY` (> 50 %), or
  `REVIEW` (not settled: 9 firms).
- `FO_Pct_AR` holds the settled value or bound as text. For example, `<=44.77` means that named Indonesian holders own
  at least 55.23 %. `FO_Lower_KSEI` / `FO_Upper_KSEI` are the bounds from KSEI custody data.

### 3.2 The flags

| Column | Meaning |
|---|---|
| **`Foreign_Manager_Core`** (recommended main variable) | 1 if a foreign national sat on the Board of Commissioners or the Board of Directors (or held a C-suite post) at any time in 2025. These positions were searched in the same way in every firm, so the variable is **comparable across firms**. 148 LOCAL firms = 1 |
| `Foreign_Manager` | As above, plus committee-only members, heads of units and senior officers named in the AR (`Other_Manager`). 155 LOCAL firms = 1. Other managers are only known when the AR lists them, so use this as a secondary variable |
| `Flag_Status` | `FOUND`, `NONE_FOUND`, `UNRESOLVED`, `NO_SOURCE`, `FO_REVIEW`, `NOT_SEARCHED_FM`, `OUT_OF_SCOPE` |
| `Foreign_Manager_Rows`, `Foreign_Board_Exec_Rows` | Number of rows in Foreign_Managers, total and Board/Executive |

**A blank cell is missing data, not 0.** Keep blanks as missing in Stata, R or Python.

### 3.3 Robustness by evidence

| Definition | Flag = 1 | Flag = 0 | Blank |
|---|---:|---:|---:|
| A. Direct evidence only (document field, company-level statement) | 153 | 564 | 88 |
| B. All (= `Foreign_Manager`, adds the 2 `INFERRED_WEAK` firms ACRO and SCCO) | 155 | 564 | 86 |

Under A, the two inferred firms are left blank, not set to 0.

### 3.4 The Foreign_Managers sheet

- Join with Companies on `Code`.
- `Raw_Position` keeps the wording of the source. `Role_Group` is the normalised group:
  - Board = Dewan Komisaris.
  - Executive = Direksi and C-suite.
  - Other_Manager = committee-only members, Sharia board, heads of units, general managers listed in the AR.
- `Nationality` is the English country name; `Nationality_Raw` is the source wording. One row has
  `Nationality = UNKNOWN` (stated "foreign" without a country), still with `Is_Foreign = 1`.
- `Appointed_Date` / `Resigned_Date` are given when the source gives them. 14 rows are members who left during 2025:
  `Note` starts with `LEFT_DURING_2025`, the nationality comes from their AR 2024 profile, and the leaving date from
  the AR 2025.
- **`Management_Include` is blank on purpose.** The research team decides whether committee-only members (15 rows,
  `BOARD_COMMITTEE_ONLY`) and other officers count as managers in the study.

### 3.5 Trace a row back to its source

- `Evidence_Quote` is the verbatim text that states the position and nationality. It was checked by machine against
  the page text when it was recorded.
- `Local_File` and `Page` give the file and the **PDF page, counted from 1** (not the printed page number).
  `Source_URL` is the download link (company website, or `www.idx.id`).
- When the name or the value sits in a graphic, `Note` says the page image was viewed.

### 3.6 Sample code (Python, pandas)

```python
import pandas as pd

f = "Indonesia_2025_Foreign_Managers.xlsx"
co = pd.read_excel(f, sheet_name="Companies")
fm = pd.read_excel(f, sheet_name="Foreign_Managers")

df = co[(co["In_Scope"] == 1) & (co["FO_Class"] == "LOCAL")].copy()     # 805 firms

# definition A (direct evidence only): firms whose only rows are INFERRED become missing
fm = fm[pd.to_numeric(fm["Is_Foreign"], errors="coerce") == 1]
direct = set(fm.loc[fm["Evidence_Type"] != "INFERRED", "Code"]) | set(
    pd.read_excel(f, sheet_name="Company_Level_Evidence")["Code"])
df["FM_direct"] = df["Foreign_Manager"].where(~((df["Foreign_Manager"] == 1) & ~df["Code"].isin(direct)))
```

---

## 4. Method in brief

The details are in `methodology.md`.

1. **Universe.** The Bloomberg list of 1,015 IDX securities has 953 companies in scope. Out of scope (62):
   - funds, ETFs and DIRE (51);
   - foreign-listed lines (6);
   - codes not listed in 2025 (5).
2. **Foreign ownership at 31 December 2025.** Settled in this order:
   - KSEI custody data (30 December 2025) gives lower/upper bounds and settles 625 firms.
   - For the rest, the AR 2025 shareholder composition: 142 tables and 88 named-holder lists accepted under fixed rules.
   - 89 firms read by hand, 32 of them from the share registrar's December 2025 report, which splits scrip and KSEI
     holdings into national and foreign.
   - FO counts the **legal nationality** of the holder: an Indonesian PT is local even when foreign-owned.
3. **Who counts.**
   - Commissioners, Directors and C-suite officers of the listed company itself, at any time in calendar 2025.
   - Committee-only members and senior officers named in the AR count as Other_Manager.
   - Positions at subsidiaries do not count.
4. **Sources for people and nationality.**
   - The AR 2025: 132 rows from company websites, 188 from IDX.
   - For members who left during 2025, the AR 2024 from IDX: 13 rows.
   - Scanned pages were OCR'd (Tesseract ind+eng). Every page with several profiles, or with names in graphics, was
     checked on the page image.
5. **Nationality rule.** Only a stated nationality counts: "Warga Negara X", "Kewarganegaraan / Nationality X",
   "X citizen", or a diversity or foreign-worker table.
   - A name alone never counted, except for 2 departed members after a web search (owner rule 10a).
   - Indian- and Chinese-origin names were not inferred: one such person was shown to be an Indonesian citizen.
6. **Nothing is deleted.** Every dropped name has a decision and a reason. Missing values are never set to 0.

---

## 5. Quality control

- **Automatic checks** (sheet `QA`, 0 violations):
  - every record is in a LOCAL firm and has a quote and a page;
  - valid role groups;
  - no member who left before 2025 or was appointed after 2025;
  - no duplicates;
  - no 0 flag without a source;
  - no flag set outside LOCAL firms.
- **Quote check:** `id_add_records.py` refuses any record whose quote is not on the cited page.
- **Page images:** viewed for every multi-profile, OCR or graphic-name page before recording.
- **Download check:** every PDF is checked for a complete file (`%%EOF`). 43 IDX reports that had been saved
  truncated were completed; 2 are damaged on IDX itself (DEWA, PCAR).
- **Re-check of automatic FO rows:** six had read the wrong table (a subsidiary table, an assets-under-management
  split, the issuer's own name). They were re-read by hand, and the screen now skips such rows.
- **Not done yet:** a random manual QA sample (records and `NONE_FOUND` firms).

---

## 6. Limits to keep in mind

1. **`NONE_FOUND` relies on stated nationality.** A foreign member whose profile states no nationality is not found.
   The 17 `UNRESOLVED` firms have profiles without any nationality label (e.g. TOTO, whose Japanese parent owns 38 %).
2. **Members who left during 2025:**
   - 501 departure mentions had no nationality nearby in the AR 2025.
   - 161 were Indonesian and 29 foreign in the AR 2024; the foreign ones are recorded or decided.
   - 290 remain open in `Open_Items`: not found in the AR 2024, no label, or no AR 2024. Many of these "names" are
     screening noise, but real foreign departures may be among them.
3. **9 firms with FO not settled** (`FO_REVIEW`):
   - CTTH: foreign 46.4–52.0 %; the AR table's 57.1 % fits neither source.
   - INPC, OBAT, RUNS: holders' nationality unknown.
   - CNTB, KUAS, MTRA, PLAS, UNIT: no AR and no December register report.
4. **69 LOCAL firms without an AR 2025:** not on IDX when queried again on 10 November 2026, cover letters only, or a
   file damaged on IDX.
5. **Foreign-majority firms are not searched**, so they cannot serve as a comparison group for managers.
6. **Legal nationality vs. registrar status.**
   - EAST: the founder is a Singapore citizen in the AR, while the registrar's form marks him "L" (local account).
     Legal nationality was used, giving foreign ownership of 72 %.
   - KOKA (50.27 %) is just over the line.
7. **Other_Manager coverage is uneven** across firms. Use `Foreign_Manager_Core` as the main variable.
8. **Calendar 2025** is used for managers, including the six firms with a non-December year end (e.g. AMOR, which
   ends in June).

---

## 7. Updating and rebuilding

- All facts are added through `indonesia/data/manual/` (each batch is kept in `batches/`):
  - `manager_records.csv`: foreign-manager rows;
  - `candidate_decisions.csv`: why a name was not recorded;
  - `ownership_ar.csv`: hand-read FO;
  - `ar_file_reviews.csv`: rejected or confirmed files;
  - `company_level_evidence.csv`: company-level statements.
- Add a batch with `.venv/bin/python -I indonesia/pipeline/id_add_records.py <batch.json>`. It checks quotes, role
  groups and nationality names before writing.
- Then run `id06_screen.py`, `id07_fo_classify.py`, `id08_propose.py`, `id09_departures.py`,
  `id09b_departures_ar2024.py` and `id10_build_workbook.py`, all from the project root with `.venv/bin/python -I`. The
  new workbook carries its own QA sheet.
- The step list and every owner decision are in `indonesia/AGENTS.md`; open questions go to
  `indonesia/OPEN_DECISIONS.md`.
