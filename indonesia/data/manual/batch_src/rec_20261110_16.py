# Records found by the TABLE_PAIR screen (bilingual profile / diversity tables, 10 Nov 2026). Page images viewed.
import sys; sys.path.insert(0, "indonesia/pipeline")
from id_batch_helpers import *
add("BBHI", 1, 368, "Sajal Bhatnagar", "Direktur Digital", E, "India",
    quote="Sajal Bhatnagar Direktur Digital Digital Director India Indian 38 Laki-laki Male", raw="India Indian",
    note="Diversity table of the Board (page image viewed)")
add("IFSH", 1, 59, "Ryan Fong Jaya", "Komisaris", B, "Singapore",
    quote="34 year old, born in 1991 Male Singapore Singaporean 2019", raw="Kewarganegaraan Citizenship: Singapura / Singapore",
    note="Profile table (page image viewed): Kewarganegaraan / Citizenship Singapura / Singapore; in office since 2019")
add("GOOD", 1, 61, "Swen Neufeldt", "Komisaris", B, "United States",
    quote="Amerika Serikat United States of America Usia Age 53 tahun 53 years old", raw="Kewarganegaraan Amerika Serikat",
    note=IMG + "; text layer partly font-encoded; field 'Kewarganegaraan Citizenship Amerika Serikat United States of America'; term 2023-2028")
add("MSJA", 1, 147, "Takushi Ishimoto", "Direktur (General Manager)", E, "Japan",
    quote="Takushi Ishimoto Yoshiharu Yamagishi Warga Negara/Citizenship Jepang/Japan Jepang/Japan Jabatan Position General Manager sekaligus Direktur Perseroan",
    raw="Warga Negara/Citizenship Jepang/Japan", note="Foreign-worker (TKA) table, page image viewed: first column Takushi Ishimoto = General Manager and concurrent Director; Direktur at 31 Dec 2025 (p29)")
add("MSJA", 1, 147, "Yoshiharu Yamagishi", "General Manager", O, "Japan",
    quote="Takushi Ishimoto Yoshiharu Yamagishi Warga Negara/Citizenship Jepang/Japan Jepang/Japan", raw="Warga Negara/Citizenship Jepang/Japan",
    note="Foreign-worker (TKA) table, page image viewed: second column Yoshiharu Yamagishi = General Manager (senior officer listed in the AR); Management_Include left for the research team")
save("indonesia/data/manual/batches/id_batch_20261110_16.json")
