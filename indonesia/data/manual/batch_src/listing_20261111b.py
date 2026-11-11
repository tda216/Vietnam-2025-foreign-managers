"""Listing events, part 2 (11 Nov 2026): delisting effective 10 Nov 2026 and the IDX list of issuers suspended > 6 months.
Appends to data/manual/listing_events.csv (run listing_20261111.py first). Run from the project root:
  .venv/bin/python -I indonesia/data/manual/batch_src/listing_20261111b.py
Sources (pages opened and quoted; web-search summaries not used as evidence):
  - KabarBursa, 13 Apr 2026 – 18 stocks delisted from 10 Nov 2026 (Peng-DEL-00001/BEI.PP1/04-2026,
    Peng-DEL-00002/BEI.PP2/04-2026, Peng-DEL-00001/BEI.PP3/04-2026 of 10 Apr 2026): 7 bankrupt, 11 suspended > 50 months.
  - CNBC Indonesia, 1 Aug 2026 – issuers suspended at 30 Jun 2026 (potential delisting list; the article names 53 of the
    59 codes and gives the months of suspension for most).
"""
import csv
from pathlib import Path

M = Path(__file__).resolve().parents[1]
ACC = "2026-11-11"
KB = "https://www.kabarbursa.com/market-hari-ini/bei-delisting-18-saham-sekaligus-siapa-saja-terdampak"
CN = "https://www.cnbcindonesia.com/market/20260731190020-17-755602/59-emiten-berpotensi-ditendang-dari-bei-ini-daftar-nama-perusahaannya"
PAILIT = "COWL MTRA SRIL TOYS SBAT TDPM TELE".split()
LONG = "LCGP SUGI MABA LMAS SKYB ENVY GOLL PLAS TRIL UNIT DUCK".split()
MONTHS = {"BEBS": 16, "WIKA": 16, "TGUK": 13, "ALTO": "", "PMMP": "", "PTMR": "", "SWAT": 12, "TGRA": 12, "ZBRA": 12,
          "KIAS": 11, "FIMP": 10, "DPNS": 8, "GLOB": 8, "MENN": 8, "BIMA": 7, "MTPS": 7, "TOPS": 7, "INRU": 6, "ARTI": 24,
          "BIKA": 24, "INAF": 24, "MKNT": 24, "POLL": 24, "IPPE": 22, "ALMI": 20, "LMSH": 17, "MFMI": 17, "MTSM": 17,
          "PLIN": 17, "WICO": 17, "SMCB": 17, "FASW": 17, "JSKY": 47, "PURE": 47, "HOTL": 47, "MAGP": 48, "CBMF": 41,
          "WSKT": 38, "CPRI": 36, "GAMA": 36, "HKMU": 36, "TECH": 35, "HOME": 77, "RIMO": 77, "POOL": 73, "NUSA": 70,
          "POSA": 68, "KBRI": 87, "BTEL": 86, "TRIO": 84, "ARMY": 80, "SMRU": 78, "TRAM": 78}
assert len(MONTHS) == 53

p = M / "listing_events.csv"
rows = [r for r in csv.DictReader(p.open(encoding="utf-8"))
        if r["Event"] not in ("IDX_DELISTED_20261110", "IDX_SUSPENDED_OVER_6M_20260630")]
for c in PAILIT + LONG:
    why = "bankrupt (pailit)" if c in PAILIT else "trading suspended for more than 50 months"
    rows.append({"Code": c, "Event": "IDX_DELISTED_20261110", "Effective_Date": "2026-11-10",
                 "Announcement": "Peng-DEL-00001/BEI.PP1/04-2026; Peng-DEL-00002/BEI.PP2/04-2026; Peng-DEL-00001/BEI.PP3/04-2026 (10 Apr 2026)",
                 "Detail": f"forced delisting by IDX, effective 10 Nov 2026: {why}", "Source_URL": KB, "Accessed": ACC,
                 "Quote": ("terdapat tujuh perusahaan yang dinyatakan pailit" if c in PAILIT else
                           "telah mengalami suspensi perdagangan lebih dari 50 bulan") +
                          " ... Kebijakan ini akan berlaku efektif pada 10 November 2026"})
for c, m in MONTHS.items():
    rows.append({"Code": c, "Event": "IDX_SUSPENDED_OVER_6M_20260630", "Effective_Date": "2026-06-30", "Announcement": "",
                 "Detail": "on the IDX list of issuers suspended for more than 6 months at 30 Jun 2026 (potential delisting)"
                           + (f"; suspended {m} months" if m else "; months not stated"),
                 "Source_URL": CN, "Accessed": ACC,
                 "Quote": "per 30 Juni 2026, ada sebanyak 59 emiten yang dihentikan perdagangannya sementara (suspensi)"})
with p.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", p)
