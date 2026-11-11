# AGENTS.md – Vietnam FY2025 (country 1 of 5 – handed over 02/11/2026)

Study-wide rules, repo layout, setup and review lessons: [../AGENTS.md](../AGENTS.md). This file holds what is specific to Vietnam.
Paths below are relative to `vietnam/`; run the scripts from the repo root (`.venv/bin/python -I vietnam/pipeline/<step>.py`).

Deliverables in `output/`: `Vietnam_2025_Foreign_Managers.xlsx` (local only since 10/11/2026: it carries Bloomberg fields;
the report refers to the current copy `1_Vietnam_2025_Foreign_Managers.xlsx`), `BAO_CAO_BAN_GIAO.md` (+ .docx), `methodology.md`.
Licensed input (not in git): `Bloomberg-Vietnam2025_8520.xlsx`. Place it in `vietnam/`; `01_universe.py`, `07_build_excel.py`
and `qa_checks.py` need it.

## Decisions specific to Vietnam (apply them; do not re-ask)

| Topic | Rule |
|---|---|
| Source basis | AR2025 → annual governance report 2025 (GOV2025) → AR2024 as a last resort, with a note |
| Ownership | VSDC "FOL 31.12.2025" file as republished by HOSE/HNX. Foreign-listed issuers are resolved by hand in `data/manual/ownership_manual.csv` (rule `RULE_FOREIGN_LISTED_FOREIGN_CONTROLLER`) |
| Search depth | "C3": deep search (websites, news) for top-200 market cap ∪ FO ≥ 10% ∪ foreign holder ≥ 5% ∪ companies where a foreign Board/Exec member was already found |
| Paid databases | None (no FiinPro, no BoardEx) |

## Folder contents

```
pipeline/            numbered steps + config.py, sources_vietstock.py, tools_add_records.py, qa_checks.py
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

## Pipeline (run = `full`, or `pilot` for the 30-company pilot)

| Step | Script | Notes |
|---|---|---|
| 1 | `01_universe.py` | Bloomberg export → `data/universe.csv` (values copied verbatim) |
| 2 | `02a`–`02d` | FO notices → parse VSDC file → classify → CafeF cross-check (`02e` = checkpoint workbook) |
| 3/4 | `03b_collect_docs.py full k n` (sharded, resumable), `04_full_run.sh` | Vietstock document index + AR2025 download; zip/rar unpacked (PDF members only, `shared/archives.py`) |
| 5 | `03c_extract_text.py` | Page text; OCR (Tesseract `vie`) only where there is no text layer; nationality-label hits |
| 5 | `03d_roster_cafef.py`, `03e_people_from_text.py` | Today's CafeF roster; person mentions in the AR |
| 5 | `05a_candidates.py` | Candidate list (HIGH/LOW). **Slow: 15–25 min** |
| 6 | `05b_verify_docs.py`, `05d_older_docs.py`, `06a_fallback_docs.py` | On-demand AGM / personnel documents 2018–2026; fallback sources for companies with no AR2025 |
| 6 | `05c_propose_records.py` | Proposals from profile blocks (name … nationality label) – a person must still review them |
| – | `tools_add_records.py full batch.json` | Appends reviewed records/decisions to `data/manual/` (format in its docstring) |
| 7 | `07_build_excel.py full` → `qa_checks.py full` | Workbook + automatic checks (must print 0 violations); `qa_checks.py full sample` draws the manual QA sample |

Typical rebuild after adding a batch (from the repo root):
```bash
.venv/bin/python -I vietnam/pipeline/tools_add_records.py full vietnam/data/manual/batches/<batch>.json
.venv/bin/python -I vietnam/pipeline/05a_candidates.py full && .venv/bin/python -I vietnam/pipeline/07_build_excel.py full \
  && .venv/bin/python -I vietnam/pipeline/qa_checks.py full
```

## Lessons (Vietnam)

- hnx.vn is not reachable from this network. Use CafeF/Vietstock republications.
- The name screen (`03d`/`05a`) flags names that are not Vietnamese syllables; CafeF rosters show today's board, not FY2025.
- `config.USER_AGENT` is still a browser string from the first run; new countries use the honest `corp-data-research/1.0`.

## Status at hand-over (02/11/2026)

- `Companies`:
  - 1,553 LOCAL companies: 145 FOUND, 1,356 NONE_FOUND, 52 blank (49 NO_SOURCE, 2 UNRESOLVED, 1 NOT_SEARCHED).
  - QA: 0 violations.
- `Foreign_Managers`: 320 rows (284 foreign, 36 UNKNOWN).
- Updated 04/11/2026 (batches `svn_*`, `vpx_*`, `vic_*`; see `output/BAO_CAO_BAN_GIAO.md`): 146 FOUND; SVN = 1 by the owner's own
  coding rule (Michael Marc Lee's country stays UNKNOWN); VPX (Steve Yam) UNRESOLVED.
- Open items (paused by the research owner on 09/11/2026 – do not pursue unless asked):
  - VFS (VinFast, US-listed): managers not searched.
  - The manual QA sample (`data/full/qa_sample_*.csv`) has **not** been reviewed yet.
  - The workbook's README sheet still names a deleted `Checkpoint1_…xlsx`. The code is fixed; this needs a rebuild with the Bloomberg file present.
  - Earlier commits still hold the workbook with the `Bloomberg_Raw` sheet (removed from git on 10/11/2026; history unchanged).
- 09/11/2026: moved from the repo root into `vietnam/`; shared helpers moved to `../shared/`. Logic unchanged
  (`05a` re-run gives the same `candidates.csv`).
