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

Result (11 Nov 2026): 806 LOCAL, 139 FOREIGN_MAJORITY, 8 not settled (`FO_REVIEW`): CTTH (foreign 46.4–52.0 % from
the BAE >= 5 % list and KSEI; the AR table's 57.1 % fits neither), INPC, OBAT, RUNS (individual or unnamed holders
without nationality, no BAE composition), MTRA, PLAS, UNIT (no AR 2025, no December register report; suspended by IDX
for not filing the audited 2025 accounts) and CNTB (delisted 30 Jul 2026 at its own request). KUAS was settled LOCAL
(27.71 %) from its AR 2025 filed as an announcement (AR table, rule 6a).

## 3. Annual reports

- AR 2025 from the company website (crawler, then download with a first-pages check: year, "annual report /
  laporan tahunan", company name), else from **IDX through www.idx.id** (owner, 8 Nov 2026; idx.co.id answers
  scripts with 403 and was never worked around). IDX reports often come in parts (cover letter + report); every part
  is read. IDX sends files without Content-Length and the connection could end cleanly after 20–30 MB: 43 reports were
  first saved truncated (0 pages, or the later pages missing). Every file is now checked for `%%EOF`; the 43 were
  completed with HTTP Range requests (`id03e_idx_repair.py`), 2 are damaged in the IDX report repository (DEWA, PCAR:
  `SOURCE_DAMAGED`; complete copies found among the announcements, below). A website file that was the parent's report (AMOR: Ashmore Group plc) was rejected. Website files that turned out to be the AR 2024 were rejected (`AR_File_Reviews`).
- **ARs filed only as IDX announcements** (11 Nov 2026, `id03h_idx_ar_announce.py`): some issuers file the AR as an
  announcement ("Penyampaian Laporan Tahunan …") and not in the IDX report repository that `id03d` queries. The
  announcement API of www.idx.id was queried for the 84 firms without an AR 2025 or with FO open (1 Jan–11 Nov 2026,
  same access rules as 3d/3f). 30 firms had AR announcements; 4 of them held only an older AR (CPRI and POOL: AR 2022;
  PMMP and one BEKS file: AR 2024 – rejected in `AR_File_Reviews`). Result: 22 NO_SOURCE firms now have their AR 2025.
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
| NO_SOURCE | blank | LOCAL, no AR 2025 (or only cover letters); reason in `No_Source_Reason` / sheet `No_Source_Reasons`; `In_Sample = 0` (owner, 11 Nov 2026) |
| FO_REVIEW | blank | FO not settled |
| NOT_SEARCHED_FM | blank | foreign-majority firm (no manager search) |
| OUT_OF_SCOPE | blank | funds, foreign-listed, not listed in 2025 |

Result (11 Nov 2026, after the manual QA and the announcement search): 159 FOUND (335 foreign-manager rows, 2 of them
INFERRED_WEAK), 572 NONE_FOUND, 22 UNRESOLVED, 53 NO_SOURCE, 8 FO_REVIEW, 139 NOT_SEARCHED_FM, 62 OUT_OF_SCOPE. The screen also reads bilingual profile /
diversity tables where the value stands apart from the label ("Kewarganegaraan Citizenship … Indonesia Indonesian",
pattern `TABLE_PAIR`), ignores generic sentences about citizens ("kesempatan yang sama kepada seluruh warga negara
Indonesia …"), and firms whose only labels belong to non-board people (committees, internal audit) are set to
UNRESOLVED after review (`Label_Reviews`).

Manual QA (10 Nov 2026, random sample, seed 20261110): 30 records (1 error: a member first appointed in 2026; 2 more
of the same kind found and removed; 1 misspelt name) and 30 NONE_FOUND firms (1 error, then 4 more of the same kind
found among 43 reviewed firms). The review also found 15 files of 14 firms that were the AR 2024 (some IDX "2025"
entries are the issuer's 2024 report; some website files carry a 2025 publication date): rejected, 7 firms re-read
from their real AR 2025 on IDX. Two QA checks were added (first appointment in 2026 on the cited page; an "AR 2025"
that names only the 2024 report).

## 6. Limitations

- KSEI bounds are wide where many shares are held as scrip; 8 firms remain unsettled after the AR and the BAE report.
- Members who left in 2025 without any stated nationality (AR 2025 or 2024) are listed in `Open_Items`. Owner 10a:
  web search first, then inference only when the name clearly points to one country (2 INFERRED_WEAK: a Japanese and a
  Korean name). Indian- and Chinese-origin names were not inferred: one of them (Navin Chandra Nathani) is an
  Indonesian citizen according to another issuer's AR.
- AR 2025 not available for 53 LOCAL firms. All 53 are on an IDX suspension list for not filing the audited 2025
  accounts: Peng-S-00020/BEI.PLP/06-2026 (71 issuers, from Session I of 30 Jun 2026; Liputan6 and topbusiness.id,
  30 Jun 2026) and Peng-S-00021/BEI.PLP/07-2026 (Acceleration Board: MENN, NINE, SOUL, from 1 Jul 2026; CNBC Indonesia,
  2 Jul 2026). The pages were opened and quoted (`data/manual/listing_events.csv`, sheet `Listing_Events_2026`;
  Liputan6 writes TGRE for Terregra Asia Energy, whose code is TGRA). Each firm's search trail (IDX repository, IDX
  announcements, website, rejected files) is in sheet `No_Source_Reasons`. 14 other suspended LOCAL firms did publish
  an AR 2025 and keep their flag.
- Sample (owner, 11 Nov 2026): the 53 NO_SOURCE firms are excluded from the share of firms with foreign managers
  (`In_Sample = 0`): 13 delisted on 10 Nov 2026, 29 under long suspension, 11 suspended in 2026 for the late FS 2025
  (rows kept; re-check IDX in 2027, `Open_Items` RECHECK_2027). Sample 753 LOCAL firms: 159 with a foreign manager
  (21.1 %), 152 Core (20.2 %), 572 none found, 22 unresolved. QA check `no_source_without_documented_status`. CEKA keeps one record from its AR 2024 (published Apr 2025; shared rule: AR 2024 as a last resort, with a note).
- Screening relies on stated nationality; a profile without a label is not counted as foreign (→ UNRESOLVED).
