# AGENTS.md – Thailand FY2025 (country 2 of 5 – handed over 09/11/2026)

Study-wide rules, repo layout, setup and review lessons: [../AGENTS.md](../AGENTS.md). This file holds what is specific to Thailand.
Paths below are relative to `thailand/`; run the scripts from the repo root (`.venv/bin/python -I thailand/pipeline/<step>.py`).

Deliverables: `output/Thailand_2025_Foreign_Managers.xlsx` (contains Bloomberg + BoardEx; in git since 11/11/2026 by user decision,
licence risk accepted – rebuild and commit it after every change), `output/BAO_CAO_BAN_GIAO.md`, `output/methodology.md`.
Inputs (git-ignored, licensed): `Bloomberg-Thailan2025_9666.xlsx`, BoardEx roles `Broad-…_9300.xlsx`, BoardEx people `Thai-…_8540.xlsx`.
`data/boardex_people.csv` / `boardex_roles.csv` are derived copies of BoardEx and stay out of git; `data/records_auto.csv` is kept in git (owner decision 09/11/2026).
Scripts put `thailand/pipeline` first on `sys.path`, then `shared/`, so `common.py`, `archives.py` and `xlsx_tables.py` bind to the Thailand `config.py`.

## Sources and access rules

- **SEC Form 56-1 One Report 2025** is the main source: a fixed template prints `Thai nationality: Yes/No` (`สัญชาติไทย: ใช่/ไม่ใช่`)
  for every director (also those who left in the year) and, in the e-form layout, for every executive in 7.4.1.
- File name from the public SET factsheet page (`/en|th/market/product/stock/quote/{T}/factsheet`, robots allow); download from
  `market.sec.or.th/public/idisc/Download?FILEID=dat/f56/<file>.zip` (robots allow). **Never** use the SET API (bot check – do not
  work around it) or `weblink.set.or.th` (robots `Disallow: /`). Honest User-Agent `corp-data-research/1.0` (no e-mail), ≥ 3 s per host, stop on 403/429.
- FO = SET factsheet "Foreign Shareholders" (as of the crawl date, Nov 2026). It only counts the foreign register within the limit:
  strategic holders with a waiver are missed (BAY/MUFG, CIMBT/CIMB) → review flagged companies in the One Report major-holder list
  (`data/manual/fo_review.csv`, `ownership_manual.csv`). Holdings through Thai-registered companies are not foreign. NVDR is never added.

## Decisions of the research owner (07–09/11/2026)

- One Report decides who is foreign; BoardEx only fills the country and adds managers below the executive list (only BoardEx-labelled
  non-Thai people – unlabelled names are not opened as candidates). Conflicts → `Source_Conflicts`, kept as One Report.
- Country of a "No" person: BoardEx → profile statement (`DOC_FIELD`, also another issuer's report: `NATIONALITY_FROM_OTHER_ISSUER`)
  → INFERRED_STRONG (own profile names the foreign parent/shareholder – not its Thai subsidiary) / MEDIUM (own profile names a school or
  employer in that country + name) / WEAK (distinctive name only; English and Malaysian/Singaporean-Chinese names are NOT enough) → UNKNOWN.
- FOREIGN_MAJORITY companies: only BoardEx and the One Report (executives without the field closed as `NOT_SEARCHED_FOREIGN_MAJORITY`).
- 09/11/2026: a Thai-HQ company listed only abroad with no controlling holder is FOREIGN_MAJORITY when identified Thai holders < 50%
  (unidentified holders count as foreign; `FO_Method = RULE_FOREIGN_LISTED_NO_THAI_CONTROLLER`).

## Pipeline (`pipeline/`)

`01_universe` → `02_boardex` → `03_factsheet` → `04_collect_reports` (all | TICKER[:f56/file.zip] …, `out=` for parallel workers)
→ `05_parse_template` → `06_ownership` → `07_people` → `10_nationality_index [workers]` (page-text cache in `data/full/text/` + index of
every "Nationality: X") → `11_country_context` (stated matches + profile context) → hand review → `tools_add_country.py <batch.json>`
→ `08_build_excel` → `qa_checks` (`sample` draws the manual QA sample; results in `data/manual/qa_manual.csv`).
Full command list: `output/BAO_CAO_BAN_GIAO.md`, section 7.

## Lessons (Thailand)

- **`05_parse_template.py` arguments are tickers**: `05 … full` parses nothing (treats "full" as a ticker). Run without arguments.
- Section headings come in 4 layouts (STRUCTURE PDF, E_FORM, bilingual "B" zip, Thai). Sub-committee lists repeat directors: they must
  map to SKIP (FMT "7.3.2 Information on each subcommittee"). Bilingual reports list everyone twice → keep the Latin half.
- A person can be in the board list and in "left during the year" → one row (07 merges them).
- One BoardEx id may fuzzy-match two siblings (SIS Lim Hwee Hai / Hwee Noi) → 07 keeps it only for the best unique match.
- BoardEx name variants must never be the bare surname: with an empty `Usual_Name` the variant " Uer-Anant" scored 100 against every
  relative (34 wrong pairs, all Thai). Ties between BoardEx ids (duplicate profiles, ANI Nichol Yeo) keep the lowest id; before the
  fix (09/11/2026) the choice changed from run to run (set order).
- Bloomberg can list the same code on two exchanges (Fabrinet `FN US` vs `FN TB`) → foreign listings get `CODE_EXCH` when they collide.
- Keyword checks for INFERRED_STRONG must stop at the next person's name and reject the Thai listed company / Thai subsidiary with the
  same name ("Synnex (Thailand) PCL", "Inoue Rubber (Thailand)").
- Some Thai PDFs have a broken font layer (SPG) → read the page image.
- Downloads of reports filed late in 2026 return a 118-byte "ไม่พบไฟล์ที่ระบุ" page – delete (`find … -size -1000c`) and retry later.
  Meanwhile, take the previous filing from the SEC 56-1 list: `market.sec.or.th/public/idisc/en/FinancialReport/R561-<id>`. The id is
  `uniqueIDReference` on the page that `…/companyprofile/listed/<SYMBOL>` redirects to (robots only disallow `*.aspx`). Then run
  `04_collect_reports.py TICKER:f56/<file>.zip`. Fiscal years ending in July (TNH, CITY) count as FY2025. A 2024 report is the last
  resort (QDC, MVP, AKS): set `Doc_Kind = AR2024` in docs.csv and add a line to `data/manual/company_source_notes.csv`.
- **Bloomberg drops "&"/"-" from SET symbols** (S&J→SNJ, SE-ED→SEED, F&D→FND, M-CHAI→MCHAI, Q-CON→QCON, L&E→LNE) and keeps
  old lines (BANPUU = Banpu before its 2026 amalgamation) → `data/manual/set_symbol_manual.csv`, `03_factsheet.py update T …`.
  A factsheet reading "ขออภัย ไม่พบข้อมูลที่คุณต้องการ" means a wrong or delisted symbol, not "no foreign holders".
- Thai companies listed abroad (THBEV, 6603, MMT) file no 56-1: use the SGX/HKEX annual report. SEC EDGAR returns 403 to the
  project's User-Agent → US filings are not read (no workaround). Subsidiary country managers do not count.
- The laptop suspends at night: long jobs pause (use `systemd-inhibit` if a run must continue).
- Do not edit `data/manual/` while 06 runs (it reads the files at start); 06 takes ~20 min.

## Status at hand-over (09/11/2026)

- LOCAL 842: FOUND 215, NONE_FOUND 625 (ALL_STATED 382 / BOARD_STATED 243), UNRESOLVED 2 (BTG, PTTGC). Core = 1 for 211.
  REVIEW 4 (AKS, ZUUS, BKMP, VPSN). QA 0 violations; manual sample 81 records + 30 flag-0 companies, 0 errors;
  independent re-check of every row added on 09/11 (31 records, 11 countries, 10 flag-0 companies) → 6 errors + 2 missed people, all fixed.
- Open: 3 executives without evidence (AWC Micheal Hariz, BTG Genevieve Siriwan Finet, PTTGC Kamel Ramdani); 115 foreign people in LOCAL
  companies with UNKNOWN country after two web-search rounds (10–11/11/2026; 154 before) – every one was searched;
  search notes of round 2 (incl. NOT_FOUND hints) in `data/web_search_round2/`. Waiting for the owner (11/11/2026): (a) ~19
  executive-committee members printed "Thai nationality: No" but not in the records (would flip `Foreign_Manager` 0→1 at AF, OGC,
  PRM, SSF; Core unchanged; AF Suthiporn Tanthikul looks like a Thai name); (b) NRF Dan Pathomvanich – One Report Thai, Companies
  House "American" (dual?); (c) "is from Singapore/Malaysia" wording (D Lucinda Chen, SMO Johson Lim) – accept as INFERRED or not; licensed 31/12/2025 FO not yet available
  (`data/manual/fo_licensed.csv`; no public source – archived factsheets only hold the bot-check page); QDC, MVP, TAPAC, MILL use 2024 reports.
