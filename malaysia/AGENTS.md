# AGENTS.md – Malaysia FY2025 (country rules)

Read the top-level `AGENTS.md` (shared rules) and `NEW_COUNTRY_PLAYBOOK.md` first. This file holds only what is specific to Malaysia. Started 7 Nov 2026. No BoardEx.

Run everything from the project root with the shared environment: `.venv/bin/python -I malaysia/pipeline/<step>.py`.

## Owner decisions (7 Nov 2026 – apply, do not re-ask)

| Topic | Rule |
|---|---|
| Universe | `malaysia/Bloomberg-malaysia2025.xlsx` (licensed, git-ignored), 1,186 securities, values copied verbatim into `data/universe.csv` |
| Foreign-listed only (US/HK/SP/AU/LN/TT tickers, 82) | Out of scope by the shared owner rule (`OWNER_RULE_FOREIGN_LISTED_OUT_OF_SCOPE`) |
| REITs | **In scope** (the REIT manager's board and officers), as in the Philippines |
| ETFs and other funds (Equity/Debt/Closed-end fund groups) | **Out of scope** (`In_Scope = 0`, `OWNER_RULE_ETF_FUND_OUT_OF_SCOPE`); rows kept |
| LEAP and ACE markets | Listed on Bursa, so in scope if listed at any time in 2025 (shared rule) |
| Year for managers | **Calendar 2025**: held the position at any time from 1 Jan to 31 Dec 2025. For a company whose financial year does not end in December, read both annual reports that overlap 2025 (FY ending in 2025 and FY ending in 2026), or boardroom-change announcements when the later report is not out yet |
| FO source and date | The "Analysis of Shareholdings" (distribution by Malaysian / Foreigners) in the **annual report for the financial year ending in 2025**. Its date is usually 1–4 months after the year end; record that date |
| FO measure | Shared rule: voting shares, legal nationality as classified in the filing (foreign nominee accounts "Asing" = foreign). Non-voting ICPS/RCPS and treasury shares do not count |
| Documents | Annual reports filed with Bursa. bursamalaysia.com and disclosure.bursamalaysia.com block scripts (Cloudflare), so do not script against them. The free malaysiastock.biz login allows only a few searches a day, so the owner chose (7 Nov 2026) **the company's own website first** (InSage-hosted IR pages, then the site found on KLSE Screener). Reports a script cannot reach are listed for download by hand |
| Labels and documents | English (as in the Philippines); replies to the user in Vietnamese |

## Sources tested (7 Nov 2026)

- bursamalaysia.com (search API, announcement pages, attachments): HTTP 403 Cloudflare challenge.
- klsescreener.com, klse.i3investor.com: open; list annual-report announcements per stock (FY end, date, attachment names), but the attachment links point back to disclosure.bursamalaysia.com.
- malaysiastock.biz: open; `GetReport.aspx?file=AR/...` serves the PDF itself; the per-company announcement search needs a login (`malaysia/.malaysiastock_login`, git-ignored, never print it) and the free account runs out of daily hits after a few searches. Paid plan about RM268–318 a year. Its company drop-down is the Bursa directory used by `my01` (it also keeps delisted names).
- klse.i3investor.com: `/web/stock/financial-annual-report/<code>` holds `var dtdata` (FY end, audited-accounts date, AR announcement date, detail URL); the detail page lists the attachment names. Rate-limited: run one process, with back-off (`my02`).
- InSage (insage.com.my), an IR-website provider: `ir/cmn/trps02/ArTop.aspx?Symbol=<code>` lists its clients' reports and serves the PDFs itself (`downloading.aspx?sFileName=…&sReportType=AR`). 167 in-scope clients (`my03a`).
- klsescreener.com stock page: "Website:" link of the company (about 45 KB into a 1.2 MB page; only the first 300 KB is read). Answers HTTP 202 now and then: one request at a time, 1.5 s pause, back-off 10/30/60 s.

## Pipeline

| Step | Script | Notes |
|---|---|---|
| 1 | `my01_universe.py` | Bloomberg → `data/universe.csv`; stock code from the ISIN (MYL1155OO000 → 1155; REIT 5110TO → 5110); directory from malaysiastock.biz → `data/bursa_directory.csv` |
| 2 | `my02_index_ar.py [k n]` | i3investor annual-report index → `data/ar_index.csv` (every FY, announcement dates) and `data/ar_attachments.csv` (attachment names for the FY ending in 2025, and in 2026 when the year end is not December). Pages cached in `raw/i3/`; resumable; run without arguments to merge |
| 2b | `my02b_pilot.py` | 30-company pilot, stratified (Main/ACE × Dec/non-Dec year end, LEAP, REIT), seed 20261107 → `data/pilot30.csv` |
| 3a | `my03a_insage.py` | InSage report links → `data/insage_ar.csv` (pages cached in `raw/insage/`) |
| 3 | `my03_web_ar.py [--check] [--workers N] (all \| codes.csv \| code …)` | Reports needed per company from the index; InSage first, then the company website (crawl ≤ 30 pages, IR links first). `--check` confirms a PDF link (first 4 KB) → `data/ar_availability.csv`; without it, downloads to `raw/web_ar/<code>/` with `.meta.json` → `data/web_ar_found.csv`, `data/web_ar_files.csv`. A run on part of the list keeps the other companies' rows. Follows IR pages on provider hosts (ChartNexus `ir2.chartnexus.com`, `*.investor.net.my`); hosts that answer with a bot challenge (Cloudflare, Incapsula, AWS WAF – e.g. `*.listedcompany.com`) are recorded as `SITE_BLOCKS_SCRIPTS`, never worked around |
| – | `ms_session.py` | Logged-in malaysiastock.biz session (`login()`, `search_announcements()`), for the few searches the free account allows |

## Status (7 Nov 2026) – can every annual report be obtained?

`my03_web_ar.py --check all` (`data/ar_availability.csv`), 1,091 Bursa codes:
- FY ending in 2025 (the main report: FO and managers), 1,025 companies with it in the index: **605 automatic**
  (150 InSage, 455 company website, PDF confirmed). Not automatic: 202 no matching file on the site, 87 site
  blocks scripts, 67 site only links to Bursa, 47 site down, 17 no website. 384 of these reports are filed on Bursa
  (about 770 PDF parts); 37 are not.
- Coverage is similar across size and board (59–66%), except LEAP (1 of 36).
- 66 codes have no FY ending in 2025 in the index (new listings, year-end changes, suspensions, LEAP): check one by one.
- Second report (year end not December, FY ending in 2026), 509 companies: 226 automatic, 91 not due yet, 77 filed on
  Bursa only, 115 not in the index yet.
- The i3investor attachment page (`/web/staticfile/view/<id>`) carries the direct Bursa file link
  (`disclosure.bursamalaysia.com/FileAccess/apbursaweb/download?id=…`). Scripts cannot fetch it, but a browser can.
- Open: how to get the reports that are not automatic (owner to choose).
