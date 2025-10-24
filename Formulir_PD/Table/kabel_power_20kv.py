import sys, os

# === Setup path agar bisa import modul dari folder utama proyek ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from MyWidget import TableUtility
from StandardValue import KlasifikasiPDTEV, KlasifikasiPDHFCT, KlasifikasiPDFinal, UpdateHasilKlasifikasi

# =========================================================
# TAB : KABEL POWER 20 KV
# =========================================================
class KabelPower20kV(QWidget):
    """
    QWidget untuk form pengujian Partial Discharge pada Kabel Power 20kV.
    Menyediakan:
    - Input metadata kabel (merk, ukuran, tahun operasi, setting mode/filter/lock)
    - Tabel hasil pengukuran TEV & HFCT
    - Tabel rekapitulasi gabungan (summary)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edits = {}
        self.combos = {}
        self.init_ui()

    # ---------------------------------------------------------
    # INISIALISASI UI
    # ---------------------------------------------------------
    def init_ui(self):

        # ===== Layout utama =====
        layout = QVBoxLayout(self)
        
        # Judul form
        layout.addWidget(QLabel("<b>PENGUJIAN PARTIAL DISCHARGE KABEL POWER 20KV</b>"))

        # Input data umum kabel power 20kV
        layout.addWidget(QLabel("<u>Data Kabel Power 20kV</u>"))

        grid = QGridLayout()
        labels = ["Merk Kabel", "Ukuran", "Tahun Operasi"]

        for row, label in enumerate(labels):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(QLabel(":"), row, 1)

            edit = QLineEdit()
            edit.setFixedWidth(200)
            grid.addWidget(edit, row, 2)
            self.edits[label] = edit

            # Tambahan satuan untuk ukuran kabel
            if label == "Ukuran":
                mm2_label = QLabel("mm<sup>2</sup>")
                grid.addWidget(mm2_label, row, 3)

        # ComboBox setting alat (mode, filter, lock)
        labels_with_combo = [
            "Set Mode ke 'Kabel PD'",
            "Set Filter ke '500kHz High Pass'",
            "Frekuensi Lock"
        ]

        for row, label in enumerate(labels_with_combo):
            grid.addWidget(QLabel(label), row, 4)
            grid.addWidget(QLabel(":"), row, 5)

            combo = QComboBox()
            combo.addItems(["Belum", "Sudah"])
            combo.setCurrentIndex(-1)
            combo.setFixedWidth(200)
            grid.addWidget(combo, row, 6)
            self.combos[label] = combo

        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(7, 1)
        layout.addLayout(grid)

        # ---------------------------------------------------------
        # WIDGET BANTU
        # ---------------------------------------------------------
        # ComboBox untuk interpretasi TEV (kategori a–g).
        def make_interpretasi_combo():
            combo = QComboBox()
            combo.addItems([chr(c) for c in range(ord("a"), ord("g") + 1)])
            combo.setCurrentIndex(-1)
            return combo

        # ComboBox untuk status unipolar waveform (HFCT).
        def make_unipolar_waveform_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo

        # ComboBox untuk status cluster dua gelombang (HFCT).
        def make_cluster_dua_gelombang_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo

        # Membuat item tabel read-only (tidak bisa di-edit).
        def make_readonly_item(text):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            return item

        # ---------------------------------------------------------
        # TABEL PENGUJIAN
        # ---------------------------------------------------------
        # Setup fasa-core
        phases = ["R", "S", "T"]
        cores_per_phase = 4

        # ===== Tabel TEV =====
        self.table_tev = QTableWidget(len(phases) * cores_per_phase, 7)
        self.table_tev.setHorizontalHeaderLabels(["FASA", "CORE", "Nilai (dB)", "PPC", "Interpretasi", "Tingkat Keparahan", "Rekomendasi Aksi"])

        row_index = 0
        for phase in phases:
            self.table_tev.setSpan(row_index, 0, cores_per_phase, 1)
            self.table_tev.setItem(row_index, 0, make_readonly_item(phase))
            for core in range(cores_per_phase):
                self.table_tev.setItem(row_index + core, 1, make_readonly_item(str(core + 1)))
                self.table_tev.setCellWidget(row_index + core, 4, make_interpretasi_combo())
            row_index += cores_per_phase

        TableUtility.update_table_height(self.table_tev)
        self.table_tev.resizeColumnsToContents()
        header_tev = self.table_tev.horizontalHeader()
        header_tev.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Tingkat Keparahan
        header_tev.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Rekomendasi Aksi
        layout.addWidget(QLabel("<b>TEV</b>"))
        layout.addWidget(self.table_tev)
        
        # Callback update klasifikasi TEV
        self.tev_updater = UpdateHasilKlasifikasi(
            table=self.table_tev,
            sensor_type="TEV",
            col_map={"nilai": 2, "ppc": 3, "interpretasi": 4},
            output_cols=(5, 6)
        )

        # Hubungkan event
        self.table_tev.cellChanged.connect(self.tev_updater.update_individual)
        for r in range(self.table_tev.rowCount()):
            combo = self.table_tev.cellWidget(r, 4)  # interpretasi
            if combo:
                combo.currentIndexChanged.connect(lambda _, row=r: self.tev_updater.update_individual(row))
        
        # ===== Tabel HFCT =====
        self.table_hfct = QTableWidget(len(phases) * cores_per_phase, 8)
        self.table_hfct.setHorizontalHeaderLabels(["FASA", "CORE", "Nilai (pC)", "PPC", "Unipolar Waveform", "Cluster Dua Gelombang", "Tingkat Keparahan", "Rekomendasi Aksi"])

        row_index = 0
        for phase in phases:
            self.table_hfct.setSpan(row_index, 0, cores_per_phase, 1)
            self.table_hfct.setItem(row_index, 0, make_readonly_item(phase))
            for core in range(cores_per_phase):
                self.table_hfct.setItem(row_index + core, 1, make_readonly_item(str(core + 1)))
                self.table_hfct.setCellWidget(row_index + core, 4, make_unipolar_waveform_combo())
                self.table_hfct.setCellWidget(row_index + core, 5, make_cluster_dua_gelombang_combo())
            row_index += cores_per_phase

        TableUtility.update_table_height(self.table_hfct)
        self.table_hfct.resizeColumnsToContents()
        header_hfct = self.table_hfct.horizontalHeader()
        header_hfct.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Tingkat Keparahan
        header_hfct.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Rekomendasi Aksi
        layout.addWidget(QLabel("<b>HFCT</b>"))
        layout.addWidget(self.table_hfct)

        # Callback update klasifikasi HFCT
        self.hfct_updater = UpdateHasilKlasifikasi(
            table=self.table_hfct,
            sensor_type="HFCT",
            col_map={"nilai": 2, "ppc": 3, "unipolar_waveform": 4, "cluster_dua_gelombang": 5},
            output_cols=(6, 7)
        )

        # Hubungkan event
        self.table_hfct.cellChanged.connect(self.hfct_updater.update_individual)
        for r in range(self.table_hfct.rowCount()):
            for c in [4, 5]:
                combo = self.table_hfct.cellWidget(r, c)
                if combo:
                    combo.currentIndexChanged.connect(lambda _, row=r: self.hfct_updater.update_individual(row))


        # ===== Tabel Rekap =====
        self.table_summary = QTableWidget(len(phases) * cores_per_phase, 4)
        self.table_summary.setHorizontalHeaderLabels([
            "FASA", "CORE", "Tingkat Keparahan Keseluruhan", "Rekomendasi Aksi Keseluruhan"
        ])

        row_index = 0
        for phase in phases:
            self.table_summary.setSpan(row_index, 0, cores_per_phase, 1)
            self.table_summary.setItem(row_index, 0, make_readonly_item(phase))
            for core in range(cores_per_phase):
                self.table_summary.setItem(row_index + core, 1, make_readonly_item(str(core + 1)))
            row_index += cores_per_phase

        TableUtility.update_table_height(self.table_summary)
        self.table_summary.resizeColumnsToContents()
        layout.addWidget(QLabel("<b>Summary</b>"))
        layout.addWidget(self.table_summary)

        # Callback update klasifikasi kombinasi
        """
        Gabungkan hasil TEV dan HFCT untuk setiap titik.
        Diproses oleh KlasifikasiPDFinal → hasil keparahan + rekomendasi final.
        """
        self.summary_updater = UpdateHasilKlasifikasi(self.table_summary)
        self.summary_updater.update_summary(
            row_map={
                "TEV": (self.table_tev, 5, 6),
                "HFCT": (self.table_hfct, 6, 7)
            },
            output_cols=(2, 3)
        )
        
        # Trigger summary setiap kali TEV berubah
        self.table_tev.cellChanged.connect(
            lambda *_: self.summary_updater.update_summary(
                row_map={"TEV": (self.table_tev, 5, 6),
                        "HFCT": (self.table_hfct, 6, 7)},
                output_cols=(2, 3)
            )
        )

        # Trigger summary setiap kali HFCT berubah
        self.table_hfct.cellChanged.connect(
            lambda *_: self.summary_updater.update_summary(
                row_map={"TEV": (self.table_tev, 5, 6),
                        "HFCT": (self.table_hfct, 6, 7)},
                output_cols=(2, 3)
            )
        )
    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    # ===== Fungsi Save =====
    def save_tab(self):
        return {
            "data_kabel": {k: v.text() for k, v in self.edits.items()},
            "settings": {k: v.currentText() for k, v in self.combos.items()},
            "tables": {
                "tev": self.save_table_data(
                    self.table_tev,
                    ["nilai", "ppc", "interpretasi", "tingkat_keparahan", "rekomendasi"]
                ),
                "hfct": self.save_table_data(
                    self.table_hfct,
                    ["nilai", "ppc", "unipolar_waveform", "cluster_dua_gelombang", "tingkat_keparahan", "rekomendasi"]
                )
            }
        }

    def save_table_data(self, table, keys):
        data = []
        for row in range(table.rowCount()):
            row_data = {}
            # mapping kolom sesuai tabel
            col_map = {
                "nilai": 2,
                "ppc": 3,
                "interpretasi": 4,
                "unipolar_waveform": 4,
                "cluster_dua_gelombang": 5,
                "tingkat_keparahan": table.columnCount() - 2,
                "rekomendasi": table.columnCount() - 1
            }

            for key in keys:
                col_idx = col_map[key]
                widget = table.cellWidget(row, col_idx)
                if widget:
                    row_data[key] = widget.currentText()
                else:
                    item = table.item(row, col_idx)
                    row_data[key] = item.text() if item else ""
            data.append(row_data)
        return data

    # ===== Fungsi Load =====
    def load_tab(self, saved_data):
        for k, v in saved_data.get("data_kabel", {}).items():
            if k in self.edits:
                self.edits[k].setText(v)

        for k, v in saved_data.get("settings", {}).items():
            if k in self.combos:
                self.combos[k].setCurrentText(v)

        tables = saved_data.get("tables", {})
        self.load_table_data(
            self.table_tev,
            tables.get("tev", []),
            ["nilai", "ppc", "interpretasi", "tingkat_keparahan", "rekomendasi"]
        )
        self.load_table_data(
            self.table_hfct,
            tables.get("hfct", []),
            ["nilai", "ppc", "unipolar_waveform", "cluster_dua_gelombang", "tingkat_keparahan", "rekomendasi"]
        )
        
    def load_table_data(self, table, table_data, keys=None):
        col_map = {
            "nilai": 2,
            "ppc": 3,
            "interpretasi": 4,
            "unipolar_waveform": 4,
            "cluster_dua_gelombang": 5,
            "tingkat_keparahan": table.columnCount() - 2,
            "rekomendasi": table.columnCount() - 1
        }

        for row, row_data in enumerate(table_data):
            for key in keys:
                value = row_data.get(key, "")
                col_idx = col_map[key]
                widget = table.cellWidget(row, col_idx)
                if widget:
                    widget.setCurrentText(value)
                else:
                    item = table.item(row, col_idx)
                    if not item:
                        item = QTableWidgetItem()
                        table.setItem(row, col_idx, item)
                    item.setText(value)

    # ===== Fungsi Reset =====
    def reset_tab(self):
        """Reset semua input di tab ke kondisi default."""
        # Kosongkan line edit
        for k, v in self.edits.items():
            v.clear()

        # Reset combo box (pilih kosong)
        for k, v in self.combos.items():
            if v.count() > 0:
                v.setCurrentIndex(-1)
            else:
                v.setCurrentText("")

        # Reset tabel TEV
        self.reset_table_data(self.table_tev)
        # Reset tabel HFCT
        self.reset_table_data(self.table_hfct)

    def reset_table_data(self, table):
        """Reset semua isi tabel (cellWidget/combo/item) ke default kosong."""
        for row in range(table.rowCount()):
            for col_idx in range(2, table.columnCount()):
                widget = table.cellWidget(row, col_idx)
                if widget:
                    if widget.count() > 0:
                        widget.setCurrentIndex(-1)  # kembali ke kosong
                    else:
                        widget.setCurrentText("")
                else:
                    item = table.item(row, col_idx)
                    if item:
                        item.setText("")