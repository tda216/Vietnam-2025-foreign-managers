# FO for BEKS and MSIE from the BAE December 2025 register (OPEN_DECISIONS 11a): their earlier FO rows came from files
# that turned out to be the AR 2024 (QA 10 Nov 2026). Run from the project root, then id_add_records.py on the JSON.
import csv, json, re
from pathlib import Path
D = Path("indonesia/data")
F = {(r["Code"], r["Part"]): r for r in csv.DictReader((D / "idx_reg_files.csv").open(encoding="utf-8")) if r["Status"] == "OK"}
O = []
def bae(c, part, p, cls, pct, anchor, length, note):
    r = F[(c, str(part))]
    t = re.sub(r"\s+", " ", json.loads((D / "reg_text" / c / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"][p - 1]["text"])
    i = t.find(anchor); assert i >= 0, (c, anchor)
    O.append({"Code": c, "FO_Class": cls, "FO_Pct": pct, "Method": "BAE_REGISTER_202512", "File": r["File"], "Page": str(p),
              "Quote": t[i:i + length].strip(), "As_Of": "2025-12-31", "Note": note + f" | IDX announcement {r['Ann_Date']} ({r['URL']})"})
bae("BEKS", 2, 1, "LOCAL", "<=33.89", "PEMERINTAH PROVINSI BANTEN", 70, "Provincial Government of Banten 66.11 % at 31 Dec 2025 -> foreign at most 33.89 %")
bae("MSIE", 2, 5, "LOCAL", "0.15", "PEMODAL ASING 1 Perorangan Asing", 200, "Bima Registra composition, December 2025: national investors 99.853 %, foreign investors 0.147 % (foreign individuals); holders >= 5 % (p4) all Status L")
(D / "manual" / "batches" / "id_fo_20261110_14_bae.json").write_text(json.dumps({"ownership": O}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(O))
