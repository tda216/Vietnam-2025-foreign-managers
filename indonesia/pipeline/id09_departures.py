"""Indonesia step 9 – people who LEFT the Board/Direksi during 2025 (no profile in the AR 2025; MBMA lesson).

For LOCAL firms: sentences with a leaving phrase (pengunduran diri, mengundurkan diri, berakhir masa jabatan, tidak lagi
menjabat, diberhentikan, digantikan, resigned, end of term, ceased, replaced) and a 2025 date, with an honorific
name (Bapak / Ibu / Mr. / Mrs. / Ms.) or a CAPS / Title-Case name right before the phrase. For each name: does any
nationality label in the company's AR text sit within 400 characters of the name (Has_Label)?
Screening only. A departed member without any label needs a source (AR 2024 profile, IDX disclosure).
Output  data/departures.csv
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id09_departures.py
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
LEAVE = re.compile(r"(?i)(pengunduran diri|mengundurkan diri|berakhir(?:nya)? masa jabatan|masa jabatan(?:nya)? berakhir|"
                   r"tidak lagi menjabat|diberhentikan|digantikan oleh|resign\w*|end of (?:his |her |the )?(?:term|tenure)|"
                   r"ceased|no longer serv\w*|replaced by|succeeded by|passed away|meninggal dunia)")
HON = re.compile(r"(?:Bapak|Ibu|Bpk\.?|Sdr\.?|Sdri\.?|Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+((?:[A-Z][A-Za-z'\-\.]+\s?){1,5})")
ROLE = re.compile(r"(?i)komisaris|direktur|director|commissioner|direksi|board")
LABEL = re.compile(r"(?i)warga\s*negara|kewarganegaraan|nationality|citizen")


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def main():
    local = {r["Code"] for r in rows("fo_classification.csv") if r["FO_Class"] == "LOCAL"}
    out = []
    for r in rows("text_index.csv"):
        c = r["Code"]
        if c not in local or not r.get("SHA256"):
            continue
        pages = json.loads((D / "text" / c / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))["pages"]
        full = [re.sub(r"\s+", " ", re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", p["text"])) for p in pages]  # OCR control chars
        seen = set()
        for k, t in enumerate(full):
            for m in LEAVE.finditer(t):
                s = t[max(0, m.start() - 250): m.end() + 250]
                if "2025" not in s or not ROLE.search(s):
                    continue
                for n in HON.finditer(s):
                    name = n.group(1).strip(" .")
                    if len(name) < 4 or name in seen:
                        continue
                    seen.add(name)
                    has = any(LABEL.search(x[max(0, x.find(name) - 400): x.find(name) + 400]) for x in full if name in x)
                    out.append({"Code": c, "File": r["File"], "Page": k + 1, "Name": name, "Has_Label_Near_Name": int(has),
                                "Context": s})
    keys = ["Code", "File", "Page", "Name", "Has_Label_Near_Name", "Context"]
    with (D / "departures.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
    print("departure mentions", len(out), "in", len({o["Code"] for o in out}), "LOCAL firms;",
          sum(1 - o["Has_Label_Near_Name"] for o in out), "names without a nationality label nearby")


if __name__ == "__main__":
    main()
