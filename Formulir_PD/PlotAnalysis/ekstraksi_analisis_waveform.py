import cv2
import json
import math
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis, entropy

# =========================================================
# MODUL : EKSTRAKSI & ANALISIS PLOT WAVEFORM
# =========================================================
class ProsesorWaveform:
    """
    Kelas untuk ekstraksi + analisis Waveform PD
    """

    def __init__(self, filepath=None, sensor_type="TEV"):
        self.filepath = filepath
        self.sensor_type = sensor_type
        self.result = {}

    def process_waveform(self):
        """
        Ekstraksi & analisis waveform dari gambar hasil pengukuran PD.
        """
        if not self.filepath:
            raise ValueError("Filepath belum diisi!")

        # ---------------------------------------------------------
        # 1) Muat gambar
        # ---------------------------------------------------------
        img = cv2.imread(self.filepath)
        if img is None:
            raise ValueError(f"Gagal membaca file gambar: {self.filepath}")

        # ---------------------------------------------------------
        # 2) Konversi ke grayscale & threshold
        # ---------------------------------------------------------
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # ---------------------------------------------------------
        # 3) Ambil titik jejak
        # ---------------------------------------------------------
        points = cv2.findNonZero(mask)
        if points is None:
            return {"waveform_data_points": [], "features": {}, "indikasi_pd": "Tidak ada jejak"}

        points = points.reshape(-1, 2)
        gh, gw = img.shape[:2]

        # ---------------------------------------------------------
        # 4) Konversi pixel ke skala (time: -5 → +6 µs, amplitude: -10 → +25 dB)
        # ---------------------------------------------------------
        t_min, t_max = -5.0, 6.0  # µs
        amp_min, amp_max = -10.0, 25.0  # dB

        waveform_data_points = []
        for (px, py) in points:
            t = (px / gw) * (t_max - t_min) + t_min
            amp = (1 - py / gh) * (amp_max - amp_min) + amp_min
            waveform_data_points.append({"time_us": float(t), "amplitude_dB": float(amp)})

        df = pd.DataFrame(waveform_data_points).sort_values("time_us")

        # ---------------------------------------------------------
        # 5) Analisis fitur waveform
        # ---------------------------------------------------------
        N = len(df)

        if N > 0:
            # ===== Statistik dasar =====
            peak_val = float(df["amplitude_dB"].max())
            peak_time = float(df.loc[df["amplitude_dB"].idxmax(), "time_us"])
            mean_val = float(df["amplitude_dB"].mean())
            std_val = float(df["amplitude_dB"].std(ddof=0))
            rms_val = float(np.sqrt(np.mean(df["amplitude_dB"]**2)))

            # ===== Energi =====
            energy_proxy = float(np.sum(df["amplitude_dB"]**2))
            crest_factor = peak_val / rms_val if rms_val > 0 else 0.0

            # ===== Statistik distribusi =====
            skew_val = float(skew(df["amplitude_dB"], bias=False))
            kurt_val = float(kurtosis(df["amplitude_dB"], bias=False))

            # ===== Bentuk pulsa =====
            # Pulse width (FWHM)
            half_peak = peak_val * 0.5
            above_half = df[df["amplitude_dB"] >= half_peak]
            if not above_half.empty:
                pulse_width = float(above_half["time_us"].max() - above_half["time_us"].min())
            else:
                pulse_width = 0.0

            # Rise time (10% → 90%)
            tenth = peak_val * 0.1
            ninetieth = peak_val * 0.9
            try:
                t10 = float(df[df["amplitude_dB"] >= tenth]["time_us"].min())
                t90 = float(df[df["amplitude_dB"] >= ninetieth]["time_us"].min())
                rise_time = t90 - t10
            except:
                rise_time = 0.0

            # Fall time (90% → 10%)
            try:
                t90_fall = float(df[df["amplitude_dB"] >= ninetieth]["time_us"].max())
                t10_fall = float(df[df["amplitude_dB"] >= tenth]["time_us"].max())
                fall_time = t10_fall - t90_fall
            except:
                fall_time = 0.0

            # Time centroid (weighted by amplitude^2)
            weights = df["amplitude_dB"]**2
            time_centroid = float(np.sum(df["time_us"] * weights) / np.sum(weights))

            # ===== Entropi =====
            hist, _ = np.histogram(df["amplitude_dB"], bins=50, density=True)
            ent_val = float(entropy(hist + 1e-12))

        else:
            peak_val = peak_time = mean_val = std_val = rms_val = 0.0
            energy_proxy = crest_factor = skew_val = kurt_val = 0.0
            pulse_width = rise_time = fall_time = time_centroid = 0.0
            ent_val = 0.0

        # ---------------------------------------------------------
        # 6) Tampilkan hasil analisis waveform
        # ---------------------------------------------------------
        features = {
            # Statistik dasar
            "Jumlah Titik (N)": int(N),
            "Puncak (dB)": float(peak_val),
            "Waktu Puncak (µs)": float(peak_time),
            "Rata-rata (dB)": float(mean_val),
            "Standar Deviasi (dB)": float(std_val),
            "RMS (dB)": float(rms_val),

            # Energi & daya
            "Proksi Energi": float(energy_proxy),

            # Bentuk gelombang
            "Crest Factor": float(crest_factor),
            "Lebar Pulsa (µs)": float(pulse_width),
            "Waktu Naik (µs)": float(rise_time),
            "Waktu Turun (µs)": float(fall_time),
            "Titik Pusat Waktu (µs)": float(time_centroid),

            # Statistik lanjutan
            "Skewness (dB)": float(skew_val),
            "Kurtosis (dB)": float(kurt_val),
            "Entropi": float(ent_val),
        }

        # ---------------------------------------------------------
        # 7) Indikasi PD Waveform (aturan threshold sederhana)
        # ---------------------------------------------------------
        pd_flag = False
        if self.sensor_type == "TEV":
            if peak_val >= 20 or rms_val >= 5:
                pd_flag = True
        elif self.sensor_type == "HFCT":
            if peak_val >= 30 or energy_proxy >= 10000:
                pd_flag = True
        else:
            if peak_val >= 15:
                pd_flag = True

        self.result = {
            "waveform_data_points": waveform_data_points,
            "features": features,
            "indikasi_pd": "Ada" if pd_flag else "Tidak signifikan"
        }
        return self.result

    
    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    def save_waveform_result(self, json_out):
        """
        Simpan hasil ke JSON.
        """
        if not self.result:
            raise ValueError("Belum ada hasil. Jalankan proses ektraksi & analisis() dulu.")
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(self.result, f, indent=4)

    def load_waveform_result(self, json_file):
        """
        Muat hasil dari JSON.
        """
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                self.result = json.load(f)
            return self.result
        except Exception as e:
            self.result = {
                "waveform_data_points": [],
                "features": {},
                "indikasi_pd": f"Gagal memuat: {e}",
            }
            return self.result
