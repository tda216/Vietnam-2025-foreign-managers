# Hand-read FO, 10 Nov 2026 (owner 8a). Run from the project root, then id_add_records.py on the JSON.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_fo_batch import own, save
own("TBMS", 2, 40, "FOREIGN_MAJORITY", "52.72", "LOCAL_FOREIGN_TABLE", "Institusi Lokal 35 40.989% Local Institution investor Institusi Asing 15 52.654%", 200,
    note="Classification at 31 Dec 2025: local institutions 40.989 %, foreign institutions 52.654 %, local individuals 6.293 %, foreign individuals 0.064 % (rows mislabelled 'Institusi' in the Indonesian column) = 100 %; FO 52.72 %; Furukawa Electric Co. Ltd 42.42 %; inside KSEI bounds 16.7-90.4 %")
own("SKBM", 1, 100, "FOREIGN_MAJORITY", ">=51.64", "NAMED_HOLDERS", "TAEL Two Partners Ltd 554,706,046", 140,
    note="As of 31 Dec 2025 (page header): TAEL Two Partners Ltd 32.06 % + Green Resources Investments Pte. Ltd. 19.58 % = 51.64 % foreign holders; inside KSEI bounds 39.9-86.6 %")
own("SMSM", 1, 30, "LOCAL", "<=49.46", "NAMED_HOLDERS", "Per 31 Desember 2025, tidak terdapat pemegang saham dengan kepemilikan saham lebih dari 5%, kecuali PT Adrindo Intiperkasa", 160,
    note="PT Adrindo Intiperkasa (Indonesian PT) 50.54 %, public 49.46 % -> foreign at most 49.46 %; inside KSEI bounds 27.4-80.4 %")
save("indonesia/data/manual/batches/id_fo_20261110_11.json")
