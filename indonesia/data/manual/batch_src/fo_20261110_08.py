# Hand-read FO, 10 Nov 2026 (owner 8a). Run from the project root, then id_add_records.py on the JSON.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_fo_batch import own, save
own("CBPE", 2, 61, "LOCAL", "<=26.85", "NAMED_HOLDERS", "Pemegang Saham Utama Perseroan adalah PT Sandhi Parama Nusa dan Gaery Djohari", 170,
    note="PT Sandhi Parama Nusa (Indonesian PT) 73.15 % at 31 Dec 2025 -> foreign at most 26.85 %; inside KSEI bounds 0.0-80.0 %")
own("BLTA", 1, 46, "LOCAL", "<=42.09", "LOCAL_FOREIGN_TABLE", "Lokal Local Institusi Institution 221", 330,
    note="Local institution 37.01 % + local individual 20.90 % + foreign institution 34.97 % + foreign individual 4.19 % + unidentified (DTE) 2.93 % = 100 %; FO 39.16 %, at most 42.09 % if all unidentified were foreign; inside KSEI bounds 18.9-55.5 %")
own("BGTG", 1, 89, "LOCAL", "35.16", "LOCAL_FOREIGN_TABLE", "Pemodal Asing Foreign Investor Perorangan Asing Foreign Individual 11 1.033.500 0,00", 160,
    note="Column 31 Dec 2025 (first column; second = 1 Jan 2025): foreign individual 0.00 % + foreign enterprise 35.16 %; national investors 64.84 % (PT 54.25 %); 1 Jan 2025 column 38.04 %; inside KSEI bounds 33.5-68.7 %")
own("BLUE", 1, 49, "LOCAL", "0.60", "LOCAL_FOREIGN_TABLE", "Pemodal Domestik Domestic Investors Individu Lokal Local Individual 2.161 277.012.375 66,27", 330,
    note="Domestic: local individual 66.27 % + local institution 33.13 % = 99.40 % of 418,000,000 shares; the foreign rows repeat the local figures (error in the report), foreign = 0.60 % by difference = KSEI foreign custody 0.6 % (lower bound); named: PT Cetak Biru Capital 28.22 %")
own("CMRY", 1, 69, "LOCAL", "20.59", "LOCAL_FOREIGN_TABLE", "Total Pemegang Saham Asing Total Foreign Shareholders 279 1.647.245.173 20,76% 298 1.633.649.786 20,59%", 120,
    note="Two columns (31 Dec 2024, 31 Dec 2025 per the header on the same page): foreign 20.76 % / 20.59 %; 20.59 % = KSEI foreign custody (lower bound 20.6 %); both far below 50 %")
own("CTRA", 1, 60, "LOCAL", "<=46.69", "NAMED_HOLDERS", "PT Sang Pelopor", 120,
    note="PT Sang Pelopor (Indonesian PT) 53.31 % -> foreign at most 46.69 %; classification table p61: national business entity 57.0 %, foreign 26.9 %; inside KSEI bounds 23.4-56.7 %")
own("DWGL", 1, 13, "LOCAL", "49.22", "NAMED_HOLDERS+KSEI", "Institusi Asing • Foreign Institutions 4.489.671.120 48,5%", 330,
    note="At 31 Dec 2025: Hawthorn-Capital Investment Pte. Ltd. 48.52 % (registered outside KSEI), KSEI 45.5 %, PT (NPWP) 6.0 %; KSEI 30 Dec 2025: foreign custody 0.70 % of listed shares, coverage 45.4 % -> FO 48.52 + 0.70 = 49.22 % (close to 50 %, read by hand)")
own("ECII", 1, 43, "LOCAL", "<=42.33", "NAMED_HOLDERS", "Kepemilikan Saham Share Ownership • PT Graha Surya Kirana : 25,57%", 230,
    note="PT Graha Surya Kirana 25.57 % + PT Artha Graha Network 23.15 % (Indonesian PTs) + treasury shares 8.95 % -> foreign at most 42.33 % (UOB Kay Hian Pte Ltd 29.78 % + public 12.44 %); inside KSEI bounds 30.5-79.3 %")
own("DEPO", 2, 301, "LOCAL", "<=30.26", "NAMED_HOLDERS", "Tuan Kambiyanto Kettin 1.543.739.100 22,74%", 330,
    note="PT Buanatata Adisentosa 23.50 % + PT Tancorp Surya Sukses 23.50 % + Kambiyanto Kettin 22.74 % (President Director, p69 'Warga Negara / Citizenship Indonesia', page image viewed) = 69.74 % -> foreign at most 30.26 % (Global House International Company Limited 22.00 %); inside KSEI bounds 24.4-94.8 %")
own("KLAS", 2, 41, "LOCAL", "<=25.04", "NAMED_HOLDERS", "Kurnyatjan Sakti Efendie Direktur Utama President Director 109.279.895.800 74,96%", 90,
    note="Kurnyatjan Sakti Efendie 74.96 % (President Director, p38 'Kewarganegaraan Nationality Indonesia', page image viewed) -> foreign at most 25.04 %; inside KSEI bounds 0.3-75.4 %")
own("GDYR", 1, 65, "FOREIGN_MAJORITY", ">=85.00", "NAMED_HOLDERS", "Pemegang saham utama dan pengendali Perseroan adalah The Goodyear Tire and Rubber Company", 140,
    note="The Goodyear Tire and Rubber Company (United States) 85 %")
own("CSAP", 1, 302, "FOREIGN_MAJORITY", ">=54.07", "NAMED_HOLDERS", "PT Buanatata Adisentosa 1.819.108.716 32,01%", 330,
    note="Capital-stock note, 31 Dec 2025 and 2024: SCG Retail Holding Co, Ltd 30.89 % + NT Asian Discovery Master FD 13.18 % + Albizia Asean Opportunities Fund 10.00 % = 54.07 % foreign holders (the two funds = KSEI foreign custody 24.5 %); PT Buanatata Adisentosa 32.01 %")
save("indonesia/data/manual/batches/id_fo_20261110_08.json")
