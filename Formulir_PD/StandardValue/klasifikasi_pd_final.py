# =========================================================
# STANDAR : KOMBINASI KLASIFIKASI PD
# =========================================================
def KlasifikasiPDFinal(hasil):
    """
    Kombinasi hasil indikasi Partial Discharge (PD) 
    dari tiga metode pengukuran: HFCT, TEV, dan Ultrasonik.

    Parameter:
        hasil (list of dict) :
            Daftar hasil dari masing-masing metode dengan format:
            {
                "metode": "HFCT"/"TEV"/"Ultrasonik",
                "tingkat_keparahan": str,
                "rekomendasi": str
            }

    Return:
        dict: {
            "keparahan_final" (str),
            "rekomendasi_final" (str)
        }
    """

    # 1) Pemetaan tingkat keparahan menjadi skor numerik
    peta_keparahan = {
        "Noise / Insignifikan": 0,
        "Rendah": 1,
        "Sedang": 2,
        "Tinggi": 3
    }

    # 2) Bobot tiap metode
    bobot_metode = {
        "HFCT": 0.5,       # dominan → indikasi internal
        "TEV": 0.3,        # menengah → indikasi eksternal
        "Ultrasonik": 0.2  # pelengkap → indikasi akustik
    }

    # 3) Kelompokkan hasil berdasarkan metode
    kelompok = {"HFCT": [], "TEV": [], "Ultrasonik": []}
    for r in hasil:
        metode = r["metode"]
        tingkat = r["tingkat_keparahan"]

        # skip jika tidak ada data
        if tingkat == "Tidak Ada Data":
            continue

        if metode in kelompok and tingkat in peta_keparahan:
            kelompok[metode].append(peta_keparahan[tingkat])

    # 4) Hitung skor akhir berbobot
    total_skor = 0
    total_bobot = 0
    for metode, daftar_skor in kelompok.items():
        if daftar_skor:
            skor_metode = max(daftar_skor)  # ambil level tertinggi
            bobot = bobot_metode[metode]
            total_skor += skor_metode * bobot
            total_bobot += bobot

    # 5) Jika semua kosong
    if total_bobot == 0:
        return {
            "keparahan_final": "Tidak Ada Data",
            "rekomendasi_final": "Tidak dapat menentukan – tidak ada hasil pengukuran"
        }

    # 6) Rata-rata berbobot (0–3) → bulatkan ke level
    skor_final = total_skor / total_bobot
    level_final = round(skor_final)

    # 7) Konversi skor → label keparahan
    peta_kebalikan = {
        0: "Noise / Insignifikan",
        1: "Rendah",
        2: "Sedang",
        3: "Tinggi"
    }
    keparahan_final = peta_kebalikan[level_final]

    # 8) Tentukan rekomendasi akhir
    if level_final == 0:
        rekomendasi = "Survey ulang dalam 12 bulan untuk trending"
    elif level_final == 1:
        rekomendasi = "Survey ulang dalam 6 bulan untuk trending"
    elif level_final == 2:
        rekomendasi = "Investigasi & penlokasi PD; perbaiki secepat praktis"
    else:  # level_final == 3
        rekomendasi = "Prioritas tinggi; perbaiki secepatnya"

    return {
        "keparahan_final": keparahan_final,
        "rekomendasi_final": rekomendasi
    }
