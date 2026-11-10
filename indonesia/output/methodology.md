# Indonesia FY2025 – Listed Companies and Foreign-National Managers: Methodology

Status: working draft, 10 November 2026. Workbook: `indonesia/output/Indonesia_2025_Foreign_Managers.xlsx`
(built by `indonesia/pipeline/id10_build_workbook.py`; sheet `QA` must show 0 violations).

## 1. Scope

- Universe: the Bloomberg list of IDX securities (1,015). Companies listed at any time in 2025 according to the KSEI
  master file (2 January and 30 December 2025) are in scope: 953 companies.
- Out of scope (owner decisions): mutual funds, ETFs and DIRE (51); foreign-listed lines (6); 5 codes absent from the
  KSEI master file in 2025 (`OWNER_RULE_NOT_LISTED_IN_2025`).
- Year: calendar 2025. A person counts if he or she held the position at any time between 1 January and
  31 December 2025. Appointments that start in 2026 are excluded (`NOT_FY2025` in `Candidate_Decisions`).

## 2. Foreign ownership (FO) at 31 December 2025

1. **KSEI holding composition, 30 Dec 2025** (`BalanceposEfek20251230`). KSEI reports local and foreign holdings in
   KSEI custody only, so it gives bounds: `FO_Lower` = foreign / listed shares, `FO_Upper` = 1 − local / listed shares.
   Upper ≤ 50 % → LOCAL; lower > 50 % → FOREIGN_MAJORITY; otherwise the bounds straddle 50 %.
2. **Straddling firms: the AR 2025.** OJK requires the shareholder composition by local / foreign institutions and
   individuals. Auto-accepted (owner 6a) when local + foreign = 100 % (± 1), the value lies inside the KSEI bounds,
   it is at least 5 points from 50 %, and a second (other-year) column, if any, is on the same side of 50 %. Named
   ≥ 5 % holders are auto-accepted (owner 8a) when one side by legal form (Indonesian PT / Persero / State vs
   foreign-incorporated Ltd / Pte / Inc / Sdn Bhd …) holds more than 55 % inside the KSEI bounds.
3. Everything else is read by hand, with page and verbatim quote (`Ownership_AR_Manual`). Individual major holders
   count as Indonesian only where a source says so (AR profile "Warga Negara Indonesia", page image viewed when the
   name sits in a graphic); a named Indonesian holder whose stake exceeds the KSEI local custody must lie outside KSEI
   and is added to it (e.g. KICI).
4. **Still open after that: the BAE monthly register report for December 2025** (owner, 10 Nov 2026). The share
   registrar's "Laporan Bulanan Registrasi Pemegang Efek", filed on IDX in January 2026, gives the composition at
   31 Dec 2025 – scrip outside KSEI (the gap in the KSEI bounds) and KSEI custody, each national / foreign – and form
   X.H.1-1 (holders >= 5 %, Status A/I). Method `BAE_REGISTER_202512`; scanned forms were read on the page image and
   are quoted as a transcription marked [page image]. It settled 32 firms (e.g. CSMI: Lisa Muchtar 56 % Status I,
   foreign 0.47 %; KOKA: the two founders Status A, foreign 50.27 %). EAST: the founder Khalid Bin Omar Abdat is
   "Warga Negara Singapura" in the AR although the BAE form marks him "L" (his KSEI account): legal nationality is used,
   foreign 72.1 %.
5. FO measure: legal nationality of the holder (a PT is local even when foreign-owned; a Singapore or BVI holding
   company is foreign even when Indonesian families control it – e.g. SIMP via Indofood Agri Resources Ltd).

Auto-accepted rows were checked again on 10 Nov 2026: six had read the wrong table (a subsidiary / associate table,
an assets-under-management split, the issuer's own name in an FS-note header or chart: AKSI, AMOR, ANTM, BBTN, FILM,
SWID). They were re-read by hand and the screen now skips such rows.

Result (10 Nov 2026): 805 LOCAL, 139 FOREIGN_MAJORITY, 9 not settled (`FO_REVIEW`): CTTH (foreign 46.4–52.0 % from
the BAE >= 5 % list and KSEI; the AR table's 57.1 % fits neither), INPC, OBAT, RUNS (individual or unnamed holders
without nationality, no BAE composition), and CNTB, KUAS, MTRA, PLAS, UNIT (no AR 2025; four have no December
register report).

## 3. Annual reports

- AR 2025 from the company website (crawler, then download with a first-pages check: year, "annual report /
  laporan tahunan", company name), else from **IDX through www.idx.id** (owner, 8 Nov 2026; idx.co.id answers
  scripts with 403 and was never worked around). IDX reports often come in parts (cover letter + report); every part
  is read. IDX sends files without Content-Length and the connection could end cleanly after 20–30 MB: 43 reports were
  first saved truncated (0 pages, or the later pages missing). Every file is now checked for `%%EOF`; the 43 were
  completed with HTTP Range requests (`id03e_idx_repair.py`), 2 are damaged on IDX itself (DEWA, PCAR:
  `SOURCE_DAMAGED`). A website file that was the parent's report (AMOR: Ashmore Group plc) was rejected. Website files that turned out to be the AR 2024 were rejected (`AR_File_Reviews`).
- AR 2024 from IDX for members who left the Board / Direksi during 2025 (owner 9a).
- Text: PDF text layer; OCR (Tesseract ind+eng, 200 dpi) for pages without text.

## 4. Managers

- Searched only in LOCAL firms (owner, 8 Nov 2026: no search in any foreign-majority firm).
- Role groups: Dewan Komisaris → Board; Direksi and C-suite officers (CFO, CTO, …) → Executive; committee-only
  members, heads of internal audit, corporate secretaries, senior officers listed in the AR → Other_Manager
  (`Management_Include` left blank for the research team). `Foreign_Manager_Core` counts Board and Executive only.
- Screening: nationality labels in Indonesian and English (`warga negara X`, `kewarganegaraan`, `X citizen`,
  `nationality: X`, value-before-label tables, `WNA`). Screening only: every foreign hit was read, the page image
  was viewed when names sit in graphics or pages hold several profiles, and the record keeps file, PDF page
  (1-based), verbatim quote (machine-checked against the page text by `id_add_records.py`) and dates.
- Members who left during 2025 have no AR 2025 profile: their names were taken from the AR 2025 change notes and
  their nationality from the AR 2024 profile.
- Nationality stated as "foreign national" without a country → `Nationality = UNKNOWN`, `Is_Foreign = 1`.

## 5. Company flags

| Flag_Status | Foreign_Manager | Meaning |
|---|---|---|
| FOUND | 1 | at least one foreign-national manager (any level) or a company-level statement |
| NONE_FOUND | 0 | LOCAL, AR 2025 read, profiles carry nationality labels, no foreign manager |
| UNRESOLVED | blank | LOCAL, AR 2025 read, but the profiles state no nationality |
| NO_SOURCE | blank | LOCAL, no AR 2025 (or only cover letters) |
| FO_REVIEW | blank | FO not settled |
| NOT_SEARCHED_FM | blank | foreign-majority firm (no manager search) |
| OUT_OF_SCOPE | blank | funds, foreign-listed, not listed in 2025 |

Result (10 Nov 2026): 155 FOUND (333 foreign-manager rows, 2 of them INFERRED_WEAK), 564 NONE_FOUND, 17 UNRESOLVED,
69 NO_SOURCE, 9 FO_REVIEW, 139 NOT_SEARCHED_FM, 62 OUT_OF_SCOPE. The screen also reads bilingual profile / diversity
tables where the value stands apart from the label ("Kewarganegaraan Citizenship … Indonesia Indonesian", pattern
`TABLE_PAIR`); this found 5 more foreign managers (BBHI, GOOD, IFSH, MSJA ×2) and turned 7 UNRESOLVED firms into
NONE_FOUND.

## 6. Limitations

- KSEI bounds are wide where many shares are held as scrip; 9 firms remain unsettled after the AR and the BAE report.
- Members who left in 2025 without any stated nationality (AR 2025 or 2024) are listed in `Open_Items`. Owner 10a:
  web search first, then inference only when the name clearly points to one country (2 INFERRED_WEAK: a Japanese and a
  Korean name). Indian- and Chinese-origin names were not inferred: one of them (Navin Chandra Nathani) is an
  Indonesian citizen according to another issuer's AR.
- AR 2025 not available for 69 LOCAL firms (not on IDX when queried again on 10 Nov 2026, only cover letters, or damaged on IDX).
- Screening relies on stated nationality; a profile without a label is not counted as foreign (→ UNRESOLVED).
