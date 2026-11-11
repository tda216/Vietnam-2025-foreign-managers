# Hand-read FO, 10 Nov 2026 (owner 8a). Run from the project root, then id_add_records.py on the JSON.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_fo_batch import own, save
own("PJAA", 1, 84, "LOCAL", "<=28.00", "NAMED_HOLDERS", "Pemegang Saham Utama sekaligus Pemegang Saham Pengendali, Pemerintah Provinsi DKI Jakarta memiliki 72,00% saham", 120,
    note="Provincial Government of DKI Jakarta 72.00 % -> foreign at most 28.00 %")
own("PMJS", 1, 38, "LOCAL", "<=49.76", "NAMED_HOLDERS", "PT Pahalamas Sejahtera 6.910.982.000", 330,
    note="PT Pahalamas Sejahtera (Indonesian PT) 50.24 % -> foreign at most 49.76 % (Mitsubishi Corporation 34.00 %, Suhanti Poniman 6.80 %, public 8.96 %); issued capital table of the AR 2025")
own("PJHB", 1, 67, "LOCAL", "<=42.25", "NAMED_HOLDERS", "Hero Gozali 720.000.000 37,50 720.000.000 37,50 Go Sioe Bie", 250,
    note="31 Dec 2025 column: Hero Gozali 37.50 % (President Commissioner, p57), Adelia Aryni Setyawan 12.75 % (Commissioner, p58), Go Sioe Bie 7.50 % (President Director, p62): each profile 'Kewarganegaraan Nationality Indonesia' (page images viewed) = 57.75 % -> foreign at most 42.25 %")
save("indonesia/data/manual/batches/id_fo_20261110_10.json")
