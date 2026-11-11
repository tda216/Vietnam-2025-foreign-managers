# Hand-read FO, 10 Nov 2026 (owner 8a). Run from the project root, then id_add_records.py on the JSON.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_fo_batch import own, save
own("MTMH", 2, 57, "LOCAL", "<=25.75", "NAMED_HOLDERS", "Pemegang Saham Pengendali Perusahaan merupakan orang perseorangan yakni Bapak Tjhin Ten Chun", 110,
    note="Shareholder chart (page image viewed): Andi Indigo 20.54 %, PT Sumatera Teknindo 32.56 %, Jacqueline Sitorus 21.15 %, each 'Nationality Indonesia'; public 25.75 % -> foreign at most 25.75 % (p55 table at 31 Dec 2025: same holdings)")
own("LMAX", 1, 35, "LOCAL", "0.01", "LOCAL_FOREIGN_TABLE", "PEMODAL LOKAL PEMODAL ASING Individu Individu", 300,
    note="Classification table (columns interleaved in the text layer): local individual 648,856,925 (99.83 %), foreign individual 87,100 (0.01 %), local institution 1,064,450 (0.16 %), foreign institution 300 (0.00 %); total 650,008,775 -> FO 0.01 % = KSEI foreign custody")
own("MPXL", 2, 29, "LOCAL", "<=0.96", "LOCAL_FOREIGN_TABLE", "SUB TOTAL 2,117 1,987,345,367.00 99.37% PEMODAL ASING FOREIGN INVESTOR", 210,
    note="End of 2025 (p28): domestic investors 99.37 % (Indonesian individuals 84.11 %, PT 14.84 %, foreign individuals with KITAS 0.32 % counted as domestic); foreign investors 0.64 % -> FO 0.64 %, at most 0.96 % counting KITAS holders as foreign")
own("NASI", 1, 239, "LOCAL", "<=31.00", "NAMED_HOLDERS", "Piero Mustafa 341.016.000 42,24%", 120,
    note="Piero Mustafa 42.24 % (President Director, p51 'Warga negara Indonesia', page image viewed) + PT Modis Cipta Kreasi 26.76 % (Indonesian PT) = 69.00 % -> foreign at most 31.00 %; same table for 31 Dec 2025 and 2024 (p238-239)")
save("indonesia/data/manual/batches/id_fo_20261110_09.json")
