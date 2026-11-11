"""Validate and append manually reviewed public FO observations, without an Excel build.

Usage: python -I philippines/pipeline/ph09_add_fo_observations.py <review_batch.json>
"""
import csv
import hashlib
import json
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "philippines"
MANUAL = PH / "data" / "manual"
FIELDS = ["Observation_ID", "Symbol", "Ticker", "Company", "FO_As_Of_Date", "Foreign_Ownership_Pct_Reported",
          "Foreign_Ownership_Pct_Computed", "Foreign_Owned_Shares", "Local_Owned_Shares", "Outstanding_Shares",
          "Share_Basis", "Foreign_Ownership_Limit_Pct", "Source_Type", "Source_URL", "Local_File", "Page",
          "Count_Page", "Date_Page", "Evidence_Quote", "Date_Quote", "Review_Status", "Note", "Reviewed_On",
          "Accessed_UTC", "PDF_SHA256"]


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def main():
    batch_path = Path(sys.argv[1])
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    mapping = {r["Symbol"]: r for r in csv.DictReader(open(PH / "data/pse_company_map.csv", encoding="utf-8-sig"))
               if r["Market"] == "PM"}
    target = MANUAL / "ownership_observations_2025.csv"
    records = list(csv.DictReader(open(target, encoding="utf-8-sig"))) if target.exists() else []
    have = {r["Observation_ID"] for r in records}
    additions = []
    for record in batch["observations"]:
        key, symbol = record["Document_ID"], record["Symbol"]
        measured = date.fromisoformat(record["FO_As_Of_Date"])
        assert measured.year == 2025, f"Non-2025 ownership observation: {key}"
        if record.get("Local_File"):
            import pymupdf
            pdf = ROOT / record["Local_File"]
            original_meta = json.loads((pdf.parent / "meta.json").read_text())
            original_file = next(f for f in original_meta["files"] if f.get("saved_as") == pdf.name)
            meta = {"SHA256": original_file["sha256"], "Source_URL": original_meta["viewer_url"],
                    "Accessed_UTC": original_meta["accessed_utc"]}
            with pymupdf.open(pdf) as document:
                pages = [{"Page": n + 1, "Text": page.get_text()} for n, page in enumerate(document)]
        else:
            folder = PH / "raw/ownership_public" / symbol
            pdf, meta_file = folder / (key + ".pdf"), folder / (key + ".meta.json")
            meta = json.loads(meta_file.read_text())
            pages = json.loads((PH / "data/ownership_source_review" / (key + ".json")).read_text())
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == meta["SHA256"], f"Source changed: {key}"
        page = flat(pages[record["Page"] - 1]["Text"])
        quote = re.search(record["Pct_Quote_Regex"], page)
        assert quote is not None, f"Percentage quotation not found: {key}"
        assert flat(record["Date_Quote"]) in flat(pages[record["Date_Page"] - 1]["Text"]), f"Date quote not found: {key}"
        count_page = flat(pages[record["Count_Page"] - 1]["Text"])
        for field in ("Foreign_Shares", "Local_Shares", "Outstanding_Shares"):
            if field in record:
                assert f"{record[field]:,}" in count_page, f"Share count not found: {key}/{field}"
        foreign, outstanding = Decimal(record["Foreign_Shares"]), Decimal(record["Outstanding_Shares"])
        computed = foreign / outstanding * 100
        reported = Decimal(record["Reported_Pct"])
        tolerance = Decimal(5).scaleb(-len(record["Reported_Pct"].split(".")[-1]) - 1)
        assert abs(computed - reported) <= tolerance, f"Reported percentage/counts mismatch: {key}"
        if "Local_Shares" in record:
            assert record["Foreign_Shares"] + record["Local_Shares"] == record["Outstanding_Shares"], key
        obs_id = key + ":" + record["Share_Basis"]
        if obs_id in have:
            continue
        mapped = mapping[symbol]
        row = {f: "" for f in FIELDS}
        row.update(Observation_ID=obs_id, Symbol=symbol, Ticker=mapped["Ticker"], Company=mapped["PSE_Company_Name"],
                   FO_As_Of_Date=record["FO_As_Of_Date"], Foreign_Ownership_Pct_Reported=record["Reported_Pct"],
                   Foreign_Ownership_Pct_Computed=str(computed.quantize(Decimal("0.000001"))),
                   Foreign_Owned_Shares=record["Foreign_Shares"], Local_Owned_Shares=record.get("Local_Shares", ""),
                   Outstanding_Shares=record["Outstanding_Shares"], Share_Basis=record["Share_Basis"],
                   Foreign_Ownership_Limit_Pct=record.get("Limit_Pct", ""), Source_Type=record["Source_Type"],
                   Source_URL=meta["Source_URL"], Local_File=str(pdf.relative_to(ROOT)), Page=record["Page"],
                   Count_Page=record["Count_Page"], Date_Page=record["Date_Page"], Evidence_Quote=quote.group(0),
                   Date_Quote=record["Date_Quote"], Review_Status=record["Review_Status"], Note=record.get("Note", ""),
                   Reviewed_On=batch["reviewed_on"], Accessed_UTC=meta["Accessed_UTC"], PDF_SHA256=meta["SHA256"])
        additions.append(row)
        have.add(obs_id)
    # All source checks finish before any reviewed observation is written.
    with target.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records + additions)
    print(json.dumps({"added": len(additions), "observations": len(records + additions),
                      "companies": len({r["Symbol"] for r in records + additions}), "source_checks": "PASS",
                      "excel_rebuilt": False}, indent=2))


if __name__ == "__main__":
    main()
