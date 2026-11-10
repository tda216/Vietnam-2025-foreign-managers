# AGENTS.md – Listed Companies & Foreign Managers, FY2025 (5 countries; shared rules + Vietnam)

Guide for coding agents (Codex, Claude Code, …) working in this repo. `CLAUDE.md` imports this file.

## Folder layout (since 7 Nov 2026)

The project folder is `Data 2025-foreign-managers/` (renamed from `Vietnam-2025-foreign-managers`). It holds one folder per country, plus the files shared by all countries at the top level:

```
Data 2025-foreign-managers/
  AGENTS.md, CLAUDE.md        shared rules (this file) and the Claude summary
  NEW_COUNTRY_PLAYBOOK.md     how to do the next country (no BoardEx; lessons from VN and PH) - READ FIRST for a new country
  README.md                   folder map and status per country
  .venv/                      Python environment shared by all countries
  vietnam/                    Vietnam: pipeline/, data/, output/ (sections below)
  philippines/                Philippines: own AGENTS.md (country rules), pipeline/, data/, output/
  <country>/                  the three remaining countries, created when their work starts
```

Cross-country files (e.g. the 5-country report, still to be written) go at the top level, not inside a country folder.

## What this project is

A research dataset covering 5 countries that use the same rules. The sections below describe Vietnam, the first country, done in 2026-11.
**All Vietnam paths below are relative to `vietnam/`.** Run Vietnam commands from inside `vietnam/`, using the shared environment one level up: `../.venv/bin/python -I pipeline/<step>.py`.

1. Classify every listed company by foreign ownership (FO) at 31/12/2025:
   - FO > 50% → `FOREIGN_MAJORITY`.
   - FO ≤ 50% → `LOCAL`.
   - Missing → `REVIEW`.
2. For `LOCAL` companies, collect every **foreign-national manager** in FY2025, in long format (1 row per person × position), with source and PDF page.
3. Set a company flag `Foreign_Manager` (1/0/blank).

Deliverables are in `output/`:
- `Vietnam_2025_Foreign_Managers.xlsx`: the main sheets are `Companies` and `Foreign_Managers`.
- `BAO_CAO_BAN_GIAO.md`: conclusions and usage guide for the client.
- `methodology.md`.

The research team works in **Vietnamese**: reply in Vietnamese, keep it simple, and avoid long tables of numbers.

## Ground rules (set by the research owner – do not relax on your own)

- Never edit raw data, and never delete valid rows. Every exclusion is a recorded decision with a reason and a page.
- Missing / UNKNOWN is **never** 0. A blank flag means "no conclusion".
- Always keep the source: document, PDF page (1-based, the number a PDF viewer shows, not the printed page number), URL, and a verbatim quote.
- When a methodology choice is open, **list the options with their trade-offs and let the user choose**. Do not silently default. The user rejected a plan once for doing that.
- Any source is acceptable if it is time-efficient and accurate: official exchange files, issuer filings, news, company websites. Paid databases (FiinPro, BoardEx) are not available.
- Commit or push only when asked.

## Decisions already made (apply them; do not re-ask)

| Topic | Rule |
|---|---|
| Year | FY2025 = held the position at any time in 2025. Record appointment/resignation dates when the source gives them |
| Who counts | Board (HĐQT), Supervisory (BKS/UBKT), Executive (TGĐ, Phó TGĐ, CFO, Kế toán trưởng, C-suite), Other_Manager (director/head level, only when a document lists them). Positions at **subsidiaries do not count**. Board-committee-only members → UNKNOWN row, `Role_Group = Other_Manager` |
| Company flag | `Foreign_Manager` = any level; `Foreign_Manager_Core` = Board/Supervisory/Executive only. Core is the comparable variable |
| Unnamed statement | A source saying "HĐQT có 1 thành viên quốc tịch nước ngoài" without a name → flag 1 (`Flag_Basis = COMPANY_LEVEL_STATEMENT`, sheet `Company_Level_Evidence`); the person stays UNKNOWN |
| Source basis | AR2025 → annual governance report 2025 (GOV2025) → AR2024 as a last resort, with a note |
| Nationality wording | "Quốc tịch: X" is best. A descriptor ("người Hàn Quốc", "Korean banker") is accepted, with Note tag `NATIONALITY_FROM_DESCRIPTOR`. "Người nước ngoài" without a country → `Is_Foreign = 1`, `Nationality = UNKNOWN`. Dual nationality → `Is_Foreign = 1`, `Dual_Nationality = 1` |
| Birthplace | A foreign place of birth or *nguyên quán*, used only when no source states nationality → `Evidence_Type = BIRTHPLACE`. Birthplace ≠ nationality in verified cases |
| Inference | Only after an exhaustive search. Mark `Evidence_Type = INFERRED`, `Nationality_Raw = INFERRED`, and `Note` = `INFERRED_STRONG` (named foreign shareholder/group representative) / `INFERRED_MEDIUM` (career/education/parent company in that country + name) / `INFERRED_WEAK` (name only) + the basis. It counts toward the flag. Never use photos. If no country can be inferred, leave the person UNKNOWN |
| Other issuers | A filing by another company about the same, identity-linked person is accepted (note `NATIONALITY_FROM_OTHER_ISSUER`) |
| Ownership | VSDC "FOL 31.12.2025" file as republished by HOSE/HNX. Foreign-listed issuers are resolved by hand in `data/manual/ownership_manual.csv` (rule `RULE_FOREIGN_LISTED_FOREIGN_CONTROLLER`). Managers are also searched for FOREIGN_MAJORITY companies with FO ≤ 55% (borderline) |
| Search depth | "C3": deep search (websites, news) for top-200 market cap ∪ FO ≥ 10% ∪ foreign holder ≥ 5% ∪ companies where a foreign Board/Exec member was already found |

## Vietnam folder layout (`vietnam/`)

```
pipeline/            numbered steps (run from inside vietnam/) + config.py, common.py, tools_add_records.py, qa_checks.py
data/manual/         HAND-REVIEWED INPUTS – the only place where facts are added or changed
  manager_records.csv      one row per foreign (or UNKNOWN) person × position, with quote/page/evidence type
  candidate_decisions.csv  why each screened name was dropped/merged (NOT_A_PERSON, OCR_NOISE, SAME_AS_RECORD,
                           NOT_A_MANAGER, NOT_FY2025, NOT_FOREIGN_STATED, SUBSIDIARY_ONLY, LABEL_PAGE_REVIEWED, …)
  candidate_promotions.csv LOW-screened names promoted to HIGH by hand
  label_page_checks.csv    nationality-label pages reviewed without a new record
  company_level_evidence.csv, ownership_manual.csv, fallback_urls.csv
  batches/*.json           every batch of records/decisions ever added (audit trail)
data/full/           intermediate CSVs of the full run (docs*.csv, candidates.csv, nationality_hits*.csv, …)
data/full/text, ocr/ per-page text/OCR (git-ignored, ~870 MB)
raw/                 downloaded PDFs/HTML (git-ignored, ~88 GB) – UNTRUSTED input
output/              deliverables
```

Not in git: `raw/`, `data/full/text/`, `data/full/ocr/`, `.venv/`, `.tools/`, and the Bloomberg input `Bloomberg-Vietnam2025_8520.xlsx`. The Bloomberg file is licensed. Place it in `vietnam/` locally (`config.ROOT` is `vietnam/`); `01_universe.py`, `07_build_excel.py` and `qa_checks.py` need it. Since 10 Nov 2026 (public repository, owner decision) the Bloomberg-derived files also stay local: every `*/data/universe.csv`, the output workbooks `*/output/*.xlsx` (they carry Market_Cap / Industry_Group, VN a Bloomberg_Raw sheet) and a few CSVs with Bloomberg columns (see `.gitignore`); rebuild them locally from the Bloomberg file.

## Setup

```bash
python3 -m venv .venv          # at the top level, shared by all countries
.venv/bin/pip install openpyxl requests beautifulsoup4 lxml pymupdf
cd vietnam
# OCR + RAR without root (Linux): download the official Ubuntu .debs and unpack them (macOS: Homebrew tesseract is used by PH)
mkdir -p .tools/debs && cd .tools/debs && apt-get download tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng \
  tesseract-ocr-osd libtesseract5 liblept5 libarchive-tools && cd ../..
for d in .tools/debs/{tesseract,libtesseract,liblept}*.deb; do dpkg -x "$d" .tools/tesseract; done
dpkg -x .tools/debs/libarchive-tools*.deb .tools/bsdtar
```

Always run Python with **`-I`**, i.e. (inside `vietnam/`) `../.venv/bin/python -I pipeline/<step>.py`, because the scripts read untrusted downloaded files. Never execute anything from `raw/`. Keep downloads in their own directories.

## Pipeline (run = `full`, or `pilot` for the 30-company pilot)

| Step | Script | Notes |
|---|---|---|
| 1 | `01_universe.py` | Bloomberg export → `data/universe.csv` (values copied verbatim) |
| 2 | `02a`–`02d` | FO notices → parse VSDC file → classify → CafeF cross-check (`02e` = checkpoint workbook) |
| 3/4 | `03b_collect_docs.py full k n` (sharded, resumable), `04_full_run.sh` | Vietstock document index + AR2025 download; zip/rar unpacked (PDF members only) |
| 5 | `03c_extract_text.py` | Page text; OCR (Tesseract `vie`) only where there is no text layer; nationality-label hits |
| 5 | `03d_roster_cafef.py`, `03e_people_from_text.py` | Today's CafeF roster; person mentions in the AR |
| 5 | `05a_candidates.py` | Candidate list (HIGH/LOW). **Slow: 15–25 min** |
| 6 | `05b_verify_docs.py`, `05d_older_docs.py`, `06a_fallback_docs.py` | On-demand AGM / personnel documents 2018–2026; fallback sources for companies with no AR2025 |
| 6 | `05c_propose_records.py` | Proposals from profile blocks (name … nationality label) – a person must still review them |
| – | `tools_add_records.py full batch.json` | Appends reviewed records/decisions to `data/manual/` (format in its docstring) |
| 7 | `07_build_excel.py full` → `qa_checks.py full` | Workbook + automatic checks (must print 0 violations); `qa_checks.py full sample` draws the manual QA sample |

Typical rebuild after adding a batch:
```bash
cd vietnam
../.venv/bin/python -I pipeline/tools_add_records.py full data/manual/batches/<batch>.json
../.venv/bin/python -I pipeline/05a_candidates.py full && ../.venv/bin/python -I pipeline/07_build_excel.py full \
  && ../.venv/bin/python -I pipeline/qa_checks.py full
```
Do not change `data/manual/` while a build is running. To stop a step, use an anchored pattern: `pkill -f "^\.\./\.venv/bin/python -I pipeline/05a"`.

## Review workflow and lessons learned (read before recording anything)

- **Screening is not evidence.** A name that "looks foreign", a CafeF roster entry or a regex hit only decides what to read next.
- **Check the page image for every OCR page and every multi-column / multi-profile page** before recording. Render it with pymupdf (`page.get_pixmap(dpi=90…110)`) and view the PNG. The text layer interleaves columns, so a career or birth year often belongs to the neighbouring profile. This happened at REE, DHC and APS.
- OCR errors:
  - Merged words hide nationalities, e.g. "ẤnĐộ".
  - Names get misspelled, producing variants such as "Mare Lee" / "Marc Lee". Settle variants with `SAME_AS_RECORD`; never create a second person.
- PDF spreads hold two printed pages on one PDF page. `Page` is always the PDF page index.
- **A candidate CV is not a position.** Check the election result in the AGM resolution before counting someone. Example: SBT Vancliff, who was a candidate but not elected.
- **Web-search summaries are not evidence.** Open the page and quote it verbatim; put the URL and access date in `Other_Sources`.
  - Read carefully: on an italaw page, "U.S." turned out to be part of a company name, not a nationality.
  - Disclosure-form PDFs are often scans, with the nationality field only in the page image.
- Check that downloaded "documents" really are documents. Some company URLs redirect to the homepage.
- hnx.vn is not reachable from this network. Use CafeF/Vietstock republications.
- QA rejects a nationality that is not in `config.NATIONALITY_EN`. Add the country there (EN + VN names), never a free-text value.
- `.gitignore` comments must be on their own line, because a trailing `# …` breaks the pattern.
- pandas reads `Is_Foreign` as a float (1.0). Compare it numerically.

## Status at hand-over (02/11/2026)

- `Companies`:
  - 1,553 LOCAL companies: 145 FOUND, 1,356 NONE_FOUND, 52 blank (49 NO_SOURCE, 2 UNRESOLVED, 1 NOT_SEARCHED).
  - QA: 0 violations.
- `Foreign_Managers`: 320 rows (284 foreign, 36 UNKNOWN).
- Open items:
  - SVN (Michael Marc Lee) and VPX (Steve Yam): no source and no inferable country.
  - VFS (VinFast, US-listed): managers not searched.
  - The manual QA sample (`data/full/qa_sample_*.csv`) has **not** been reviewed yet.
  - The workbook's README sheet still names a deleted `Checkpoint1_…xlsx`. The code is fixed; this needs a rebuild with the Bloomberg file present.

## Adapting to another country

**Start with `NEW_COUNTRY_PLAYBOOK.md`** (top level). It covers the day-0 decisions, a statement-first approach to ownership, managers from the companies' own director/officer tables, and the lessons from the Philippines. BoardEx is no longer used (owner, 7 Nov 2026). Create the country's own folder at the top level, next to `vietnam/` and `philippines/`.

Reusable as-is:
- The schema, flag rules, evidence types and inference tiers.
- `05a` logic, `tools_add_records.py`, `07_build_excel.py` and `qa_checks.py`.
- The manual-review workflow above.

Country-specific, so replace these:
- `config.py`: `COUNTRY`, `YEAR`, `FO_AS_OF`, file names, `NATIONALITY_EN` (add local-language country names).
- Ownership source (`02a`/`02b`): the local exchange or depository foreign-ownership file.
- Document source (`sources_vietstock.py`, `03b`): the local filing portal.
- OCR language in `03c`.
- The name screen (`03d`/`05a` flag names that are not Vietnamese syllables): a different country needs its own "non-local name" test.
- Label/demonym terms in `03c`.

Follow the same three checkpoints with the research owner:
1. Ownership distribution and the REVIEW list.
2. A 30-company pilot workbook.
3. The final workbook with QA and the manual sample.
