# Data 2025 – Listed companies and foreign managers, FY2025 (5 countries)

A research dataset. For every listed company:
1. Classify it by foreign ownership: `FOREIGN_MAJORITY` (> 50%) or `LOCAL` (≤ 50%).
2. For `LOCAL` firms, find every foreign-national board member or manager in FY2025, with the source document, page and a verbatim quote.

All countries use the same rules and the same workbook layout.

## Folder map

| Path | What it is |
|---|---|
| `AGENTS.md` | Shared rules for agents (evidence, flags, review workflow, repo layout). Each country folder has its own `AGENTS.md`. `CLAUDE.md` is a short Vietnamese summary |
| `NEW_COUNTRY_PLAYBOOK.md` | How to do the next country fast and accurately (no BoardEx; lessons from Vietnam and the Philippines). **Read first** |
| `vietnam/` | Vietnam: `pipeline/`, `data/` (hand-reviewed inputs in `data/manual/`), `output/` (workbook, handover report, methodology) |
| `philippines/` | Philippines: `AGENTS.md` (country rules and owner decisions), `pipeline/` (ph01–ph12), `data/manual/`, `raw/` (filings, not in git), `output/` |
| `malaysia/` | Malaysia (started 7 Nov 2026): `AGENTS.md` (country rules and owner decisions), `pipeline/` (my01–my03), `data/`, `raw/` (not in git) |
| `indonesia/` | Indonesia (started 7 Nov 2026): `AGENTS.md` (country rules and owner decisions), `OPEN_DECISIONS.md` (questions waiting for the owner), `pipeline/` (id01–id10 + helpers), `data/`, `raw/` (not in git) |
| `thailand/` | Thailand: `AGENTS.md` (country rules, owner decisions, status), `pipeline/` (01–11), `data/` (hand-reviewed inputs in `data/manual/`), `output/` (handover report, methodology) |
| `shared/` | Python helpers used by Vietnam and Thailand (HTTP cache/throttle, archives, workbook tables, nationality list) |
| Top level | Cross-country files, e.g. the 5-country report (not written yet) |
| `.venv/` | Python environment shared by all countries. Always run with `-I` |

## Status

| Country | Status | Main result |
|---|---|---|
| Vietnam | Done, handed over 2 Nov 2026 | `vietnam/output/1_Vietnam_2025_Foreign_Managers.xlsx`: 1,553 LOCAL firms, 146 with a foreign manager (`Foreign_Manager = 1`), 36 with one in an executive/management position |
| Philippines | Done 7 Nov 2026 | `philippines/output/Philippines_2025_Foreign_Managers.xlsx`: 257 LOCAL firms, 91 with a foreign manager (88 at board/executive level), 34 with one in an executive/management position (updated 9 Nov 2026) |
| Malaysia | In progress (started 7 Nov 2026): universe, annual-report index and availability check done (605 of 1,025 FY2025 reports downloadable by script) | – |
| Indonesia | Done 11 Nov 2026 (manual QA sample reviewed): workbook `indonesia/output/Indonesia_2025_Foreign_Managers.xlsx` – 806 LOCAL / 139 foreign-majority / 8 FO open; 159 LOCAL firms with foreign managers (335 rows), 572 none found, 22 unresolved, 53 without AR 2025 (delisted or suspended by IDX; excluded from the 753-firm sample, owner 11 Nov 2026: 21.1 % with foreign managers); QA 0 violations; handover report `indonesia/output/HANDOVER_REPORT.md` (+ .docx) | – |
| Thailand | Handed over 9 Nov 2026; country of foreign people searched on the web 10–11 Nov 2026 | `thailand/output/Thailand_2025_Foreign_Managers.xlsx` (in git; contains Bloomberg + BoardEx fields): 842 LOCAL firms, 215 with a foreign manager (600 people; 113 without a known country), QA 0 violations; handover report `thailand/output/BAO_CAO_BAN_GIAO.md` |

## Running

- **Vietnam**: from the top level, run `.venv/bin/python -I vietnam/pipeline/<step>.py full` (or from inside `vietnam/`: `../.venv/bin/python -I pipeline/<step>.py full`). The licensed Bloomberg file `Bloomberg-Vietnam2025_8520.xlsx` must be placed in `vietnam/` for steps 01 and 07 and for QA.
- **Indonesia**: from the top level, run `.venv/bin/python -I indonesia/pipeline/<script>.py` (steps in `indonesia/AGENTS.md`). The licensed Bloomberg file `Bloomberg-Indonesia2025.xlsx` must be placed in `indonesia/`.
- **Malaysia**: from the top level, run `.venv/bin/python -I malaysia/pipeline/<script>.py` (steps in `malaysia/AGENTS.md`). The licensed Bloomberg file `Bloomberg-malaysia2025.xlsx` must be placed in `malaysia/`.
- **Thailand**: from the top level, run `.venv/bin/python -I thailand/pipeline/<step>.py` (steps in `thailand/AGENTS.md`). The licensed Bloomberg and BoardEx files must be placed in `thailand/`.
- **Philippines**: from the top level, run `.venv/bin/python -I philippines/pipeline/<script>.py`. The workbook is built by `ph10_build_workbook.py` (QA must report 0 violations).
