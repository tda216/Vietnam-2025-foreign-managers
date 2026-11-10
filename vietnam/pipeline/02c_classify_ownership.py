"""Step 2c – attach 31/12/2025 foreign ownership to the universe and classify (preliminary).

Matching: VSDC row by ISIN (Bloomberg ISIN), falling back to the local ticker; any ISIN/ticker
disagreement is reported, never silently fixed. Rule: FO > 50 -> FOREIGN_MAJORITY, FO <= 50 -> LOCAL,
no figure -> REVIEW. This is preliminary: the annual-report cross-check (step 5) can raise FO_Conflict.

Securities the VSDC file cannot cover (foreign-listed, delisted) are resolved by hand from filings in
data/manual/ownership_manual.csv (one row per decision, with source, page and evidence); those rows
override the automatic fields and are also written to the observations table.

Outputs: data/ownership_observations.csv (long, one row per figure per source),
         data/companies_step2.csv (universe + ownership + manager-search scope + preliminary deep tier).
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv, write_csv
from config import DATA, DEEP_FO_MIN, DEEP_TOP_N_MCAP, FO_AS_OF, FO_BORDERLINE_UPPER, FO_THRESHOLD

OBS_FIELDS = ["Ticker", "Ticker_Local", "ISIN", "Foreign_Ownership_Pct", "FO_Bound", "FO_As_Of_Date", "Qty_Issued",
              "Qty_Foreign_Held", "Max_Foreign_Ratio_Pct", "Exchange_At_Source", "Match_Key", "FO_Method", "Source",
              "Source_URL", "Local_File", "Page", "Note"]
MANUAL_FILE = DATA / "manual" / "ownership_manual.csv"
MANUAL_OVERRIDES = ["Ownership_Type", "Foreign_Ownership_Pct", "FO_Bound", "FO_As_Of_Date", "FO_Method", "FO_Source",
                    "FO_Source_URL", "FO_Page", "FO_Note", "In_Scope", "Exclusion_Reason", "Manager_Search",
                    "Manager_Search_Reason"]
# Bloomberg market caps are in each listing's currency; only VN listings (VND) are ranked together.
# A foreign-listed company joins the top-N if its cap exceeds the N-th VND cap even at this low VND/USD rate.
VND_PER_USD_FLOOR = 20000


def classify(fo):
    if fo == "" or fo is None:
        return "REVIEW"
    return "FOREIGN_MAJORITY" if float(fo) > FO_THRESHOLD else "LOCAL"


def main():
    uni = read_csv(DATA / "universe.csv")
    vsdc = [r for r in read_csv(DATA / "fo_vsdc_20251231.csv") if r["Exchange"] != "DEPOX"]
    depox = [r for r in read_csv(DATA / "fo_vsdc_20251231.csv") if r["Exchange"] == "DEPOX"]
    by_isin = {r["ISIN"]: r for r in vsdc}
    by_ticker = {}
    for r in vsdc:
        if r["Ticker_Local"]:
            by_ticker.setdefault(r["Ticker_Local"], []).append(r)
    depox_isin = {r["ISIN"]: r for r in depox}
    depox_ticker = {r["Ticker_Local"]: r for r in depox if r["Ticker_Local"]}

    manual = {r["Ticker"]: r for r in read_csv(MANUAL_FILE)} if MANUAL_FILE.exists() else {}

    # Top-N market cap among VN-listed companies (Bloomberg, VND), for the C3 deep tier.
    ranked = sorted((u for u in uni if u["Security_Class"] == "COMPANY_VN" and u["Market_Cap_LCL"]),
                    key=lambda u: float(u["Market_Cap_LCL"]), reverse=True)
    mcap_rank = {u["Ticker"]: i for i, u in enumerate(ranked, start=1)}
    nth_cap_vnd = float(ranked[DEEP_TOP_N_MCAP - 1]["Market_Cap_LCL"])

    obs, out, issues = [], [], []
    for u in uni:
        hit, key = None, ""
        if u["ISIN"] in by_isin:
            hit, key = by_isin[u["ISIN"]], "ISIN"
            if hit["Ticker_Local"] and hit["Ticker_Local"] != u["Ticker_Local"] and u["Security_Class"] == "COMPANY_VN":
                issues.append(f"{u['Ticker']}: ISIN match but VSDC ticker is {hit['Ticker_Local']}")
        elif u["Security_Class"] == "COMPANY_VN" and len(by_ticker.get(u["Ticker_Local"], [])) == 1:
            hit, key = by_ticker[u["Ticker_Local"]][0], "TICKER"
            issues.append(f"{u['Ticker']}: matched by ticker only (Bloomberg ISIN {u['ISIN']} vs VSDC {hit['ISIN']})")

        depox_hit = depox_isin.get(u["ISIN"]) or (depox_ticker.get(u["Ticker_Local"]) if u["Security_Class"] == "COMPANY_VN" else None)
        if hit:
            obs.append({
                "Ticker": u["Ticker"], "Ticker_Local": u["Ticker_Local"], "ISIN": hit["ISIN"],
                "Foreign_Ownership_Pct": hit["Foreign_Ownership_Pct"], "FO_Bound": "", "FO_As_Of_Date": hit["FO_As_Of_Date"],
                "Qty_Issued": hit["Qty_Issued"], "Qty_Foreign_Held": hit["Qty_Foreign_Held"],
                "Max_Foreign_Ratio_Pct": hit["Max_Foreign_Ratio_Pct"], "Exchange_At_Source": hit["Exchange"],
                "Match_Key": key, "FO_Method": "VSDC_COMPUTED", "Source": hit["Source"], "Source_URL": hit["Source_URL"],
                "Local_File": hit["Local_File"], "Page": hit["Page"], "Note": "",
            })

        fo = hit["Foreign_Ownership_Pct"] if hit else ""
        otype = classify(fo) if u["In_Scope"] == "1" else ("REVIEW" if u["Security_Class"] == "NO_ISIN" else "")
        if u["In_Scope"] != "1":
            scope_reason = "OUT_OF_SCOPE_" + u["Security_Class"]
        elif otype == "LOCAL":
            scope_reason = "LOCAL"
        elif otype == "REVIEW":
            scope_reason = "REVIEW"
        elif float(fo) <= FO_BORDERLINE_UPPER:
            scope_reason = "FOREIGN_MAJORITY_BORDERLINE"
        else:
            scope_reason = ""

        deep = []
        if u["Ticker"] in mcap_rank and mcap_rank[u["Ticker"]] <= DEEP_TOP_N_MCAP:
            deep.append(f"TOP{DEEP_TOP_N_MCAP}_MCAP")
        if fo != "" and float(fo) >= DEEP_FO_MIN:
            deep.append(f"FO_GE_{DEEP_FO_MIN:g}")

        row = {
            **u,
            "Exchange_At_FO_Date": hit["Exchange"] if hit else ("DEPOX" if depox_hit else ""),
            "Foreign_Ownership_Pct": fo,
            "FO_Bound": "",
            "FO_As_Of_Date": FO_AS_OF if hit else "",
            "FO_Method": "VSDC_COMPUTED" if hit else "",
            "Ownership_Type": otype,
            "FO_Source": hit["Source"] if hit else "",
            "FO_Source_URL": hit["Source_URL"] if hit else "",
            "FO_Page": hit["Page"] if hit else "",
            "FO_Note": "" if hit else (
                "In VSDC file only under DEPOX (registered, not trading) at 31/12/2025" if depox_hit
                else ("Foreign-listed: not covered by VSDC" if u["Security_Class"] == "FOREIGN_LISTED"
                      else "Not in VSDC 31/12/2025 file")),
            "Manager_Search": 1 if scope_reason and u["In_Scope"] == "1" else 0,
            "Manager_Search_Reason": scope_reason or "FOREIGN_MAJORITY",
            "Mcap_Rank": mcap_rank.get(u["Ticker"], ""),
            "Deep_Prelim": 0,
            "Deep_Reason_Prelim": "",
        }

        m = manual.get(u["Ticker"])
        if m:
            for k in MANUAL_OVERRIDES:
                row[k] = m[k]
            if m["Foreign_Ownership_Pct"] or m["FO_Bound"]:
                obs.append({
                    "Ticker": u["Ticker"], "Ticker_Local": u["Ticker_Local"], "ISIN": u["ISIN"],
                    "Foreign_Ownership_Pct": m["Foreign_Ownership_Pct"], "FO_Bound": m["FO_Bound"],
                    "FO_As_Of_Date": m["FO_As_Of_Date"], "Qty_Issued": "", "Qty_Foreign_Held": "",
                    "Max_Foreign_Ratio_Pct": "", "Exchange_At_Source": "", "Match_Key": "MANUAL",
                    "FO_Method": m["FO_Method"], "Source": m["FO_Source"], "Source_URL": m["FO_Source_URL"],
                    "Local_File": "", "Page": m["FO_Page"], "Note": m["FO_Note"],
                })
            if u["Security_Class"] == "FOREIGN_LISTED" and u["Market_Cap_LCL"] and \
                    float(u["Market_Cap_LCL"]) * VND_PER_USD_FLOOR > nth_cap_vnd and u["Ticker"].endswith(" US Equity"):
                deep.append(f"TOP{DEEP_TOP_N_MCAP}_MCAP_USD_LISTING")

        if row["In_Scope"] == "1" and row["Manager_Search"] in (1, "1") and deep:
            row["Deep_Prelim"], row["Deep_Reason_Prelim"] = 1, ";".join(deep)
        out.append(row)

    write_csv(DATA / "ownership_observations.csv", obs, OBS_FIELDS)
    write_csv(DATA / "companies_step2.csv", out, list(out[0].keys()))

    scope = [r for r in out if r["In_Scope"] == "1"]
    print("issues:", len(issues))
    for s in issues[:30]:
        print("  ", s)
    print("in-scope:", len(scope))
    print("Ownership_Type:", Counter(r["Ownership_Type"] for r in scope).most_common())
    print("Exchange_At_FO_Date:", Counter(r["Exchange_At_FO_Date"] for r in scope).most_common())
    print("Manager_Search:", Counter(r["Manager_Search_Reason"] for r in scope).most_common())
    print("Deep_Prelim:", sum(r["Deep_Prelim"] for r in scope),
          Counter(r["Deep_Reason_Prelim"] for r in scope if r["Deep_Prelim"]).most_common())


if __name__ == "__main__":
    main()
