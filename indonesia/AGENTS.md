# AGENTS.md – Indonesia FY2025 (country rules)

Read the top-level `AGENTS.md` (shared rules) and `NEW_COUNTRY_PLAYBOOK.md` first. This file holds only what is specific to Indonesia. Started 7 Nov 2026. No BoardEx.

Run everything from the project root with the shared environment: `.venv/bin/python -I indonesia/pipeline/<step>.py`.

## Owner decisions (7 Nov 2026 – apply, do not re-ask)

| Topic | Rule |
|---|---|
| Universe | `indonesia/Bloomberg-Indonesia2025.xlsx` (licensed, git-ignored), 1,015 securities, values copied verbatim into `data/universe.csv` |
| Foreign-listed only (US/HK/SP tickers, 6) | Out of scope by the shared owner rule (`OWNER_RULE_FOREIGN_LISTED_OUT_OF_SCOPE`) |
| Not in the KSEI master file in 2025 (owner, 8 Nov 2026) | 1789071D (old Siloam line), ITTG, FINN, PRIM, AMAN: out of scope (`In_Scope = 0`, `OWNER_RULE_NOT_LISTED_IN_2025`); rows kept |
| Year for managers (owner, 8 Nov 2026) | **Calendar 2025** (any time 1 Jan–31 Dec 2025), as in Malaysia. For the few non-December year ends (screen: IKBI, HEXA, RIGS, CANI, AMOR, AMIN) read both reports that overlap 2025 when needed. FO date stays KSEI 30 Dec 2025; an AR shareholder table carries the company's own year-end date (record it) |
| ETFs, mutual funds and DIRE (51; ISIN `IDN…`/`IDX…`) | **All out of scope**, DIRE included (`In_Scope = 0`, `OWNER_RULE_ETF_FUND_OUT_OF_SCOPE`); rows kept. DIRE are KIK collective-investment contracts run by an investment manager, not companies with their own board |
| FO source | **KSEI holding-composition file for 30 Dec 2025** (last trading day of 2025) for every company: `FO_Lower` = foreign holdings at KSEI / listed shares, `FO_Upper` = 1 − local holdings at KSEI / listed shares (shares outside KSEI custody are unknown). Where the bounds straddle 50 %, use the **shareholder-composition table at 31 Dec 2025 in the 2025 annual report** (OJK annual-report rule: local/foreign institutions and individuals) or the list of ≥ 5 % holders with nationality |
| FO measure | Shared rule: voting shares, legal nationality (KSEI's local/foreign investor status; place of incorporation for a named holder). Treasury shares and non-voting shares do not count |
| Role groups | **Dewan Komisaris → Board**; **Direksi → Executive** (Direktur Utama = CEO); **Dewan Pengawas Syariah → Other_Manager** (not Core). Committee-only members, corporate secretary, head of internal audit → Other_Manager when the filing lists them (shared rule) |
| Documents | idx.co.id blocks scripts (Cloudflare 403; never work around it). **Company website first** (OJK requires the annual report on the issuer's website); reports a script cannot reach are listed for download by hand from IDX in a browser |
| Labels and documents | English (as in the Philippines and Malaysia); replies to the user in Vietnamese |
| Reports not reachable by script (owner, 8 Nov 2026) | First a second, deeper script pass (60 pages, retry failed sites, common IR paths); then a priority list for manual download from IDX in a browser (FO-straddle firms first, then LOCAL) |
| Pilot (owner, 8 Nov 2026) | Yes: 30 firms, stratified (LOCAL / FO-straddle; large / small; banks; foreign holders), about 8 of them from the manual-download list, before downloading everything |

| Foreign-majority firms (owner, 8 Nov 2026) | **No manager search for any FOREIGN_MAJORITY firm (FO > 50 %)**: "công ty trên 50% không phải tìm quản lý nước ngoài". Replaces the shared FM ≤ 55 % borderline band **for Indonesia only** (Vietnam and Philippines unchanged). FM firms need no AR |
| FO from the AR (owner, 8 Nov 2026) | Auto-accept the AR local/foreign table when all hold: foreign + local = 100 % (± 1); the value lies inside the KSEI bounds (± 0.5 point); \|FO − 50 %\| ≥ 5 points; with a second (2024/2025) column, both columns on the same side of 50 %. Recorded with page and parsed rows. Everything else (near 50 %, named-holder results, tables off the bounds) is read by hand with a verbatim quote in `data/manual/ownership_ar.csv` |
| IDX downloads by script (owner, 8 Nov 2026) | Allowed **from `www.idx.id` only** (same IDX site; answers scripts with 200, no bot challenge). idx.co.id stays untouched (403; never work around). Slow: one thread, a pause of several seconds per request; URL, time and SHA-256 recorded per file; first-pages check as for website files. **Stop at once** and fall back to manual download if www.idx.id starts blocking (403/429/challenge page) |
| FO from named holders (owner, 9 Nov 2026) | Also auto-accept a NAMED_HOLDERS result when one side (Indonesian legal entities: PT / Persero / State; or foreign-incorporated: Ltd / Pte / Inc / Sdn Bhd …) holds > 55 % and the implied FO lies inside the KSEI bounds; recorded with page and parsed rows. The rest of the straddle firms: improve the parser once, then read by hand |
| Members who left during 2025 (owner, 9 Nov 2026) | Check them: download the AR 2024 from IDX (www.idx.id, same slow rule) for LOCAL firms with departures, screen for a nationality label next to the departed names; foreign ones are read and recorded (source AR 2024, leaving date from AR 2025); names with no information go to the limitations |
| Departed members without stated nationality (owner, 10 Nov 2026) | Web / news search first (open the page, quote it, URL + access date in `Other_Sources`); if still nothing, infer only when the name clearly points to one country (as in the Philippines) → `Evidence_Type = INFERRED`, `Note = INFERRED_WEAK` + basis, counts toward the flag; otherwise limitations |
| FO still open after hand reading (owner, 10 Nov 2026, OPEN_DECISIONS 11a) | BAE monthly register report for December 2025 ("Laporan Bulanan Registrasi Pemegang Efek", filed on IDX in Jan 2026): "Komposisi Kepemilikan Saham" at 31 Dec 2025 (scrip outside KSEI + KSEI custody, each national / foreign) and form X.H.1-1 (holders >= 5 %, Status A/I). Fetched slowly from www.idx.id (the announcement API gives idx.co.id links; the same file sits under www.idx.id/Portals/0/StaticData/..., the path the AR downloads use; idx.co.id itself is never used). Scans: read the page image; Method `BAE_REGISTER_202512` |
| Sample (owner, 11 Nov 2026) | LOCAL firms without an AR 2025 that are delisted or suspended by IDX (missing audited FS) are excluded from the share of firms with foreign managers: `In_Sample = 0` + `Sample_Note`, rows never deleted. All three status groups are excluded (DELISTED, LONG_SUSPENSION, SUSPENDED_2026_LATE_FS2025); the late filers are re-checked on IDX in 2027 |
Open decisions waiting for the owner: `OPEN_DECISIONS.md` (this folder).

## Sources tested (7 Nov 2026)

- **KSEI** (ksei.co.id), open to scripts. Page *Publikasi → Data & Statistik → Kepemilikan Efek* lists the monthly
  files; the store `https://www.ksei.co.id/storage/Download/BalanceposEfek<YYYYMMDD>.zip` also serves daily dates
  (20251229 and 20251230 tested; 20251231 does not exist, the market was closed). One pipe-separated text file:
  `Date|Code|Type|Sec. Num|Price|Local IS|CP|PF|IB|ID|MF|SC|FD|OT|Total|Foreign IS…OT|Total` (investor types:
  insurance, corporate, pension fund, bank, individual, mutual fund, securities company, foundation, other).
  1,002 EQUITY codes on 30 Dec 2025. It counts **only shares in KSEI custody**: controlling blocks held outside
  KSEI are missing (TCID: Mandom Corp ~60 % missing; ASII 55 %, HMSP 93 %, UNVR 86 % missing). On this file
  alone, 956 companies: 530 LOCAL, 97 FOREIGN_MAJORITY, 329 straddle 50 %.
- **KSEI master file** ("Master File Efek", page *Statik Efek*): `.../storage/Download/StatisEfek<YYYYMMDD>.txt.zip`
  (daily dates work; 20240102, 20250102, 20251230 downloaded). Per security: code, ISIN, issuer, status (only
  ACTIVE rows), stock exchange, listing date, Num. of Sec, Total Scripless, Local/Foreign % of scripless.
  `Total Scripless` = the holding-composition total, so the KSEI gap = shares not converted to scripless
  (scrip held at the share registrar), e.g. TCID 71.6 m of 402 m; CNTB 0 of 130 m ("Seri B company listing").
  The Stock Exchange field is blank for some trading stocks (TALF, KOPI, PPRO, DMAD, BRAU): not used.
- **idx.co.id**: HTTP 403 Cloudflare challenge for the home page and the `primary/ListedCompany/...` API.
  Also blocked: idnfinancials.com, marketscreener.com (403); DuckDuckGo html (202 bot challenge).
- **stockanalysis.com** `/quote/idx/<code>/company/`: open (robots.txt allows `/quote/`), gives the company
  website; used only to find annual reports. **Wikidata** (IDX = Q1661737, P856): websites for 633 of 958.

## Annual-report content (checked on SONA and AALI AR 2025, 7 Nov 2026)

- Bilingual (Indonesian / English) on the same page. Text layer present in both.
- **Shareholder composition** required by OJK (SEOJK 30/2016, cited in SONA's checklist p133): "Jumlah pemegang
  saham dan persentase kepemilikan … berdasarkan klasifikasi: institusi lokal; institusi asing; individu lokal;
  individu asing". SONA p41: "Badan Usaha Asing / Foreign Institutions … 49,59" and "Badan Usaha Dalam Negeri /
  Local Institutions … 31,66". Wording varies ("Domestic", "Pemodal Asing", "Badan Usaha Asing").
- **Nationality of each Commissioner/Director and committee member** in the profile: "Warga Negara Indonesia …
  / An Indonesian citizen, born in 1966 …" (AALI p77–87, p182–201). Foreigners: "Warga Negara <country>",
  "Kewarganegaraan: <country>", "<demonym> citizen". The label screen needs Indonesian country names
  (Jepang, Singapura, Tiongkok, Korea Selatan, Amerika Serikat, Inggris, Belanda, Jerman, Perancis, …).

## Pipeline

| Step | Script | Notes |
|---|---|---|
| 1 | `id01_universe.py` | Bloomberg → `data/universe.csv`; Code = Bloomberg ticker (prefix `R/` dropped; `data/manual/ticker_map.csv` for renamed tickers); Security_Kind COMPANY / FUND_ETF / DIRE / FOREIGN_LISTED; listed in 2025 = EQUITY code in the KSEI master file of 2 Jan or 30 Dec 2025 |
| 2 | `id02_ksei_fo.py [YYYYMMDD …]` | KSEI holding composition → `data/fo_ksei_<date>.csv`: FO_Lower, FO_Upper, KSEI_Class (LOCAL / FOREIGN_MAJORITY / STRADDLE). Classification date 20251230; 20250131 and 20250630 kept as extra observations |
| 3a | `id03a_websites.py` | Website per company: stockanalysis.com → Wikidata → `data/manual/websites_manual.csv` → `data/websites.csv` (one host, 1.5 s pause, ~1 h for all) |
| 3 | `id03_web_ar.py [--check] (all \| codes.csv \| code …)` | Crawl the website (≤ 30 pages, IR links first, Indonesian keywords) for the AR 2025 PDF; `--check` = availability only → `data/ar_availability.csv`; otherwise download to `raw/web_ar/<code>/` with `.meta.json` (streamed, 3 tries; `--known` reuses the check-pass candidate links instead of crawling again) → `data/web_ar_files.csv` with a first-pages check (VERIFIED / CHECK). A CHECK file is used only after a reviewer confirms it in `data/manual/ar_file_reviews.csv` (CONFIRMED_AR2025 / REJECTED_…, page + quote). Links to idx.co.id → `IDX_LINK_ONLY` (manual). Adapted from `malaysia/pipeline/my03_web_ar.py` |
| 3b | `id03b_manual_list.py` | Priority list of reports to download by hand from IDX → `data/manual_ar_list.csv` (1 pilot, 2 FO straddle, 3 LOCAL; FOREIGN_MAJORITY never listed, owner 8 Nov 2026); files go to `raw/manual_ar/<CODE>/`. IDX page confirmed 8 Nov 2026 via `www.idx.id` (same IDX site, canonical idx.co.id; idx.co.id itself answers 403 to scripts): "Laporan Keuangan dan Tahunan" with year / period (Triwulan 1–3, Tahunan) / company filters |
| 3c | `id03c_register_manual.py` | Registers PDFs saved by hand in `raw/manual_ar/<CODE>/`: `.meta.json` (IDX_MANUAL, SHA-256) + first-pages check → `data/manual_ar_files.csv` |
| 4 | `id04_pilot.py` | 30-firm stratified pilot (seed 20261108) → `data/pilot30.csv`: 22 automatic + 8 manual; 3 banks and 1 non-December year end forced in. Redrawn 8 Nov 2026 after the second availability pass |
| 5 | `id05_text.py (codes.csv \| code …)` | Page text of the checked AR files → `data/text/<CODE>/<sha12>.json` (git-ignored) + `data/text_index.csv`; OCR (Tesseract ind+eng, 200 dpi) only for pages with < 40 characters of text |
| 6 | `id06_screen.py [codes.csv]` | Screening only: (a) nationality labels (warga negara X, kewarganegaraan, X citizen, nationality: X, WNA) → `data/screen_nationality.csv`, per document `data/screen_docs.csv`; (b) local/foreign shareholder composition table (leaf rows, sub-totals, SUM_OK when foreign + local ≈ 100, TWO_DATES flag) → `data/screen_composition.csv` |
| 7 | `id07_fo_classify.py` | Final FO class: KSEI bounds (LOCAL / FM) → `data/manual/ownership_ar.csv` (hand-read, quote) → auto-accepted AR table (OPEN_DECISIONS 6a) → else REVIEW (NEEDS_MANUAL / NO_AR). `Search_Managers` = 1 only for LOCAL → `data/fo_classification.csv` |
| 3d | `id03d_idx_ar.py (manual \| codes.csv \| CODE …) [--year 2024]` | AR from IDX through www.idx.id (owner 8 Nov 2026): one thread, 3 s pause, stop on any block; parts att1…attN; checks VERIFIED / SET_VERIFIED / IDX_RECORD → `data/idx_ar_files.csv` (other years: `idx_ar_files_<year>.csv`) |
| 3e | `id03e_idx_repair.py [--pause 3]` | Repairs IDX downloads without `%%EOF` (IDX sends no Content-Length and can cut at ~20–30 MB): resumes with HTTP Range until 416, new file name, old rows dropped from `text_index.csv`; log `data/idx_repair_log.csv` (REPAIRED / SOURCE_SAME_SIZE / FAILED). `fetch_pdf` itself now probes with Range when the size is unknown |
| 3h | `id03h_idx_ar_announce.py (codes.csv \| CODE …) [--pause 3]` | AR 2025 filed only as an IDX announcement ("Penyampaian Laporan Tahunan", 1 Jan–11 Nov 2026), same access rules as 3f → `raw/idx_ar_ann/<CODE>/`, `data/idx_ar_ann_files.csv` (read by id05, id10, id_add_records). Check the report year of every file (AR 2022 / 2024 files found) |
| 3i | `id03i_idx_status.py (codes.csv \| CODE …) [--pause 3]` | Trading status from IDX announcement titles 2024–Nov 2026 (titles only, no download; same access rules as 3f): SUSPEND / UNSUSPEND / DELIST_POTENTIAL / DELIST / FS_FILED / AR_FILED → `data/idx_status_titles.csv` (read by id10 for `No_Source_Reasons`) |
| 3f | `id03f_idx_register.py (review \| codes.csv \| CODE …)` | BAE monthly register report Dec 2025 (OPEN_DECISIONS 11a) from the IDX announcement API; attachments fetched at www.idx.id/Portals/0/StaticData/… (never idx.co.id) → `raw/idx_reg/<CODE>/`, `data/idx_reg_files.csv` |
| 5b | `id05b_reg_text.py` | Text + OCR of the register reports → `data/reg_text/` (git-ignored), tagged pages `data/reg_pages.csv`. Part 1 = IDX e-form (text: holders > 5 %, position, scrip / scripless public); later parts = BAE forms (composition national / foreign, X.H.1-1 Status A/I), mostly scans → read the page image |
| 8 | `id08_propose.py` | Record proposals for LOCAL firms from the nationality screen: name / role candidates, appointment / leaving hints, context PROFILE / STATEMENT / OTHER; labels already covered by a record on the same page (distinct ages) are skipped → `data/proposals.csv` |
| 9 | `id09_departures.py`, `id09b_departures_ar2024.py` | Members who left during 2025 (no AR 2025 profile): names near leaving phrases → `data/departures.csv`; their nationality in the AR 2024 → `data/departures_ar2024.csv` |
| – | `id_add_records.py <batch.json>` | Appends reviewed records / ownership rows; refuses the batch if a quote is not on the cited page, a role group or country is invalid, or a record is duplicated; keeps the batch in `data/manual/batches/` |
| – | `id_review_page.py text\|find\|image <CODE> …` | Reviewer helper: cached page text, regex search, page image (always view the image for OCR / multi-column pages before recording) |

## Status (8 Nov 2026)

- Universe: 1,015 securities = 958 companies, 51 funds/ETF/DIRE (out), 6 foreign-listed (out). Of the 958:
  953 listed in 2025 by the KSEI master file (933 all year, 20 listed during 2025); 5 not in it
  (1789071D, ITTG, FINN, PRIM, AMAN) → out of scope (owner, 8 Nov 2026). In scope: 953 companies.
- FO from KSEI 30 Dec 2025 (956 companies in the holding file): 530 LOCAL, 97 FOREIGN_MAJORITY (8 of them with
  FO_Lower ≤ 55 %), 329 STRADDLE (median KSEI coverage 27 %) → the AR 2025 shareholder table is needed for them.
  Classes flip between 30 Jun and 30 Dec 2025 for LPGI, AMMS (LOCAL → FOREIGN_MAJORITY) and NIRO (reverse).
- Pitfall: `Sec. Num` is the listed share line only. Issuers with another (unlisted) share series, e.g. CNTB
  "Seri B company listing", or TLKM's Series A share, need the AR for total voting shares.
- Websites (id03a): 951 of 958 (902 stockanalysis, 49 Wikidata), 7 none. stockanalysis fiscal year (screen only):
  899 January–December, 6 other (IKBI, HEXA Apr–Mar; RIGS, CANI, AMOR Jul–Jun; AMIN Feb–Jan), 53 blank →
  calendar 2025 (owner, 8 Nov 2026).
- Crawler test on 12 large firms: AR 2025 found for AALI, ADRO, MEGA, SONA, TLKM; KLBF, TCID are JavaScript-only
  sites, UNVR refuses scripts (403), TRIM times out.
- Availability check (`id03_web_ar.py --check --workers 8 all`, finished 8 Nov 2026; the Mac slept overnight,
  so keep it awake with `caffeinate -i -w <pid>` for long runs): 958 companies → **404 AVAILABLE_WEBSITE**, 358
  NOT_FOUND, 66 JS_ONLY_SITE, 62 SITE_ERROR, 54 SITE_BLOCKS_SCRIPTS, 7 NO_WEBSITE, 5 IDX_LINK_ONLY, 2 SCRIPT_ERROR
  (UnicodeError). Needed firms (LOCAL 530 + STRADDLE 329): 360 automatic. Similar across size (top-200 48 %, rest 44 %).
- Known false positives in AVAILABLE: AR 2024 published in 2025 with the publication date in the file name
  (TAMA "…2024_29-April-2025…", RCCC "…AR-30-04-2025", MDKI "20250430…"), and BYAN, PEHA (AR 2024). The download
  mode's first-pages check (year 2025 + "annual report/laporan tahunan" + name) must confirm every file.
- Owner 8 Nov 2026 (questions 1–4 all option a): second pass running (`--check --workers 8 --max-pages 60 --guess
  data/ar_pass2_codes.csv`, 547 codes, log `data/logs/id03_check_pass2.log`; pass-1 results kept in
  `data/ar_availability_pass1.csv`).
- Second pass finished 8 Nov 2026: only **+11** → 415 AVAILABLE_WEBSITE of 958 (365 NOT_FOUND, 58 SITE_ERROR,
  58 SITE_BLOCKS_SCRIPTS, 50 JS_ONLY_SITE, 7 NO_WEBSITE, 5 IDX_LINK_ONLY). Needed firms: LOCAL 218/530,
  STRADDLE 152/329 automatic. Deeper crawling does not pay; the rest is manual (IDX in a browser).
- Pilot redrawn (`data/pilot30.csv`): 22 AUTO + 8 MANUAL, 4 banks (BNII, BACA, ARTO, BBMD), AMIN (Feb–Jan year),
  17 with KSEI foreign ≥ 10 %. Manual list (`data/manual_ar_list.csv`): 491 firms = 8 pilot, 174 STRADDLE,
  307 LOCAL, 2 FM borderline.
- Pilot download (22 AUTO): 18 files, 17 VERIFIED + LMSH confirmed by hand (cover is an image). KEEN, LPLI, MBMA
  links work (PDF, 20–154 MB) but the in-memory download failed → downloader now streams with retries; retried.
  BAUT: the check-pass link was the Integrated Report **2024** (published Apr 2025) → no AR 2025 on the site, moved to
  the manual list (REJECTED_AR2024 in `data/manual/ar_file_reviews.csv`). Lesson: an AVAILABLE status from `--check`
  is only a link; the download check decides.
- Screens tested on 11 ARs: composition table parsed (SUM_OK) for SONA 49.59 % foreign, BNBR 83.07 %, AMIN 82.24 %,
  JAWA 1.45 %; layouts vary (bilingual label pairs, Foreign/Local section headers with Individual/Institution rows,
  nested sub-totals). Nationality: SONA has US, German, Australian, Indian labels (pp. 32–37); BUVA's profiles carry no
  nationality label at all → read by hand.
- Background processes on this Mac can be slow (a 16-minute run used 15 s of CPU); network downloads of large ARs
  are the main time cost.
- Pilot screens on the 18 AUTO reports with text (8 Nov 2026):
  - FO for all 9 STRADDLE pilot firms from the AR, all inside the KSEI bounds: table SUM_OK for AMIN 82.2 %, JARR
    0.01 %, LMSH 60.9 %, TINS 7.6 %, TOWR 21.3 %, UCID 74.3 %; named ≥ 5 % holders for BNII (Maybank entities 79.0 %
    → FM), HOKI (PT Buyung Investama Gemilang 59.95 % → LOCAL), CGAS (PT holders 65.7 % → LOCAL). Not yet quoted
    into a manual file: waits for OPEN_DECISIONS 6 (auto-accept rule).
  - Nationality: every report carries labels. **Lesson:** bilingual profiles print "Kewarganegaraan Citizenship
    Indonesia" / "Warga Negara Nationality Indonesia" – the first regex missed them (and BUVA's Korean commissioner);
    fixed. Noise removed: "Australian National University", "National Australia Bank". Employee statistics ("WNA 2",
    BNBR p200) and fit-and-proper rules (BNII p468) are not managers.
  - Recorded (`data/manual/manager_records.csv`, page image viewed): BUVA Park Seong Hoon (South Korea, Independent
    Commissioner), EMAS David Thomas Fowler (Australia, Director), EMTK Jay Geoffrey Wacher (Australia, Director),
    TOWR Stephen Duffus Weiss (United States, Vice President Director, tenure ended at the AGM of 23 Apr 2025).
  - LOCAL pilot firms with only Indonesian labels: CGAS, FLMC, HOKI, JARR, JAWA, KOBX, PNSE, PTRO, TINS → NONE_FOUND
    candidates (profile coverage still to be checked).
  - Owner 8 Nov 2026: OPEN_DECISIONS 5 → no manager search for any FM firm (no borderline band); 6 → option a (auto-accept rule).
- KEEN (154 MB) downloaded after the streaming/resume fix; KEEN, LPLI, MBMA screened. Recorded (images viewed): KEEN
  Takasawa Kazunori (Japan, Engineering Director) and Yamaguchi Masahiro (Japan, Commissioner), both from the AGM of
  5 Jun 2025; LPLI Roberto Fernandez Feliciano (Philippines, Audit Committee member only → Other_Manager,
  BOARD_COMMITTEE_ONLY, Management_Include blank); MBMA Jason Laurence Greive (Australia, Vice President Director,
  resigned at the AGM of 10 Jun 2025). **Lesson:** a member who left during 2025 has no profile; his nationality was
  only in the board-composition sentence (p210, unnamed) and the name in the change note (p73) – read both.
- **Lesson (FO):** LPLI's AR table sums to 100 % but gives 4.4 % foreign while KSEI says 20.6 % (fully scripless) –
  the table covers another basis (e.g. public float only). The KSEI-bounds check catches this; never accept an AR
  value outside the bounds. Pilot manual list now 9 (8 + BAUT); total manual list 492.
- FO classification (id07, 8 Nov 2026): pilot STRADDLE firms all settled – 6 auto (AMIN, LMSH, UCID → FM; JARR,
  TINS, TOWR → LOCAL), 3 by hand in `data/manual/ownership_ar.csv` (BNII FM 78.98 %; HOKI, CGAS LOCAL via Indonesian PT
  holders). The parser now keeps the second (other-year) column: **LPLI's first column was 2024** (4.38 %) and the
  second 2025 (20.64 % = KSEI) – the first column is not always 2025. CGAS p63 shareholder chart misprints 32,32 % for
  every holder; p43 has the real split. All in-scope: 534 LOCAL, 100 FM, 319 REVIEW (NO_AR, waiting for reports).
- Pilot manager search (LOCAL only): 16 LOCAL pilot firms with an AR → 7 with a foreign manager recorded, 9 with only
  Indonesian labels (CGAS, FLMC, HOKI, JARR, JAWA, KOBX, PNSE, PTRO, TINS). FM pilot firms not searched: AMIN, BNII,
  LMSH, UCID, BNBR, BAUT. Waiting for the 8 manual pilot reports (PANI, ARTO, SRTG, BBMD, CLAY, BACA, MAPB, PKPK).
- IDX via www.idx.id (owner 8 Nov 2026, `id03d_idx_ar.py`): the site's own API
  `/primary/ListedCompany/GetFinancialReport?...&reportType=rda&periode=audit&kodeEmiten=<CODE>` lists the AR files;
  an AR often comes in parts (att1 = 1–2 page cover letter, att2 = the report) → every part is a document; checks
  VERIFIED / SET_VERIFIED / IDX_RECORD (CLAY's first pages carry only www.cpr.co.id). Pilot: 7 of 8 manual firms
  downloaded; BACA has no AR 2025 on IDX (only the financial statements, 31 Mar 2026) and its website fails → no AR.
  Bulk run on the manual list (482 firms, pause 3 s, log `data/logs/id03d_idx_manual.log`) started 8 Nov 2026.
- Pilot after the IDX files: 30 firms = 23 LOCAL (10 with a foreign manager, 15 records; 12 with only Indonesian
  labels; BACA no AR) + 7 FOREIGN_MAJORITY (not searched). New records (images viewed): ARTO Jerry Ng (Singapore,
  President Commissioner), Umakanth Rama Pai (India, Director), Nicholas Tan Yanming (Singapore, Head of Retail
  Banking, Other_Manager); MAPB Virendra Prakash Sharma (India, President Commissioner), Neal Leroux Kok (Australia,
  Independent Commissioner), Anthony Valentine Mc Evoy (Ireland, President Director); PKPK Lee Yaw Loong Francis
  (Singapore, Commissioner). CLAY FO by hand (PT Citra Putra Mandiri 77.8 % → LOCAL).
- **Lessons:** profiles often give the first name only ("Jerry, warga negara Singapura") – take the full name from
  the board table / meeting list; MAPB's spread pages interleave two profiles (33-year-old Indonesian next to the
  38-year-old Australian) – the image settles it.
- Still to do for NONE_FOUND: check members who left during 2025 (no profile; MBMA lesson) for the 12 LOCAL pilot
  firms with only Indonesian labels.
- Full run (8–9 Nov 2026): reports for ~750 of 953 companies (415 websites incl. a few rejected as AR 2024 – BYAN,
  MOLI; the rest IDX, 68 firms with no AR 2025 on IDX). FO: 688 LOCAL, 126 FM, 139 REVIEW. Records: 219 foreign
  managers in ~130 LOCAL firms after batches 1–4 (`data/manual/batches/id_batch_*`), every quote machine-checked.
- **Screen lessons (full run):** "Universiti Kebangsaan Malaysia" read as a label (fixed); label and value in separate
  columns (NCKL, fixed with GAP words); proposals deduplicated per page hid a second person of the same nationality on
  a page (ERTX Bejoy Balakrishnan; fixed); names often only in the page graphic → page-grid images (`scratchpad grid`);
  appointment in 2026 is common in AR 2025 profiles (HMSP, SRAJ, BOGA, BWPT → NOT_FY2025 decisions).
- **Resume after a restart (9 Nov 2026).** Everything done is on disk (records in `data/manual/`, downloads in `raw/`,
  text cache in `data/text/`). Jobs that were running and how to resume them (all resumable, run from the top level):
  1. AR 2024 for members who left in 2025: `caffeinate -i .venv/bin/python -I indonesia/pipeline/id03d_idx_ar.py
     indonesia/data/departure_codes.csv --year 2024 --pause 3` (skips companies already FOUND).
  2. Then (never two IDX downloads at once) AR 2025 refetch for BYAN, MOLI (website files were the AR 2024), CSAP, YULE:
     `… id03d_idx_ar.py indonesia/data/refetch_codes.csv --pause 3`.
  3. Screens: `id05_text.py indonesia/data/codes_with_files.csv --workers 6` (cached docs are skipped), then
     `id06_screen.py`, `id07_fo_classify.py`, `id08_propose.py`, `id09_departures.py`, and after step 1
     `id09b_departures_ar2024.py`.
  Next review work: batch 5 of `data/proposals.csv` (LOCAL firms, PROFILE/STATEMENT rows), foreign rows of
  `data/departures_ar2024.csv`, FO by hand for NEEDS_MANUAL firms (`data/fo_classification.csv`), NONE_FOUND checks.
- **Status 9 Nov 2026 (evening):** workbook `output/Indonesia_2025_Foreign_Managers.xlsx` (id10) and
  `output/methodology.md`. FO: 749 LOCAL, 127 FM, 77 FO_REVIEW (25 settled by hand in `data/manual/ownership_ar.csv`).
  Flags: 142 FOUND (314 records), 502 NONE_FOUND, 23 UNRESOLVED, 82 NO_SOURCE. QA 0 violations.
  Screen patterns added on 9 Nov: "Kewarganegaraan / Citizen X", value-before-label ("Thailand Thai Kewarganegaraan
  Nationality", TPIA/BREN/ESSA), loose label (noisy; skipped in review unless confirmed). Helpers: `id_fo_review.py`
  (FO by hand), `id_fo_batch.py` + `id_batch_helpers.py` (batch writers), `id_review_page.py grid` (page thumbnails).
  Open: OPEN_DECISIONS 10 (13 departed foreign-looking names), 77 FO_REVIEW, 23 UNRESOLVED (e.g. TOTO: profiles
  without nationality), EAST (Singaporean President Director, FO unsettled).
- 10 Nov 2026: OPEN_DECISIONS 10 → a. Web search done for the departed foreign-looking names: Navin Chandra Nathani is
  Indonesian (SRAJ AR 2025), so Indian/Chinese-origin names are NOT inferred; INFERRED_WEAK only for Daisuke Morishita
  (SCCO, Japan) and Lim Sung Pil (ACRO, Korea). Company sites had removed old profiles; SATS pages answer 403 (not
  worked around). Workbook: 144 FOUND (316 records), 500 NONE_FOUND; QA 0.
- 10 Nov 2026 (later): 43 IDX reports had been saved truncated (no `%%EOF`; 0 pages or later pages missing) – repaired by
  `id03e`; DEWA and PCAR damaged on IDX itself (`SOURCE_DAMAGED` in `ar_file_reviews.csv`). AMOR's website file was the
  parent's report (Ashmore Group plc) → `REJECTED_WRONG_COMPANY`, IDX file used. IDX re-queried for the 70 firms
  without AR: only AMAG and AMOR new. Six auto FO rows had read a subsidiary table / AuM split / the issuer's own name
  (AKSI, AMOR, ANTM, BBTN, FILM, SWID) → re-read by hand, id06 guards added (`AUM`, `self_core`). FO by hand
  (batches id_fo_20261110_07–12) and from the BAE register (OPEN_DECISIONS 11a, batch id_fo_20261110_13_bae, 32 firms):
  REVIEW 77 → 9 (CTTH, INPC, OBAT, RUNS, CNTB, KUAS, MTRA, PLAS, UNIT). 11 new records in newly LOCAL firms (batch
  id_batch_20261110_14: CMRY, DEPO ×2, ECII, FILM, KRYA, PALM, PMJS ×3, WOMF). Workbook: 151 FOUND / 327 rows / QA 0.
  Lessons: always check `%%EOF`; a BAE form status "L" is the KSEI account type, legal nationality comes from the
  AR (EAST: Khalid Bin Omar Abdat, Singapore); INDO's AR text layer is font-shifted by 28 ('-RHSRIWME' = 'Indonesia').
  Next: AR 2024 for 41 codes with new unlabelled departures (`data/departure_codes_20261110.csv`), then id09b.
- 10 Nov 2026 (end of day): AR 2024 for 41 more codes (35 found); id09b → Chiew Sin Cheok (AUTO, Malaysia, AR 2024 p75,
  left 29 Apr 2025) recorded (was a limitation); UNIC Jimmy Masrin NOT_FOREIGN_STATED; KARW Farid Belbouab / A. Ravi
  Menon, PBRX Gita Rusmida Sjahrir NO_NATIONALITY_STATED (web search done). id06 fixes: the json `file` can be an
  unchecked website copy of the same report (ALKA, AGAR skipped) → use text_index files; `TABLE_PAIR` for bilingual
  tables → 5 new records (batch id_batch_20261110_16: BBHI, IFSH, GOOD, MSJA ×2), LAPD's Singapore members NOT_FY2025
  (appointed 14 Jan 2026). Workbook: 155 FOUND / 333 rows / 564 NONE_FOUND / 17 UNRESOLVED / 69 NO_SOURCE / 9 FO_REVIEW,
  QA 0. Open: Open_Items (departed names without label / not found in AR 2024), 17 UNRESOLVED (profiles without
  nationality, e.g. TOTO), 9 FO_REVIEW, handover report.
- 10 Nov 2026: handover report `output/HANDOVER_REPORT.md` (English, structure of the VN report). id10 now writes numbers
  as numbers (In_Scope, Is_Foreign, Page, Market_Cap, KSEI bounds) and '' as empty cells; Code, dates and FO_Pct_AR stay
  text (`TEXT` set in id10).
- 10 Nov 2026: `output/HANDOVER_REPORT.docx` built from the .md by `pipeline/id_md2docx.py` (real tables; rebuild after
  every edit of the .md). Note: the VN `BAO_CAO_BAN_GIAO.docx` was made with macOS textutil, which turns every table
  cell into a separate paragraph.
- 10 Nov 2026 (manual QA, `id11_qa_sample.py` seed 20261110, verdicts `data/manual/qa_review.csv`): records 28/30 OK
  (TPIA 2026 appointees: Pongpun Amornvivat + Rungnapa Janchookiat + Konlakan Chankachangchaeng removed → NOT_FY2025,
  batch `id_qa_20261110_corrections.json`; CCSI name → Chai Khye Yeien); NONE_FOUND firms 29/30 OK (KOCI). Follow-up
  review of 43 firms (`id_qa_labels.py`, `id_qa_boardpages.py`) → `data/manual/label_reviews.csv` (NO_BOARD_NATIONALITY:
  KOCI, MBSS, MEJA, BBMD, IKAI → UNRESOLVED; BOARD_LABELS_IN_IMAGE: BIKE, ATAP, HALO, HELI, TAXI, TFAS; LAPD 2025 board
  from AR 2024). 15 files of 14 firms were the AR 2024 (REJECTED_AR2024): MDKI, OMRE, RANC, RMKE, RMKO, TAMA, TNCA
  re-read from their IDX AR 2025 (new record: OMRE Chiu Man Sing, Singapore); BEKS, MARI, MSIE, POLI, TAMU, RCCC →
  NO_SOURCE; CEKA keeps Darwin Indigo from its AR 2024 (SOURCE_AR2024 note). BEKS / MSIE FO from the BAE register.
  id06: generic citizen sentences no longer count; id10: QA checks `ar_file_looks_like_2024`,
  `record_page_first_appointed_2026`, sheets `Label_Reviews`, `QA_Sample`. Workbook: 156 FOUND / 331 rows / 552
  NONE_FOUND / 22 UNRESOLVED / 75 NO_SOURCE / 9 FO_REVIEW, QA 0 (10 checks).
- 11 Nov 2026 (no-source follow-up): `id03h` found ARs filed only as IDX announcements for 30 of 84 firms; CPRI, POOL
  (AR 2022), PMMP and a BEKS file (AR 2024) rejected. 22 NO_SOURCE firms now sourced: 4 new records (GIAA Balagopal
  Kunduvara SG + Neil Raymond Mills UK, Directors from 15 Oct 2025; MNCN Joel Richard Hogarth UK, Ind. Commissioner;
  DEWA Nalinkant Amratlal Rathod IN, Commissioner), JAST Kennard Jr S Kurnia = Indonesian; KUAS FO settled LOCAL.
  Every remaining NO_SOURCE firm (53) is on the IDX suspension lists for missing audited FS 2025 (Peng-S-00020/
  BEI.PLP/06-2026, Peng-S-00021/BEI.PLP/07-2026); CNTB delisted 30 Jul 2026. Evidence `data/manual/listing_events.csv`
  (batch_src/listing_20261111.py), id10 column `No_Source_Reason`, sheets `No_Source_Reasons`, `Listing_Events_2026`.
  Workbook: 159 FOUND / 335 rows / 572 NONE_FOUND / 22 UNRESOLVED / 53 NO_SOURCE / 8 FO_REVIEW, QA 0.
  Trading status (step 3i `id03i_idx_status.py`: IDX announcement titles 2024–2026 → `data/idx_status_titles.csv`;
  batch_src/listing_20261111b.py: delisting 10 Nov 2026 (KabarBursa) and the > 6-month suspension list (CNBC, 1 Aug
  2026)): id10 columns `Status_Group` (DELISTED 13 / LONG_SUSPENSION 29 / SUSPENDED_2026_LATE_FS2025 11),
  `Last_Annual_FS_Filing_IDX`. Owner (11 Nov 2026): exclude all 53 NO_SOURCE firms from the sample (`In_Sample = 0`,
  `Sample_Note`), keep the rows; the 11 late filers are re-checked on IDX in 2027 (Open_Items RECHECK_2027). Sample 753:
  159 FM = 21.1 %, Core 152 = 20.2 %. New QA check `no_source_without_documented_status` (11 checks, 0 violations).

