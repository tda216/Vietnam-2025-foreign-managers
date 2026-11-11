# New-country playbook – foreign ownership and foreign managers (lessons from Vietnam 2025 and Philippines 2025)

Read this together with `AGENTS.md` (shared evidence rules) and the country's own `AGENTS.md`. Written 7 Nov 2026 after the Philippines file was finished.
Put the new country in its own top-level folder (e.g. `thailand/`, next to `vietnam/` and `philippines/`) with `pipeline/`, `data/manual/`, `raw/` and `output/`, and its own `AGENTS.md` for the country rules.
Purpose: do the next country **faster and with fewer corrections**. Every rule below cost time in Vietnam or the Philippines.

**Research-owner decision (7 Nov 2026): do not use BoardEx for future countries.**
Use the companies' own filings, as in Vietnam. The reasons from the Philippines are listed in section 5.

---

## 1. Day-0 decision sheet

Settle these with the owner **before any download**. In the Philippines, half the rework came from rules decided mid-way. The defaults below are already decided, so confirm them and do not re-ask.

| Topic | Decided default |
|---|---|
| Year | FY = held the role at any time in the year. Record appointment and resignation dates when given |
| Securities listed only abroad (LN/US/SGX tickers in the Bloomberg list) | Out of scope: `In_Scope = 0`, recorded `FOREIGN_MAJORITY` by owner rule |
| Delisted, merged or not listed on the local exchange | In scope if listed during the FY (e.g. ATI, delisted April 2026). Not listed on the local exchange → out of scope. No usable filing at all → ask the owner; in PH such rows were excluded with a reason |
| FO measure | Share of **voting power** held by holders whose **legal** nationality is not local (place of incorporation, or the citizenship written in the filing; not the ultimate owner). One-share-one-vote → % of outstanding common shares. Voting preferred shares count; non-voting shares and treasury shares do not. Basis: IMF BPM6 §6.12/6.19 |
| FO date | Any date in the FY. Record the date; keep several observations |
| FO class | > 50 `FOREIGN_MAJORITY`; ≤ 50 `LOCAL`; otherwise bounds (unknown holders local = lower bound, foreign = upper bound); straddling 50 → `REVIEW` |
| Manager search | `LOCAL` firms, plus `FOREIGN_MAJORITY` firms with FO ≤ 55% |
| Manager universe | Board, Supervisory, Executive (CEO/President, deputy-CEO level, CFO, chief accountant/treasurer, C-suite), and Other_Manager (director/head level, only when a filing lists them). **At the sampled listed company itself only.** A role at a listed subsidiary that is in the sample goes to that subsidiary. A role only at an unlisted subsidiary does not count (`UNLISTED_SUBSIDIARY_ONLY`) |
| Nationality evidence | Stated citizenship > descriptor ("Japanese banker") > birthplace > inference. Dual nationality = foreign (`Dual_Nationality = 1`) |
| Name rules (owner, PH) | (a) Undisclosed person with a clearly **local** name → local (`INFERRED_WEAK`). (b) Clearly **foreign** name → foreign (`INFERRED_WEAK`), only if a country can be inferred and only after the filing and web search. (c) Otherwise → `Review_Open` |
| Concluding a firm (owner, PH) | If no foreign person is identified → `NONE_FOUND` (`Flag_Basis = NO_FOREIGN_IDENTIFIED_OWNER_RULE`). Only people with a foreign indication keep a firm open |
| Flags | Exactly as in Vietnam (`vietnam/pipeline/07_build_excel.py`). `Foreign_Manager_Core` is blank whenever `Foreign_Manager` is blank |
| Headline numbers | (1) # LOCAL firms; (2) # with `Foreign_Manager = 1`; (3) # with a foreign national in an `Executive` or `Other_Manager` position (Vietnam definition: 34 Executive + 4 Other − 2 overlap = 36). Also report Core = 1 and Executive-only |

---

## 2. Pipeline – do it in this order

Each step is a script that is rerun freely, with hand-reviewed facts only in `data/manual/*.csv` batches. Copy the Philippines scripts (section 6) and replace only the country-specific parts.

### Step 1. Universe and listing status
- Map every Bloomberg ticker to the local exchange's company directory.
- Flag foreign-listed, dual-listed, delisted, merged and not-listed securities **now**. In PH, AR, ATI, LAND, DMPI, AAA, MJIC and ROX were only sorted out at the end.
- Do not trust names alone. Example: MJIC = MJC Investments Corp., not MJC (Manila Jockey Club).

### Step 2. Filing index, then targeted downloads
- **Index first.** Run one listing pass per company for FY and FY+1 (form code, date, report number, URL). Identify these forms:
  - annual report (PH 17-A);
  - top-holders list at FY end (PH 17-12-A);
  - public-ownership report (PH POR-1);
  - foreign-ownership report (PH 17-13);
  - company registry sheet (PH GIS, filed as 17-18);
  - information statement (PH 17-5).
- **Download only what the next step needs:** FY-end top-holders list, latest annual report, and ownership reports for FY end. Fallback documents only for firms still open.
  - Large annual reports are slow (about 55 KB/s per connection in PH). Run downloads resumably in a few shards. Never re-download.
- Save `meta.json` per filing (URL, time, SHA-256). Keep downloads in their own folder and never execute them.

### Step 3. Foreign ownership – "statement first"
1. **National foreign-holding file** (like Vietnam's VSDC "FOL" file). Spend one hour looking for one before anything else. Test it on 3 firms.
2. **Company-level statements in documents already downloaded.** Run `ph09_scan_fo_statements.py`-style patterns:
   - "foreign ownership level … %";
   - "owned by foreigners/non-Filipino";
   - Filipino/Foreign tables;
   - "Number of Foreign-Owned Shares";
   - registry-sheet "Percentage of Foreign Equity" and the Filipino/Foreign subscribed-capital split.

   In PH these settled the hardest cases fastest: 27 firms from issuer statements, 4 from the GIS, and the voting-basis cases.
3. **Bounds for the rest**, from the top-holders list. The depository nominee line split local/foreign (PH "PCD Nominee – Non-Filipino") is the floor. Named holders' nationality comes from the annual report's top-20 and beneficial-owner tables.
4. **Remaining REVIEW cases:**
   - the registry sheet (GIS) top-20 list with nationality;
   - the issuer website's foreign-ownership reports;
   - a parent's incorporation sentence in the notes ("a company incorporated in the Philippines");
   - the parent's own annual report cover (place of incorporation).
5. **Voting preferred shares** (screen "voting preferred"). Recompute on votes. Check who holds the preferred block; a worst-case check is enough when it cannot flip the class.

**Pitfalls to code against** (all happened in PH):

| Pitfall | PH example |
|---|---|
| A nationality word taken from the next row | SMPH, AGI, PAL, RFM, PIZZA. Use strict row-level matching |
| One-word names matching inside other words | "Cisco" in "Francisco". Use whole-word, case-insensitive matching; never `upper()` and then index |
| Brokers or custodians counted twice | They sit inside the depository totals |
| Two tables in one PDF (common + preferred, record + beneficial) | Totals above 100% |
| Treasury shares, and percentages on different denominators | Common vs common + preferred |
| Scanned pages | OCR, then check the page image before recording |
| Fiscal years not ending in December | PMPC, VLC, VMC, NXGEN |
| "Matsushita" = Panasonic | Former names of the same holder |

### Step 4. Foreign managers – from the companies' own filings (no BoardEx)
1. **Locate the director/officer section** of the annual report (PH 17-A "Item 9/10 Directors and Executive Officers"; VN annual report governance chapter). Collect name, age, citizenship, position and dates.
   - In PH, every 17-A has a citizenship column or a "Name, Filipino, 58" bio line. **One table per firm settles most firms.**
2. **Broad label screen** on those pages: any non-local nationality word next to a person cue (age, title, "Citizenship", "national"). Then **read every hit**.
   - The strict patterns alone missed formats with a gender column ("Ho Poh Wah 63 Male Singaporean"), honorifics ("Dato Timothy Ong Teck, Bruneian") and surname-first names ("Watanabe Masashi").
   - Noise to drop: currencies, "British Virgin Islands", company names ("Thai San Miguel"), education ("American Law Program"), customer/shareholder statistics, and first names such as "Irish" or "German".
3. **Firms without a citizenship column** (Vietnam case): use the non-local-name screen (Vietnam `05a`) → candidates → profiles in the AGM documents, information statement, registry sheet or the previous annual report → name rules (section 1).
4. **Scope checks before recording:**
   - Is the role at the listed company? Bios also list roles "in other companies".
   - Candidate or elected? Check the election result.
   - Resigned or appointed in the FY? Check table footnotes.
   - Duplicates from OCR name variants → `SAME_AS_RECORD`.
5. Other_Manager is counted only when the filing itself lists the person.

### Step 5. Flags, workbook, QA
- Copy `philippines/pipeline/ph10_build_workbook.py`. It already applies the Vietnam flag rules, owner exclusions, the latest-decision-wins logic, `Review_Open`, and a 16-check QA. QA must print 0 violations.
- Keep every exclusion as a row with In_Scope = 0 and a reason. Never delete rows.

### Step 6. Owner checkpoints
1. Listing and scope list plus FO distribution, with the REVIEW list.
2. A 30-firm pilot of managers, including every tricky format.
3. Final workbook, headline numbers (section 1), QA and a manual sample.

---

## 3. Speed rules (what cost the most time in PH)
- **Resolving FO REVIEW cases one by one** (51 → 0). Running the statement-first scan and the registry sheet before the bounds would have settled most of them in one pass.
- **Cleaning BoardEx.** This meant role groups from flags, subsidiary roles, placeholder dates, 2,575 undisclosed nationalities, and missing people. Filings avoid all of it.
- **Owner rules arriving late**: voting basis, legal nationality, GIS as source, name rules, and the NONE_FOUND rule. Use the day-0 sheet.
- **Token and usage limits.** Four parallel agents used up the 5-hour limit twice. Work in one session, scripts first, and read only the pages a screen points to.
- **Too many downloads.** Index first and download per step.

## 4. Never
- Record anything from a chatbot or web-search summary without opening the document and quoting it. In PH, a chatbot asserted:
  - a Dutch PSE director ("Niek Johan van Veen") – not in any filing;
  - a Korean PSE director – actually on Security Bank's board;
  - "VVT = Vitarich" – it is Vivant;
  - "AAA does not exist" – it is Asia Amalgamated Holdings;
  - "MJIC = Manila Jockey Club" – it is MJC Investments;
  - Toyota/Sumitomo directors at GT Capital – none.
- Treat a database's role or nationality as evidence.
- Turn unknown into 0, except through the owner's explicit NONE_FOUND rule.
- Use photos to infer nationality.
- Trust a file name, a publication date or an exchange's year field for the report year (Indonesia, 10 Nov 2026: 15 "AR 2025"
  files were the AR 2024 – a 2025 date in the file name, or the issuer's 2024 report filed under year 2025). Check the
  content: the report must name its own year (count "Annual Report 2024" vs "2025" mentions).
- Count a firm as "none found" because some nationality label exists somewhere in its report. The labels must belong to
  the Board / executive profiles – committee members, the internal-audit head or an HR sentence are not enough
  (Indonesia QA: 5 of 43 such firms had Board profiles without any nationality).
- Call a report "not available" after searching only the exchange's report repository. Also search the exchange's
  announcements: in Indonesia (11 Nov 2026) 22 of 75 "missing" ARs had been filed only as announcements (3 of them
  with foreign managers). For firms that still have no report, look for the exchange's suspension / delisting notices
  (missing audited accounts) and record them as the documented reason for leaving the firm out.

## 5. Why not BoardEx (Philippines facts)
- **40 of the 92 FOUND firms** rested on BoardEx alone, against 47 with filing evidence.
- **14 people that BoardEx reported as foreign** had to be corrected or excluded:
  - roles at unlisted subsidiaries (EMI's Whyte & Mackay, VVT's Vivant Infracore);
  - a role belonging to a listed subsidiary (FDC → EW);
  - unverifiable "Chairman/Executive/Portfolio Manager" rows with placeholder dates 1900–9999 (DITO, GTCAP, PNB, PNX, VVT);
  - a nationality different from the filing (BLOOM: BoardEx "United States", 17-A "Dominican").
- **Undisclosed nationality for 2,575 role rows.** 576 were filled from filings and about 1,050 by name inference.
- **People missing from BoardEx** but stated foreign in the 17-A: DITO (Chinese director), EMI (Singaporean), CNVRG (Canadian), CREC (Indonesian).
- **"Executive" from BoardEx's leadership-team flag** included hundreds of Vice Presidents, which is not the Vietnam definition.

## 6. Reusable code (Philippines → next country)

| Script | Re-use | Change |
|---|---|---|
| `ph01_index_pse.py`, `ph02_download_pse.py`, `ph_fetch_filing.py` | index + resumable download with `meta.json`, shards | the exchange portal endpoints and form codes |
| `ph03`/`ph04` top-holders form + PDF table parser | logic (word positions, ranked rows) | nominee line names, column layout |
| `ph05` nationality screen, `ph11` name/label patterns S1–S5, `ph12` + broad screen | patterns, noise list, name-part logic | demonyms in the local language; local-name test |
| `ph06_ocr_17a.py` | OCR cache per page | Tesseract language |
| `ph07`/`ph08` bounds + classification | bounds, participant exclusion, strict row rule, manual overrides | nominee/participant names |
| `ph09_scan_fo_statements.py` | statement patterns | local-language phrasing |
| `ph_add_records.py`, `ph_add_holders.py`, `ph_add_ownership.py` | batch → manual CSV with validation | nationality list |
| `ph10_build_workbook.py` | flags (Vietnam rules), owner rules, Review_Open, QA, sheets | the BoardEx parts can be dropped |

## 7. About "fast" ownership shortcuts (evaluated 7 Nov 2026)
A chatbot suggested Google Sheets `IMPORTHTML/IMPORTXML` (MarketWatch or PSE Edge), or a Python call to "the public PSE Edge API" at `edge.pse.com.ph/companyDirectory/form.do`. This does not help:
- That URL is the **Company List** page: 0 mentions of "foreign" or "ownership". The project already uses it (ph01).
- PSE Edge has no foreign-ownership API. The figures sit inside filings: Top 100 forms, POR, 17-13 and annual-report tables.
- Sheets `IMPORTHTML` cannot send the POST searches PSE Edge needs, nor read PDFs.
- MarketWatch was not tested. It is a price and fundamentals site, not a source of dated, citable foreign-holding figures.

The real speed-ups are:
- a national foreign-holding file, where one exists;
- the statement-first scan;
- the registry sheet (GIS);
- for companies with foreign-ownership limits, monthly foreign-ownership reports on issuer websites (e.g. Petron, Solid Group).
