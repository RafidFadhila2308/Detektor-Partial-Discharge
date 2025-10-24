import sys, os

# === Setup path agar bisa import modul dari folder utama proyek ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from MyWidget import RowEditors
from StandardValue import KlasifikasiPDUltrasonik, UpdateHasilKlasifikasi


# =========================================================
# TAB : JALUR KABEL 20 KV
# =========================================================
class JalurKabel20kV(QWidget):
    """
    QWidget untuk form pengujian Partial Discharge pada Jalur Kabel 20kV.
    Menyediakan:
    - Input frekuensi lock
    - Tabel hasil pengukuran Flexible Mic
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    # ---------------------------------------------------------
    # INISIALISASI UI
    # ---------------------------------------------------------
    def init_ui(self):

        # ===== Layout utama =====
        layout = QVBoxLayout(self)

        # Judul form
        layout.addWidget(QLabel("<b>PENGUJIAN PARTIAL DISCHARGE JALUR KABEL 20kV</b>"))

        # Input frekuensi lock
        grid = QGridLayout()
        grid.addWidget(QLabel("Frekuensi Lock"), 0, 0)
        grid.addWidget(QLabel(":"), 0, 1)

        self.freqlock = QComboBox()
        self.freqlock.addItems(["Belum", "Sudah"])
        self.freqlock.setCurrentIndex(-1)
        self.freqlock.setFixedWidth(200)
        grid.addWidget(self.freqlock, 0, 2)

        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(7, 1)
        layout.addLayout(grid)

        # ---------------------------------------------------------
        # WIDGET BANTU
        # ---------------------------------------------------------
        def make_interpretasi_combo():
            combo = QComboBox()
            combo.addItems(["PD", "Noise"])
            combo.setCurrentIndex(-1)
            return combo

        def make_suara_gemerosok_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo

        def make_cluster_dua_gelombang_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo

        # ---------------------------------------------------------
        # SETUP ROW TABEL
        # ---------------------------------------------------------
        def setup_row(table, row_index):
            """Buat struktur row default untuk tabel Jalur Kabel."""
            # Kolom 0: nomor titik (read-only)
            titik_item = QTableWidgetItem(str(row_index + 1))
            titik_item.setFlags(titik_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_index, 0, titik_item)

            # Kolom input
            table.setItem(row_index, 1, QTableWidgetItem(""))                       # Nilai
            table.setItem(row_index, 2, QTableWidgetItem(""))                       # Kepastian
            table.setCellWidget(row_index, 3, make_interpretasi_combo())            # Interpretasi
            table.setCellWidget(row_index, 4, make_suara_gemerosok_combo())         # Suara
            table.setCellWidget(row_index, 5, make_cluster_dua_gelombang_combo())   # Cluster
            table.setItem(row_index, 6, QTableWidgetItem(""))                       # Lokasi temuan
            table.setItem(row_index, 7, QTableWidgetItem(""))                       # Keparahan
            table.setItem(row_index, 8, QTableWidgetItem(""))                       # Rekomendasi

        # Simpan callback agar bisa dipanggil di fungsi load
        self.setup_row = setup_row

        # -----------------------------------------------------
        # TABEL PENGUJIAN
        # -----------------------------------------------------
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Titik", "Nilai (dBμV)", "Kepastian (%)", "Interpretasi",
            "Suara Gemeresok", "Cluster Dua Gelombang", "Lokasi Temuan",
            "Tingkat Keparahan", "Rekomendasi Aksi"
        ])

        # Insert row pertama
        self.table.insertRow(0)
        self.setup_row(self.table, 0)

        # Atur lebar kolom untuk hasil klasifikasi
        header = self.table.horizontalHeader()
        for c in [4, 5, 6, 7, 8]:
            header.setSectionResizeMode(c, QHeaderView.ResizeToContents)

        layout.addWidget(QLabel("<b>Flexible Mic</b>"))
        layout.addWidget(self.table)

        # Kontrol tambah/hapus row
        layout.addWidget(RowEditors([self.table], row_setup_callback=self.setup_row))

        # ---------------------------------------------------------
        # UPDATE KLASIFIKASI
        # ---------------------------------------------------------
        """
        Proses klasifikasi otomatis ketika user mengisi/ubah data.
        Ambil input (nilai, kepastian, interpretasi, suara_gemerosok, cluster_dua_gelombang),
        lalu jalankan KlasifikasiPDUltrasonik → isi kolom keparahan & rekomendasi.
        """
        self.updater = UpdateHasilKlasifikasi(
            table=self.table,
            sensor_type="Ultrasonik",
            col_map={
                "nilai": 1,
                "kepastian": 2,
                "interpretasi": 3,
                "suara_gemerosok": 4,
                "cluster_dua_gelombang": 5
            },
            output_cols=(7, 8),
            extra_params={"sensor": "Flexible Mic"}
        )

    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    # ===== Fungsi Save =====
    def save_tab(self):
        """Simpan semua isi form ke dictionary (untuk JSON)."""
        return {
            "frekuensi_lock": self.freqlock.currentText(),
            "table": {
                "flexible_mic": self.save_table_data(self.table)
            }
        }
    
    def save_table_data(self, table):
        """Ambil isi tabel per row ke dalam list of dict."""
        data = []
        for row in range(table.rowCount()):
            row_data = {
                "titik": table.item(row, 0).text() if table.item(row, 0) else "",
                "nilai": table.item(row, 1).text() if table.item(row, 1) else "",
                "kepastian": table.item(row, 2).text() if table.item(row, 2) else "",
                "interpretasi": table.cellWidget(row, 3).currentText() if table.cellWidget(row, 3) else "",
                "suara_gemerosok": table.cellWidget(row, 4).currentText() if table.cellWidget(row, 4) else "",
                "cluster_dua_gelombang": table.cellWidget(row, 5).currentText() if table.cellWidget(row, 5) else "",
                "lokasi_temuan": table.item(row, 6).text() if table.item(row, 6) else "",
                "tingkat_keparahan": table.item(row, 7).text() if table.item(row, 7) else "",
                "rekomendasi": table.item(row, 8).text() if table.item(row, 8) else "",
            }
            data.append(row_data)
        return data

    # ===== Fungsi Load =====
    def load_tab(self, saved_data):
        """Load isi form dari dictionary hasil save_tab()."""
        self.freqlock.setCurrentText(saved_data.get("frekuensi_lock", ""))
        table_data = saved_data.get("table", {}).get("flexible_mic", [])
        self.load_table_data(self.table, table_data)

    def load_table_data(self, table, table_data):
        """Isi ulang tabel dari list of dict."""
        table.setRowCount(0)
        for i, row_data in enumerate(table_data):
            table.insertRow(i)
            self.setup_row(table, i)

            # Mapping isi ke setiap kolom
            if table.item(i, 0): table.item(i, 0).setText(row_data.get("titik", ""))
            if table.item(i, 1): table.item(i, 1).setText(row_data.get("nilai", ""))
            if table.item(i, 2): table.item(i, 2).setText(row_data.get("kepastian", ""))
            if table.cellWidget(i, 3): table.cellWidget(i, 3).setCurrentText(row_data.get("interpretasi", ""))
            if table.cellWidget(i, 4): table.cellWidget(i, 4).setCurrentText(row_data.get("suara_gemerosok", ""))
            if table.cellWidget(i, 5): table.cellWidget(i, 5).setCurrentText(row_data.get("cluster_dua_gelombang", ""))
            if table.item(i, 6): table.item(i, 6).setText(row_data.get("lokasi_temuan", ""))
            table.setItem(i, 7, QTableWidgetItem(row_data.get("tingkat_keparahan", "")))
            table.setItem(i, 8, QTableWidgetItem(row_data.get("rekomendasi", "")))

    # ===== Fungsi Reset =====
    def reset_tab(self):
        """Reset semua input ke kondisi kosong (UI tetap ada)."""
        self.freqlock.setCurrentIndex(-1)
        self.reset_table_data(self.table)

    def reset_table_data(self, table):
        """Kosongkan isi tabel tanpa hapus struktur row/col."""
        for row in range(table.rowCount()):
            # Kosongkan teks di kolom 0–2, 6–8
            for col in (0, 1, 2, 6, 7, 8):
                item = table.item(row, col)
                if item:
                    item.setText("")

            # Reset combobox (interpretasi, suara, cluster)
            for col in (3, 4, 5):
                widget = table.cellWidget(row, col)
                if widget:
                    widget.setCurrentIndex(-1)
