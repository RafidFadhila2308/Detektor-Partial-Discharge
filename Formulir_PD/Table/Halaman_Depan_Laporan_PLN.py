import sys, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QMessageBox
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt
from MyWidget import PlaceholderLineEdit, PlaceholderComboBox, MenuBar
from DataManager import DataSave, DataLoad, DataResetReport

# =========================================================
# HALAMAN : COVER DEPAN LAPORAN
# =========================================================
class HalamanDepanLaporanPLN(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Judul & ukuran jendela
        self.setWindowTitle("Cover Laporan Pengujian Partial Discharge")
        self.setFixedSize(700, 750)

        # ===== Inisialisasi Pengatur Data dengan JSON =====
        self.data_save = DataSave("saved_data.json")
        self.data_load = DataLoad("saved_data.json")
        self.data_reset = DataResetReport("saved_data.json")

        # Registrasi fungsi pengatur data per section
        self.data_save.register_section_save("halaman_depan", self.save_data)
        self.data_load.register_section_load("halaman_depan", self.load_data)
        self.data_reset.register_section_reset("halaman_depan", self.reset_data)

        # ===== Widget utama =====
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        # ===== Menubar (Save, Load, Reseet, Previous Page, Next Page) =====
        self.menu_bar = MenuBar(
            self,
            save_function=self.data_save.save_to_file,
            load_function=self.data_load.load_from_file,
            reset_all_function=self.data_reset.reset_file,
            reset_current_function=lambda: self.data_reset.reset_current("halaman_depan"),
            next_page=self.go_next,
            prev_page=self.go_prev,
            first_page=True   # Karena ini halaman pertama
        )
        self.setMenuBar(self.menu_bar)

        # Daftar pilihan GI
        self.gardu_induk_list = [
            "GI Rangkasbitung Baru", "GI Kopo", "GI Saketi",
            "GI Malimping", "GI Menes Baru", "GIS Labuan", "GI Bayah"
        ]

        # Panggil fungsi untuk membangun UI
        self.init_ui()
        self.refresh_data()   # Auto-load saat membuka halaman
        
    # ---------------------------------------------------------
    # INISIALISASI USER INTERFACE
    # ---------------------------------------------------------
    def init_ui(self):
        # Font untuk judul, subjudul, underline
        title_font = QFont("Arial", 14, QFont.Bold)
        subtitle_font = QFont("Arial", 12, QFont.Bold)
        underline_font = QFont("Arial", 10)
        underline_font.setUnderline(True)

        # Judul utama
        self.main_layout.addWidget(QLabel("LAPORAN PENGUJIAN PARTIAL DISCHARGE", font=title_font, alignment=Qt.AlignCenter))
        self.main_layout.addWidget(QLabel("KABEL POWER DAN KUBIKEL INCOMING 20KV", font=subtitle_font, alignment=Qt.AlignCenter))
        self.main_layout.addWidget(QLabel("(ONLINE)", font=subtitle_font, alignment=Qt.AlignCenter))

        # Form utama
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        # Input gardu induk
        gi_label = QLabel("GARDU INDUK"); gi_label.setFont(underline_font)
        gi_colon = QLabel(":")
        self.gi_combo = PlaceholderComboBox("-- Pilih Gardu Induk --", self.gardu_induk_list, width=547)
        gi_combo_layout = QHBoxLayout(); gi_combo_layout.addWidget(self.gi_combo)
        gi_combo_widget = QWidget(); gi_combo_widget.setLayout(gi_combo_layout)
        form_layout.addWidget(gi_label, 0, 0, alignment=Qt.AlignLeft)
        form_layout.addWidget(gi_colon, 0, 1)
        form_layout.addWidget(gi_combo_widget, 0, 2)

        # Input tanggal (DD/MM/YYYY)
        tanggal_label = QLabel("TANGGAL"); tanggal_label.setFont(underline_font)
        tanggal_colon = QLabel(":")
        self.hari_entry = PlaceholderLineEdit("DD", 2)
        self.bulan_entry = PlaceholderLineEdit("MM", 2)
        self.tahun_entry = PlaceholderLineEdit("YYYY", 4)
        # Hubungkan auto-advance antar field
        self.hari_entry.next_widget = self.bulan_entry
        self.bulan_entry.next_widget = self.tahun_entry
        # Layout tanggal
        tanggal_input_layout = QHBoxLayout()
        tanggal_input_layout.addWidget(self.hari_entry); tanggal_input_layout.addWidget(QLabel("/"))
        tanggal_input_layout.addWidget(self.bulan_entry); tanggal_input_layout.addWidget(QLabel("/"))
        tanggal_input_layout.addWidget(self.tahun_entry)
        tanggal_widget = QWidget(); tanggal_widget.setLayout(tanggal_input_layout)
        form_layout.addWidget(tanggal_label, 1, 0, alignment=Qt.AlignLeft)
        form_layout.addWidget(tanggal_colon, 1, 1)
        form_layout.addWidget(tanggal_widget, 1, 2)

        # Input jam (HH:MM)
        jam_label = QLabel("JAM"); jam_label.setFont(underline_font)
        jam_colon = QLabel(":")
        self.jam_entry = PlaceholderLineEdit("HH", 2)
        self.menit_entry = PlaceholderLineEdit("MM", 2)
        self.jam_entry.setFixedWidth(263); self.menit_entry.setFixedWidth(263)
        self.jam_entry.next_widget = self.menit_entry
        # Layout jam
        jam_input_layout = QHBoxLayout()
        colon = QLabel(":"); colon.setFixedWidth(10); colon.setAlignment(Qt.AlignCenter)
        jam_input_layout.addWidget(self.jam_entry); jam_input_layout.addWidget(colon); jam_input_layout.addWidget(self.menit_entry)
        jam_input_layout.setSpacing(5)
        jam_widget = QWidget(); jam_widget.setLayout(jam_input_layout)
        form_layout.addWidget(jam_label, 2, 0, alignment=Qt.AlignLeft)
        form_layout.addWidget(jam_colon, 2, 1)
        form_layout.addWidget(jam_widget, 2, 2)

        self.main_layout.addLayout(form_layout)

        # Logo PLN
        BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(BASE_DIR, "Logo", "Logo_PLN.png")
        pixmap = QPixmap(logo_path).scaled(200, 300, Qt.KeepAspectRatio)
        logo = QLabel()
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(logo)

        # Footer (Info PLN)
        for text in [
            "PT. PLN (PERSERO)",
            "UNIT INDUK TRANSMISI JAWA BAGIAN BARAT",
            "UPT Cilegon",
            "ULTG Rangkasbitung"
        ]:
            footer = QLabel(text, font=QFont("Arial", 10))
            footer.setAlignment(Qt.AlignCenter)
            self.main_layout.addWidget(footer)

    # ---------------------------------------------------------
    # VALIDASI INPUT
    # ---------------------------------------------------------
    def validate(self):
        """Return True jika valid, else tampilkan warning."""
        if (
            self.gi_combo.currentIndex() < 0
            or not self.gi_combo.currentText()
            or self.hari_entry.text() in ("", "DD")
            or self.bulan_entry.text() in ("", "MM")
            or self.tahun_entry.text() in ("", "YYYY")
            or self.jam_entry.text() in ("", "HH")
            or self.menit_entry.text() in ("", "MM")
        ):
            QMessageBox.warning(self, "Peringatan", "Semua data harus diisi!")
            return False
        return True

    # ---------------------------------------------------------
    # NAVIGASI HALAMAN
    # ---------------------------------------------------------
    def go_prev(self):
        pass # Halaman pertama -> tidak ada aksi
    
    def go_next(self):
        """Pindah ke halaman konversi data gambar"""
        from Halaman_Konversi_Data_Gambar_Filtered import HalamanEkstraksiPRPD
        if not self.validate():
            return
        self.data_save.save_to_file()
        next_page = HalamanEkstraksiPRPD()
        next_page.show()
        QApplication.processEvents()
        self.close()

    # ---------------------------------------------------------
    # PENGATUR DATA (SAVE, LOAD, RESET)
    # ---------------------------------------------------------
    def save_data(self, old_data=None):
        return {
            "gardu_induk": self.gi_combo.currentText(),
            "hari": self.hari_entry.text(),
            "bulan": self.bulan_entry.text(),
            "tahun": self.tahun_entry.text(),
            "jam": self.jam_entry.text(),
            "menit": self.menit_entry.text(),
        }

    def load_data(self, data: dict):
        gi_value = data.get("gardu_induk", "")
        index = self.gi_combo.findText(gi_value)
        if index >= 0:
            self.gi_combo.setCurrentIndex(index)
        else:
            self.gi_combo.setCurrentIndex(-1)  # biarkan placeholder
        self.hari_entry.setText(data.get("hari", ""))
        self.bulan_entry.setText(data.get("bulan", ""))
        self.tahun_entry.setText(data.get("tahun", ""))
        self.jam_entry.setText(data.get("jam", ""))
        self.menit_entry.setText(data.get("menit", ""))

    def reset_data(self):
        self.gi_combo.setCurrentIndex(-1)
        self.hari_entry.clear(); self.bulan_entry.clear(); self.tahun_entry.clear()
        self.jam_entry.clear(); self.menit_entry.clear()

    def refresh_data(self):
        """Muat ulang JSON ketika navigasi balik ke halaman ini."""
        try:
            self.data_load.load_from_file()
            data = self.data_load.data.get("halaman_depan", {})
            if data:
                self.load_data(data)
                print("Data halaman depan dimuat ulang")
            else:
                print("Tidak ditemukan data halaman depan")
        except Exception as e:
            print("Tidak ada data tersimpan untuk dimuat:", e)

# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    cover = HalamanDepanLaporanPLN()
    cover.show()
    sys.exit(app.exec())