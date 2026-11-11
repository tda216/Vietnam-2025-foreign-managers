# Bloomberg ownership request — Philippines FY2025

The research owner accepts an ownership measurement date anywhere in calendar year 2025. Year-end is not mandatory. This note is a request for verification on the Bloomberg Terminal; it does not assert that a particular Bloomberg field covers the sample.

## Message for Bloomberg Help

> I am studying foreign ownership of Philippine listed companies. Do you provide the total percentage of outstanding shares held by foreign investors, preferably as reported by the issuer or the Philippine Stock Exchange? I can use an observation measured on any date from 1 January to 31 December 2025; it does not have to be 31 December. Please identify the field mnemonic, definition, source, actual ownership as-of date, historical retrieval method, and Excel export settings. Does the measure cover common shares only or all share classes? Please distinguish total foreign ownership from foreign institutional ownership, ownership by investor domicile, and the foreign ownership limit. If no suitable total measure is available, please confirm that rather than substituting a different measure.

## Requested export

Use the securities in `Bloomberg-Philippines2025.xlsx` and retain missing observations as missing. Useful columns are:

- Bloomberg ticker and ISIN.
- Total foreign ownership percentage.
- Actual ownership measurement date in 2025.
- Reported data source and publication/report date, if available.
- Field mnemonic and definition.
- Share basis: common shares, all outstanding shares, or voting shares.
- Foreign-owned share count and matching outstanding-share count, if available.

Start with a small sample to check the definition and historical coverage before exporting the full list. Retain the field-description text or a screenshot, especially the denominator, date settings, and treatment of unknown holders.

Do not replace missing data with zero or calculate foreign ownership as 100% minus domestic ownership unless the coverage and treatment of unknown holders establish that this is valid. If multiple 2025 dates are returned, keep the dates and observations for review.
