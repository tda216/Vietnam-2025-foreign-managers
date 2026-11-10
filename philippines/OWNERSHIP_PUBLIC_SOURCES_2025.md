# Public ownership source research — Philippines 2025

Research date: 5 November 2026. This work collects dated ownership observations and source evidence. No Excel workbook has been rebuilt.

## Confirmed free source types

1. **Foreign Ownership Report, often PSE Form 17-13, on the issuer's website.** These reports can state foreign-owned shares, local-owned shares, outstanding shares, voting and total foreign ownership percentages, and the foreign ownership limit separately. Verified examples include AREIT, SOCResources, Solid Group, and San Miguel Food and Beverage.
2. **Stock transfer agent monitoring reports.** China Bank and EastWest publish reports prepared by Stock Transfer Service, Inc.; Italpinas publishes a BDO report; Upson includes its PNB report as an attachment. These can provide the underlying counts needed to check the reported percentage.
3. **Public Ownership Reports containing a separate foreign ownership field.** Aboitiz Equity Ventures' report on the Philippine Dealing System website separately states foreign ownership and public ownership. Use the explicit foreign field, not the public float percentage. Not every POR contains this information.
4. **Annual reports with explicit foreign ownership statements or tables.** Geograce's 2025 annual report gives foreign-owned shares and their percentage at 31 December 2025. The same page also reports a 2026 observation; the dates must be distinguished.

General Information Sheets are another source to investigate, but their subscribed/paid-up capital tables, nationality categories, and measurement dates need careful review. The downloaded 2025 Keppel Philippines Properties GIS is a scanned candidate and has not been accepted as an ownership observation.

## Reviewed observations saved

The reviewed input is `data/manual/ownership_observations_2025.csv`. It currently contains **12 observations for 11 companies**: CBC, EW, AEV, AREIT, MER, SOC, SGI, FB, IDC, UPSON, and GEO. Eleven observations pass the source checks without an identified field conflict; one SGI observation has an explicit source inconsistency flag.

The accepted date window is any date in 2025. The collection includes September and November observations as well as December. Multiple observations are retained separately; no single-date selection policy or averaging rule has been imposed.

Each observation retains the actual date, reported percentage, percentage recomputed from the supplied counts, numerator, denominator, share basis, source type, URL, local PDF, PDF page, verbatim percentage/date evidence, review status, access timestamp, and SHA256. Batch JSON files preserve the reviewed inputs.

The source checks verify that the date is in 2025, quotations and counts occur on the cited pages, foreign plus local shares reconcile when both are provided, and recomputation agrees with the reported percentage within its rounding precision. Relevant table pages were rendered and viewed before recording.

## Issues found

- **Solid Group, December 2025:** the report's total-outstanding field is 1.24%, which agrees with its share counts, but its voting-share percentage field says 40 despite reporting no non-voting shares. This observation is marked `SOURCE_FIELD_CONFLICT_REQUIRES_CONFIRMATION`. The September report separately gives consistent 1.24% figures. Preserve both observations; the source inconsistency must remain visible.
- **Public float differs from foreign ownership:** AEV's report separately states public ownership and foreign ownership. The two fields cannot be substituted for each other.
- **PCD Non-Filipino is not necessarily total foreign ownership:** GEO's explicit total foreign figure exceeds its PCD Non-Filipino line. Foreign certificated/direct holdings can be outside that nominee line. Do not use the nominee line alone as the total, or add participants to nominee totals without checking for double counting.
- **Report year is not the observation date:** some annual reports labelled 2025 state ownership as of March 2026; others filed in 2026 discuss 2022–2024 ownership. These do not become 2025 observations merely because of their filename or filing date.
- **Share basis matters:** preserve common shares, total outstanding shares, voting shares, issued shares, and subscribed capital as distinct bases. Do not silently combine them into one series.

A text scan of 496 cached annual-report/attachment PDFs found 34 candidate passages across 24 companies. These are stored in `data/ownership_statement_candidates.json` for review; they are not 34 verified 2025 ownership observations. Only GEO from that scan has been added to the reviewed observation file in this research pass.

## Evidence and reproduction

- Source URL manifest: `data/manual/ownership_public_sources_2025.json`.
- Newly downloaded source PDFs and metadata: `raw/ownership_public/<symbol>/`.
- Rendered review pages and extracted page text: `data/ownership_source_review/`.
- Reviewed batches: `data/manual/batches/own_public_sources_2025_01.json` and `own_public_sources_2025_02.json`.
- Downloader: `pipeline/ph08_cache_fo_documents.py`.
- Observation validator/appender: `pipeline/ph09_add_fo_observations.py`.

SM Prime's public ownership PDFs were readable through the web research tool, but direct local downloads returned HTTP 403. They are retained as source leads in the URL manifest and have not been counted among the locally reviewed observations. The document acquisition status is recorded separately from ownership findings.

This collection supplies free evidence to compare with the Bloomberg export. It does not replace the existing manual ownership decisions, select the study's final share basis, or classify the entire sample.
