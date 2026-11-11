# Hand-read FO, 10 Nov 2026 (owner 8a: read the rest by hand). Run from the project root:
#   .venv/bin/python -I indonesia/data/manual/batch_src/fo_20261110_07.py  -> then id_add_records.py on the JSON
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_fo_batch import own, save, O
own("AEGS", 1, 81, "LOCAL", "<=44.77", "NAMED_HOLDERS", "dr. Josephat Suwanta Sinarya 555.649.980", 80,
    note="Dr. J. Suwanta Sinarya 55.23 % at 31 Dec 2025 is an Indonesian citizen (p82: 'Dr. J. Suwanta Sinarya merupakan warga negara Indonesia') -> foreign at most 44.77 %; inside KSEI bounds 6.6-66.8 %")
own("ALKA", 1, 73, "LOCAL", "0.83", "LOCAL_FOREIGN_TABLE", "Foreign Institution 4 13 1.275.200 0.251 2 38 448.828.105 88.410 3 27 2.945.923 0.580", 120,
    note="Classification table (columns interleaved in the text layer): Indonesian individual 10.758 %, Indonesian institution 88.410 % (PT. Gesit Perkasa 84 %), foreign individual 0.580 %, foreign institution 0.251 % -> FO 0.83 %; sum 99.999 %")
own("ASRM", 1, 115, "LOCAL", "<=49.32", "NAMED_HOLDERS", "Syahril, S.E. 402.728.008 31,51", 200,
    note="Syahril 31.51 % (p105 'Warga Negara Indonesia') + A. Winoto Doeriat 19.17 % (p101 'Warga Negara Indonesia') = 50.68 % Indonesian citizens -> foreign at most 49.32 % (Korean Reinsurance Company 10.00 %); inside KSEI bounds 0.8-81.2 %")
own("ATAP", 2, 57, "LOCAL", "<=24.00", "NAMED_HOLDERS", "Struktur pemegang saham Perseroan per 31 Desember 2025 dapat dilihat pada bagan berikut", 90,
    note="Chart in the page image (viewed 10 Nov 2026): PT Trimitra Prawara Goldland 76.00 %, Yoyo Sugeng Triyogo 2.00 %, Indriati 2.00 %, Masyarakat 20.00 % -> Indonesian PT 76 %, foreign at most 24 %; inside KSEI bounds 0.1-80.1 %")
own("BAIK", 2, 25, "LOCAL", "<=20.99", "NAMED_HOLDERS", "PT Anak Baik Sejahtera Yeni Isnawati Nanang Suherman Masyarakat / Public Total", 150,
    note="PT Anak Baik Sejahtera (Indonesian PT) 79.01 % -> foreign at most 20.99 %; inside KSEI bounds 0.0-80.0 %")
own("BAJA", 1, 29, "LOCAL", "<=26.07", "NAMED_HOLDERS", "Pandji Surya Soerjoprahono : 16,47%", 170,
    note="Five individuals, all Board/Direksi members with profile field Kewarganegaraan / Citizenship 'Indonesia Indonesian' for both profiles on p37, p39, p40 (Soediarto, Ibnu, Handaja, Pandji, Entario) hold 73.93 % -> foreign at most 26.07 %; inside KSEI bounds 0.0-77.8 %")
save("indonesia/data/manual/batches/id_fo_20261110_07.json")
