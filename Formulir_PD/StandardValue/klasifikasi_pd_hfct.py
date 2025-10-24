# =========================================================
# STANDAR : KLASIFIKASI PD HFCT
# =========================================================
def KlasifikasiPDHFCT(nilai_pc=None, ppc=None, unipolar_waveform=None, cluster_dua_gelombang=None):
    """
    Klasifikasi Partial Discharge (PD) berdasarkan sensor HFCT

    Parameter:
        nilai_pc (float)            : Nilai discharge dalam pC
        ppc (int)                   : Pulses per cycle
        unipolar_waveform (str)     : "Ada" jika terdeteksi unipolar
        cluster_dua_gelombang (str) : "Ada" jika ada cluster 2 gelombang stabil (PRPD)
    
    Return:
        dict: {
            'tingkat_keparahan' (str),
            'rekomendasi' (str)
        }
    """

    #  1) Tangani kasus tidak ada data 
    if (not nilai_pc or nilai_pc == 0) and (not ppc or ppc == 0) \
       and (not unipolar_waveform) and (not cluster_dua_gelombang):
        return {
            "tingkat_keparahan": "Tidak Ada Data",
            "rekomendasi": "Tidak dapat menentukan – data tidak tersedia"
        }

    # Default agar tidak error jika None
    nilai_pc = nilai_pc or 0
    ppc = ppc or 0
    unipolar_waveform = (unipolar_waveform or "").lower()
    cluster_dua_gelombang = (cluster_dua_gelombang or "").lower()

    #  2) Basis klasifikasi dari nilai pC & cluster 
    if cluster_dua_gelombang != "ada":
        if nilai_pc > 500:
            # Kasus khusus: besar tapi tanpa cluster
            level = 2   # Sedang
            rekomendasi_flag = "Flagged suspect noise (cek coupling / sensor lain)"
        elif ppc > 50:
            level = 0   # Noise / Insignifikan
            rekomendasi_flag = "Kemungkinan noise/EMI – pola repetitif tanpa cluster"
        else:
            level = 0   # Noise / Insignifikan
            rekomendasi_flag = "Tidak signifikan; kemungkinan noise"
    else:
        # Ada cluster → tentukan level dari pC
        if nilai_pc < 250:
            level = 1  # Rendah
        elif 250 <= nilai_pc <= 500:
            level = 2  # Sedang
        else:  # >500
            level = 3  # Tinggi
        rekomendasi_flag = ""

    #  3) Aturan tambahan berbasis PPC 
    if cluster_dua_gelombang == "ada":
        if 5 <= ppc <= 20:
            level = min(level + 1, 3)  # naik 1 level
        elif ppc > 20:
            level = min(level + 2, 3)  # naik 2 level

    #  4) Aturan tambahan berbasis unipolar waveform 
    if unipolar_waveform == "ada":
        if cluster_dua_gelombang == "ada":
            # Jika ada cluster, turunkan 1 level tapi tidak boleh <1
            level = max(level - 1, 1)
            rekomendasi_flag += " (Unipolar → PD lemah)"
        else:
            # Jika tidak ada cluster → lebih mirip noise
            level = max(level - 1, 0)
            rekomendasi_flag += " (Unipolar tanpa cluster → lebih noise-like)"

    #  5) Mapping level ke tingkat keparahan 
    reverse_map = {
        0: "Noise / Insignifikan",
        1: "Rendah",
        2: "Sedang",
        3: "Tinggi"
    }
    tingkat_keparahan = reverse_map[level]

    #  6) Tentukan rekomendasi aksi 
    if level == 0:
        rekomendasi = "Survey ulang dalam 12 bulan"
    elif level == 1:
        rekomendasi = "Survey ulang dalam 6 bulan (trending)"
    elif level == 2:
        rekomendasi = "Investigasi & penlokasi PD; perbaiki secepat praktis"
    else:  # Tinggi
        rekomendasi = "Prioritas tinggi; perbaiki secepatnya"

    # Tambahkan catatan flag khusus jika ada
    if rekomendasi_flag:
        rekomendasi += f" → {rekomendasi_flag.strip()}"

    return {
        "tingkat_keparahan": tingkat_keparahan,
        "rekomendasi": rekomendasi
    }
