"""Append reviewed records from a batch JSON to data/manual/ (Indonesia; audit trail in data/manual/batches/).

Batch JSON: {"records": [...], "ownership": [...]}
  record keys: Code, File (as in data/text_index.csv), Page, Manager_Name, Raw_Position, Role_Group
               (Board / Executive / Other_Manager), Nationality (English country), Nationality_Raw, Evidence_Quote;
               optional Appointed_Date, Resigned_Date, Note, Other_Sources, Dual_Nationality, Evidence_Type (DOC_FIELD).
  ownership keys: as data/manual/ownership_ar.csv (Code, FO_Class, FO_Pct, Method, File, Page, Quote, As_Of, Note).
Filled in: Company, Year, Is_Foreign 1, Source (website / IDX), Source_URL, Local_File, Reviewed_On.
Checks (the batch is refused on any failure): the quote occurs on that page (whitespace and case ignored, "..." = gap);
Role_Group valid; Nationality from the country list of id06; no duplicate (Code, Manager_Name, Raw_Position).
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id_add_records.py <batch.json>
"""
import csv, datetime as dt, importlib.util, json, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data"
M = D / "manual"
spec = importlib.util.spec_from_file_location("id06", HERE / "id06_screen.py")
id06 = importlib.util.module_from_spec(spec); spec.loader.exec_module(id06)
COUNTRIES = set(id06.NAT.values()) | {"UNKNOWN"}  # UNKNOWN: "Warga Negara Asing" without a country (shared rule)
REC = M / "manager_records.csv"
OWN = M / "ownership_ar.csv"


def rows(p):
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_ok(pages, page, quote):
    t = norm(pages[int(page) - 1]["text"])
    pos = 0
    for part in [norm(x) for x in re.split(r"\.\.\.|…", quote) if x.strip()]:
        k = t.find(part, pos)
        if k < 0:
            return part
        pos = k + len(part)
    return ""


def main():
    src = Path(sys.argv[1]); batch = json.loads(src.read_text(encoding="utf-8"))
    idx = {r["File"]: r for r in rows(D / "text_index.csv")}
    urls = {r["File"]: (r["URL"], "Annual Report 2025 (company website)") for r in rows(D / "web_ar_files.csv") if r.get("File")}
    urls.update({r["File"]: (r["URL"], "Annual Report 2025 (IDX, via www.idx.id)") for r in rows(D / "idx_ar_files.csv") if r.get("File")})
    urls.update({r["File"]: (r["URL"], f"Annual Report 2025 (IDX announcement of {r['Ann_Date']}, via www.idx.id)") for r in rows(D / "idx_ar_ann_files.csv") if r.get("File")})
    uni = {r["Code"]: r for r in rows(D / "universe.csv")}
    old = rows(REC)
    keys = list(old[0].keys()) if old else []
    have = {(r["Code"], r["Manager_Name"].lower(), r["Raw_Position"].lower()) for r in old}
    errs, new = [], []
    today = dt.date.today().isoformat()

    ar2024 = {r["File"]: r for r in rows(D / "idx_ar_files_2024.csv") if r.get("File")}
    urls.update({f: (r["URL"], "Annual Report 2024 (IDX, via www.idx.id) – nationality of a member who left in 2025")
                 for f, r in ar2024.items()})

    def pages_of(f):
        if f in ar2024:  # AR 2024 (members who left during 2025): read the page text directly
            import fitz  # pymupdf; untrusted file, read as data
            return [{"text": pg.get_text()} for pg in fitz.open(ROOT / f)]
        sha = idx[f]["SHA256"][:12]
        return json.loads((D / "text" / idx[f]["Code"] / f"{sha}.json").read_text(encoding="utf-8"))["pages"]

    for r in batch.get("records", []):
        tag = f"{r.get('Code')} {r.get('Manager_Name')}"
        if r.get("File") not in idx and r.get("File") not in ar2024:
            errs.append(f"{tag}: file not in text_index / idx_ar_files_2024"); continue
        miss = quote_ok(pages_of(r["File"]), r["Page"], r["Evidence_Quote"])
        if miss:
            errs.append(f"{tag}: quote not on page {r['Page']}: {miss[:80]!r}")
        if r["Role_Group"] not in ("Board", "Executive", "Other_Manager"):
            errs.append(f"{tag}: Role_Group {r['Role_Group']!r}")
        for n in r["Nationality"].split(";"):
            if n.strip() not in COUNTRIES:
                errs.append(f"{tag}: nationality {n!r} not in the id06 country list")
        k = (r["Code"], r["Manager_Name"].lower(), r["Raw_Position"].lower())
        if k in have:
            errs.append(f"{tag}: duplicate")
        have.add(k)
        url, source = urls.get(r["File"], ("", "Annual Report 2025 (manual download from IDX)"))
        new.append({"Company": uni[r["Code"]].get("KSEI_Issuer") or uni[r["Code"]]["Short_Name"], "Code": r["Code"], "Year": 2025,
                    "Manager_Name": r["Manager_Name"], "Raw_Position": r["Raw_Position"], "Role_Group": r["Role_Group"],
                    "Nationality": r["Nationality"], "Nationality_Raw": r["Nationality_Raw"], "Is_Foreign": 1,
                    "Dual_Nationality": r.get("Dual_Nationality", ""), "Appointed_Date": r.get("Appointed_Date", ""),
                    "Resigned_Date": r.get("Resigned_Date", ""), "Source": source, "Source_URL": url,
                    "Local_File": "indonesia/" + r["File"], "Page": r["Page"], "Evidence_Type": r.get("Evidence_Type", "DOC_FIELD"),
                    "Evidence_Quote": r["Evidence_Quote"], "Other_Sources": r.get("Other_Sources", ""), "Reviewed_On": today,
                    "Note": r.get("Note", ""), "Management_Include": ""})
    own_new = []
    for o in batch.get("ownership", []):
        if o.get("File") in idx:
            miss = quote_ok(pages_of(o["File"]), str(o["Page"]).split(";")[0], o["Quote"].split(" (p")[0])
            if miss:
                errs.append(f"{o['Code']} ownership: quote not on page {o['Page']}: {miss[:80]!r}")
        own_new.append(dict(o, Reviewed_On=today))
    if errs:
        print("REFUSED – nothing written:"); print("\n".join("  " + e for e in errs)); sys.exit(1)
    if new:
        with REC.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys or list(new[0])); w.writeheader(); w.writerows(old + new)
    if own_new:
        oo = rows(OWN)
        with OWN.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(oo[0]) if oo else list(own_new[0])); w.writeheader(); w.writerows(oo + own_new)
    (M / "batches").mkdir(exist_ok=True)
    dst = M / "batches" / src.name
    if src.resolve() != dst.resolve():
        shutil.copy(src, dst)
    print(f"added {len(new)} records, {len(own_new)} ownership rows; batch kept as {dst.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
