import matplotlib
matplotlib.use("QtAgg")
matplotlib.rcParams["interactive"] = False
matplotlib.rcParams["figure.autolayout"] = True
import sys, os
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from MyWidget import PlaceholderComboBox, PlaceholderLineEdit, MenuBar
from DataManager import DataSave, DataLoad, DataResetExtract
from PlotAnalysis import ProsesorPRPD, ProsesorWaveform

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

# =========================================================
# HALAMAN : EKSTRAKSI & ANALISIS PLOT HASIL PENGUKURAN
# =========================================================
class HalamanEkstraksiPRPD(QWidget):
    def __init__(self):
        super().__init__()

        # Judul & ukuran jendela
        self.setWindowTitle("Halaman Ekstraksi Data Gelombang & PRPD")
        self.setGeometry(200, 200, 900, 600)
        
        # ===== Inisialisasi Pengatur Data dengan JSON =====
        self.data_save = DataSave(json_file="plot_data.json")
        self.data_load = DataLoad(json_file="plot_data.json")
        self.data_reset = DataResetExtract(json_file="plot_data.json")

        # Registrasi fungsi pengatur data per section (gabungan PRPD + Waveform)
        self.data_save.register_section_save("hasil_plot", self.save_plot_result)
        self.data_load.register_section_load("hasil_plot", self.load_plot_result)
        self.data_reset.register_section_reset("hasil_plot", self.clear_current_widgets)
        
        # Deklarasi awal data analisis PD
        self.prpd_file = ""
        self.waveform_file = ""
        self.last_prpd_result = {}
        self.last_waveform_result = {}

        # ===== Layout utama =====
        main_layout = QVBoxLayout()

        # ===== Menubar (Save, Load, Reseet, Previous Page, Next Page) =====
        menu_bar = MenuBar(
            self,
            save_function=self.data_save.save_to_file,
            load_function=self.data_load.load_from_file,
            reset_all_function=self.reset_all_page,
            reset_current_function=self.reset_current_page,
            next_page=self.go_next,
            prev_page=self.go_prev
        )
        main_layout.setMenuBar(menu_bar)

        # ---------------------------------------------------------
        # FORM LAYOUT
        # ---------------------------------------------------------
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        form_layout.setColumnStretch(0, 0)
        form_layout.setColumnStretch(1, 0)
        form_layout.setColumnStretch(2, 1)
        form_layout.setColumnMinimumWidth(1, 10)

        # Lokasi pengukuran
        lokasi_label = QLabel("Lokasi Pengukuran")
        lokasi_colon = QLabel(":")
        self.combo_lokasi = PlaceholderComboBox(
            "Pilih Lokasi", ["Sisi LV Trafo", "Kabel Power", "Jalur Kabel", "Kubikel Incoming"]
        )
        lokasi_combo_layout = QHBoxLayout()
        lokasi_combo_layout.addWidget(self.combo_lokasi)
        lokasi_combo_widget = QWidget(); lokasi_combo_widget.setLayout(lokasi_combo_layout)
        form_layout.addWidget(lokasi_label, 0, 0, alignment=Qt.AlignLeft)
        form_layout.addWidget(lokasi_colon, 0, 1)
        form_layout.addWidget(lokasi_combo_widget, 0, 2)

        # Jenis sensor
        sensor_label = QLabel("Jenis Sensor")
        sensor_colon = QLabel(":")
        self.combo_sensor = PlaceholderComboBox("Pilih Sensor", ["TEV", "HFCT", "Ultrasonik"])
        sensor_combo_layout = QHBoxLayout()
        sensor_combo_layout.addWidget(self.combo_sensor)
        sensor_combo_widget = QWidget(); sensor_combo_widget.setLayout(sensor_combo_layout)
        form_layout.addWidget(sensor_label, 1, 0, alignment=Qt.AlignLeft)
        form_layout.addWidget(sensor_colon, 1, 1)
        form_layout.addWidget(sensor_combo_widget, 1, 2)

        # Ketika isi combobox berubah, widget hasil akan di clear
        self.combo_lokasi.currentIndexChanged.connect(self.clear_current_widgets)
        self.combo_sensor.currentIndexChanged.connect(self.clear_current_widgets)

        # Tambahkan ke layout utama
        main_layout.addLayout(form_layout)

        # ===== Bagian Waveform =====
        hbox_waveform = QHBoxLayout()
        self.line_waveform = PlaceholderLineEdit("Masukkan gambar bentuk gelombang", max_length=255)
        self.line_waveform.setReadOnly(True)
        self.line_waveform.setFocusPolicy(Qt.NoFocus)
        hbox_waveform.addWidget(self.line_waveform)

        btn_wave = QPushButton("Pilih")
        btn_wave.clicked.connect(self.load_waveform_image)
        hbox_waveform.addWidget(btn_wave)
        main_layout.addLayout(hbox_waveform)

        wf_result_layout = QHBoxLayout()
        self.wf_result = QTextEdit()
        self.wf_result.setPlaceholderText("Hasil ekstraksi & analisis waveform ditampilkan di sini...")
        self.wf_result.setMinimumWidth(1200)
        self.wf_result.setMinimumHeight(150)
        self.wf_result.setReadOnly(True)
        
        btn_wf_analyze = QPushButton("Ekstrak && Analisis")
        btn_wf_analyze.clicked.connect(self.process_waveform)
        wf_result_layout.addWidget(self.wf_result)
        wf_result_layout.addWidget(btn_wf_analyze)
        main_layout.addLayout(wf_result_layout)

        # Waveform canvas + toolbar
        self.canvas_waveform = MplCanvas(self, width=5, height=10, dpi=100)
        self.toolbar_waveform = NavigationToolbar(self.canvas_waveform, self)
        self.canvas_waveform.setMinimumWidth(1200)
        self.canvas_waveform.setMinimumHeight(600)
        main_layout.addWidget(self.toolbar_waveform)
        main_layout.addWidget(self.canvas_waveform)

        # ===== Bagian PRPD =====
        hbox_prpd = QHBoxLayout()
        self.line_prpd = PlaceholderLineEdit("Masukkan gambar PRPD", max_length=255)
        self.line_prpd.setReadOnly(True)
        self.line_prpd.setFocusPolicy(Qt.NoFocus)
        hbox_prpd.addWidget(self.line_prpd)

        btn_prpd = QPushButton("Pilih")
        btn_prpd.clicked.connect(self.load_prpd_image)
        hbox_prpd.addWidget(btn_prpd)
        main_layout.addLayout(hbox_prpd)

        prpd_result_layout = QHBoxLayout()
        self.prpd_result = QTextEdit()
        self.prpd_result.setPlaceholderText("Hasil ekstraksi & analisis PRPD ditampilkan di sini...")
        self.prpd_result.setMinimumWidth(1200)
        self.prpd_result.setMinimumHeight(150)
        self.prpd_result.setReadOnly(True)
        
        btn_prpd_analyze = QPushButton("Ekstrak && Analisis")
        btn_prpd_analyze.clicked.connect(self.process_prpd)
        prpd_result_layout.addWidget(self.prpd_result)
        prpd_result_layout.addWidget(btn_prpd_analyze)
        main_layout.addLayout(prpd_result_layout)

        self.canvas_prpd = MplCanvas(self, width=5, height=10, dpi=100)
        self.toolbar_prpd = NavigationToolbar(self.canvas_prpd, self)
        self.canvas_prpd.setMinimumWidth(1200)
        self.canvas_prpd.setMinimumHeight(600)
        main_layout.addWidget(self.toolbar_prpd)
        main_layout.addWidget(self.canvas_prpd)

        # Pasang layout utama yang scrollable
        container = QWidget()
        container.setLayout(main_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        outer_layout = QVBoxLayout()
        outer_layout.addWidget(scroll)
        self.setLayout(outer_layout)

        # ===== Path json =====
        if getattr(sys, 'frozen', False):
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.json_file = os.path.join(BASE_DIR, "plot_data.json")

    # ---------------------------------------------------------
    # MATPLOTLIB CLEANUP (mencegah crash saat window ditutup)
    # ---------------------------------------------------------
    def cleanup_canvas(self):
        """Forcefully disconnect, clear, and delete all Matplotlib canvases."""
        import matplotlib.pyplot as plt
        import gc

        for name in ["canvas_waveform", "canvas_prpd"]:
            canvas = getattr(self, name, None)
            if canvas:
                try:
                    # disconnect all mpl events safely
                    if hasattr(canvas, "mpl_disconnect"):
                        for cid in list(getattr(canvas, "_mpl_disconnect_ids", [])):
                            try:
                                canvas.mpl_disconnect(cid)
                            except Exception:
                                pass

                    # stop timers, animations, or draw_idle pending updates
                    if hasattr(canvas, "flush_events"):
                        try:
                            canvas.flush_events()
                        except Exception:
                            pass

                    # close and delete
                    canvas.figure.clear()
                    plt.close(canvas.figure)
                    canvas.deleteLater()
                    setattr(self, name, None)
                except Exception:
                    pass

        # aggressively collect garbage
        gc.collect()

    # ---------------------------------------------------------
    # NAVIGASI HALAMAN
    # ---------------------------------------------------------
    def closeEvent(self, event):
        """Override Qt close event untuk melepas Matplotlib objects secara aman."""
        self.cleanup_canvas()
        event.accept()

    def go_prev(self):
        """Pindah ke halaman depan laporan"""
        from Halaman_Depan_Laporan_PLN import HalamanDepanLaporanPLN
        self.data_save.save_to_file()
        QApplication.processEvents()
        self.cleanup_canvas()
        QApplication.processEvents()
        self.new_window = HalamanDepanLaporanPLN()
        self.new_window.show()
        self.close()


    def go_next(self):
        """Pindah ke halaman formulir laporan"""
        from Halaman_Formulir_Laporan_PLN import HalamanFormulirLaporanPLN
        self.data_save.save_to_file()
        QApplication.processEvents()
        self.cleanup_canvas()
        QApplication.processEvents()  
        self.new_window = HalamanFormulirLaporanPLN()
        self.new_window.show()
        self.close()

    # ---------------------------------------------------------
    # MEMUAT GAMBAR PLOT
    # ---------------------------------------------------------
    def load_waveform_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pilih gambar waveform", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.waveform_file = file
            self.line_waveform.setText(file)
    
    def load_prpd_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pilih gambar PRPD", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.prpd_file = file
            self.line_prpd.setText(file)

    # ---------------------------------------------------------
    # ANALISIS GAMBAR PLOT
    # ---------------------------------------------------------
    def process_waveform(self):
        valid, sensor_type = self.validate_inputs(self.waveform_file, is_prpd=False)
        if not valid:
            return

        sensor_type = self.combo_sensor.currentText()
        processor = ProsesorWaveform(self.waveform_file, sensor_type)
        result = processor.process_waveform()
        self.last_waveform_result = result # Simpan hasil supaya bisa diakses save_plot_result

        # Plot ke canvas
        df = pd.DataFrame(result["waveform_data_points"])
        self.canvas_waveform.axes.clear()
        if not df.empty:
            self.canvas_waveform.axes.plot(df["time_us"], df["amplitude_dB"], c="red", linewidth=1)
            self.canvas_waveform.axes.set_xlabel("Time (µs)")
            self.canvas_waveform.axes.set_ylabel("Amplitude (dB)")
            self.canvas_waveform.axes.set_title("Extracted Waveform Data")
            self.canvas_waveform.axes.grid(True)
        self.canvas_waveform.draw()

        # Update dan tampilkan hasil
        msg = "Fitur Waveform:\n"
        for k, v in result["features"].items():
            msg += f" - {k}: {v:.3f}\n" if isinstance(v, float) else f" - {k}: {v}\n"
        msg += "\n🔎 Indikasi PD: " + result["indikasi_pd"]
        self.wf_result.setText(msg)

    def process_prpd(self):
        valid, sensor_type = self.validate_inputs(self.prpd_file, is_prpd=True)
        if not valid:
            return

        sensor_type = self.combo_sensor.currentText()
        processor = ProsesorPRPD(self.prpd_file, sensor_type)
        result = processor.process_prpd()
        self.last_prpd_result = result # Simpan hasil supaya bisa diakses save_plot_result

        # Plot ke canvas
        df = pd.DataFrame(result["prpd_data_points"])
        self.canvas_prpd.axes.clear()
        if not df.empty:
            self.canvas_prpd.axes.scatter(df["phase_deg"], df["intensity_dB"], s=5, c="blue")
            self.canvas_prpd.axes.set_xlabel("Phase (deg)")
            self.canvas_prpd.axes.set_ylabel("Amplitude (dB)")
            self.canvas_prpd.axes.set_title("Grafik Data PRPD (Terfilter)")
            self.canvas_prpd.axes.grid(True)
        self.canvas_prpd.draw()

        # Update dan tampilkan hasil
        msg = "Fitur PRPD:\n"
        for k, v in result["features"].items():
            msg += f" - {k}: {v:.3f}\n" if isinstance(v, float) else f" - {k}: {v}\n"
        msg += "\n🔎 Indikasi PD: " + result["indikasi_pd"]
        self.prpd_result.setText(msg)

    def validate_inputs(self, file_path: str, is_prpd: bool = False) -> tuple[bool, str]:
        """
        Validasi input lokasi, sensor, dan file.
        Return (status, sensor_type).
        - status = False -> sudah tampilkan QMessageBox, langsung return
        - sensor_type -> string sensor yang dipilih kalau valid
        """
        lokasi = self.combo_lokasi.currentText()
        sensor_type = self.combo_sensor.currentText()

        if not lokasi and not sensor_type:
            QMessageBox.critical(self, "Peringatan", "Lengkapi lokasi dan sensor terlebih dahulu!")
            return False, ""
        elif not lokasi:
            QMessageBox.warning(self, "Peringatan", "Lokasi pengukuran belum dipilih!")
            return False, ""
        elif not sensor_type:
            QMessageBox.warning(self, "Peringatan", "Jenis sensor belum dipilih!")
            return False, ""

        if not file_path:
            if is_prpd:
                QMessageBox.critical(self, "Peringatan", "Silakan pilih gambar PRPD terlebih dahulu!")
            else:
                QMessageBox.critical(self, "Peringatan", "Silakan pilih gambar waveform terlebih dahulu!")
            return False, ""
        return True, sensor_type

    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    # ===== Fungsi Save =====
    def save_plot_result(self, all_data=None):
        """Simpan path + hasil ekstraksi PRPD dan waveform untuk lokasi+sensor."""
        lokasi = self.combo_lokasi.currentText()
        sensor = self.combo_sensor.currentText()
        key = f"{lokasi}|{sensor}"

        if not self.last_prpd_result and not self.last_waveform_result:
            return all_data if all_data else {}

        # kalau belum ada data lama, buat dict kosong
        if all_data is None:
            all_data = {}
        
        if key in all_data:
            print(f"Overwrite data untuk {key}")
        else:
            print(f"Tambah data baru untuk {key}")

        # update / tambahkan entry untuk key spesifik
        all_data[key] = {
            "waveform": {
                "path": self.waveform_file if self.waveform_file else "",
                "waveform_data_points": self.last_waveform_result.get("waveform_data_points", []),
                "features": self.last_waveform_result.get("features", {}),
                "indikasi_pd": self.last_waveform_result.get("indikasi_pd", "Tidak ada")
            },
            "prpd": {
                "path": self.prpd_file if self.prpd_file else "",
                "prpd_data_points": self.last_prpd_result.get("prpd_data_points", []),
                "features": self.last_prpd_result.get("features", {}),
                "indikasi_pd": self.last_prpd_result.get("indikasi_pd", "Tidak ada")
            }
        }

        return all_data

    # ===== Fungsi Load =====
    def load_plot_result(self, data):
        """Muat path + hasil ekstraksi PRPD & waveform untuk lokasi+sensor tertentu."""
        lokasi = self.combo_lokasi.currentText().strip()
        sensor = self.combo_sensor.currentText().strip()

        # Cek kalau lokasi/sensor belum dipilih
        if not lokasi or not sensor:
            QMessageBox.warning(self, "Peringatan", "Silakan lengkapi pilihan Lokasi dan Sensor sebelum melakukan Load.")
            return

        key = f"{lokasi}|{sensor}"

        # Cek kalau data kosong atau key tidak ada
        if not data or key not in data:
            QMessageBox.information(self, "Info", f"Tidak ada hasil tersimpan untuk kombinasi:\n\nLokasi: {lokasi}\nSensor: {sensor}")
            return

        # Kalau ada, muat data
        selected = data[key]
        self.prpd_result.setText("Data berhasil dimuat.")
        QMessageBox.information(self, "Sukses", f"Data berhasil dimuat untuk:\n\nLokasi: {lokasi}\nSensor: {sensor}")

        # --- Waveform ---
        if "waveform" in selected:
            waveform = selected["waveform"]
            self.waveform_file = waveform.get("path", "")
            self.line_waveform.setText(self.waveform_file)
            self.last_waveform_result = {
                "waveform_data_points": waveform.get("waveform_data_points", []),
                "features": waveform.get("features", {}),
                "indikasi_pd": waveform.get("indikasi_pd", "Tidak ada")
            }

            # tampilkan text hasil waveform
            msg_wf = "📈 Waveform Data:\n"
            for k, v in self.last_waveform_result["features"].items():
                msg_wf += f" - {k}: {v:.3f}\n" if isinstance(v, float) else f" - {k}: {v}\n"
            msg_wf += f"\n🔎 Indikasi PD: {self.last_waveform_result['indikasi_pd']}\n"
            self.wf_result.setText(msg_wf)

            # gambar ulang ke canvas
            df_wf = pd.DataFrame(self.last_waveform_result["waveform_data_points"])
            self.canvas_waveform.axes.clear()
            if not df_wf.empty:
                self.canvas_waveform.axes.plot(df_wf["time_us"], df_wf["amplitude_dB"], c="red", linewidth=1)
                self.canvas_waveform.axes.set_xlabel("Time (µs)")
                self.canvas_waveform.axes.set_ylabel("Amplitude (dB)")
                self.canvas_waveform.axes.set_title("Extracted Waveform Data")
                self.canvas_waveform.axes.grid(True)
            self.canvas_waveform.draw()

        # --- PRPD ---
        if "prpd" in selected:
            prpd = selected["prpd"]
            self.prpd_file = prpd.get("path", "")
            self.line_prpd.setText(self.prpd_file)
            self.last_prpd_result = {
                "prpd_data_points": prpd.get("prpd_data_points", []),
                "features": prpd.get("features", {}),
                "indikasi_pd": prpd.get("indikasi_pd", "Tidak ada")
            }

            # tampilkan text hasil PRPD
            msg_prpd = "📊 PRPD Data:\n"
            for k, v in self.last_prpd_result["features"].items():
                msg_prpd += f" - {k}: {v:.3f}\n" if isinstance(v, float) else f" - {k}: {v}\n"
            msg_prpd += f"\n🔎 Indikasi PD: {self.last_prpd_result['indikasi_pd']}\n"
            self.prpd_result.setText(msg_prpd)

            # gambar ulang ke canvas
            df_prpd = pd.DataFrame(self.last_prpd_result["prpd_data_points"])
            self.canvas_prpd.axes.clear()
            if not df_prpd.empty:
                self.canvas_prpd.axes.scatter(df_prpd["phase_deg"], df_prpd["intensity_dB"], s=5, c="blue")
                self.canvas_prpd.axes.set_xlabel("Phase (deg)")
                self.canvas_prpd.axes.set_ylabel("Amplitude (dB)")
                self.canvas_prpd.axes.set_title("Grafik Data PRPD (Terfilter)")
                self.canvas_prpd.axes.grid(True)
            self.canvas_prpd.draw()

    def reset_all_page(self):
        """Reset seluruh isi JSON (hapus semua data PRPD + waveform)."""
        self.data_reset.reset_file()
        self.prpd_result.clear()
        self.wf_result.clear()
        self.line_waveform.clear()
        self.line_prpd.clear()
        self.canvas_waveform.axes.clear()
        self.canvas_prpd.axes.clear()
        self.canvas_waveform.draw()
        self.canvas_prpd.draw()
        self.last_prpd_result = {}
        self.last_waveform_result = {}

    def reset_current_page(self):
        """Reset hanya data untuk lokasi+sensor saat ini."""
        lokasi = self.combo_lokasi.currentText()
        sensor = self.combo_sensor.currentText()
        key = f"{lokasi}|{sensor}"
        self.data_reset.reset_current(key, section="hasil_plot")

    def clear_current_widgets(self):
        """Hanya bersihkan tampilan halaman (widget & variabel), TIDAK menyentuh JSON."""
        self.prpd_result.clear()
        self.wf_result.clear()
        self.line_waveform.clear()
        self.line_prpd.clear()
        self.canvas_waveform.axes.clear()
        self.canvas_prpd.axes.clear()
        self.canvas_waveform.draw()
        self.canvas_prpd.draw()
        self.last_prpd_result = {}
        self.last_waveform_result = {}

# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------
if __name__ == "__main__":
    import atexit, matplotlib.pyplot as plt
    @atexit.register
    def cleanup_matplotlib():
        plt.close("all")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = HalamanEkstraksiPRPD()
    window.show()
    sys.exit(app.exec())

