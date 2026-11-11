"""Listing events 2026 that explain why a firm has no AR 2025 (reviewer: news pages opened and quoted, 11 Nov 2026).
Writes data/manual/listing_events.csv (one row per code x event). Run from the project root:
  .venv/bin/python -I indonesia/data/manual/batch_src/listing_20261111.py
Sources (web-search summaries were not used as evidence; each page was opened):
  - Liputan6, 30 Jun 2026 – list of 71 issuers suspended / kept suspended for the audited FS at 31 Dec 2025.
    Liputan6 writes "TGRE" for PT Terregra Asia Energy Tbk; the IDX code is TGRA (topbusiness.id, universe).
  - topbusiness.id, 30 Jun 2026 – same 71 codes, announcement Peng-S-00020/BEI.PLP/06-2026.
  - CNBC Indonesia, 2 Jul 2026 – MENN, NINE, SOUL (Acceleration Board), Peng-S-00021/BEI.PLP/07-2026.
  - detik.com, 31 Jul 2026 – CNTX and CNTB delisted from 30 Jul 2026 at the company's request of 5 Aug 2024.
"""
import csv
from pathlib import Path

M = Path(__file__).resolve().parents[1]
ACC = "2026-11-11"
L6 = "https://www.liputan6.com/saham/read/8119807/daftar-71-emiten-kena-sanksi-gara-gara-laporan-keuangan"
TB = ("https://www.topbusiness.id/131417/bei-bekukan-perdagangan-dan-denda-71-emiten-yang-telat-sampaikan-laporan-"
      "keuangan-2025.html")
CN = ("https://www.cnbcindonesia.com/market/20260702093830-17-747416/belum-laporan-lapkeu-2025-bei-suspensi-3-emiten-"
      "sekaligus")
DT = "https://finance.detik.com/bursa-dan-valas/d-8598035/bei-resmi-coret-raksasa-tekstil-cntx-dari-pasar-modal"

S71 = ("AIMS ALTO ARKA ARMY ARTI ASMI BEBS BHAT BIKA BOSS BTEL CBMF COAL COWL CPRI CRAB DEAL DUCK ENVY ETWA GAMA GOLL "
       "GTBO HILL HITS HKMU HOME HOTL INAF INCF INDX IPPE JMAS JSKY KAYU KBRI LCGP LCKM LMAS MABA MAGP MREI MTRA NUSA "
       "PLAS PMMP POOL PTDU PURE RAFI RIMO SBAT SIMA SKYB SMRU SRIL SUGI SWAT TAYS TDPM TECH TELE TGRA TOPS TOYS TRAM "
       "TRIL TRUE UNIT ZATA ZBRA").split()
assert len(S71) == 71 == len(set(S71))

rows = []
for c in S71:
    rows.append({"Code": c, "Event": "IDX_SUSPENDED_NO_AUDITED_FS2025", "Effective_Date": "2026-06-30",
                 "Announcement": "Peng-S-00020/BEI.PLP/06-2026",
                 "Detail": "suspended (16 new from Session I 30 Jun 2026, 55 kept suspended): audited FS at 31 Dec 2025 "
                           "not filed and/or late-filing fine not paid, from the 91st calendar day after the deadline",
                 "Source_URL": L6 + " ; " + TB, "Accessed": ACC,
                 "Quote": "BEI memutuskan suspensi efek terhadap 16 perusahaan tercatat atau emiten di pasar regular dan "
                          "tunai ... sejak sesi I pada 30 Juni 2026 ... BEI juga tetap melakukan suspensi efek untuk 55 "
                          "perusahaan tercatat (Liputan6); Bursa telah memberikan Peringatan Tertulis III dan denda sebesar "
                          "Rp150.000.000 (topbusiness.id)"})
for c in ("MENN", "NINE", "SOUL"):
    rows.append({"Code": c, "Event": "IDX_SUSPENDED_NO_AUDITED_FS2025", "Effective_Date": "2026-07-01",
                 "Announcement": "Peng-S-00021/BEI.PLP/07-2026",
                 "Detail": "Acceleration Board issuer suspended: audited annual FS at 31 Dec 2025 not filed",
                 "Source_URL": CN, "Accessed": ACC,
                 "Quote": "belum menyampaikan laporan keuangan auditan tahunan per 31 Desember 2025 ... sejak Sesi I "
                          "tanggal 1 Juli 2026"})
rows.append({"Code": "CNTB", "Event": "IDX_DELISTED_VOLUNTARY", "Effective_Date": "2026-07-30", "Announcement": "",
             "Detail": "CNTX and CNTB (Century Textile Industry Tbk) delisted at the company's request of 5 Aug 2024 "
                       "(go-private); not in the KSEI holding file of 30 Dec 2025",
             "Source_URL": DT, "Accessed": ACC,
             "Quote": "kode perdagangan CNTX dan CNTB ... efektif pada 30 Juli 2026 ... berdasarkan surat permohonan yang "
                      "diajukan CNTX pada 5 Agustus 2024 silam"})

with (M / "listing_events.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", M / "listing_events.csv")
