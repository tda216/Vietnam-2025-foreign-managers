# AGENTS.md – Listed Companies & Foreign Managers (FY2025, 5 countries)

Guide for coding agents (Codex, Claude Code, …) working in this repo. `CLAUDE.md` imports this file.
This file holds the rules shared by every country. Each country folder has its own `AGENTS.md` (and a `CLAUDE.md` that
imports it) with its sources, pipeline, lessons and status. **Read it before working in that folder.**

| Country | Folder | Status |
|---|---|---|
| Vietnam (1 of 5) | `vietnam/` – [vietnam/AGENTS.md](vietnam/AGENTS.md) | handed over 02/11/2026 |
| Philippines | `philippines/` – [philippines/AGENTS.md](philippines/AGENTS.md) | done 07/11/2026 (data/ and output/ stay local) |
| Thailand | `thailand/` – [thailand/AGENTS.md](thailand/AGENTS.md) | handed over 09/11/2026; country search 11/11/2026 |
| Indonesia | `indonesia/` – [indonesia/AGENTS.md](indonesia/AGENTS.md), `OPEN_DECISIONS.md` | done 11/11/2026 |
| Malaysia | `malaysia/` – [malaysia/AGENTS.md](malaysia/AGENTS.md) | in progress (universe + report index) |

**Starting a new country: read [NEW_COUNTRY_PLAYBOOK.md](NEW_COUNTRY_PLAYBOOK.md) first** (day-0 decisions, statement-first
ownership, managers from the companies' own director/officer tables, lessons from Vietnam and the Philippines).
Status per country for people: [README.md](README.md).

## What this project is

A research dataset covering 5 countries with the same rules.

1. Classify every listed company by foreign ownership (FO) at 31/12/2025:
   - FO > 50% → `FOREIGN_MAJORITY`.
   - FO ≤ 50% → `LOCAL`.
   - Missing → `REVIEW`.
2. For `LOCAL` companies, collect every **foreign-national manager** in FY2025, in long format (1 row per person × position), with source and PDF page.
3. Set a company flag `Foreign_Manager` (1/0/blank).

Deliverables of each country are in `<country>/output/`:
- `<Country>_2025_Foreign_Managers.xlsx`: the main sheets are `Companies` and `Foreign_Managers`.
- `BAO_CAO_BAN_GIAO.md`: conclusions and usage guide for the client.
- `methodology.md`.

The research team works in **Vietnamese**: reply in Vietnamese, keep it simple, and avoid long tables of numbers.

## Ground rules (set by the research owner – do not relax on your own)

- Never edit raw data, and never delete valid rows. Every exclusion is a recorded decision with a reason and a page.
- Missing / UNKNOWN is **never** 0. A blank flag means "no conclusion".
- Always keep the source: document, PDF page (1-based, the number a PDF viewer shows, not the printed page number), URL, and a verbatim quote.
- When a methodology choice is open, **list the options with their trade-offs and let the user choose**. Do not silently default. The user rejected a plan once for doing that.
- Any source is acceptable if it is time-efficient and accurate: official exchange files, issuer filings, news, company websites.
  Paid databases (FiinPro, BoardEx) are not available, except extracts the team supplies as input files (Thailand: BoardEx).
- Respect each site's robots.txt and terms. Use an honest User-Agent (`corp-data-research/1.0`, never a personal e-mail),
  keep ≥ 3 s between requests to one host, and stop on 403/429 or a bot check. Never work around a block.
- The GitHub repo is **public**: licensed inputs (Bloomberg, BoardEx) and anything derived from them that carries personal
  data stay out of git (see `.gitignore`). Since 10/11/2026 (owner decision) Bloomberg-derived files also stay local: every
  `*/data/universe.csv`, the output workbooks `*/output/*.xlsx` (Market_Cap, Industry_Group; VN: `Bloomberg_Raw` sheet) and the
  CSVs with Bloomberg columns listed in `.gitignore`. Rebuild them locally from the Bloomberg file.
- BoardEx is not used for new countries (owner, 07/11/2026). Thailand keeps the BoardEx extract the team supplied.
- Commit or push only when asked.

## Decisions already made for every country (apply them; do not re-ask)

| Topic | Rule |
|---|---|
| Year | FY2025 = held the position at any time in 2025. Record appointment/resignation dates when the source gives them |
| Who counts | Board (HĐQT), Supervisory (BKS/UBKT), Executive (TGĐ, Phó TGĐ, CFO, Kế toán trưởng, C-suite), Other_Manager (director/head level, only when a document lists them). Positions at **subsidiaries do not count**. Board-committee-only members → UNKNOWN row, `Role_Group = Other_Manager` |
| Company flag | `Foreign_Manager` = any level; `Foreign_Manager_Core` = Board/Supervisory/Executive only. Core is the comparable variable |
| Unnamed statement | A source saying "HĐQT có 1 thành viên quốc tịch nước ngoài" without a name → flag 1 (`Flag_Basis = COMPANY_LEVEL_STATEMENT`, sheet `Company_Level_Evidence`); the person stays UNKNOWN |
| Source basis | The FY2025 annual report → other FY2025 governance filings → the FY2024 report as a last resort, with a note. Country details in the country `AGENTS.md` |
| Nationality wording | "Quốc tịch: X" is best. A descriptor ("người Hàn Quốc", "Korean banker") is accepted, with Note tag `NATIONALITY_FROM_DESCRIPTOR`. "Người nước ngoài" without a country → `Is_Foreign = 1`, `Nationality = UNKNOWN`. Dual nationality → `Is_Foreign = 1`, `Dual_Nationality = 1` |
| Birthplace | A foreign place of birth or *nguyên quán*, used only when no source states nationality → `Evidence_Type = BIRTHPLACE`. Birthplace ≠ nationality in verified cases |
| Inference | Only after an exhaustive search. Mark `Evidence_Type = INFERRED`, `Nationality_Raw = INFERRED`, and `Note` = `INFERRED_STRONG` (named foreign shareholder/group representative) / `INFERRED_MEDIUM` (career/education/parent company in that country + name) / `INFERRED_WEAK` (name only) + the basis. It counts toward the flag. Never use photos. If no country can be inferred, leave the person UNKNOWN |
| Other issuers | A filing by another company about the same, identity-linked person is accepted (note `NATIONALITY_FROM_OTHER_ISSUER`) |
| Ownership | Threshold 50% (`FO_THRESHOLD`). Foreign-listed issuers are resolved by hand in `<country>/data/manual/ownership_manual.csv`. Managers are also searched for FOREIGN_MAJORITY companies with FO ≤ 55% (borderline, `FO_BORDERLINE_UPPER`). Ownership source per country: see the country `AGENTS.md` |

## Repo layout

```
AGENTS.md, CLAUDE.md   this guide (study-wide rules) + a short Vietnamese summary; README.md = folder map and status for people
NEW_COUNTRY_PLAYBOOK.md how to do the next country fast and accurately
shared/                code used by Vietnam and Thailand (it imports the *country* config.py – see "Running").
                       Philippines (ph*), Malaysia (my*) and Indonesia (id*) pipelines are self-contained and do not use it yet
  common.py              cached + throttled HTTP, download with .meta.json/SHA256, CSV I/O, strip_accents; TOOLS = .tools/
  archives.py            PDF members of untrusted zip/RAR archives (size caps, names flattened, bsdtar for RAR)
  xlsx_tables.py         add_table / cell_value: one styled sheet per table in the workbooks
  nationality.py         accepted nationality values (English + Vietnamese names); country configs add local-language names
<country>/             vietnam/, thailand/, … – self-contained, same layout:
  AGENTS.md, CLAUDE.md   country guide (sources, pipeline, lessons, status)
  pipeline/              numbered steps + config.py (ROOT = the country folder) + qa_checks.py + tools_add_*.py
  data/manual/           HAND-REVIEWED INPUTS – the only place where facts are added or changed; batches/*.json = audit trail
  data/                  intermediate CSVs (git); data/full/text, ocr, logs = page text/OCR/logs (git-ignored)
  raw/                   downloaded PDFs/HTML (git-ignored) – UNTRUSTED input
  output/                deliverables
  *.xlsx                 licensed inputs (Bloomberg, BoardEx) sit here (git-ignored)
.venv/, .tools/        shared Python environment and tesseract/bsdtar (git-ignored)
```

Paths stored in the CSVs (`Local_File`, `Container_File`, …) are relative to the country folder (`raw/docs/<T>/…`).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install openpyxl requests beautifulsoup4 lxml pymupdf rapidfuzz
# OCR + RAR without root: download the official Ubuntu .debs and unpack them
mkdir -p .tools/debs && cd .tools/debs && apt-get download tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng \
  tesseract-ocr-osd libtesseract5 liblept5 libarchive-tools && cd ../..
for d in .tools/debs/{tesseract,libtesseract,liblept}*.deb; do dpkg -x "$d" .tools/tesseract; done
dpkg -x .tools/debs/libarchive-tools*.deb .tools/bsdtar
```

## Running

- Run from the repo root: `.venv/bin/python -I <country>/pipeline/<step>.py` (every country). Paths come from
  `config.ROOT`/`Path(__file__)`, so Vietnam also runs from inside `vietnam/` (`../.venv/bin/python -I pipeline/<step>.py`).
- Always use **`-I`**, because the scripts read untrusted downloaded files. Never execute anything from `raw/`. Keep
  downloads in their own directories.
- `-I` drops the script's folder from `sys.path`, so every script starts with
  `sys.path[:0] = [<its own pipeline folder>, <repo>/shared]` (copy the line from an existing step). The country
  `config.py` therefore wins, and `shared/` modules (`from config import …`) bind to that country's paths, User-Agent
  and throttle.
- To stop a step, use an anchored pattern: `pkill -f "^.venv/bin/python -I vietnam/pipeline/05a"`.
- Do not change `<country>/data/manual/` while a build of that country is running.
- A change in `shared/` touches every country. Re-run a cheap step of each country and compare the outputs, for
  example Vietnam `05a` (git diff) and Thailand `07` → `08` → `qa_checks`.
- Python randomises the iteration order of string sets on every run, and `-I` ignores `PYTHONHASHSEED`. Sort before
  picking among ties, otherwise two runs give different rows (seen in Thailand `07`, BoardEx matching).

## Review workflow and lessons learned (all countries – read before recording anything)

- **Screening is not evidence.** A name that "looks foreign", a roster entry or a regex hit only decides what to read next.
- **Check the page image for every OCR page and every multi-column / multi-profile page** before recording. Render it with pymupdf (`page.get_pixmap(dpi=90…110)`) and view the PNG. The text layer interleaves columns, so a career or birth year often belongs to the neighbouring profile. This happened at REE, DHC and APS (Vietnam) and LRH (Thailand).
- OCR errors:
  - Merged words hide nationalities, e.g. "ẤnĐộ".
  - Names get misspelled, producing variants such as "Mare Lee" / "Marc Lee". Settle variants with `SAME_AS_RECORD`; never create a second person.
- PDF spreads hold two printed pages on one PDF page. `Page` is always the PDF page index.
- **A candidate CV is not a position.** Check the election result in the AGM resolution before counting someone. Example: SBT Vancliff, who was a candidate but not elected.
- **Web-search summaries are not evidence.** Open the page and quote it verbatim; put the URL and access date in `Other_Sources`.
  - Read carefully: on an italaw page, "U.S." turned out to be part of a company name, not a nationality.
  - Disclosure-form PDFs are often scans, with the nationality field only in the page image.
- Check that downloaded "documents" really are documents. Some company URLs redirect to the homepage; some portals return a tiny "file not found" page.
- QA rejects a nationality that is not in the country's `config.NATIONALITY_EN`. Add the country to `shared/nationality.py`
  (English and Vietnamese names) or to the country `config.py` (local-language names), never a free-text value.
- `.gitignore` comments must be on their own line, because a trailing `# …` breaks the pattern.
- pandas reads `Is_Foreign` as a float (1.0). Compare it numerically.

## Adding a country

1. Read `NEW_COUNTRY_PLAYBOOK.md`. Create `<country>/` with the layout above. Put the licensed inputs in the folder itself; `.gitignore` already
   ignores `/*/raw/`, `/*/data/full/{text,ocr,logs}/` and `/*/*.xlsx` for every country. Add rules for any other
   licensed or personal-data file (Thailand: workbook and BoardEx CSVs).
2. Write `pipeline/config.py` with the same names as the existing ones: `ROOT` (= the country folder), `RAW`,
   `RAW_WEB_CACHE`, `RAW_OWNERSHIP`, `RAW_DOCS`, `DATA`, `OUTPUT`, `BLOOMBERG_FILE`, `COUNTRY`, `YEAR`, `FO_AS_OF`,
   `FO_THRESHOLD`, `FO_BORDERLINE_UPPER`, `USER_AGENT` (honest, as in Thailand), `MIN_SECONDS_BETWEEN_REQUESTS`, and
   `NATIONALITY_EN = dict(shared NATIONALITY_EN) | {local-language names}`.
3. Reusable as-is:
   - The schema, flag rules, evidence types and inference tiers.
   - The manual-review workflow above.
   - The QA check names and the batch JSON format of `tools_add_*.py`.
   - Templates: Thailand's pipeline fits a country whose filings use a fixed template with a nationality field.
     Vietnam's fits a country where nationality must be mined from free text: `05a` candidate screen and `03c` OCR.
4. Country-specific, so replace these:
   - The ownership source: the local exchange or depository foreign-ownership file.
   - The document source: the local filing portal.
   - The OCR language.
   - The name screen: the "non-local name" test (Vietnam: non-Vietnamese syllables; Thailand: trigram model).
   - Label/demonym terms.
5. Write `<country>/AGENTS.md` and `<country>/CLAUDE.md` (`@AGENTS.md`), and add a row to the table at the top.

Follow the same three checkpoints with the research owner:
1. Ownership distribution and the REVIEW list.
2. A 30-company pilot workbook.
3. The final workbook with QA and the manual sample.
