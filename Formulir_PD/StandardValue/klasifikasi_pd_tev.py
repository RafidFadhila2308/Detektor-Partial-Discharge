# =========================================================
# STANDAR : KLASIFIKASI PD TEV
# =========================================================
def KlasifikasiPDTEV(nilai_db=None, ppc=None, interpretasi=None):
    """
    Klasifikasi Partial Discharge (PD) berdasarkan sensor TEV

    Parameter:
        nilai_db (float)    : Level TEV dalam dB
        ppc (int)           : Pulses per cycle
        interpretasi (str)  : Interpretasi (a–g) dari UltraTev 2 Plus
    
    Return:
        dict: {
            'tingkat_keparahan' (str),
            'rekomendasi' (str)
        }
    """

    #  1) Tangani kasus tidak ada data 
    if (nilai_db is None or nilai_db == 0) and (ppc is None or ppc == 0) and not interpretasi:
        return {
            "tingkat_keparahan": "Tidak Ada Data",
            "rekomendasi": "Tidak dapat menentukan – data tidak tersedia"
        }

    # Default agar tidak error jika None
    nilai_db = nilai_db or 0
    ppc = ppc or 0

    #  2) Tentukan zona berdasarkan nilai dB 
    if nilai_db < 10:
        d_zone = "D0"
    elif 10 <= nilai_db <= 19:
        d_zone = "D1"
    elif 20 <= nilai_db <= 29:
        d_zone = "D2"
    else:  # >= 30
        d_zone = "D3"

    #  3) Tentukan zona berdasarkan PPC 
    if ppc <= 4:
        p_zone = "P0"
        tipe_ppc = "Sangat rendah / kemungkinan noise"
    elif 5 <= ppc <= 19:
        p_zone = "P1"
        tipe_ppc = "Discharge berulang (rendah–menengah)"
    else:  # >=20
        p_zone = "P2"
        tipe_ppc = "Discharge signifikan / permukaan"

    #  4) Matriks interpretasi kombinasi dB–PPC 
    matrix = {
        ("D0", "P0"): ("a", "Tidak memerlukan perhatian"),
        ("D0", "P1"): ("b", "PPC tinggi, kemungkinan noise"),
        ("D0", "P2"): ("d", "Kemungkinan discharge permukaan – cek ultrasonik"),
        ("D1", "P0"): ("a", "Tidak memerlukan perhatian"),
        ("D1", "P1"): ("c", "Kemungkinan PD tingkat rendah"),
        ("D1", "P2"): ("d", "Kemungkinan discharge permukaan – cek ultrasonik"),
        ("D2", "P0"): ("e", "Kemungkinan PD tingkat menengah"),
        ("D2", "P1"): ("e", "Kemungkinan PD tingkat menengah"),
        ("D2", "P2"): ("d", "Kemungkinan discharge permukaan – cek ultrasonik"),
        ("D3", "P0"): ("f", "Kemungkinan PD tingkat tinggi"),
        ("D3", "P1"): ("f", "Kemungkinan PD tingkat tinggi"),
        ("D3", "P2"): ("g", "Kemungkinan logam mengambang / koneksi jelek (atau noise sangat tinggi)"),
    }

    kode, dasar_kode = matrix[(d_zone, p_zone)]

    #  5) Tentukan tingkat keparahan berdasarkan zona 
    if (d_zone, p_zone) in [("D0", "P0"), ("D1", "P0"), ("D0", "P1")]:
        tingkat_keparahan = "Noise / Insignifikan"
        dasar_db = "Tidak memerlukan perhatian; survey ulang 12 bulan"
    elif (d_zone, p_zone) in [("D0", "P2"), ("D1", "P1"), ("D1", "P2")]:
        tingkat_keparahan = "Rendah"
        dasar_db = "Survey ulang 6 bulan untuk trending"
    elif d_zone == "D2":
        tingkat_keparahan = "Sedang"
        dasar_db = "Investigasi & penlokasi PD; perbaiki secepat praktis"
    else:  # D3
        tingkat_keparahan = "Tinggi"
        dasar_db = "Prioritas tinggi; perbaiki secepatnya"

    #  6) Aturan tambahan berbasis PPC 
    aturan_ppc = ""
    if p_zone == "P2":
        aturan_ppc = "Cek ultrasonik & validasi fase/PRPD"
        if ppc >= 50:
            aturan_ppc += " | PPC sangat tinggi → curigai noise/EMI atau koneksi longgar"

    # 7) Override interpretasi jika user input manual
    if interpretasi and interpretasi.lower() in list("abcdefg"):
        kode = interpretasi.lower()

    # 8) Gabungkan rekomendasi aksi
    rekomendasi_text = f"[{kode}], {dasar_kode}, {dasar_db}, {tipe_ppc}, {aturan_ppc}"

    return {
        "tingkat_keparahan": tingkat_keparahan,
        "rekomendasi": rekomendasi_text
    }
