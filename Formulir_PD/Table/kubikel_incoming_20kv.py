import sys, os

# === Setup path agar bisa import modul dari folder utama proyek ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from PySide6.QtWidgets import ( 
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from MyWidget import RowEditors, TableUtility
from StandardValue import KlasifikasiPDTEV, KlasifikasiPDUltrasonik, KlasifikasiPDFinal, UpdateHasilKlasifikasi

# =========================================================
# TAB : KUBIKEL INCOMING 20 KV
# =========================================================
class KubikelIncoming20kV(QWidget):
    """
    Form untuk pengujian partial discharge (PD) pada Kubikel Incoming 20kV.
    Menyediakan:
    - Input data umum (merk, tipe, tahun buat, tahun operasi, frekuensi lock)
    - Tabel hasil pengukuran (tev, contact probe, flexible mic)
    - Tabel rekapitulasi
    """
    def __init__(self):
        super().__init__()
        self.busbar_combos = {}  # Menyimpan referensi combobox busbar untuk sinkronisasi
        self.init_ui()

    #  Fungsi bantu untuk sinkronisasi combobox cell busbar
    def sync_busbar(self, row_key, source_combo):
        """
        Sinkronkan semua combobox busbar.
        row_key: identitas unik busbar.
        """
        idx = source_combo.currentIndex()
        for combo in self.busbar_combos.get(row_key, []):
            if combo is not source_combo:
                combo.blockSignals(True)
                combo.setCurrentIndex(idx)
                combo.blockSignals(False)

    # ---------------------------------------------------------
    # INISIALISASI UI
    # ---------------------------------------------------------
    def init_ui(self):

        # ===== Layout utama =====
        layout = self.layout  # Pakai container layout
        layout = QVBoxLayout(self)
        # Judul form
        layout.addWidget(QLabel("<b>PENGUJIAN PARTIAL DISCHARGE KUBIKEL INCOMING 20KV</b>"))
        layout.addWidget(QLabel("<u>Data Kubikel Incoming 20kV</u>"))

        # Input data umum kubikel
        grid = QGridLayout()
        labels_left = ["Merk", "Type", "Tahun Buat", "Tahun Operasi"]
        self.extra_fields = {}

        for row, label in enumerate(labels_left):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(QLabel(":"), row, 1)

            edit = QLineEdit()
            edit.setFixedWidth(200)
            grid.addWidget(edit, row, 2)
            self.extra_fields[label] = edit

        grid.addWidget(QLabel("Frekuensi Lock"), 0, 4)
        grid.addWidget(QLabel(":"), 0, 5)
        self.freqlock = QComboBox()
        self.freqlock.addItems(["Belum", "Sudah"])
        self.freqlock.setCurrentIndex(-1)
        self.freqlock.setFixedWidth(200)
        grid.addWidget(self.freqlock, 0, 6)

        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(7, 1)
        layout.addLayout(grid)

        titik_default = ["Ruang CT", "Ruang VT", "Busbar", "PMT 20kV"]

        # ---------------------------------------------------------
        # WIDGET BANTU
        # ---------------------------------------------------------
        def make_interpretasi_tev_combo():
            # Combobox untuk interpretasi hasil TEV (a - g)
            combo = QComboBox()
            combo.addItems([chr(c) for c in range(ord("a"), ord("g") + 1)])
            combo.setCurrentIndex(-1)
            return combo

        # Combobox untuk interpretasi hasil ultrasonik (Noise / PD)
        def make_interpretasi_ultrasonik_combo():
            combo = QComboBox()
            combo.addItems(["Noise", "PD"])
            combo.setCurrentIndex(-1)
            return combo

        # Combobox untuk kondisi suara gemeresok (Ada / Tidak Ada)
        def make_suara_gemerosok_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo
        
        # Combobox untuk kondisi cluster dua gelombang (Ada / Tidak Ada)
        def make_cluster_dua_gelombang_combo():
            combo = QComboBox()
            combo.addItems(["Tidak Ada", "Ada"])
            combo.setCurrentIndex(-1)
            return combo
        
        # Widget gabungan label + combobox busbar (Atas / Bawah)
        def make_busbar_combo():
            container = QWidget()
            hbox = QHBoxLayout(container)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(5)
            label = QLabel("Busbar")
            combo = QComboBox()
            combo.addItems(["Atas", "Bawah"])
            combo.setCurrentIndex(-1)
            hbox.addWidget(label)
            hbox.addWidget(combo)
            return container

        self.make_interpretasi_tev_combo = make_interpretasi_tev_combo
        self.make_interpretasi_ultrasonik_combo = make_interpretasi_ultrasonik_combo
        self.make_suara_gemerosok_combo = make_suara_gemerosok_combo
        self.make_cluster_dua_gelombang_combo = make_cluster_dua_gelombang_combo
        self.make_busbar_combo = make_busbar_combo

        # ---------------------------------------------------------
        # UNIVERSAL ROW SETUP
        # ---------------------------------------------------------
        def setup_row(table, row, table_type, titik=None):
            """
            Membuat isi default untuk 1 baris pada tabel tertentu.
            table_type menentukan format input (TEV / Contact Probe / Flexible Mic).
            """
            if table_type in ["tev", "contact_probe"]:
                if titik and titik.startswith("Busbar"):
                    widget = self.make_busbar_combo()
                    table.setCellWidget(row, 0, widget)

                    combo = widget.findChild(QComboBox)
                    if combo:
                        self.busbar_combos.setdefault("busbar", []).append(combo)
                        combo.currentIndexChanged.connect(
                            lambda _, rr="busbar", c=combo: self.sync_busbar(rr, c)
                        )
                        if "Atas" in titik:
                            combo.setCurrentText("Atas")
                        elif "Bawah" in titik:
                            combo.setCurrentText("Bawah")
                else:
                    if titik:
                        item = QTableWidgetItem(titik)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        table.setItem(row, 0, item)

                # Khusus TEV → interpretasi
                if table_type == "tev":
                    table.setCellWidget(row, 3, self.make_interpretasi_tev_combo())
                # Khusus Contact Probe → interpretasi + suara + cluster
                elif table_type == "contact_probe":
                    table.setCellWidget(row, 3, self.make_interpretasi_ultrasonik_combo())
                    table.setCellWidget(row, 4, self.make_suara_gemerosok_combo())
                    table.setCellWidget(row, 5, self.make_cluster_dua_gelombang_combo())

            elif table_type == "flexible_mic":
                if not titik:
                    titik_item = QTableWidgetItem(str(row + 1))
                    if row == 0:
                        titik_item.setFlags(titik_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 0, titik_item)
                else:
                    item = QTableWidgetItem(titik)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 0, item)

                # ===== Inisialisasi Kolom Input =====
                # Kolom 1: Nilai (dBµV)
                nilai_item = QTableWidgetItem("")
                table.setItem(row, 1, nilai_item)

                # Kolom 2: Kepastian (%)
                table.setItem(row, 2, QTableWidgetItem(""))

                # Kolom 3–5: ComboBox untuk interpretasi & fitur tambahan
                table.setCellWidget(row, 3, self.make_interpretasi_ultrasonik_combo())  # Interpretasi
                table.setCellWidget(row, 4, self.make_suara_gemerosok_combo())          # Suara gemeresok 
                table.setCellWidget(row, 5, self.make_cluster_dua_gelombang_combo())    # Cluster dua gelombang

                # Kolom 6: Lokasi temuan
                table.setItem(row, 6, QTableWidgetItem(""))

                # Kolom 7: Tingkat keparahan (hasil klasifikasi)
                table.setItem(row, 7, QTableWidgetItem(""))

                # Kolom 8: Rekomendasi aksi (hasil klasifikasi)
                table.setItem(row, 8, QTableWidgetItem(""))
        
        # Simpan callback agar bisa dipanggil di fungsi load
        self.setup_row = setup_row
        
        # ---------------------------------------------------------
        # TABEL PENGUJIAN
        # ---------------------------------------------------------
        # ===== Tabel TEV =====
        self.table1 = QTableWidget(len(titik_default), 6)  
        self.table1.setHorizontalHeaderLabels([
            "Titik", "Nilai (dB)", "PPC", "Interpretasi", 
            "Tingkat Keparahan", "Rekomendasi Aksi"
        ])

        # Isi tabel awal
        for r, t in enumerate(titik_default):
            self.setup_row(self.table1, r, table_type="tev", titik=t)

        layout.addWidget(QLabel("<b>TEV</b>"))
        layout.addWidget(self.table1)

        # Fix tinggi agar 4 row pas
        TableUtility.update_table_height(self.table1)

        # Atur lebar kolom
        header1 = self.table1.horizontalHeader()
        header1.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header1.setSectionResizeMode(5, QHeaderView.Stretch)
        
        # Callback update klasifikasi TEV
        self.tev_updater = UpdateHasilKlasifikasi(
            table=self.table1,
            sensor_type="TEV",
            col_map={"nilai": 1, "ppc": 2, "interpretasi": 3},
            output_cols=(4, 5)
)

        # ===== Tabel Contact Probe =====
        self.table2 = QTableWidget(len(titik_default), 8)  # 8 kolom sesuai header
        self.table2.setHorizontalHeaderLabels([
            "Titik", "Nilai (dBμV)", "Kepastian (%)", "Interpretasi", "Suara Gemeresok",
            "Cluster Dua Gelombang", "Tingkat Keparahan", "Rekomendasi Aksi"
        ])

        # Isi baris default
        for r, t in enumerate(titik_default):
            self.setup_row(self.table2, r, table_type="contact_probe", titik=t)

        layout.addWidget(QLabel("<b>Contact Probe</b>"))
        layout.addWidget(self.table2)

        # Fix tinggi agar 4 row pas
        TableUtility.update_table_height(self.table2)
        
        # Atur lebar otomatis kolom tertentu
        header2 = self.table2.horizontalHeader()
        for col in [4, 5, 6]:
            header2.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        header2.setSectionResizeMode(7, QHeaderView.Stretch)

        # Callback update klasifikasi Contact Probe (Ultrasonik)
        self.contact_probe_updater = UpdateHasilKlasifikasi(
            table=self.table2,
            sensor_type="Ultrasonik",
            col_map={"nilai": 1, "kepastian": 2, "interpretasi": 3, "suara_gemerosok": 4, "cluster_dua_gelombang": 5},
            output_cols=(6, 7),
            extra_params={"sensor": "contact_probe"}
        )

        # ===== Tabel Rekap TEV + Contact Probe =====
        self.table_summary = QTableWidget(len(titik_default), 3)
        self.table_summary.setHorizontalHeaderLabels([
            "Titik", "Tingkat Keparahan Keseluruhan", "Rekomendasi Aksi Keseluruhan"
        ])

        # Isi kolom titik
        for r, t in enumerate(titik_default):
            if t == "Busbar":
                # busbar pakai widget khusus
                widget = self.make_busbar_combo()
                self.table_summary.setCellWidget(r, 0, widget)

                combo = widget.findChild(QComboBox)
                if combo:
                    combo.setEnabled(False)  # summary follow-only
                    self.busbar_combos.setdefault("busbar", []).append(combo)

            else:
                # Titik normal → text read-only
                item = QTableWidgetItem(t)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table_summary.setItem(r, 0, item)

            # Kolom keparahan + rekomendasi semula kosong
            self.table_summary.setItem(r, 1, QTableWidgetItem(""))
            self.table_summary.setItem(r, 2, QTableWidgetItem(""))

        # Fix tinggi agar 4 row pas
        TableUtility.update_table_height(self.table_summary)

        # Atur lebar otomatis
        header_summary = self.table_summary.horizontalHeader()
        header_summary.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_summary.setSectionResizeMode(2, QHeaderView.Stretch)

        # Tambah ke layout
        layout.addWidget(QLabel("<b>Rekap TEV + Contact Probe</b>"))
        layout.addWidget(self.table_summary)

        # Callback update klasifikasi kombinasi
        self.summary_updater = UpdateHasilKlasifikasi(self.table_summary)
        self.summary_updater.update_summary(
            row_map={
                "TEV": (self.table1, 4, 5),
                "Ultrasonik": (self.table2, 6, 7)
            },
            output_cols=(1, 2)
        )
        # Auto trigger summary kalau hasil TEV berubah
        self.table1.cellChanged.connect(
            lambda *_: self.summary_updater.update_summary(
                row_map={
                    "TEV": (self.table1, 4, 5),
                    "Ultrasonik": (self.table2, 6, 7)
                },
                output_cols=(1, 2)
            )
        )

        # Auto trigger summary kalau hasil Contact Probe berubah
        self.table2.cellChanged.connect(
            lambda *_: self.summary_updater.update_summary(
                row_map={
                    "TEV": (self.table1, 4, 5),
                    "Ultrasonik": (self.table2, 6, 7)
                },
                output_cols=(1, 2)
            )
        )

        # ===== Tabel Flexible Mic =====
        self.table3 = QTableWidget(0, 9)
        self.table3.setHorizontalHeaderLabels([
            "Titik", "Nilai (dBμV)", "Kepastian (%)", "Interpretasi", "Suara Gemeresok", 
            "Cluster Dua Gelombang", "Lokasi Temuan", "Tingkat Keparahan", "Rekomendasi Aksi"
        ])
        # Mulai dengan 1 row default
        self.table3.insertRow(0)
        self.setup_row(self.table3, 0, table_type="flexible_mic")

        layout.addWidget(QLabel("<b>Flexible Mic</b>"))
        layout.addWidget(self.table3)

        # Matikan scroll internal & auto fit tinggi tabel
        TableUtility.connect_auto_resize(self.table3)


        # Atur lebar otomatis
        header3 = self.table3.horizontalHeader()
        for col in [4, 5, 7]:
            header3.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        header3.setSectionResizeMode(8, QHeaderView.Stretch)

        # Tombol kontrol tambah/hapus row di bawah tabel
        layout.addWidget(RowEditors(
            [self.table3],
            row_setup_callback=lambda t, r: self.setup_row(t, r, "flexible_mic")
        ))

        # Callback update klasifikasi Flexible Mic
        self.flexible_mic_updater = UpdateHasilKlasifikasi(
            table=self.table3,
            sensor_type="Ultrasonik",
            col_map={"nilai": 1, "kepastian": 2, "interpretasi": 3, "suara_gemerosok": 4, "cluster_dua_gelombang": 5},
            output_cols=(7, 8),
            extra_params={"sensor": "flexible_mic"}
        )

    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    # ===== Fungsi Save =====
    def save_tab(self):
        return {
            "frekuensi_lock": self.freqlock.currentText(),
            "extra_fields": {label: edit.text() for label, edit in self.extra_fields.items()},
            "tables": {
                "tev": self.save_table_data(self.table1, "tev"),
                "contact_probe": self.save_table_data(self.table2, "contact_probe"),
                "flexible_mic": self.save_table_data(self.table3, "flexible_mic"),
            }
        }

    def save_table_data(self, table, table_type):
            data = []
            for row in range(table.rowCount()):
                row_data = {}

                if table.cellWidget(row, 0):
                    label = table.cellWidget(row, 0).layout().itemAt(0).widget().text()
                    combo = table.cellWidget(row, 0).layout().itemAt(1).widget()
                    row_data["titik"] = f"{label} {combo.currentText()}" if combo.currentText() else label
                elif table.item(row, 0):
                    row_data["titik"] = table.item(row, 0).text()

                if table_type == "tev":
                    row_data["nilai"] = table.item(row, 1).text() if table.item(row, 1) else ""
                    row_data["ppc"] = table.item(row, 2).text() if table.item(row, 2) else ""
                    combo = table.cellWidget(row, 3)
                    row_data["interpretasi"] = combo.currentText() if combo else ""
                    row_data["tingkat_keparahan"] = table.item(row, 4).text() if table.item(row, 4) else ""
                    row_data["rekomendasi"] = table.item(row, 5).text() if table.item(row, 5) else ""

                elif table_type == "contact_probe":
                    row_data["nilai"] = table.item(row, 1).text() if table.item(row, 1) else ""
                    row_data["kepastian"] = table.item(row, 2).text() if table.item(row, 2) else ""
                    combo1 = table.cellWidget(row, 3)
                    combo2 = table.cellWidget(row, 4)
                    combo3 = table.cellWidget(row, 5)
                    row_data["interpretasi"] = combo1.currentText() if combo1 else ""
                    row_data["suara_gemerosok"] = combo2.currentText() if combo2 else ""
                    row_data["cluster_dua_gelombang"] = combo3.currentText() if combo3 else ""
                    row_data["tingkat_keparahan"] = table.item(row, 6).text() if table.item(row, 6) else ""
                    row_data["rekomendasi"] = table.item(row, 7).text() if table.item(row, 7) else ""

                elif table_type == "flexible_mic":
                    row_data["nilai"] = table.item(row, 1).text() if table.item(row, 1) else ""
                    row_data["kepastian"] = table.item(row, 2).text() if table.item(row, 2) else ""
                    combo1 = table.cellWidget(row, 3)
                    combo2 = table.cellWidget(row, 4)
                    combo3 = table.cellWidget(row, 5)
                    row_data["interpretasi"] = combo1.currentText() if combo1 else ""
                    row_data["suara_gemerosok"] = combo2.currentText() if combo2 else ""
                    row_data["cluster_dua_gelombang"] = combo3.currentText() if combo3 else ""
                    row_data["lokasi_temuan"] = table.item(row, 6).text() if table.item(row, 6) else ""
                    row_data["tingkat_keparahan"] = table.item(row, 7).text() if table.item(row, 7) else ""
                    row_data["rekomendasi"] = table.item(row, 8).text() if table.item(row, 8) else ""

                data.append(row_data)
            return data

    # ===== Fungsi Load =====
    def load_tab(self, saved_data):
        self.freqlock.setCurrentText(saved_data.get("frekuensi_lock", ""))
        for label, edit in self.extra_fields.items(): edit.setText(saved_data.get("extra_fields", {}).get(label, ""))
        tables = saved_data.get("tables", {})
        self.load_table_data(self.table1, tables.get("tev", []), "tev")
        self.load_table_data(self.table2, tables.get("contact_probe", []), "contact_probe")   # <-- fix
        self.load_table_data(self.table3, tables.get("flexible_mic", []), "flexible_mic")  

    def load_table_data(self, table, table_data, table_type):
        table.setRowCount(0)

        for i, row_data in enumerate(table_data):
            table.insertRow(i)
            titik = row_data.get("titik", "")

            if table_type in ("tev", "contact_probe") and "Busbar" in titik:
                self.setup_row(table, i, table_type, "Busbar")
                combo = table.cellWidget(i, 0).findChild(QComboBox)
                if combo:
                    if "Atas" in titik: combo.setCurrentText("Atas")
                    elif "Bawah" in titik: combo.setCurrentText("Bawah")
            
            else:
                if not titik:
                    titik = f"Titik {i+1}" if table_type != "flexible_mic" else str(i+1)
                self.setup_row(table, i, table_type, titik)

            if table_type == "tev":
                if row_data.get("nilai"): table.setItem(i, 1, QTableWidgetItem(row_data["nilai"]))
                if row_data.get("ppc"): table.setItem(i, 2, QTableWidgetItem(row_data["ppc"]))
                if table.cellWidget(i, 3): table.cellWidget(i, 3).setCurrentText(row_data.get("interpretasi", ""))
                if row_data.get("tingkat_keparahan"):   table.setItem(i, 4, QTableWidgetItem(row_data["tingkat_keparahan"]))
                if row_data.get("rekomendasi"): table.setItem(i, 5, QTableWidgetItem(row_data["rekomendasi"]))
            
            elif table_type == "contact_probe":
                if row_data.get("nilai"):       table.setItem(i, 1, QTableWidgetItem(row_data["nilai"]))
                if row_data.get("kepastian"):   table.setItem(i, 2, QTableWidgetItem(row_data["kepastian"]))
                if table.cellWidget(i, 3):      table.cellWidget(i, 3).setCurrentText(row_data.get("interpretasi", ""))
                if table.cellWidget(i, 4):      table.cellWidget(i, 4).setCurrentText(row_data.get("suara_gemerosok", ""))
                if table.cellWidget(i, 5):      table.cellWidget(i, 5).setCurrentText(row_data.get("cluster_dua_gelombang", ""))
                if row_data.get("tingkat_keparahan"):   table.setItem(i, 6, QTableWidgetItem(row_data["tingkat_keparahan"]))
                if row_data.get("rekomendasi"): table.setItem(i, 7, QTableWidgetItem(row_data["rekomendasi"]))

                if titik and "Busbar" not in titik:
                    table.setItem(i, 0, QTableWidgetItem(titik))

            elif table_type == "flexible_mic":
                if row_data.get("nilai"):       table.setItem(i, 1, QTableWidgetItem(row_data["nilai"]))
                if row_data.get("kepastian"):   table.setItem(i, 2, QTableWidgetItem(row_data["kepastian"]))
                if table.cellWidget(i, 3):      table.cellWidget(i, 3).setCurrentText(row_data.get("interpretasi", ""))
                if table.cellWidget(i, 4):      table.cellWidget(i, 4).setCurrentText(row_data.get("suara_gemerosok", ""))
                if table.cellWidget(i, 5):      table.cellWidget(i, 5).setCurrentText(row_data.get("cluster_dua_gelombang", ""))
                if row_data.get("lokasi_temuan"):      table.setItem(i, 6, QTableWidgetItem(row_data["lokasi_temuan"]))
                if row_data.get("tingkat_keparahan"):   table.setItem(i, 7, QTableWidgetItem(row_data["tingkat_keparahan"]))
                if row_data.get("rekomendasi"): table.setItem(i, 8, QTableWidgetItem(row_data["rekomendasi"]))

                if titik:
                    table.setItem(i, 0, QTableWidgetItem(titik))

    # ===== Fungsi Reset =====
    def reset_tab(self):
        self.freqlock.setCurrentIndex(-1)
        for edit in self.extra_fields.values(): edit.clear()
        self.reset_table(self.table1, "tev")
        self.reset_table(self.table2, "contact_probe")    # <-- fix
        self.reset_table(self.table3, "flexible_mic")   # <-- fix


    def reset_table(self, table, table_type):
        table.setRowCount(0)
        table.insertRow(0)
        self.setup_row(table, 0, table_type)

        if table_type == "tev":
            for col in range(1, 6):  # clear nilai, ppc, interp, keparahan, rekomendasi
                if col in (1, 2, 4, 5) and table.item(0, col):
                    table.item(0, col).setText("")
                if col == 3 and table.cellWidget(0, col):
                    table.cellWidget(0, col).setCurrentIndex(-1)

        elif table_type == "contact_probe":
            for col in range(1, 8):
                if col in (1, 2, 6, 7) and table.item(0, col):
                    table.item(0, col).setText("")
                if col in (3, 4, 5) and table.cellWidget(0, col):
                    table.cellWidget(0, col).setCurrentIndex(-1)

        elif table_type == "flexible_mic":
            for col in range(1, 9):
                if col in (1, 2, 6, 7, 8) and table.item(0, col):
                    table.item(0, col).setText("")
                if col in (3, 4, 5) and table.cellWidget(0, col):
                    table.cellWidget(0, col).setCurrentIndex(-1)