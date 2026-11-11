"""Step 5 – people from the SEC One Report template: directors (current and left during the year) and executives.

Usage: python -I thailand/pipeline/05_parse_template.py [TICKER ...]   (default: every company in data/docs.csv)

The One Report (Form 56-1) prints, for every director and – in the e-form layout – every executive, a fixed block:
  <N.> <name> / Gender / Age / education / Thai nationality: Yes|No / Residing in Thailand: Yes|No
  (Thai: เพศ / อายุ / วุฒิการศึกษา / สัญชาติไทย: ใช่|ไม่ใช่ / ถิ่นที่อยู่ในประเทศไทย: ใช่|ไม่ใช่)
next to a Position column, a date column and an expertise column. Columns are found from each person's first row
(the position starts right of the name on the same line), so the parser does not depend on table headers.
Sections (by heading, in page order): BOARD (7.2.2 current directors), LEFT (directors who resigned / vacated during
the year), EXECUTIVE (7.4.1); sub-committees (7.3), employees (7.5) and section 8 are skipped.
Check: the number of BOARD people equals "Total number of directors" / "กรรมการรวม" in table 7.2.1 when printed.
Outputs: data/people_onereport.csv (one row per person x section), data/report_stats.csv (one row per company)
"""
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

import pymupdf

from common import read_csv, write_csv
from config import DATA, ROOT

SECTION_RX = [  # (section, pattern) – first match wins for a heading line
    ("LEFT", re.compile(r"^List of (the )?(board of )?directors who resigned|^รายชื่อกรรมการที่ลาออก")),
    ("BOARD", re.compile(r"\(7\.2\.2\)|^List of the board of directors( \(\d\))?$|^รายชื่อกรรมการชุดปัจจุบัน$"
                        r"|^รายชื่อคณะกรรมการบริษัท( \(\d\))?$")),
    ("EXECUTIVE", re.compile(r"\(7\.4\.1\)|^List of the highest-ranking executive|^รายชื่อผู้บริหารสูงสุด")),
    ("SKIP", re.compile(r"\(7\.3\)|\(7\.2\.3\)|^7\.(2\.3|3(\.\d)?)\s+[A-Za-z฀-๿]|^Sub-?committees|^List of audit committee|^List of the board of directors by position"
                        r"|^Other information about the board|^ข้อมูลเกี่ยวกับคณะกรรมการอื่น|^ข้อมูลเกี่ยวกับคณะกรรมการชุดย่อย"
                        r"|^Executives and controller|^List of executive committee|^รายชื่อกรรมการบริหาร"
                        r"|^รายชื่อกรรมการ จำแนกตามตำแหน่ง|^รายชื่อคณะกรรมการ(ตรวจสอบ|บริหาร|ชุดย่อย)|^รายชื่อกรรมการตรวจสอบ")),
    ("END", re.compile(r"\(7\.5\)|\(7\.4\.2|\(8\.1\)|^Executives’ remuneration|^ข้อมูลเกี่ยวกับพนักงาน \(7\.5\)|^Additional Explanation"
                       r"|^คำอธิบายเพิ่มเติม|^Organization structure|^List of persons assigned|^List of the company secretary"
                       r"|^List of directors whose terms|^List of newly appointed|^รายชื่อผู้ที่ได้รับมอบหมาย|^รายชื่อเลขานุการ"
                       r"|^รายชื่อหัวหน้า|^แผนผังโครงสร้าง|^รายชื่อกรรมการที่ครบวาระ|^รายชื่อกรรมการใหม่")),
]
GENDER = re.compile(r"^(Gender|เพศ)\s*:")
NUMBERED = re.compile(r"^(\d{1,2})\.\s*(.*)$")
STOP_POS = re.compile(r"^(Director type|Type of director|Authorized director|ประเภทของกรรมการ|กรรมการผู้มีอำนาจ"
                      r"|Date position|Date directorship|วันที่ดำรงตำแหน่ง|วันที่พ้นจากตำแหน่ง|Highest responsibility"
                      r"|ผู้รับผิดชอบสูงสุด)", re.I)
THAI = re.compile(r"(?:Thai nationality|สัญชาติไทย)\s*:\s*(Yes|No|ใช่|ไม่ใช่)", re.I)
RESIDE = re.compile(r"(?:Residing in Thailand|Residence in Thailand|ถิ่นที่อยู่ในประเทศไทย)\s*:\s*(Yes|No|ใช่|ไม่ใช่)", re.I)
AGE = re.compile(r"(?:Age|อายุ)\s*:\s*(\d{1,3})")
SEX = re.compile(r"(?:Gender|เพศ)\s*:\s*(\S+)")
EN_MONTH = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
TH_MONTH = {m: i for i, m in enumerate("ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.".split(), 1)}
DATE_RX = re.compile(r"(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})"
                     r"|(\d{1,2})\s*(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s*(\d{4})")
TOTAL = re.compile(r"^(Total number of directors|กรรมการรวม)$")
FOOTNOTE = re.compile(r"\s*(\[\d+\]|\(\*+\)|\*+)")
YESNO = {"yes": "Yes", "ใช่": "Yes", "no": "No", "ไม่ใช่": "No"}
HONORIFIC = re.compile(r"^((Mr|Mrs|Ms|Miss|Dr|Prof|Assoc|Asst|Gen|Lt|Pol|Adm|Air|M\.L|M\.R|H\.E|Khun|Professor|Doctor)\.?\s+"
                       r"|(นาย|นางสาว|นาง|ดร\.?|ศ\.|รศ\.|ผศ\.|พล\.\S*|ม\.ล\.|ม\.ร\.ว\.|คุณ)\s*)+", re.I)


def iso(m: re.Match) -> str:
    try:
        if m.group(1):
            return date(int(m.group(3)), EN_MONTH[m.group(2)[:3]], int(m.group(1))).isoformat()
        return date(int(m.group(6)) - 543, TH_MONTH[m.group(5)], int(m.group(4))).isoformat()
    except (ValueError, KeyError):
        return ""


def lines_of(doc) -> list[tuple]:
    """(page, y, x, text) for every text line, in reading order."""
    out = []
    for pno, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"]).strip()
                if t:
                    out.append((pno, round(ln["bbox"][1], 1), round(ln["bbox"][0], 1), t))
    return sorted(out)


def section_of(t: str) -> str:
    return next((s for s, rx in SECTION_RX if rx.search(t)), "")


def parse_pdf(path: Path) -> tuple[list[dict], dict]:
    doc = pymupdf.open(path)
    L = lines_of(doc)
    total = ""
    for i, (p, y, x, t) in enumerate(L):
        if TOTAL.match(t):
            nums = [u for (p2, y2, x2, u) in L[i + 1:i + 6] if p2 == p and abs(y2 - y) < 3 and re.fullmatch(r"\d{1,2}", u)]
            total = nums[0] if nums else total
            break
    # section of every line
    sec, tagged = "", []
    for (p, y, x, t) in L:
        s = section_of(t) if len(t) < 120 else ""
        if s:
            sec = s
        tagged.append((p, y, x, t, sec))
    people = []
    idx = [i for i, l in enumerate(tagged) if l[4] in ("BOARD", "LEFT", "EXECUTIVE") and GENDER.match(l[3])]
    for k, gi in enumerate(idx):
        p, gy, gx, _, sec = tagged[gi]
        # name rows: lines in the name column (x within 20pt left of the Gender line) just above it, back to the number
        j, name_parts, row_y, num = gi - 1, [], None, ""
        while j >= 0 and tagged[j][0] == p and gy - tagged[j][1] < 80:
            pj, yj, xj, tj, _ = tagged[j]
            if gx - 25 <= xj <= gx + 3:
                m = NUMBERED.match(tj)
                if m and (m.group(2) or xj < gx - 5):
                    num, row_y = m.group(1), yj
                    if m.group(2):
                        name_parts.insert(0, m.group(2))
                    break
                if xj >= gx - 3:
                    name_parts.insert(0, tj)
                    row_y = yj
            j -= 1
        if row_y is None:
            continue
        # the person's block: until the next person's row on this page (or page end)
        nxt = idx[k + 1] if k + 1 < len(idx) else None
        end_y = 10 ** 6
        if nxt is not None and tagged[nxt][0] == p:
            ny = tagged[nxt][1]
            prev_rows = [l[1] for l in tagged[gi:nxt] if l[0] == p and NUMBERED.match(l[3]) and l[2] <= gx + 3 and l[1] < ny]
            end_y = min(prev_rows) if prev_rows else ny - 1
        heads = [l[1] for l in tagged if l[0] == p and l[1] > gy and len(l[3]) < 120 and section_of(l[3])]
        end_y = min([end_y] + heads)  # the last person of a section stops at the next heading
        block = [l for l in tagged if l[0] == p and row_y - 2 <= l[1] < end_y]
        row = sorted({l[2] for l in block if abs(l[1] - row_y) < 3 and l[2] > gx + 60})
        pos_x = row[0] if row else gx + 140
        date_x = row[1] if len(row) > 1 else pos_x + 120
        exp_x = row[2] if len(row) > 2 else 10 ** 4
        left = " \n".join(l[3] for l in block if l[2] < pos_x - 5)
        pos_lines, mid = [], [l for l in block if pos_x - 5 <= l[2] < exp_x - 5]
        last_y = row_y
        for l in [l for l in mid if l[2] < date_x - 5]:
            if STOP_POS.match(l[3]) or l[1] - last_y > 40:  # label of the next field, or a gap: the position has ended
                break
            last_y = l[1]
            if not NUMBERED.fullmatch(l[3]) or NUMBERED.match(l[3]).group(2):
                pos_lines.append(l[3])
        midtext = " ".join(l[3] for l in mid)
        dtype = re.search(r"(?:Director type|Type of director|ประเภทของกรรมการ)\s*:\s*(.+?)(?=\s*(?:Date |วันที่|\d{1,2} |Part \d|Position|$))", midtext)
        ended = re.search(r"(?:Date directorship ended|Date position ended|วันที่พ้นจากตำแหน่ง)\s*:?\s*(?:" + DATE_RX.pattern + ")", midtext)
        dates = [iso(m) for m in DATE_RX.finditer(midtext)]
        thai, res = THAI.search(left), RESIDE.search(left)
        name = re.sub(r"\s+", " ", " ".join(name_parts)).strip()
        people.append({"Section": sec, "Seq": num, "Page": p, "Name_Raw": name,
                       "Name_Clean": HONORIFIC.sub("", FOOTNOTE.sub("", name)).strip(),
                       "Gender": (SEX.search(left).group(1) if SEX.search(left) else ""),
                       "Age": (AGE.search(left).group(1) if AGE.search(left) else ""),
                       "Thai_Nationality": YESNO[thai.group(1).lower()] if thai else "",
                       "Residing_In_Thailand": YESNO[res.group(1).lower()] if res else "",
                       "Position_Raw": re.sub(r"\s+", " ", " ".join(pos_lines)).strip(),
                       "Director_Type": dtype.group(1).strip() if dtype else "",
                       "Date_Assumed": dates[0] if dates else "",
                       "Date_Ended": iso(re.search(DATE_RX, ended.group(0))) if ended else (dates[1] if sec == "LEFT" and len(dates) > 1 else ""),
                       "Quote": re.sub(r"\s+", " ", name + " | " + " ".join(l[3] for l in block if l[2] < pos_x - 5))[:400]})
    n_board = sum(1 for r in people if r["Section"] == "BOARD")
    latin = [r for r in people if re.search(r"[A-Za-z]{2}", r["Name_Clean"])]
    if total and n_board == 2 * int(total) and 0 < len(latin) < len(people):  # bilingual report: keep the English half
        people = latin
    return people, {"Total_7_2_1": total, "N_Pages": len(doc)}


def choose(docs: list[dict]) -> list[dict]:
    order = {"E_FORM": 0, "STRUCTURE": 1, "MAIN": 2}
    return sorted((d for d in docs if d["Status"] == "OK" and d["Local_File"].lower().endswith(".pdf")),
                  key=lambda d: order.get(d["Member_Role"], 3))


def main():
    docs = read_csv(DATA / "docs.csv")
    want = set(sys.argv[1:])
    by_t = {}
    for d in docs:
        if not want or d["Ticker_Local"] in want:
            by_t.setdefault(d["Ticker_Local"], []).append(d)
    old_p = [r for r in read_csv(DATA / "people_onereport.csv")] if want and (DATA / "people_onereport.csv").exists() else []
    old_s = [r for r in read_csv(DATA / "report_stats.csv")] if want and (DATA / "report_stats.csv").exists() else []
    out_p = [r for r in old_p if r["Ticker_Local"] not in by_t]
    out_s = [r for r in old_s if r["Ticker_Local"] not in by_t]
    for t, ds in sorted(by_t.items()):
        st = {"Ticker_Local": t, "Parsed_File": "", "Member_Role": "", "Report_Lang": ds[0].get("Report_Lang", ""),
              "Status": ds[0]["Status"] if not choose(ds) else "NO_TEMPLATE"}
        best = None  # every member is parsed; the one stating the most nationalities wins (e.g. GPSC: the STRUCTURE file
        for d in choose(ds):  # lists executives without the field, the e-form main report has it)
            try:
                people, info = parse_pdf(ROOT / d["Local_File"])
            except Exception as e:  # unreadable PDF: try the next member
                st["Error"] = f"{type(e).__name__}: {e}"[:120]
                continue
            if not any(r["Section"] == "BOARD" for r in people):
                continue
            score = sum(1 for r in people if r["Thai_Nationality"])
            if best is None or score > best[0]:
                best = (score, d, people, info)
        if best:
            _, d, people, info = best
            n = Counter(r["Section"] for r in people)
            st.update({"Parsed_File": d["Local_File"], "Member_Role": d["Member_Role"], "Status": "OK", **info,
                       "N_Board": n["BOARD"], "N_Left": n["LEFT"], "N_Executive": n["EXECUTIVE"],
                       "N_Board_Field": sum(1 for r in people if r["Section"] == "BOARD" and r["Thai_Nationality"]),
                       "N_Exec_Field": sum(1 for r in people if r["Section"] == "EXECUTIVE" and r["Thai_Nationality"]),
                       "N_Not_Thai": sum(1 for r in people if r["Thai_Nationality"] == "No"),
                       "Board_Count_Check": ("" if not info["Total_7_2_1"] else
                                             "OK" if int(info["Total_7_2_1"]) == n["BOARD"] else "MISMATCH"),
                       # e-forms print no table 7.2.1: the director numbers must then run 1..n without a gap
                       "Board_Seq_Check": "OK" if sorted(int(r["Seq"]) for r in people if r["Section"] == "BOARD" and r["Seq"])
                                                  == list(range(1, n["BOARD"] + 1)) else "GAP"})
            out_p += [{"Ticker_Local": t, "Local_File": d["Local_File"], "Report_Lang": d.get("Report_Lang", ""), **r} for r in people]
        out_s.append(st)
    pcols = ["Ticker_Local", "Local_File", "Report_Lang", "Section", "Seq", "Page", "Name_Raw", "Name_Clean", "Gender", "Age",
             "Thai_Nationality", "Residing_In_Thailand", "Position_Raw", "Director_Type", "Date_Assumed", "Date_Ended", "Quote"]
    write_csv(DATA / "people_onereport.csv", out_p, pcols)
    write_csv(DATA / "report_stats.csv", out_s, list(dict.fromkeys(k for r in out_s for k in r)))
    ok = [s for s in out_s if s["Status"] == "OK"]
    print(len(out_s), "companies |", len(ok), "parsed |", dict(Counter(s.get("Board_Count_Check", "") for s in ok)),
          "| people", len(out_p), "| not Thai", sum(1 for r in out_p if r["Thai_Nationality"] == "No"))


if __name__ == "__main__":
    main()
