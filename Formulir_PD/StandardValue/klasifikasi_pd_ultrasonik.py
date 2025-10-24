# =========================================================
# STANDAR : KLASIFIKASI PD ULTRASONIK
# =========================================================
def KlasifikasiPDUltrasonik(nilai_dbuv=None, kepastian=None,
                             cluster_dua_gelombang=None,
                             suara_gemerosok=None,
                             interpretasi=None,
                             sensor="UltraDish"):
    """
    Klasifikasi Partial Discharge (PD) berdasarkan Ultrasonik (Acoustic/TEV)
    dengan kombinasi level dBµV, kepastian (%), pola cluster, suara gemerosok,
    interpretasi alat, dan jenis sensor.

    Parameter:
        nilai_dbuv (float)          : Level ultrasonik dalam dBµV
        kepastian (float)           : Kepastian (%) dari alat
        cluster_dua_gelombang (str) : "Ada" jika ada cluster 2 gelombang stabil (PRPD)
        suara_gemerosok (str)       : "Ada" jika terdengar suara khas PD
        interpretasi (str)          : Interpretasi langsung alat ("Noise", "PD", dll.)
        sensor (str)                : Jenis sensor ("Contact Probe", "UltraDish", "Flexible Mic")

    Return:
        dict: {
            "tingkat_keparahan" (str),
            "rekomendasi" (str)
        }
    """

    # 1) Default handling untuk nilai None
    nilai_dbuv = nilai_dbuv or 0
    kepastian = kepastian or 0
    cluster_dua_gelombang = (cluster_dua_gelombang or "").lower()
    suara_gemerosok = (suara_gemerosok or "").lower()
    interpretasi = (interpretasi or "").lower()

    # 2) Zona dasar (berdasarkan dBµV + kepastian)
    if nilai_dbuv < 3:
        level = 1 if kepastian > 70 else 0
    elif 3 <= nilai_dbuv <= 6:
        if kepastian <= 50:
            level = 0
        elif 50 < kepastian <= 70:
            level = 1
        else:  # >70
            level = 2
    else:  # >6 dBµV
        if kepastian <= 50:
            level = 1
        elif 50 < kepastian <= 70:
            level = 2
        else:  # >70
            level = 3

    # 3) Aturan cluster dua gelombang
    if cluster_dua_gelombang == "ada":
        level = min(level + 1, 3)
    elif cluster_dua_gelombang == "tidak ada":
        if nilai_dbuv > 6 and kepastian > 70:
            level = max(level - 1, 0)
        elif nilai_dbuv > 500:  # kasus khusus
            level = 2
        else:
            level = 0

    # 4) Aturan suara gemerosok
    if suara_gemerosok == "ada":
        level = min(level + 1, 3)

    # 5) Override interpretasi alat
    if interpretasi == "noise" and level > 0:
        level = max(level - 1, 0)

    # 6) Pembobotan jenis sensor
    bobot_sensor = {
        "contact probe": 1.2,
        "ultradish": 1.0,
        "flexible mic": 0.8
    }
    bobot = bobot_sensor.get(sensor.lower(), 1.0)
    level = round(level * bobot)
    level = max(0, min(level, 3))  # clamp ke 0–3

    # 7) Mapping level → label keparahan
    reverse_map = {
        0: "Noise / Insignifikan",
        1: "Rendah",
        2: "Sedang",
        3: "Tinggi"
    }
    tingkat_keparahan = reverse_map[level]

    # 8) Rekomendasi aksi
    if level == 0:
        rekomendasi = "Survey ulang dalam 12 bulan untuk trending"
    elif level == 1:
        rekomendasi = "Survey ulang dalam 6 bulan untuk trending"
    elif level == 2:
        rekomendasi = "Investigasi & penlokasi PD; perbaiki secepat praktis"
    else:  # Tinggi
        rekomendasi = "Prioritas tinggi; perbaiki secepatnya"

    return {
        "tingkat_keparahan": tingkat_keparahan,
        "rekomendasi": rekomendasi
    }
