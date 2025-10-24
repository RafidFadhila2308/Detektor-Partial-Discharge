import sys, json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, 
    QTabWidget, QScrollArea, QLabel, QLineEdit, QPushButton
)
from MyWidget import CheckableComboBox, MenuBar
from DataManager import DataSave, DataLoad, DataResetReport
from Table import IndikasiPD, JalurKabel20kV, KabelPower20kV, KubikelIncoming20kV, SisiLVTrafo

# =========================================================
# HALAMAN : FORMULIR LAPORAN
# =========================================================
class HalamanFormulirLaporanPLN(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Judul & ukuran jendela
        self.setWindowTitle("Formulir Laporan Pengujian Partial Discharge")
        self.setGeometry(100, 100, 1200, 700)

        # ===== Inisialisasi Pengatur Data dengan JSON =====
        self.data_save = DataSave("saved_data.json")
        self.data_load = DataLoad("saved_data.json")
        self.data_reset = DataResetReport("saved_data.json")

        # Registrasi fungsi pengatur data per section
        self.data_save.register_section_save("formulir_laporan", self.save_all_form)
        self.data_load.register_section_load("formulir_laporan", self.load_main_form)
        self.data_reset.register_section_reset("formulir_laporan", self.reset_main_form)

        # Deklarasi awal dictionary data tab formulir tiap trafo
        self.sisi_lv_widgets = {}
        self.kabel_power_widgets = {}
        self.jalur_kabel_widgets = {}
        self.kubikel_widgets = {}

        # Panggil fungsi untuk membangun UI
        self.init_ui()

    # ---------------------------------------------------------
    # INISIALISASI USER INTERFACE
    # ---------------------------------------------------------
    def init_ui(self):
        
        # ===== Layout utama =====
        main_layout = QVBoxLayout()

        # ===== Menubar (Save, Load, Reset, Previous Page, Next Page) =====
        menu_bar = MenuBar(
            self,
            save_function=self.data_save.save_to_file,
            load_function=self.load_all_form,
            reset_all_function=self.reset_all_form,
            reset_current_function=self.reset_current_trafo,
            prev_page=self.go_prev,
            next_page=self.go_next
        )
        main_layout.setMenuBar(menu_bar)

        # ===== Data Umum Kondisi Pengukuran =====
        top_frame = QGridLayout()

        # Input suhu
        top_frame.addWidget(QLabel("Suhu"), 0, 0)
        top_frame.addWidget(QLabel(":"), 0, 1)
        self.suhu_entry = QLineEdit()
        self.suhu_entry.setFixedWidth(80)
        top_frame.addWidget(self.suhu_entry, 0, 2)
        top_frame.addWidget(QLabel("\u00b0C"), 0, 3)

        # Input kelembaban
        top_frame.addWidget(QLabel("Kelembaban"), 1, 0)
        top_frame.addWidget(QLabel(":"), 1, 1)
        self.kelembaban_entry = QLineEdit()
        self.kelembaban_entry.setFixedWidth(80)
        top_frame.addWidget(self.kelembaban_entry, 1, 2)
        top_frame.addWidget(QLabel("%"), 1, 3)

        # Input jumlah trafo
        top_frame.addWidget(QLabel("Jumlah Trafo"), 0, 4)
        top_frame.addWidget(QLabel(":"), 0, 5)
        self.jumlah_trafo_entry = QLineEdit()
        self.jumlah_trafo_entry.setFixedWidth(80)
        top_frame.addWidget(self.jumlah_trafo_entry, 0, 6)
        # Update isi combobox jika jumlah trafo berubah
        self.jumlah_trafo_entry.textChanged.connect(self.update_trafo_list)

        # Input trafo yang ditinjau (multi-select)
        top_frame.addWidget(QLabel("Trafo yang ditinjau"), 1, 4)
        top_frame.addWidget(QLabel(":"), 1, 5)
        self.trafo_combobox = CheckableComboBox(placeholder_text="Pilih Trafo...")
        self.trafo_combobox.setFixedWidth(150)
        top_frame.addWidget(self.trafo_combobox, 1, 6)

        # Tombol untuk menghasilkan formulir (tab-tab trafo)
        buat_form_button = QPushButton("Buat Formulir")
        buat_form_button.clicked.connect(self.generate_tabs)
        top_frame.addWidget(buat_form_button, 2, 0)

        main_layout.addLayout(top_frame)

        # ===== Tab Formulir Halaman =====
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

        # Saat pertama kali buka → coba load data sebelumnya
        self.load_all_form()
    
    # ---------------------------------------------------------
    # LOGIKA FORMULIR
    # ---------------------------------------------------------
    def update_trafo_list(self):
        """Update daftar trafo di combobox sesuai jumlah trafo."""
        try:
            jumlah = int(self.jumlah_trafo_entry.text())
        except ValueError:
            self.trafo_combobox.ItemsList = []
            return
        self.trafo_combobox.ItemsList = [str(i) for i in range(1, jumlah + 1)]

    def generate_tabs(self):
        """Buat ulang tab sesuai trafo yang dipilih."""
        self.tabs.clear()
        self.jalur_kabel_widgets.clear()

        # Ambil jumlah trafo
        try:
            jumlah = int(self.jumlah_trafo_entry.text())
        except ValueError:
            return

        selected_numbers = self.trafo_combobox.SelectedItems
        if not selected_numbers:
            return

        # Format nama trafo
        selected_trafos = [f"TRF#{num}" for num in selected_numbers]

        # Tab Indikasi PD (umum untuk semua trafo)
        self.indikasi_pd_tab = IndikasiPD(selected_trafos)
        self.tabs.addTab(self.indikasi_pd_tab, "Indikasi PD")

        # Buat tab per trafo
        for num in selected_numbers:
            self.add_trafo_tab(num)

        # Jika ada data tersimpan → load kembali
        saved_indikasi = self.data_save.data.get("formulir_laporan", {}).get("indikasi_pd", [])
        if saved_indikasi:
            self.indikasi_pd_tab.load_tab(saved_indikasi)

        saved_lv = self.data_save.data.get("formulir_laporan", {}).get("sisi_lv_trafo", {})
        for num, widget in self.sisi_lv_widgets.items():
            if str(num) in saved_lv:
                widget.load_tab(saved_lv[str(num)])

        saved_kabel = self.data_save.data.get("formulir_laporan", {}).get("kabel_power", {})
        for num, widget in self.kabel_power_widgets.items():
            if str(num) in saved_kabel:
                widget.load_tab(saved_kabel[str(num)])

        saved_jalur = self.data_save.data.get("formulir_laporan", {}).get("jalur_kabel", {})
        for num, widget in self.jalur_kabel_widgets.items():
            if str(num) in saved_jalur:
                widget.load_tab(saved_jalur[str(num)])

        saved_kubikel = self.data_save.data.get("formulir_laporan", {}).get("kubikel_incoming", {})
        for num, widget in self.kubikel_widgets.items():
            if str(num) in saved_kubikel:
                widget.load_tab(saved_kubikel[str(num)])

    def add_scrollable_tab(self, tab_widget: QTabWidget, widget: QWidget, title: str):
        """Tambahkan widget ke dalam tab dengan scrollable support."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)       # Supaya isi ikut ukuran
        scroll.setWidget(widget)              # Masukkan widget ke scroll area
        tab_widget.addTab(scroll, title)

    def add_trafo_tab(self, trafo_number):
        """Tambahkan tab-tab detail untuk setiap trafo dengan scroll."""
        trafo_tab = QTabWidget()

        # Sisi LV Trafo
        sisi_lv_widget = SisiLVTrafo()
        self.sisi_lv_widgets[trafo_number] = sisi_lv_widget
        self.add_scrollable_tab(trafo_tab, sisi_lv_widget, "SISI LV TRAFO")

        # Kabel Power 20kV
        kabel_power_widget = KabelPower20kV()
        self.kabel_power_widgets[trafo_number] = kabel_power_widget
        self.add_scrollable_tab(trafo_tab, kabel_power_widget, "KABEL POWER 20kV")

        # Jalur Kabel 20kV
        jalur_kabel_widget = JalurKabel20kV()
        self.jalur_kabel_widgets[trafo_number] = jalur_kabel_widget
        self.add_scrollable_tab(trafo_tab, jalur_kabel_widget, "JALUR KABEL 20KV")

        # Kubikel Incoming 20kV
        kubikel_widget = KubikelIncoming20kV()
        self.kubikel_widgets[trafo_number] = kubikel_widget
        self.add_scrollable_tab(trafo_tab, kubikel_widget, "KUBIKEL INCOMING 20KV")

        # Tambahkan ke tab utama
        self.tabs.addTab(trafo_tab, f"TRAFO {trafo_number}")

    # ---------------------------------------------------------
    # NAVIGASI HALAMAN (Next/Prev)
    # ---------------------------------------------------------
    def go_prev(self):
        """Pindah ke halaman depan laporan"""
        from Halaman_Konversi_Data_Gambar_Filtered import HalamanEkstraksiPRPD
        self.data_save.save_to_file()  # Autosave
        self.new_window = HalamanEkstraksiPRPD()
        self.new_window.show()
        self.close()

    def go_next(self):
        """Pindah ke halaman konversi laporan"""
        from Halaman_Konversi_Laporan_PLN import HalamanKonversiLaporanPLN
        self.data_save.save_to_file()  # Autosave
        self.new_window = HalamanKonversiLaporanPLN()
        self.new_window.show()
        self.close()

    # ---------------------------------------------------------
    # PENGATUR DATA (SAVE, LOAD, RESET)
    # ---------------------------------------------------------
    def save_main_form(self, old_data=None):
        """Simpan input bagian atas (data umum)."""
        return {
            "suhu": self.suhu_entry.text(),
            "kelembaban": self.kelembaban_entry.text(),
            "jumlah_trafo": self.jumlah_trafo_entry.text(),
            "trafo_ditinjau": self.trafo_combobox.SelectedItems
        }
    
    def load_main_form(self, data=None):
        """Load data bagian atas (data umum)."""
        if not data:
            self.data_load.load_from_file()
            data = (
                self.data_load.data
                .get("formulir_laporan", {})
                .get("data_umum", {})
            )

        if data:
            self.suhu_entry.setText(data.get("suhu", ""))
            self.kelembaban_entry.setText(data.get("kelembaban", ""))
            self.jumlah_trafo_entry.setText(data.get("jumlah_trafo", ""))
            self.trafo_combobox.SelectedItems = data.get("trafo_ditinjau", [])
            if data.get("jumlah_trafo") and data.get("trafo_ditinjau"):
                self.generate_tabs()

    def reset_main_form(self):
        """Reset input bagian atas dan hapus semua tab."""
        self.suhu_entry.clear()
        self.kelembaban_entry.clear()
        self.jumlah_trafo_entry.clear()
        self.trafo_combobox.ItemsList = []
        self.tabs.clear()
    
    def save_all_form(self, old_data=None):
        if not self.suhu_entry.text() and not self.kelembaban_entry.text() and not self.jumlah_trafo_entry.text():
            return {}

        return {
            "data_umum": self.save_main_form(),
            "indikasi_pd": (
                self.indikasi_pd_tab.save_tab() 
                if hasattr(self, "indikasi_pd_tab") else {}
            ),
            "sisi_lv_trafo": {str(num): w.save_tab() for num, w in self.sisi_lv_widgets.items()},
            "kabel_power" : {str(num): w.save_tab() for num, w in self.kabel_power_widgets.items()},
            "jalur_kabel": {str(num): w.save_tab() for num, w in self.jalur_kabel_widgets.items()},
            "kubikel_incoming": {str(num): w.save_tab() for num, w in self.kubikel_widgets.items()}
        }

    def load_all_form(self, data=None):
        """Load semua bagian form dari JSON."""
        if not data:
            self.data_load.load_from_file()
            data = self.data_load.data.get("formulir_laporan", {})

        if not data:
            return

        # Load form utama (otomatis generate tab)
        self.load_main_form(data.get("data_umum", {}))
        # Setelah tab terbentuk → load kontennya
        self.load_tabbed_sections(data)

    def load_tabbed_sections(self, data):
        """Load isi tab (indikasi PD, sisi LV, kabel power, jalur kabel, kubikel incoming)."""
        if "indikasi_pd" in data and hasattr(self, "indikasi_pd_tab"):
            self.indikasi_pd_tab.load_tab(data["indikasi_pd"])

        if "sisi_lv_trafo" in data:
            for num, widget in self.sisi_lv_widgets.items():
                if str(num) in data["sisi_lv_trafo"]:
                    widget.load_tab(data["sisi_lv_trafo"][str(num)])

        if "kabel_power" in data:
            for num, widget in self.kabel_power_widgets.items():
                if str(num) in data["kabel_power"]:
                    widget.load_tab(data["kabel_power"][str(num)])

        if "jalur_kabel" in data:
            for num, widget in self.jalur_kabel_widgets.items():
                if str(num) in data["jalur_kabel"]:
                    widget.load_tab(data["jalur_kabel"][str(num)])

        if "kubikel_incoming" in data:
            for num, widget in self.kubikel_widgets.items():
                if str(num) in data["kubikel_incoming"]:
                    widget.load_tab(data["kubikel_incoming"][str(num)])

    def reset_all_form(self):
        """Reset seluruh form, tapi biarkan halaman depan tetap ada."""
        # Reset UI (hapus data widgets/tabs)
        self.reset_main_form()
        if hasattr(self, "indikasi_pd_tab"):
            self.indikasi_pd_tab.reset_tab()
        for widget in self.sisi_lv_widgets.values():
            widget.reset_tab()
        for widget in self.kabel_power_widgets.values():
            widget.reset_tab()
        for widget in self.jalur_kabel_widgets.values():
            widget.reset_tab()
        for widget in self.kubikel_widgets.values():
            widget.reset_tab()

        # Load JSON
        data = self.data_load.load_from_file() or {}

        # Hapus semua isi formulir laporan sepenuhnya di JSON
        if "formulir_laporan" in data:
            data["formulir_laporan"] = {}
        self.data_save.data = data
        self.data_save.save_to_file()

    def reset_current_trafo(self):
        """
        Reset hanya data TRAFO aktif:
        - Hapus/clear beban_trafo untuk TRF#n di indikasi_pd (JSON) dan reset widget.
        - Bersihkan hasil pengukuran untuk trafo n di sisi_lv_trafo, kabel_power, jalur_kabel, kubikel_incoming (JSON)
        - Reset UI untuk widget trafo terkait (panggil reset_tab pada widget trafo yang sesuai)
        - TIDAK menyentuh data_umum atau data trafo lain
        """
        from PySide6.QtWidgets import QMessageBox

        try:
            # Pastikan ada tab aktif dan format 'TRAFO n'
            idx = self.tabs.currentIndex()
            if idx == -1:
                return

            tab_name = self.tabs.tabText(idx)
            if not tab_name.startswith("TRAFO "):
                QMessageBox.information(self, "Info", "Fungsi ini hanya untuk tab TRAFO.")
                return

            trafo_num = tab_name.replace("TRAFO ", "").strip()
            trf_key = f"TRF#{trafo_num}"     

            # Muat seluruh JSON
            try:
                with open(self.data_save.json_file, "r", encoding="utf-8") as f:
                    full_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                full_data = {}

            formulir = full_data.get("formulir_laporan", {})
            indikasi = formulir.get("indikasi_pd", {})
            
            # Hapus entri beban trafo-n
            beban = indikasi.get("beban_trafo", {})
            if trf_key in beban:
                del beban[trf_key]
            indikasi["beban_trafo"] = beban

            # Temukan indeks di indikasi_pd UI mapping
            col_index = None
            if hasattr(self, "indikasi_pd_tab"):
                try:
                    col_index = self.indikasi_pd_tab.trafo_names.index(trf_key)
                except ValueError:
                    col_index = None

            # Modifikasi baris di JSON hanya pada indeks yang ditemukan
            rows = indikasi.get("rows", [])
            if col_index is not None:
                for row in rows:
                    trafo_list = row.get("trafo", [])
                    if col_index < len(trafo_list):
                        trafo_list[col_index] = {"yes": False, "lokasi": ""}
                        row["trafo"] = trafo_list
            indikasi_updated = indikasi
            formulir["indikasi_pd"] = indikasi_updated

            # Hapus trafo-n data di tab pengukuran
            for section_name in ["sisi_lv_trafo", "kabel_power", "jalur_kabel", "kubikel_incoming"]:
                if section_name in formulir and trafo_num in formulir[section_name]:
                    del formulir[section_name][trafo_num]

            # Simpan ulang modifikasi data ke JSON
            full_data["formulir_laporan"] = formulir
            with open(self.data_save.json_file, "w", encoding="utf-8") as f:
                json.dump(full_data, f, indent=4, ensure_ascii=False)

            # Reset tampilan UI trafo-n
            if col_index is not None and hasattr(self, "indikasi_pd_tab"):
                try:
                    self.indikasi_pd_tab.reset_trafo_column(col_index)
                except Exception:
                    pass

            # Reset widgets trafo-n
            for dname, d in [
                ("sisi_lv_trafo", self.sisi_lv_widgets),
                ("kabel_power", self.kabel_power_widgets),
                ("jalur_kabel", self.jalur_kabel_widgets),
                ("kubikel_incoming", self.kubikel_widgets)
            ]:
                widget = d.get(trafo_num)
                if widget and hasattr(widget, "reset_tab"):
                    try:
                        widget.reset_tab()
                    except Exception:
                        pass

            QMessageBox.information(self, "Sukses", f"Beban dan data pengukuran untuk TRAFO {trafo_num} berhasil di-reset.")

        except Exception as e:
            QMessageBox.critical(self, "Kesalahan", f"Gagal mereset: {e}")

# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HalamanFormulirLaporanPLN()
    window.show()
    sys.exit(app.exec())
