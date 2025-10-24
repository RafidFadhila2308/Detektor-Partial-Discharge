import sys, os

# === Setup path agar bisa import modul dari folder utama proyek ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from MyWidget import RowEditors, TableUtility
from StandardValue import KlasifikasiPDUltrasonik, KlasifikasiPDFinal, UpdateHasilKlasifikasi

# =========================================================
# TAB : SISI LV TRAFO
# =========================================================
class SisiLVTrafo(QWidget):
    """
    Kelas QWidget untuk form pengujian Partial Discharge pada Sisi LV Trafo.
    Menyediakan:
    - Input frekuensi lock
    - Tabel hasil pengukuran (Ultradish, Flexible Mic, Contact Probe)
    - Tabel rekapitulasi
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tables = []    # Menyimpan referensi semua tabel sensor
        self.init_ui()

    # ---------------------------------------------------------
    # INISIALISASI UI
    # ---------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)

        # Judul halaman
        layout.addWidget(QLabel("<b>PENGUJIAN PARTIAL DISCHARGE SISI LV TRAFO</b>"))

        # Input Frekuensi Lock
        grid = QGridLayout()
        grid.addWidget(QLabel("Frekuensi Lock"), 0, 0)
        grid.addWidget(QLabel(":"), 0, 1)

        self.freqlock = QComboBox()
        self.freqlock.addItems(["Belum", "Sudah"])
        self.freqlock.setCurrentIndex(-1)   # default kosong
        self.freqlock.setFixedWidth(200)

        grid.addWidget(self.freqlock, 0, 2)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(7, 1)
        layout.addLayout(grid)

        # ---------------------------------------------------------
        # WIDGET BANTU
        # ---------------------------------------------------------
        # Combobox untuk interpretasi hasil (PD / Noise)
        def make_interpretasi_combo():
            combo = QComboBox()
            combo.addItems(["PD", "Noise"])
            combo.setCurrentIndex(-1)
            return combo

        # Combobox untuk pilihan suara gemerosok
        def make_suara_gemerosok_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo

        # Combobox untuk cluster dua gelombang
        def make_cluster_dua_gelombang_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo

        # Widget gabungan lokasi PD (Fasa + Core)
        def lokasi_muncul_pd_widget():
            """Widget untuk memilih lokasi PD berdasarkan fasa dan core."""
            container = QWidget()
            hbox = QHBoxLayout(container)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(5)

            hbox.addWidget(QLabel("Fasa"))
            combo_fasa = QComboBox()
            combo_fasa.addItems(["R", "S", "T"])
            combo_fasa.setCurrentIndex(-1)
            hbox.addWidget(combo_fasa)

            hbox.addWidget(QLabel("Core"))
            combo_core = QComboBox()
            combo_core.addItems(["1", "2", "3", "4"])
            combo_core.setCurrentIndex(-1)
            hbox.addWidget(combo_core)

            return container

        # ---------------------------------------------------------
        # UNIVERSAL ROW SETUP
        # ---------------------------------------------------------
        def setup_row(table, row):
            """
            Membuat isi default untuk 1 baris pada tabel tertentu.
            Kolom: Titik, Nilai, Kepastian, Interpretasi, Suara, Cluster, Lokasi, Keparahan, Rekomendasi
            """
            # Kolom 0: Titik (read-only)
            titik_item = QTableWidgetItem(str(row + 1))
            titik_item.setFlags(titik_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, titik_item)

            # Kolom 1: Nilai (dBµV)
            table.setItem(row, 1, QTableWidgetItem(""))
            
            # Kolom 2: Kepastian (%)
            table.setItem(row, 2, QTableWidgetItem(""))

            # Kolom 3-5: ComboBox untuk interpretasi & fitur tambahan
            table.setCellWidget(row, 3, make_interpretasi_combo()) 
            table.setCellWidget(row, 4, make_suara_gemerosok_combo())
            table.setCellWidget(row, 5, make_cluster_dua_gelombang_combo())
            
            # Kolom 6: Lokasi temuan
            table.setCellWidget(row, 6, lokasi_muncul_pd_widget())

            # Kolom 7: Tingkat keparahan (hasil klasifikasi)
            table.setItem(row, 7, QTableWidgetItem(""))

            # Kolom 8: Rekomendasi aksi (hasil klasifikasi)
            table.setItem(row, 8, QTableWidgetItem(""))

        # Simpan callback agar bisa dipanggil di fungsi load
        self.setup_row = setup_row

        # ---------------------------------------------------------
        # TABEL PENGUJIAN
        # ---------------------------------------------------------
        def make_table(title):
            """
            Membuat tabel pengujian baru dengan header standar PD.
            Menyediakan 9 kolom sesuai parameter pengukuran.
            """
            layout.addWidget(QLabel(f"<b>{title}</b>"))

            table = QTableWidget(0, 9)
            table.setHorizontalHeaderLabels([
                "Titik", "Nilai (dBμV)", "Kepastian (%)", "Interpretasi",
                "Suara Gemerosok", "Cluster Dua Gelombang",
                "Lokasi Muncul PD", "Tingkat Keparahan", "Rekomendasi Aksi"
            ])

            # Tambahkan 1 baris default
            table.insertRow(0)
            setup_row(table, 0)

            self.tables.append(table)
            layout.addWidget(table)

            # Atur lebar kolom agar rapi
            header = table.horizontalHeader()
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
            table.setColumnWidth(6, 200)
            
            TableUtility.connect_auto_resize(table)

            return table

        # Buat tabel tiap sensor
        self.table1 = make_table("Ultradish <br> Terminasi LV (Terbuka)")
        self.table2 = make_table("Flexible Mic <br> Box Bushing LV (Tertutup)")
        self.table3 = make_table("Contact Probe")

        # Tombol kontrol tambah/hapus row di bawah tabel
        layout.addWidget(RowEditors(self.tables, row_setup_callback=setup_row))

        # ---------------------------------------------------------
        # UPDATE KLASIFIKASI PER TABEL (INDIVIDUAL)
        # ---------------------------------------------------------
        sensors = [
            ("ultradish", self.table1),
            ("flexible_mic", self.table2),
            ("contact_probe", self.table3),
        ]

        self.updaters = {}
        for name, table in sensors:
            self.updaters[name] = UpdateHasilKlasifikasi(
                table=table,
                sensor_type="Ultrasonik",
                col_map={"nilai": 1, "kepastian": 2, "interpretasi": 3, "suara_gemerosok": 4, "cluster_dua_gelombang": 5},
                output_cols=(7, 8),
                extra_params={"sensor": name}
            )

        # ---------------------------------------------------------
        # TABEL REKAPITULASI KESELURUHAN
        # ---------------------------------------------------------
        self.table_summary = QTableWidget(0, 3)
        self.table_summary.setHorizontalHeaderLabels([
            "Titik", "Tingkat Keparahan Keseluruhan", "Rekomendasi Aksi Keseluruhan"
        ])
        header_summary = self.table_summary.horizontalHeader()
        header_summary.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_summary.setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(QLabel("<b>Rekapitulasi Keseluruhan</b>"))
        layout.addWidget(self.table_summary)

        TableUtility.connect_auto_resize(self.table_summary)

        # Updater summary pakai UpdateHasilKlasifikasi
        self.summary_updater = UpdateHasilKlasifikasi(
            table=self.table_summary,
            sensor_type=None,   # summary mode
        )

        # Mapping sensor → tabel + kolom hasil
        row_map = {
            "Ultradish":      (self.table1, 7, 8),
            "Flexible Mic":   (self.table2, 7, 8),
            "Contact Probe":  (self.table3, 7, 8),
        }

        # Hubungkan perubahan tabel sensor ke summary updater
        for table in [self.table1, self.table2, self.table3]:
            table.cellChanged.connect(
                lambda row, col, t=table: self.summary_updater.update_summary(row_map, (1, 2))
            )

    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    # ===== Fungsi Save =====
    def save_tab(self):
        """Simpan semua isi tab ke dictionary (untuk JSON)."""
        return {
            "frekuensi_lock": self.freqlock.currentText(),
            "tables": {
                "ultradish": self.save_table_data(self.table1),
                "flexible_mic": self.save_table_data(self.table2),
                "contact_probe": self.save_table_data(self.table3),
            }
        }

    def save_table_data(self, table):
        """Ambil isi tabel (per row) jadi list of dict."""
        data = []
        for row in range(table.rowCount()):
            row_data = {
                "titik": table.item(row, 0).text() if table.item(row, 0) else "",
                "nilai": table.item(row, 1).text() if table.item(row, 1) else "",
                "kepastian": table.item(row, 2).text() if table.item(row, 2) else "",
                "interpretasi": table.cellWidget(row, 3).currentText() if table.cellWidget(row, 3) else "",
                "suara_gemerosok": table.cellWidget(row, 4).currentText() if table.cellWidget(row, 4) else "",
                "cluster_dua_gelombang": table.cellWidget(row, 5).currentText() if table.cellWidget(row, 5) else "",
                "lokasi_fasa": table.cellWidget(row, 6).layout().itemAt(1).widget().currentText() if table.cellWidget(row, 6) else "",
                "lokasi_core": table.cellWidget(row, 6).layout().itemAt(3).widget().currentText() if table.cellWidget(row, 6) else "",
                "tingkat_keparahan": table.item(row, 7).text() if table.item(row, 7) else "",
                "rekomendasi": table.item(row, 8).text() if table.item(row, 8) else "",
            }
            data.append(row_data)
        return data
    
    # ===== Fungsi Load =====
    def load_tab(self, saved_data):
        """Load semua data tab dari dictionary."""
        self.freqlock.setCurrentText(saved_data.get("frekuensi_lock", ""))
        tables = saved_data.get("tables", {})
        self.load_table_data(self.table1, tables.get("ultradish", []))
        self.load_table_data(self.table2, tables.get("flexible_mic", []))
        self.load_table_data(self.table3, tables.get("contact_probe", []))

    def load_table_data(self, table, table_data):
        """Isi ulang tabel dari list of dict (data JSON)."""
        table.setRowCount(0)
        for i, row_data in enumerate(table_data):
            table.insertRow(i)
            self.setup_row(table, i)

            # Isi data sesuai mapping kolom
            if table.item(i, 0): table.item(i, 0).setText(row_data.get("titik", ""))
            if table.item(i, 1): table.item(i, 1).setText(row_data.get("nilai", ""))
            if table.item(i, 2): table.item(i, 2).setText(row_data.get("kepastian", ""))
            if table.cellWidget(i, 3): table.cellWidget(i, 3).setCurrentText(row_data.get("interpretasi", ""))
            if table.cellWidget(i, 4): table.cellWidget(i, 4).setCurrentText(row_data.get("suara_gemerosok", ""))
            if table.cellWidget(i, 5): table.cellWidget(i, 5).setCurrentText(row_data.get("cluster_dua_gelombang", ""))
            if table.cellWidget(i, 6):
                layout = table.cellWidget(i, 6).layout()
                layout.itemAt(1).widget().setCurrentText(row_data.get("lokasi_fasa", ""))
                layout.itemAt(3).widget().setCurrentText(row_data.get("lokasi_core", ""))
            if table.item(i, 7): table.setItem(i, 7, QTableWidgetItem(row_data.get("tingkat_keparahan", "")))
            if table.item(i, 8): table.setItem(i, 8, QTableWidgetItem(row_data.get("rekomendasi", "")))

    # ===== Fungsi Reset =====
    def reset_tab(self):
        """Reset isi tab ke kondisi kosong (UI tetap ada)."""
        self.freqlock.setCurrentIndex(-1)
        for table in [self.table1, self.table2, self.table3]:
            self.reset_table_data(table)

    def reset_table_data(self, table):
        """Kosongkan isi tabel tanpa menghapus strukturnya."""
        for row in range(table.rowCount()):
            # Kosongkan kolom teks
            for col in (0, 1, 2, 7, 8):
                item = table.item(row, col)
                if item:
                    item.setText("")

            # Reset combobox
            for col in (3, 4, 5):
                widget = table.cellWidget(row, col)
                if widget:
                    widget.setCurrentIndex(-1)

            # Reset lokasi PD (fasa+core)
            if table.cellWidget(row, 6):
                layout = table.cellWidget(row, 6).layout()
                layout.itemAt(1).widget().setCurrentIndex(-1)
                layout.itemAt(3).widget().setCurrentIndex(-1)
