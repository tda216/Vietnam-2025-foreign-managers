# FO from the BAE monthly register report for December 2025 (owner 10 Nov 2026, OPEN_DECISIONS 11a), read 10 Nov 2026.
# Part 1 = the IDX e-form "Laporan Bulanan Registrasi Pemegang Efek" (text layer: holders > 5 %, position, scrip /
# scripless public); later parts = the BAE's own forms (composition national / foreign; X.H.1-1 Status A/I), mostly
# scans: those figures were read on the page image and are given as a transcription marked [page image].
# Run from the project root, then id_add_records.py on the JSON.
import csv, json, re
from pathlib import Path
ROOT = Path("indonesia"); D = ROOT / "data"
F = {(r["Code"], r["Part"]): r for r in csv.DictReader((D / "idx_reg_files.csv").open(encoding="utf-8")) if r["Status"] == "OK"}
O = []


def txt(c, part, p):
    r = F[(c, str(part))]
    j = json.loads((D / "reg_text" / c / f"{r['SHA256'][:12]}.json").read_text(encoding="utf-8"))
    return r, re.sub(r"\s+", " ", j["pages"][p - 1]["text"])


def bae(c, part, p, cls, pct, anchor=None, length=200, image=None, note=""):
    r, t = txt(c, part, p)
    if anchor:
        i = t.find(anchor)
        if i < 0:  # the e-form table can run onto the next page
            p += 1; r, t = txt(c, part, p); i = t.find(anchor)
        assert i >= 0, (c, part, p, anchor)
        q = t[i:i + length].strip()
    else:
        q = "[page image] " + image
    O.append({"Code": c, "FO_Class": cls, "FO_Pct": pct, "Method": "BAE_REGISTER_202512", "File": r["File"], "Page": str(p),
              "Quote": q, "As_Of": "2025-12-31", "Note": note + f" | IDX announcement {r['Ann_Date']} ({r['URL']})"})


bae("AKSI", 1, 1, "LOCAL", "<=7.54", "PT Batulicin Enam", 260, note="PT Batulicin Enam Sembilan (Indonesian PT) 92 % + its affiliate 0.46 % = controller 92.46 % -> foreign at most 7.54 %. Replaces the auto row (issuer's own name in an FS note)")
bae("AMOR", 1, 1, "FOREIGN_MAJORITY", ">=60.04", "Ashmore Investment", 120, note="Ashmore Investment Management Limited (61 Aldwych, London) 60.0354 % at 31 Dec 2025 (AR, FY to 30 Jun 2025: 60.0 %). Replaces the auto row (assets-under-management split)")
bae("AREA", 1, 1, "LOCAL", "<=20.14", "PT Dwi Tunggal Putra", 330, note="At 31 Dec 2025: PT Dwi Tunggal Putra 38.06 % + Sugeng Alifen (Komisaris) 30.74 % + Michael Kurnia Wirawan Alifen (Direksi, p2) 11.06 % = 79.86 %; both individuals 'Warga Negara Indonesia' in the AR 2025 (p17, p18) -> foreign at most 20.14 % (the AR 2025 itself only gave the 31 Dec 2023 structure)")
bae("ASPR", 2, 2, "LOCAL", "11.38", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Pemegang Saham Pendiri Alex Yoe 47,64 / Susan Yoewono 20,32 / Ricky Winoto 2,10; A.2.2 Pemodal Asing 0,00; B.2.1 Pemodal Nasional Lainnya 18,56; B.2.2 Pemodal Asing Lainnya 11,38; Total 100,00. Form X.H.1-1 (p4): Alex Yoe Status I 47,64 %; Susan Yoewono Status I 20,32 %",
    note="Foreign = public foreign 11.38 % (at most 13.48 % if Ricky Winoto 2.10 % were foreign); founders >= 5 % Status I")
bae("BISI", 2, 2, "FOREIGN_MAJORITY", "63.91", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 PT Agrindo Pratama 31,00; A.2.2 Pemodal Asing (Field / Valley / Vista Investment Holdings Pte. Ltd 6,36 each; lainnya 4,08) Sub Total 23,14; B.2.1 Pemodal Nasional 5,09; B.2.2 Pemodal Asing (UBS AG Singapore 6,13; United Overseas Bank Nominees 5,09; lainnya 29,55) Sub Total 40,77; Total 100,00",
    note="Foreign = 23.14 % (scrip) + 40.77 % (KSEI) = 63.91 %; X.H.1-1 (p4): the Singapore holders Status A, PT Agrindo Pratama Status I")
bae("CPRI", 1, 1, "LOCAL", "<=28.80", "PT RDW Global", 120, note="PT RDW Global (Indonesian PT) 71.2 % -> foreign at most 28.8 %")
bae("CSMI", 2, 2, "LOCAL", "0.47", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Pemegang Saham Pendiri Lisa Muchtar 56,15; A.2.2 Pemodal Asing 0,00; B.2.1 Pemodal Nasional Lainnya 43,38; B.2.2 Pemodal Asing Lainnya 0,47; Total 100,00. Form X.H.1-1 (p4): Lisa Muchtar Status I 56,15 %",
    note="Foreign = 0.47 % (= KSEI foreign custody)")
bae("DCII", 1, 1, "LOCAL", "<=47.59", "Otto Toto Sugiri", 200, note="Otto Toto Sugiri (Direksi) 29.9 % + Marina Budiman (Komisaris) 22.51 % = 52.41 %; AR 2025 p121 / p131 'Kewarganegaraan Nationality Indonesia' (page images viewed) -> foreign at most 47.59 %")
bae("EAST", 2, 2, "FOREIGN_MAJORITY", ">=72.10", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Pemegang Saham Pendiri Fauziah Umar Abdat 4,94 / Khalid Bin Omar Abdat 40,00; B.1 Pemegang Saham Pendiri (Ali Bin Said Abdat 1,41; Fauzi Omar Abdat 2,73; Fazlina Omar Abdat 2,19; Helmi Khalid Abdat 0,90; Khalid Bin Omar Abdat 3,74; Lubna Binte Ali Abdat 0,76; Nadiah Khalid Abdat 4,85) 16,58; B.2.1 Pemodal Nasional 10,12; B.2.2 Pemodal Asing 28,36; Total 100,00. Form X.H.1-1 (p4): Khalid Bin Omar Abdat, 29 Flora Road #08-08 Singapore, Status 'L', 43,74 %",
    note="FO measure = legal nationality (owner): Khalid Bin Omar Abdat is 'Warga Negara Singapura' in the AR 2025 (p16) although the BAE form marks him 'L' (his KSEI account); foreign = 43.74 % + public foreign 28.36 % = 72.10 % (more with the Singapore / Malaysia family holders); KSEI foreign custody 35.5 %")
bae("GIAA", 1, 1, "LOCAL", "<=7.97", "PT Danantara Asset", 160, note="PT Danantara Asset Management (State) 92.031 % at 31 Dec 2025 -> foreign at most 7.97 %")
bae("INDO", 1, 1, "LOCAL", "<=43.39", "Leslie Soemedi Jakarta Pusat", 120, note="Leslie Soemedi 32.21 % + Nevin Soemedi 12.46 % = 44.67 %, both Direksi with 'Warga Negara Nationality Indonesia' in the AR 2025 p39-40 (the AR text layer is font-shifted: '-RHSRIWME' = 'Indonesia'); public 12.35 % all scripless while KSEI foreign custody is 0.41 % -> at least 11.94 % local public -> foreign at most 43.39 %")
bae("IOTF", 1, 1, "LOCAL", "<=31.95", "Alamsyah", 150, note="Alamsyah (Direktur Utama) 48.3 % + Gracia Puspita Suciono (Komisaris Utama) 19.75 % = 68.05 %; AR 2025 p58 / p55 'Warga Negara Indonesia' (page images viewed) -> foreign at most 31.95 %")
bae("KICI", 1, 1, "LOCAL", "<=37.38", "PT Kedawung Subur", 120, note="PT Kedawung Subur (Indonesian PT) 43.62 %; KSEI 30 Dec 2025 local custody is only 19.0 % of listed shares, so the 43.62 % lies outside KSEI and adds to it: local >= 62.62 % -> foreign at most 37.38 % (DK Lim & Sons, Singapore, 31.4 %)")
bae("KIJA", 2, 2, "LOCAL", "31.08", "PEMODAL ASING", 230, note="Datindo composition at 31 Dec 2025: national 68.92 %, foreign 31.08 %; form p1: Mu'min Ali Gunawan 'PERORANGAN INDONESIA' 21.087 %, Islamic Development Bank 'BADAN USAHA ASING' 11.526 %")
bae("KOKA", 2, 2, "FOREIGN_MAJORITY", "50.27", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Pemegang Saham Pendiri Gao Jing 42,75 / Gao Jinfeng 5,40 / PT Kreatif Konstruksi Indonesia 24,75; B.2.1 Pemodal Nasional (Ling Sun 5,60; lainnya 19,39) 24,98; B.2.2 Pemodal Asing Lainnya 2,12; Total 100,00. Form X.H.1-1 (p4): Gao Jing Status A 42,75 %; Gao Jinfeng Status A 5,40 %; PT Kreatif Konstruksi Indonesia Status I; Ling Sun Status I",
    note="Foreign = 42.75 + 5.40 + 2.12 = 50.27 % (just above 50 %)")
bae("LFLO", 1, 1, "LOCAL", "<=32.60", "Ang Phek Tuan", 330, note="Erlangga Ksatria 24.43 % (Direktur Utama, AR p45) and Purnamawati Gumulya 24.43 % (Komisaris, AR p43) 'Warga Negara Indonesia' (page images viewed); no public scrip (Masyarakat warkat 0 %) and KSEI foreign custody ~0.0 % -> foreign at most Ang Phek Tuan's 32.57 % (+0.03)")
bae("MARK", 2, 2, "FOREIGN_MAJORITY", ">=52.47", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Tecable (HK) Co. Limited 38,00 / Sutiyoso Bin Risman 0,13; B.1 Tecable (HK) Co. Limited 4,39 / Sutiyoso Bin Risman 1,37; B.2.1 Pemodal Nasional (PT Dyna Capital Indo 20,70; PT Mark Capital Indo 15,39; lainnya 9,95) 46,04; B.2.2 Pemodal Asing Lainnya 10,08; Total 100,00. Form X.H.1-1 (p4): Tecable (HK) Co. Limited Status A 42,39 %",
    note="Foreign = Tecable 42.39 % + public foreign 10.08 % = 52.47 % (53.97 % if Sutiyoso Bin Risman were foreign)")
bae("MDLA", 5, 2, "LOCAL", "18.95", "PEMODAL ASING", 230, note="Datindo composition at 31 Dec 2025: national 81.05 %, foreign 18.95 %; form p1: Hetty Soetikno 'PERORANGAN INDONESIA' 65.94 %")
bae("MPIX", 1, 1, "LOCAL", "<=40.00", "PT Madura Prima", 130, note="PT Madura Prima (Indonesian PT) 59.9975 % -> foreign at most 40.00 %")
bae("MPRO", 2, 1, "LOCAL", "<=19.03", "1 JONATHAN TAHIR", 300, note="Form >= 5 % (Ficomindo), Status L/A: Jonathan Tahir, Tahir, Jane Dewi Tahir, Dewi Victoria Riady, Grace Dewi Riady, PT Bintang Express Sarana all 'L', total 80.967 % -> foreign at most 19.03 %")
bae("MTSM", 1, 1, "LOCAL", "<=39.73", "PT. Perkasa Makmur", 330, note="PT Perkasa Makmur 19.186 % + PT Suryasakti Budimarkarti 6.559 % + PT Yakin Wiskon 34.527 % (Indonesian PTs) = 60.27 % -> foreign at most 39.73 % (Bara Pte Ltd 20.671 %)")
bae("NZIA", 2, 9, "LOCAL", "0.09", image="Daftar Komposisi Pemilik Efek, tanggal 31-12-2025 (Sinartama Gunita): Pemodal Nasional Sub Total 99.91 %; Pemodal Asing (Individual - Foreign 0.00 %, Institution - Foreign 0.09 %) Sub Total 0.09 %; Total 100.00 %. Form >= 5 % (p10): Richard Rachmadi Wiriahardja Indonesia/I 44.5034 %; Ristia Bintang Mahkota Sejati Tbk PT Indonesia/I 34.4931 %",
    note="Foreign 0.09 %")
bae("OBMD", 1, 1, "LOCAL", "<=48.93", "PT Indotek Driling Solusi", 110, note="PT Indotek Driling Solusi (Indonesian PT) 51.07 % -> foreign at most 48.93 %")
bae("OILS", 1, 1, "LOCAL", "<=45.06", "SULASTRI", 120, note="PT Mandalindo (Indonesian PT) 47.85 % + Sulastri (Komisaris Utama, AR p52 'Warga Negara Indonesia') 7.09 % = 54.94 % -> foreign at most 45.06 %")
bae("PMUI", 2, 5, "LOCAL", "<=20.00", image="Form X.H.1-1, 31 Desember 2025: Rudy Susanto Wijaya Kaswan Status I 56,00 %; Agus Susanto Status I 24,00 %; Jumlah 80,00 %",
    note="Both founders Status I -> foreign at most the public 20 %")
bae("RGAS", 2, 2, "LOCAL", "0.08", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Pemegang Saham Pendiri (Agus Salim 17,34; Taufik Dwicahyono 14,46; Edy Nurhamid Amin 14,46; Fadjar Tri Ananda 11,56; Kian Megah Investama, PT 9,64; Platinum Berkah Abadi, PT 9,64) 77,10; B.2.1 Pemodal Nasional 22,82; B.2.2 Pemodal Asing 0,08; Total 100,00. Form X.H.1-1 (p4): all six Status I",
    note="Foreign 0.08 %")
bae("SMIL", 1, 1, "LOCAL", "<=45.01", "Hadi Suhermin", 200, note="Hadi Suhermin (Direktur Utama) 46.99 % + Winston Suhermin (Direktur) 8 % = 54.99 %; AR 2025 p31 / p32 'Indonesian citizen' / 'Warga Negara Indonesia' -> foreign at most 45.01 % (Lucia Irawaty Lie, Komisaris Utama, 24 % also Indonesian per p29)")
bae("TCID", 1, 1, "FOREIGN_MAJORITY", ">=65.23", "Mandom Corporation", 80, note="Mandom Corporation (Japan) 65.23 %")
bae("TMPO", 1, 1, "LOCAL", "<=25.49", "PT Grafiti Pers", 330, note="PT Grafiti Pers 24.28 % + Yayasan Tempo 21 Juni 17.13 % + PT Jaya Raya Utama 16.28 % + Yayasan Pembangunan Jaya 8.54 % + Yayasan Karyawan Tempo 8.28 % (Indonesian entities) = 74.51 % -> foreign at most 25.49 %")
bae("TYRE", 2, 2, "LOCAL", "0.08", image="Komposisi Kepemilikan Saham per 31 Desember 2025: A.1 Pemegang Saham Pendiri (PT Kingland Investindo Nusantara 31,60; Harris Muliawan 32,21; Indra Muliawan 15,93; Hardi Muliawan 0,07) 79,81; B.2.1 Pemodal Nasional (Harris Muliawan 1,85; lainnya 18,26) 20,11; B.2.2 Pemodal Asing 0,08; Total 100,00. Form X.H.1-1 (p4): PT Kingland Investindo Nusantara, Harris Muliawan, Indra Muliawan all Status I",
    note="Foreign 0.08 %")
bae("WIIM", 1, 1, "LOCAL", "<=44.14", "Indahtati Widjajadi", 200, note="Indahtati Widjajadi (Komisaris Utama) 25.48 % + Stephen Walla (Komisaris) 15.18 % + Ronald Walla (Direktur Utama) 15.20 % = 55.86 %; AR 2025 p60 (page image), p61, p64 'Kewarganegaraan Citizenship Indonesia' -> foreign at most 44.14 %")
bae("WTON", 1, 1, "LOCAL", "<=40.00", "PT Wijaya Karya", 120, note="PT Wijaya Karya (Persero) Tbk 60 % -> foreign at most 40 %")
out = D / "manual" / "batches" / "id_fo_20261110_13_bae.json"
out.write_text(json.dumps({"ownership": O}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(O), "rows ->", out)
