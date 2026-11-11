"""Step 3d/4 – current management roster from CafeF ("Ban lãnh đạo") + name screening for prioritisation.

Usage: python -I vietnam/pipeline/03d_roster_cafef.py pilot|full

CafeF shows today's roster (not as of 2025), without nationality; it is used to (a) cross-check the
FY2025 roster read from the annual/governance reports and (b) pick names to verify first.
Name_Screen is a prioritisation hint only and is NEVER evidence of nationality:
  NON_VN_STYLE = at least one name token is not a well-formed Vietnamese syllable (e.g. "Toshikazu");
  VN_STYLE     = all tokens are Vietnamese syllables (Sino-Vietnamese readings of foreign names also land here).

Output: data/<run>/roster_cafef.csv
"""
import json
import re
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from common import fetch, read_csv, strip_accents, write_csv
from config import DATA

URL = "https://cafef.vn/du-lieu/Ajax/PageNew/ListCeo.ashx?Symbol={sym}&PositionGroup=0"
FIELDS = ["Ticker_Local", "Group_Name", "Name_Raw", "Position_Raw", "CeoCode", "Name_Screen", "Source", "Source_URL",
          "Fetched_At"]
ONSET = r"(?:ngh|ch|gh|gi|kh|ng|nh|ph|qu|th|tr|b|c|d|g|h|k|l|m|n|p|r|s|t|v|x)?"
NUCLEUS = r"(?:uye|uya|ieu|uoi|uou|oai|oay|oeo|uay|uye|ai|ao|au|ay|eo|eu|ia|ie|iu|oa|oe|oi|oo|ua|ue|ui|uo|uu|uy|ya|ye|yeu|a|e|i|o|u|y)"
CODA = r"(?:ch|ng|nh|c|m|n|p|t|i|y|o|u)?"
SYLLABLE_RE = re.compile(rf"^{ONSET}{NUCLEUS}{CODA}$")


def name_screen(name: str) -> str:
    tokens = re.sub(r"^(ông|bà|mr\.?|mrs\.?|ms\.?)\s+", "", name.strip(), flags=re.I).split()
    folded = [strip_accents(t).strip(".,()") for t in tokens]
    # OCR (Tesseract vie) often reads "y" as "u" ("Nguuễn", "Huuền"); accept the syllable if the y-reading is valid
    ok = lambda t: bool(SYLLABLE_RE.match(t) or SYLLABLE_RE.match(t.replace("uu", "uy")))
    return "VN_STYLE" if folded and all(ok(t) for t in folded if t) else "NON_VN_STYLE"


def tickers_for(run: str) -> list[str]:
    if run == "pilot":
        return [r["Ticker_Local"] for r in read_csv(DATA / "pilot_sample.csv")]
    return [c["Ticker_Local"] for c in read_csv(DATA / "companies_step2.csv")
            if c["Manager_Search"] == "1" and c["Security_Class"] == "COMPANY_VN"]


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    out = []
    for t in tickers_for(run):
        url = URL.format(sym=t)
        body, meta = fetch(url)
        for group in (json.loads(body).get("Data") or []):
            for p in group.get("values") or []:
                out.append({"Ticker_Local": t, "Group_Name": group.get("GroupName", ""), "Name_Raw": p.get("Name", ""),
                            "Position_Raw": p.get("Position", ""), "CeoCode": p.get("CeoCode", ""),
                            "Name_Screen": name_screen(p.get("Name", "")), "Source": "CafeF – Ban lãnh đạo (current)",
                            "Source_URL": url, "Fetched_At": meta["fetched_at"]})
    write_csv(DATA / run / "roster_cafef.csv", out, FIELDS)
    print("people:", len(out), "| NON_VN_STYLE:", sum(r["Name_Screen"] == "NON_VN_STYLE" for r in out))
    for r in out:
        if r["Name_Screen"] == "NON_VN_STYLE":
            print(f"  {r['Ticker_Local']:5s} {r['Name_Raw']:35s} {r['Position_Raw']}")


if __name__ == "__main__":
    main()
