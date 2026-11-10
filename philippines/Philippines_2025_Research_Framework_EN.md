# Listed Companies and Foreign Managers — Philippines FY2025

Prepared: 4 November 2026.

This English research brief adapts the agreed Vietnam project framework to the Philippines. It defines the intended study; it does not report Philippine research results. The Philippine company list has not yet been supplied, and the country-specific data sources and pipeline have not yet been implemented.

## 1. Objective and deliverables

For each security in the supplied company list:

1. Classify the issuer using a foreign-ownership observation measured during calendar year 2025, retaining its actual measurement date.
2. For companies classified as LOCAL, identify every foreign-national manager who held an eligible position at any time in 2025.
3. Produce company-level indicators and an auditable person-by-position dataset.

Also search FOREIGN_MAJORITY companies with foreign ownership above 50% and at or below 55%, following the agreed borderline rule.

Planned deliverables:

- `Philippines_2025_Foreign_Managers.xlsx`, with `Companies` and `Foreign_Managers` as the main sheets.
- `HANDOVER_REPORT_EN.md`, explaining results, use, limitations, and outstanding cases.
- `methodology_EN.md`, documenting the implemented method and decisions.

Documentation, standardized labels, and reporting will be in English. Preserve source quotations, names, and raw position titles as written. Any English translation of a quotation must be identified separately from the verbatim evidence.

## 2. Company universe and foreign ownership

Preserve the supplied company list and its original values. Record exclusions, including their reason and supporting evidence, while retaining the original rows. If the input is a Bloomberg export, retain an unchanged values copy in `Bloomberg_Raw`.

| Foreign ownership measured during 2025 | Ownership_Type |
|---|---|
| Above 50% | FOREIGN_MAJORITY |
| At or below 50% | LOCAL |
| Missing or insufficient to classify | REVIEW |

LOCAL is a foreign-ownership classification; it is not a finding about every shareholder's nationality or ultimate control.

Use actual foreign shareholding, not the maximum permitted foreign ownership or remaining foreign investment capacity. Keep the measurement date, calculation basis, numerator and denominator where available, source URL, document, page, and supporting quotation. Preserve conflicting observations for review rather than overwriting them silently.

The research owner relaxed the date requirement on 5 November 2026: any ownership measurement date in 2025 is acceptable; 31 December is not mandatory. A document published in 2026 can be used when its ownership observation is dated in 2025. Retain each observation's actual date. If several observations are available, preserve them and resolve the selection policy explicitly before assigning a single study value; do not average observations or silently choose a value that changes the classification around 50%.

The Philippine ownership source must be verified before collection. If the available source does not provide the agreed measure or date, present the available alternatives, their coverage and trade-offs to the research owner before adopting a substitute.

Companies listed outside the Philippines require documented manual review. The existing Vietnam rule for foreign-listed issuers is a precedent to examine against Philippine evidence; absence of disclosed Filipino shareholders alone must not silently become a new ownership rule.

## 3. Eligible managers and time period

FY2025 means holding an eligible position at any time in calendar year 2025, including a position that ended during the year. Record appointment and resignation/departure times when the source provides them, preserving the source's stated precision. Leave an undisclosed departure time blank; BoardEx's far-future placeholders are not actual departure dates. Verify actual appointment or election; a candidate biography alone does not establish that the person held office.

| Role_Group | Scope |
|---|---|
| Board | Board chair and directors |
| Supervisory | Supervisory or audit oversight roles mapped to the agreed definition |
| Executive | CEO, president/general manager where applicable, deputies, CFO, chief accountant, and other C-suite roles |
| Other_Manager | Director/head-level managers only when listed in the source document |

Map Philippine titles to these groups using the role and context in the filing. Refer ambiguous mappings to the research owner. The unit of observation is **each listed company in the research sample**. Attribute an eligible position to the listed company where the person actually held it. If a subsidiary is separately listed and in the sample, count the person at that subsidiary, not automatically at its listed parent. If a person holds eligible roles at both sampled listed companies, record the person separately for each company. Positions held only at unlisted subsidiaries are outside the study regardless of country. A role at a listed subsidiary outside the study sample is outside this sample. Verify the employing entity and its listing/scope status before inclusion; unresolved cases remain open. Record `UNLISTED_SUBSIDIARY_ONLY` exclusions with entity, reason, and source PDF page or workbook row, while preserving source rows.

For a person whose only qualifying connection is membership of a board committee, retain an UNKNOWN row with `Role_Group = Other_Manager`, following the existing rule. Leave `Management_Include` available for the research owner's inclusion decision.

## 4. Nationality and evidence

Assess whether the person has a nationality other than Philippine nationality, applying the agreed dual-nationality rule. Nationality and foreign ownership are separate variables.

Apply the established evidence rules:

1. **Explicit nationality:** prefer a nationality or citizenship field identifying the person.
2. **Nationality descriptor:** accept wording such as “Japanese executive” when it unambiguously describes the same person. Add `NATIONALITY_FROM_DESCRIPTOR` to `Note`.
3. **Foreign national, country unspecified:** set `Is_Foreign = 1`, `Nationality = UNKNOWN` when the source explicitly establishes foreign nationality without naming a country.
4. **Dual nationality:** set `Is_Foreign = 1` and `Dual_Nationality = 1` when the source states a foreign nationality alongside another nationality.
5. **Other issuer's disclosure:** accept evidence about an identity-linked person from another issuer. Add `NATIONALITY_FROM_OTHER_ISSUER`.
6. **Birthplace or ancestral origin:** use the agreed proxy only when no source states nationality. Mark `Evidence_Type = BIRTHPLACE`. This proxy does not establish citizenship.
7. **Inference:** use only after an exhaustive source search. Set `Evidence_Type = INFERRED`, `Nationality_Raw = INFERRED`, and record one of the following tags and the actual basis in `Note`.

| Inference tag | Agreed basis |
|---|---|
| INFERRED_STRONG | Named representative of a foreign shareholder or group |
| INFERRED_MEDIUM | Career, education, or parent-company connection to a country, together with the name |
| INFERRED_WEAK | Name alone, after exhausting other sources |

These labelled proxies and inferences count toward the agreed indicator, but must remain distinguishable from direct nationality evidence. Never use photographs as evidence. If foreign status cannot be established under the agreed rules and no country can be inferred, retain UNKNOWN with `Is_Foreign` blank.

Automated name screening only prioritizes review. The Vietnam name classifier cannot be transferred unchanged; a Philippine screening approach must be examined during the pilot before adoption.

Record-specific overrides in the Vietnam project, including the Michael Marc Lee/SVN decision dated 4 November 2026, remain specific to those records. They do not establish a general rule that missing local nationality or identification proves foreign nationality.

## 5. Company indicators

`Foreign_Manager` covers all eligible role groups. `Foreign_Manager_Core` covers Board, Supervisory, and Executive only and is the main comparable variable.

| Flag_Status | Foreign_Manager | Meaning |
|---|---|---|
| FOUND | 1 | At least one qualifying foreign person, or an accepted company-level statement |
| NONE_FOUND | 0 | Source basis reviewed, screening completed, and no unresolved HIGH candidate or UNKNOWN person remains |
| UNRESOLVED | Blank | Unresolved candidate or UNKNOWN person, with no positive evidence sufficient for flag 1 |
| NO_SOURCE | Blank | No readable accepted source basis |
| NOT_SEARCHED | Blank | Research has not been completed |
| OUT_OF_SCOPE | Blank | Outside the agreed search scope |

A source stating that the board includes a foreign-national member is sufficient for flag 1 even when it does not give a name. Record the statement in `Company_Level_Evidence`, with `Flag_Basis = COMPANY_LEVEL_STATEMENT`; do not invent a named person or nationality.

A positive company flag can coexist with unresolved additional people. A zero means “none found under this method,” not “every manager verified as Filipino.” Missing values must never be converted to zero. Do not derive the Core flag solely from a positive Other_Manager record.

## 6. Sources and review workflow

Use the established company-level source order: annual report 2025 (AR2025), then annual governance report 2025 (GOV2025), then annual report 2024 (AR2024) as a documented last resort. An AR2024 fallback reflects the roster at its publication date and does not establish complete FY2025 coverage.

Use additional filings, election results, appointment/resignation notices, biographies, company websites, and news to verify people. A separately listed subsidiary's own filing can establish a role at that subsidiary. Verify the issuer identity before assigning the role; a parent's filing can support a person's nationality but does not itself transfer a subsidiary position to the parent. Older documents may support nationality, but the FY2025 role must be established separately. Current management rosters are screening aids rather than proof of a 2025 position. No paid database is assumed available.

Workflow:

1. Import the company universe and resolve identifiers and recorded exclusions.
2. Collect and reconcile ownership observations; produce the REVIEW list.
3. Index and download reports, keeping URLs, download timestamps, and file hashes.
4. Extract text by PDF page; OCR pages without usable text.
5. Screen nationality labels, foreign-national descriptions, and candidate names.
6. Review source pages and verify identity, role, dates, and nationality.
7. Record accepted rows, unresolved people, rejected candidates, spelling variants, and page-review decisions in reviewed inputs.
8. Rebuild the workbook, resolve QA violations, and complete the manual sample.

Open the page image for every OCR-derived record and every multi-column or multi-profile page before recording evidence. Use PDF viewer page numbers starting at 1, not printed page numbers. Open web sources and quote their actual content; search-result summaries are not evidence. Record the URL and access date for web evidence.

Apply C3 deep research to the union of: top 200 by market capitalization; foreign ownership at least 10%; a foreign holder with at least 5%; and companies where a foreign Board or Executive member has already been found. Keep the reason and evidence of completed searches.

## 7. Dataset and audit trail

`Companies` contains one row per input security. `Foreign_Managers` contains one row per person × position, with a shared company-specific `Manager_ID` for the same person across positions.

Core person fields:

`Company`, `Ticker`, `Year`, `Manager_Name`, `Raw_Position`, `Role_Group`, `Nationality`, `Nationality_Raw`, `Is_Foreign`, `Dual_Nationality`, `Appointed_Date`, `Resigned_Date`, `Source`, `Source_URL`, `Local_File`, `Page`, `Evidence_Type`, `Evidence_Quote`, `Other_Sources`, `Reviewed_On`, `Note`, and `Management_Include`. For any role mentioned through a corporate group, record the actual employing entity and the evidence that it is the sampled listed issuer before assigning the row to that issuer.

Use standardized English country names while preserving nationality wording in `Nationality_Raw`. Keep reviewed factual changes in the country's own `data/manual/` files and retain batch JSON audit records. Use separate manual files for records, candidate decisions, promotions, label-page checks, company-level evidence, ownership decisions, and fallback URLs.

Preserve valid records and raw files. Merge spelling variants through recorded decisions rather than creating duplicate people. Keep the Philippine research inputs and outputs separate from the Vietnam dataset.

## 8. Quality assurance and checkpoints

Automatic checks must cover input preservation, ownership classification, company flags, unresolved candidates, evidence fields, standardized nationality values, duplicates, and source/page locators. A passing automated report is not a substitute for reviewing the underlying evidence.

Prepare and review the manual sample: approximately 10% of manager rows and 30 companies with flag 0, including any outstanding OCR image checks. Record actual review outcomes; generating a sample alone does not complete QA.

Use the same three owner checkpoints:

1. Ownership distribution and the REVIEW list.
2. A 30-company pilot workbook.
3. The final workbook, automatic QA results, and completed manual sample.

Open methodology choices must be presented with options and trade-offs for the owner's decision. Do not silently choose a new substitute ownership measure, source-date rule, role mapping, or screening threshold.

## 9. Implementation preparation

Reuse the schema, evidence labels, flag logic, and audit workflow. Adapt the source collectors, identifiers, local-versus-foreign nationality checks, title/name extraction, OCR settings, sampling strata, workbook text, and QA assumptions. Review hard-coded Vietnam and year references throughout the scripts; changing `config.py` alone is insufficient.

Run Python with `-I`. Treat downloaded files as untrusted input and never execute content from `raw/`. Do not edit reviewed inputs while a build is running. Commit or push only when asked.

The next required input is the Philippine company list, including identifiers such as ticker and ISIN where available. After inspecting it, verify the country-specific sources and prepare the first ownership checkpoint.
