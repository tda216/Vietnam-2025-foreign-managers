# Handover report – Listed companies and foreign-national managers, Indonesia FY2025

Updated: 11 November 2026 · Data file: `Indonesia_2025_Foreign_Managers.xlsx` (built by `id10_build_workbook.py`,
sheet `QA` = 0 violations on all 10 checks; manual QA sample in sheet `QA_Sample`)

---

## 1. Conclusions

**Of the 753 LOCAL listed companies in the sample (foreign ownership ≤ 50 % at 31 December 2025), 159 (21.1 %) had at
least one foreign-national manager at some time in 2025 (`Foreign_Manager = 1`).** 152 (20.2 %) have a foreign member
of the Board of Commissioners or the Board of Directors (`Foreign_Manager_Core = 1`). Counting only the 731 firms with a
conclusion (flag 1 or 0), the shares are 21.8 % and 20.8 %.

The sample is the 806 LOCAL firms minus 53 firms that have no AR 2025 and are delisted or suspended by IDX (owner
decision, 11 November 2026; column `In_Sample`, section 6). Their rows are kept; 11 of them are re-checked in 2027.

| LOCAL companies in the sample (753) | Companies | Meaning |
|---|---:|---|
| `Foreign_Manager = 1` | 159 | at least one foreign manager, any level |
| `Foreign_Manager_Core = 1` | 152 | foreign Commissioner (Board) or Director (Executive) |
| Foreign member of the Board of Commissioners (Dewan Komisaris) | 97 | 29 of them have a foreign President Commissioner |
| Foreign member of the Board of Directors (Direksi) or C-suite | 98 | 21 of them have a foreign President Director |
| Foreign Executive or Other_Manager | 112 | 98 Executive + 24 Other_Manager, 10 firms in both; 50 of the 112 also have a foreign Commissioner |
| `Foreign_Manager = 0` | 572 | none found in the AR 2025 (see the limits in section 6) |
| `Foreign_Manager` blank | 22 | `UNRESOLVED`: the Board / Direksi profiles state no nationality |
| Not in the sample (`In_Sample = 0`) | 53 | `NO_SOURCE`: no AR 2025; delisted (13) or suspended by IDX (40) for not filing the audited accounts |

Main points:

1. **Indonesia has a two-tier board.** Commissioners (`Board`) supervise and Directors (`Executive`) run the company.
   Nobody can hold both seats, so there is no Board/Executive overlap at person level. In the 112 firms with a foreign
   executive or other manager, the foreign executives and the foreign Commissioners are always different people.
2. **The nationalities are mostly Asian: 29 groups.** Counting the 333 distinct foreign persons, the largest groups are
   Singapore (49), Japan (46), India (38), Malaysia (38), Australia (27), Thailand (20), United Kingdom (20),
   South Korea (19), United States (15), China (15) and the Philippines (13).
3. **Large firms have a much higher rate.** Of the 161 LOCAL firms among the 200 largest by market capitalisation, 60
   (37 %) have `Foreign_Manager = 1`, against 21 % for the whole sample.
4. **The evidence is almost all direct.** 333 of the 335 rows cite a document field that states the nationality: an
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
| **Foreign_Managers** | person × position (335 rows, 333 persons) | **Main**: names, positions, nationality, source, PDF page, verbatim quote |
| README | – | Column definitions and the rules applied; read once |
| FO_Classification | in-scope company | How FO was settled: KSEI bounds, AR table, named holders, or hand reading |
| Ownership_AR_Manual | hand-read FO value | Page, verbatim quote (or `[page image]` transcription of a scan) and reasoning for 91 firms |
| Company_Level_Evidence | 1 row | NCKL: a company-level statement on a foreign member |
| Candidate_Decisions | name | Why a screened name was not recorded (not FY2025, not foreign, not a manager, no nationality stated, …) |
| AR_File_Reviews | file | Files rejected or confirmed by hand: AR 2024 instead of 2025 (25 files), AR 2022 (5 files), a parent's report, files damaged on IDX |
| No_Source_Reasons | company without an AR 2025 | Why: the IDX suspension or delisting, plus the trail of every search (IDX repository, IDX announcements, website, rejected files) |
| Listing_Events_2026 | code × event | The IDX suspensions and delisting used above: announcement number, date, news URL, verbatim quote |
| Label_Reviews | company | Company-level reviews of the nationality labels: Board profiles without nationality (→ `UNRESOLVED`), labels only in page graphics |
| QA_Sample | sampled item | The manual QA sample and its verdicts (section 5) |
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

In **Companies**, filter on `In_Sample = 1`. This gives 753 companies: the 806 LOCAL firms (`In_Scope = 1`,
`FO_Class = LOCAL`) minus the 53 excluded firms (`In_Sample = 0`, reason in `Sample_Note`).

- `FO_Class` is based on foreign ownership at 31 December 2025: `LOCAL` (≤ 50 %), `FOREIGN_MAJORITY` (> 50 %), or
  `REVIEW` (not settled: 8 firms).
- `FO_Pct_AR` holds the settled value or bound as text. For example, `<=44.77` means that named Indonesian holders own
  at least 55.23 %. `FO_Lower_KSEI` / `FO_Upper_KSEI` are the bounds from KSEI custody data.

### 3.2 The flags

| Column | Meaning |
|---|---|
| **`Foreign_Manager_Core`** (recommended main variable) | 1 if a foreign national sat on the Board of Commissioners or the Board of Directors (or held a C-suite post) at any time in 2025. These positions were searched in the same way in every firm, so the variable is **comparable across firms**. 152 LOCAL firms = 1 |
| `Foreign_Manager` | As above, plus committee-only members, heads of units and senior officers named in the AR (`Other_Manager`). 159 LOCAL firms = 1. Other managers are only known when the AR lists them, so use this as a secondary variable |
| `Flag_Status` | `FOUND`, `NONE_FOUND`, `UNRESOLVED`, `NO_SOURCE`, `FO_REVIEW`, `NOT_SEARCHED_FM`, `OUT_OF_SCOPE` |
| **`In_Sample`**, `Sample_Note` | 1 = LOCAL firm in the sample (753); 0 = excluded `NO_SOURCE` firm with its IDX status (`EXCLUDED_DELISTED`, `EXCLUDED_LONG_SUSPENSION`, `EXCLUDED_SUSPENDED_2026_LATE_FS2025; re-check IDX in 2027`); blank = not LOCAL |
| `Foreign_Manager_Rows`, `Foreign_Board_Exec_Rows` | Number of rows in Foreign_Managers, total and Board/Executive |

**A blank cell is missing data, not 0.** Keep blanks as missing in Stata, R or Python.

### 3.3 Robustness by evidence

| Definition | Flag = 1 | Flag = 0 | Blank |
|---|---:|---:|---:|
| A. Direct evidence only (document field, company-level statement) | 157 | 572 | 24 |
| B. All (= `Foreign_Manager`, adds the 2 `INFERRED_WEAK` firms ACRO and SCCO) | 159 | 572 | 22 |

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

df = co[co["In_Sample"] == 1].copy()     # 753 LOCAL firms in the sample

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
   - For the rest, the AR 2025 shareholder composition: 141 tables and 88 named-holder lists accepted under fixed rules.
   - 91 firms read by hand, 34 of them from the share registrar's December 2025 report, which splits scrip and KSEI
     holdings into national and foreign.
   - FO counts the **legal nationality** of the holder: an Indonesian PT is local even when foreign-owned.
3. **Who counts.**
   - Commissioners, Directors and C-suite officers of the listed company itself, at any time in calendar 2025.
   - Committee-only members and senior officers named in the AR count as Other_Manager.
   - Positions at subsidiaries do not count.
4. **Sources for people and nationality.**
   - The AR 2025: 132 rows from company websites, 189 from IDX (4 of them from ARs filed only as IDX announcements).
   - The AR 2024 from IDX: 13 rows for members who left during 2025, and 1 row (CEKA) where IDX holds only the AR 2024
     (published April 2025; shared rule: AR 2024 as a last resort, with a note).
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
  - no flag set outside LOCAL firms;
  - no cited page that says the person was first appointed in 2026;
  - no file used as the AR 2025 that names only the 2024 report.
- **Quote check:** `id_add_records.py` refuses any record whose quote is not on the cited page.
- **Page images:** viewed for every multi-profile, OCR or graphic-name page before recording.
- **Download check:** every PDF is checked for a complete file (`%%EOF`). 43 IDX reports that had been saved
  truncated were completed; 2 are damaged in the IDX report repository (DEWA, PCAR), whose complete copies were
  then found among the IDX announcements.
- **Re-check of automatic FO rows:** six had read the wrong table (a subsidiary table, an assets-under-management
  split, the issuer's own name). They were re-read by hand, and the screen now skips such rows.
- **Manual QA sample** (10 November 2026; `id11_qa_sample.py`, seed 20261110; verdicts in sheet `QA_Sample`):
  - 30 random rows of Foreign_Managers re-read in the source: 28 correct, 1 minor (a misspelt name, corrected) and
    1 error: a commissioner first appointed in January 2026 (TPIA). A scan of all rows found 2 more TPIA members
    appointed in 2026; the 3 rows were removed (`NOT_FY2025`) and a QA check now catches this case.
  - 30 random `NONE_FOUND` firms re-read: 29 correct, 1 error (KOCI: the only "Indonesia" label was an HR sentence;
    the Board profiles state no nationality). A follow-up review of the 43 `NONE_FOUND` firms whose labels did not
    sit next to a Board / Direksi title found 4 more such firms (MBSS, MEJA, BBMD, IKAI); all 5 are now `UNRESOLVED`
    (sheet `Label_Reviews`).
  - The review also showed that 15 files of 14 firms were the AR 2024 and not the AR 2025 (the IDX "2025" entry of
    a few issuers is their 2024 report, and some website files carry a 2025 publication date). They were rejected;
    7 firms now use their real AR 2025 from IDX (one more foreign commissioner found, OMRE), the others are
    `NO_SOURCE` except CEKA (see section 4). A QA check now flags any such file.
  - Reading: 1 error in 30 in each half is an observed rate of about 3 %, with a 95 % upper bound of about 17 % (exact
    binomial); the errors found were fixed together with every other case of the same kind, so the remaining rate
    should be lower, but the sample cannot show by how much.

---

## 6. Limits to keep in mind

1. **`NONE_FOUND` relies on stated nationality.** A foreign member whose profile states no nationality is not found.
   The 22 `UNRESOLVED` firms have Board / Direksi profiles without any nationality label (e.g. TOTO, whose Japanese
   parent owns 38 %). Board labels that exist only in page graphics are not read by the screen; such firms were
   checked by hand only in the QA review (`Label_Reviews`).
2. **Members who left during 2025:**
   - 501 departure mentions had no nationality nearby in the AR 2025.
   - 161 were Indonesian and 29 foreign in the AR 2024; the foreign ones are recorded or decided.
   - 289 remain open in `Open_Items`: not found in the AR 2024, no label, or no AR 2024. Many of these "names" are
     screening noise, but real foreign departures may be among them.
3. **8 firms with FO not settled** (`FO_REVIEW`):
   - CTTH: foreign 46.4–52.0 %; the AR table's 57.1 % fits neither source.
   - INPC, OBAT, RUNS: holders' nationality unknown.
   - MTRA, PLAS, UNIT: no AR and no December register report; all three are suspended by IDX for not filing the
     audited 2025 accounts.
   - CNTB (Century Textile, series B shares): delisted by IDX on 30 July 2026 at the company's request (go-private).
4. **53 LOCAL firms without an AR 2025** (`NO_SOURCE`, sheet `No_Source_Reasons`). **Every one of them is on an IDX
   suspension list for not filing its audited accounts for 2025** (announcement Peng-S-00020/BEI.PLP/06-2026,
   suspension from 30 June 2026, 51 firms; Peng-S-00021/BEI.PLP/07-2026, Acceleration Board, from 1 July 2026: MENN,
   SOUL). The news pages were opened and quoted (sheet `Listing_Events_2026`). Each firm was searched in the IDX report
   repository, the IDX announcements of 1 January–11 November 2026 and the company website. Three of them (CPRI,
   POOL, PMMP) filed only an older AR (2022 or 2024) in 2026.
   - A suspension is not a delisting: IDX lifts it only when the issuer has filed the overdue reports, paid the fines
     and resolved the cause, and even then at its discretion (IDX, KabarBursa 8 Apr 2026); after 24 months of
     suspension IDX may delist. Status in November 2026 (column `Status_Group`, from the IDX announcement titles
     2024–2026 and the news pages in `Listing_Events_2026`):
     - **13 delisted on 10 November 2026** (Peng-DEL-00001/BEI.PP1/04-2026 and two others of 10 April 2026): 5
       bankrupt (COWL, SRIL, TOYS, SBAT, TELE) and 8 suspended for more than 50 months (LCGP, SUGI, MABA, LMAS, SKYB,
       ENVY, TRIL, DUCK). MTRA, PLAS and UNIT (FO open) were delisted on the same day, CNTB on 30 July 2026.
     - **29 under long suspension**: on the IDX list of issuers suspended for more than 6 months at 30 June 2026
       (potential delisting), or suspended since before July 2025. Several have been suspended since 2019–2020 (KBRI,
       BTEL, ARMY, TRAM, HOME, RIMO, POOL, NUSA).
     - **11 suspended only in 2026 for the late FS 2025** (ARKA, BHAT, COAL, DEAL, INCF, JMAS, MREI, PTDU, RAFI,
       SOUL, TAYS): they filed their 2024 accounts normally in 2025. COAL, INCF and JMAS have filed annual accounts
       since (May, September and 5 November 2026), so their AR 2025 may still appear.
   - **Owner decision (11 November 2026): all three groups are excluded from the sample** used for the share of firms
     with foreign managers (`In_Sample = 0`, `Sample_Note`). No row is deleted. The 11 late filers are kept for a
     re-check of IDX in 2027 (`Open_Items`, type `RECHECK_2027`). `Foreign_Manager` stays blank, never 0.
   - The 11 November 2026 search also found 22 more ARs 2025 that had been filed only as IDX announcements (not in
     the IDX report repository): 3 of these firms have a foreign manager (GIAA, MNCN, DEWA) and 19 have none.
   - Not every suspended firm lacks an AR: 14 suspended LOCAL firms published their AR 2025 later or on their website
     (e.g. BOSS, CRAB, HILL, INAF, LCKM, SWAT) and keep their flag.
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
  - `company_level_evidence.csv`: company-level statements;
  - `label_reviews.csv`: company-level reviews of the nationality labels;
  - `qa_review.csv`: the manual QA sample verdicts.
- Add a batch with `.venv/bin/python -I indonesia/pipeline/id_add_records.py <batch.json>`. It checks quotes, role
  groups and nationality names before writing.
- Then run `id06_screen.py`, `id07_fo_classify.py`, `id08_propose.py`, `id09_departures.py`,
  `id09b_departures_ar2024.py` and `id10_build_workbook.py`, all from the project root with `.venv/bin/python -I`. The
  new workbook carries its own QA sheet.
- The step list and every owner decision are in `indonesia/AGENTS.md`; open questions go to
  `indonesia/OPEN_DECISIONS.md`.
