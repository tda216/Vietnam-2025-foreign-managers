# Hand-read FO, 10 Nov 2026: corrections of auto-accepted rows whose evidence was a subsidiary / associate table or the
# issuer's own name (AKSI / FILM / SWID / ANTM / BBTN lesson; id06 guard added). Run from the project root.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_fo_batch import own, save
own("ANTM", 1, 247, "LOCAL", "<=35.00", "NAMED_HOLDERS", "per tanggal 31 Desember 2025, Pemegang Saham Utama dan Pengendali dari Perseroan yaitu Negara Republik Indonesia", 200,
    note="Chart on the same page: PT Mineral Industri Indonesia (Persero) 65 % Series B shares + Republic of Indonesia 1 Dwiwarna Series A share -> foreign at most 35 %. Replaces the auto row from p418 (an associate, PT MJIS)")
own("BBTN", 3, 209, "LOCAL", "<=40.00", "NAMED_HOLDERS", "miliki oleh PT Danantara Asset Management dengan kepemilikan saham sebesar 60,00%", 200,
    note="PT Danantara Asset Management (State) 60.00 % -> foreign at most 40.00 %; inside KSEI bounds 10.6-70.6 % (auto row had the same value but read the issuer's name in the chart)")
own("FILM", 1, 88, "LOCAL", "22.78", "LOCAL_FOREIGN_TABLE", "Pemegang Saham Lokal Local Shareholders Individu Individual 1.826.162.047", 330,
    note="Local individual 16.77 % + local institution 60.45 % + foreign individual 0.18 % + foreign institution 22.60 % = 100 % -> FO 22.78 % (= KSEI foreign custody 22.8 %). Replaces the auto row from p98 (subsidiary PT White Tiger Studios)")
own("SWID", 1, 76, "LOCAL", "0.03", "LOCAL_FOREIGN_TABLE", "Kepemilikan Institusi Lokal Local Institutional Ownership 4 0,08122% 66,29729%", 330,
    note="Ownership: local institutions 66.297 % (PT Saraswanti Utama 63.52 %), foreign institutions 0.022 %, local individuals 33.675 %, foreign individuals 0.007 % -> FO 0.03 %. Replaces the auto row that read the issuer's own name")
save("indonesia/data/manual/batches/id_fo_20261110_12.json")
