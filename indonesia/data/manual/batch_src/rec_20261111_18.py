# Records from the ARs 2025 filed as IDX announcements (id03h, 11 Nov 2026). Page images viewed for every record.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_batch_helpers import *
add("GIAA", 3, 102, "Balagopal Kunduvara", "Direktur Keuangan dan Manajemen Risiko / Director of Finance and Risk Management", E,
    "Singapore", quote="Kepemilikan Saham Garuda Indonesia Garuda Indonesia Share Ownership Tidak memiliki None Kewarganegaraan "
    "Nationality Warga Negara Singapura Singaporean citizen", raw="Warga Negara Singapura", ap="2025-10-15",
    note=IMG + "; first appointed by the EGMS of 15 October 2025 (same page); born in India")
add("GIAA", 3, 107, "Neil Raymond Mills", "Direktur Transformasi / Director of Transformation", E, "United Kingdom",
    quote="Kewarganegaraan Nationality Warga Negara Inggris United Kingdom Citizen", raw="Warga Negara Inggris", ap="2025-10-15",
    note=IMG + "; first appointed by the EGMS of 15 October 2025 (same page); born in Pretoria, South Africa")
add("MNCN", 2, 46, "Joel Richard Hogarth", "Komisaris Independen / Independent Commissioner", B, "United Kingdom",
    quote="Warga Negara Inggris, lahir pada tahun 1976. Joel Richard Hogarth menjabat sebagai Komisaris Independen PT Media "
    "Nusantara Citra Tbk sejak 26 Agustus 2020", raw="Warga Negara Inggris", ap="2020-08-26",
    note=IMG + "; also Chairman of the Audit Committee and the Nomination & Remuneration Committee")
add("DEWA", 9, 63, "Nalinkant Amratlal Rathod", "Komisaris / Commissioner", B, "India",
    quote="Nalinkant Amratlal Rathod Komisaris Commissioner Tempat, Tanggal Lahir Place, Date of Birth India, 12 Mei 1950 India, "
    "May 12, 1950 Usia Age 75 tahun 75 years old Kewarganegaraan Citizenship India", raw="Kewarganegaraan India",
    note=IMG + "; legal basis Deed No. 7 dated 8 July 2025; concurrent-positions list says 'Presiden Komisaris PT Darma Henwa "
    "Tbk (2020-saat ini)' while the profile title is Komisaris – title of the profile kept")
save("indonesia/data/manual/batches/id_batch_20261111_18.json")
