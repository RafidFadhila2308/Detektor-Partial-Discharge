import cv2
import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis, entropy
from sklearn.cluster import DBSCAN

# =========================================================
# MODUL : EKSTRAKSI & ANALISIS PLOT PRPD
# =========================================================
class ProsesorPRPD:
    """
    Kelas untuk ekstraksi + analisis PRPD
    """

    def __init__(self, filepath=None, sensor_type="Umum"):
        self.filepath = filepath
        self.sensor_type = sensor_type
        self.result = {}

    def process_prpd(self):
        """
        Ekstraksi & analisis PRPD dari gambar hasil pengukuran PD.
        """
        if not self.filepath:
            raise ValueError("Filepath belum diisi!")
        
        # ---------------------------------------------------------
        # 1️) Muat gambar
        # ---------------------------------------------------------
        img = cv2.imread(self.filepath)
        if img is None:
            raise ValueError(f"Gagal membaca file gambar: {self.filepath}")

        # ---------------------------------------------------------
        # 2️) Mask warna (disesuaikan dengan plot PRPD)
        # ---------------------------------------------------------
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_blue = cv2.inRange(hsv, (100, 80, 80), (130, 255, 255))
        mask_red1 = cv2.inRange(hsv, (0, 80, 80), (10, 255, 255))
        mask_red2 = cv2.inRange(hsv, (170, 80, 80), (180, 255, 255))
        mask_green = cv2.inRange(hsv, (40, 50, 50), (80, 255, 255))
        mask_brown = cv2.inRange(hsv, (10, 100, 20), (20, 255, 200))
        mask = mask_blue | mask_red1 | mask_red2 | mask_green | mask_brown

        # ---------------------------------------------------------
        # 3️) Filter noise
        # ---------------------------------------------------------
        mask = cv2.medianBlur(mask, 3)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # ---------------------------------------------------------
        # 4️) Ambil titik
        # ---------------------------------------------------------
        points = cv2.findNonZero(mask)
        if points is None:
            return {"prpd_data_points": [], "features": {}, "indikasi_pd": "Tidak ada titik"}

        points = points.reshape(-1, 2)

        # ---------------------------------------------------------
        # 5️) Kalibrasi ke skala PRPD
        # ---------------------------------------------------------
        gh, gw, _ = img.shape
        phase_min, phase_max = 0, 360
        amp_min, amp_max = 0, 60

        prpd_data_points = []
        for (px, py) in points:
            phase = (px / gw) * (phase_max - phase_min) + phase_min
            intensity_dB = (1 - py / gh) * (amp_max - amp_min) + amp_min
            prpd_data_points.append({"phase_deg": float(phase), "intensity_dB": float(intensity_dB)})

        df = pd.DataFrame(prpd_data_points).sort_values("phase_deg")

        # ---------------------------------------------------------
        # 6) Analisis fitur PRPD
        # ---------------------------------------------------------
        N = len(df)

        # ===== Statistik amplitudo =====
        ppc = N
        mean_amp = float(df["intensity_dB"].mean()) if N > 0 else 0.0
        median_amp = float(df["intensity_dB"].median()) if N > 0 else 0.0
        std_amp = float(df["intensity_dB"].std(ddof=0)) if N > 1 else 0.0
        skew_amp = float(df["intensity_dB"].skew()) if N > 2 else 0.0
        kurt_amp = float(df["intensity_dB"].kurtosis()) if N > 3 else 0.0


        # ===== Energi =====
        linear_amp = 10 ** (df["intensity_dB"] / 20) if N > 0 else np.array([])
        energy_proxy = float((linear_amp ** 2).sum()) if N > 0 else 0.0

        # ===== Distribusi fasa =====
        if N > 0:
            angles_rad = np.deg2rad(df["phase_deg"].values)
            C, S = np.sum(np.cos(angles_rad)), np.sum(np.sin(angles_rad))
            R = math.sqrt(C * C + S * S) / N
            mean_phase_deg = (math.degrees(math.atan2(S, C)) + 360) % 360
        else:
            R, mean_phase_deg = 0.0, 0.0

        n_pos = len(df[df["phase_deg"] < 180])
        n_neg = len(df[df["phase_deg"] >= 180])
        polarity_ratio = float(n_pos / n_neg) if n_neg > 0 else float("inf") if n_pos > 0 else 0.0

        # Sebaran fasa 90%
        if N > 0:
            phases_sorted = np.sort(df["phase_deg"].values)
            arr = np.concatenate([phases_sorted, phases_sorted + 360])
            k = int(0.9 * N)
            min_width = 360.0
            for i in range(len(phases_sorted)):
                j = i + k - 1
                if j < len(arr):
                    min_width = min(min_width, arr[j] - arr[i])
            phase_spread_90 = float(min_width)
        else:
            phase_spread_90 = 360.0

        # ===== Pola PD =====
        if N >= 10:
            arr2 = df[["phase_deg", "intensity_dB"]].values
            db = DBSCAN(eps=5, min_samples=10).fit(arr2)
            labels = db.labels_
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            in_cluster_frac = float(np.sum(labels != -1) / len(labels))
        else:
            n_clusters, in_cluster_frac = 0, 0.0

        # Entropi distribusi fasa
        if N > 0:
            hist, _ = np.histogram(df["phase_deg"].values, bins=10, range=(0, 360), density=True)
            hist = hist + 1e-12
            entropy = -float(np.sum(hist * np.log(hist)))
        else:
            entropy = 0.0
        
        # ---------------------------------------------------------
        # 7) Tampilkan hasil analisis PRPD
        # ---------------------------------------------------------
        features = {
            # Statistik amplitudo
            "Jumlah Titik (N)": int(N),
            "Pulse per Cycle (PPC)": float(ppc),
            "Rata-rata dB": float(mean_amp),
            "Median dB": float(median_amp),
            "Standar Deviasi dB": float(std_amp),
            "Skewness dB": float(skew_amp),
            "Kurtosis dB": float(kurt_amp),

            # Energi
            "Proksi Energi": float(energy_proxy),

            # Distribusi fasa
            "Koefisien Konsentrasi Fasa (R)": float(R),
            "Rata-rata Fasa (derajat)": float(mean_phase_deg),
            "Sebaran Fasa 90%": float(phase_spread_90),
            "Jumlah Titik Positif (0–180°)": int(n_pos),
            "Jumlah Titik Negatif (180–360°)": int(n_neg),
            "Rasio Polaritas": float(polarity_ratio),

            # Pola PD (berbasis klaster/entropi)
            "Jumlah Klaster": int(n_clusters),
            "Fraksi Titik dalam Klaster": float(in_cluster_frac),
            "Entropi Distribusi Fasa": float(entropy),
        }

        # ---------------------------------------------------------
        # 8) Indikasi PD Waveform (aturan threshold sederhana)
        # ---------------------------------------------------------
        pd_flag = False
        if self.sensor_type == "TEV":
            if ppc >= 30 or mean_amp >= 2.0 or energy_proxy >= 5000:
                pd_flag = True
        elif self.sensor_type == "HFCT":
            if ppc >= 100 or mean_amp >= 6.0 or (R >= 0.3 and in_cluster_frac >= 0.25) or energy_proxy >= 20000:
                pd_flag = True
        elif self.sensor_type == "Ultrasonik":
            if ppc >= 50 or mean_amp >= 8.0 or (R >= 0.4 and in_cluster_frac >= 0.2) or energy_proxy >= 10000:
                pd_flag = True
        else:
            if ppc >= 50 or mean_amp >= 5.0:
                pd_flag = True

        self.result = {
            "prpd_data_points": prpd_data_points,
            "features": features,
            "indikasi_pd": "Ada" if pd_flag else "Tidak signifikan"
        }
        return self.result

    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    def save_plot_result(self, json_out):
        """
        Simpan hasil ke JSON.
        """
        if not self.result:
            raise ValueError("Belum ada hasil. Jalankan process() dulu.")
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(self.result, f, indent=4)

    def load_plot_result(self, json_file):
        """
        Muat hasil dari JSON.
        """
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                self.result = json.load(f)
            return self.result
        except Exception as e:
            self.result = {
                "prpd_data_points": [],
                "features": {},
                "indikasi_pd": f"Gagal load: {e}",
            }
            return self.result