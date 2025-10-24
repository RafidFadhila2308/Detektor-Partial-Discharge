from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QFrame, QHBoxLayout,
    QGridLayout, QLabel, QRadioButton, QButtonGroup, QLineEdit, QHeaderView
)
from PySide6.QtCore import Qt

# =========================================================
# TAB : INDIKASI PD KESELURUHAN
# =========================================================
class IndikasiPD(QWidget):
    """
    QWidget untuk tab Indikasi PD.
    Menyediakan:
    - Input beban trafo (Ampere) untuk tiap trafo
    - Tabel titik pengujian dengan pilihan hasil (✔/✖) per sensor
    - Kolom lokasi temuan (aktif hanya jika ✔ dipilih)
    """

    def __init__(self, trafo_names):
        super().__init__()
        self.trafo_names = trafo_names
        self.table = self._create_table(trafo_names)
        self.init_ui()

    # ---------------------------------------------------------
    # INISIALISASI UI
    # ---------------------------------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)

        # Judul input beban
        layout.addWidget(QLabel("<u>Beban Trafo</u>"))

        # Grid input beban per trafo
        grid = QGridLayout()
        self.trafo_load_edits = {}

        for row, trafo in enumerate(self.trafo_names, start=1):
            # Label trafo
            grid.addWidget(QLabel(f"TRF#{row}"), row-1, 0)
            grid.addWidget(QLabel(":"), row-1, 1)

            # Input angka beban
            edit = QLineEdit()
            edit.setFixedWidth(100)
            grid.addWidget(edit, row-1, 2)

            # Label satuan
            grid.addWidget(QLabel("A"), row-1, 3)

            # Simpan ke dict
            self.trafo_load_edits[f"TRF#{row}"] = edit

        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)


        # ===== Tabel utama =====
        layout.addWidget(self.table)
        self.setLayout(layout)

    # ---------------------------------------------------------
    # SETUP TABEL UTAMA
    # ---------------------------------------------------------
    def _create_table(self, trafo_names):
        data = [
            ("Sisi LV Trafo", ["Ultradish", "Contact Probe*", "Flexible Mic*"]),
            ("Kabel Power 20kV", ["HFCT", "TEV"]),
            ("Jalur Kabel 20kV", ["Flexible Mic"]),
            ("Kubikel Incoming 20kV", ["TEV", "Flexible Mic", "Contact Probe"]),
        ]

        total_rows = sum(len(sensors) for _, sensors in data)
        col_headers = ["Titik Pengujian", "Tipe Sensor"] + trafo_names

        table = QTableWidget(total_rows, len(col_headers))
        table.setHorizontalHeaderLabels(col_headers)

        row_index = 0
        for section, sensors in data:
            for sensor in sensors:
                # Kolom titik (read-only)
                titik_item = QTableWidgetItem(section)
                titik_item.setFlags(titik_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, 0, titik_item)

                # Kolom sensor (read-only)
                sensor_item = QTableWidgetItem(sensor)
                sensor_item.setFlags(sensor_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_index, 1, sensor_item)

                # Kolom trafo (✔/✖ + lokasi)
                for col in range(len(trafo_names)):
                    frame = QFrame()
                    frame_layout = QHBoxLayout(frame)
                    frame_layout.setContentsMargins(0, 0, 0, 0)
                    frame_layout.setSpacing(5)

                    group = QButtonGroup(frame)

                    # Tombol ✔ dan ✖
                    btn_yes = QRadioButton("✔")
                    btn_no = QRadioButton("✖")
                    btn_no.setChecked(True)
                    group.addButton(btn_yes)
                    group.addButton(btn_no)

                    # Input lokasi (aktif jika ✔)
                    lokasi_edit = QLineEdit()
                    lokasi_edit.setPlaceholderText("Lokasi Temuan")
                    lokasi_edit.setReadOnly(True)
                    lokasi_edit.setFixedWidth(120)

                    def toggle_edit(checked, edit=lokasi_edit):
                        edit.setReadOnly(not checked)
                        if not checked:
                            edit.clear()
                    btn_yes.toggled.connect(toggle_edit)

                    # Susun layout cell
                    frame_layout.addWidget(btn_yes)
                    frame_layout.addWidget(btn_no)
                    frame_layout.addWidget(lokasi_edit)
                    frame_layout.addStretch(1)
                    frame.setMaximumWidth(220)

                    table.setCellWidget(row_index, col + 2, frame)

                row_index += 1

        # Merge kategori titik
        current_text = None
        start_row = 0
        span_count = 0
        for row in range(table.rowCount()):
            text = table.item(row, 0).text()
            if text == current_text:
                span_count += 1
            else:
                if span_count > 1:
                    table.setSpan(start_row, 0, span_count, 1)
                current_text = text
                start_row = row
                span_count = 1
        if span_count > 1:
            table.setSpan(start_row, 0, span_count, 1)

        # -----------------------------------------------------
        # PENGATURAN KOLOM
        # -----------------------------------------------------
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Fixed)

        table.setColumnWidth(0, 150)   # Titik
        table.setColumnWidth(1, 120)   # Sensor
        for col in range(len(trafo_names)):
            table.setColumnWidth(col + 2, 220)

        table.verticalHeader().setVisible(False)
        return table

    # ---------------------------------------------------------
    # PENGATUR DATA
    # ---------------------------------------------------------
    # ===== Fungsi Save =====
    def save_tab(self):
        """
        Simpan isi tabel + input beban ke dict.
        Struktur:
        {
            "rows": [ { titik, sensor, trafo:[{yes, lokasi}, ...] }, ... ],
            "beban_trafo": { "TRF#1": "...", ... }
        }
        """
        result = []
        for row in range(self.table.rowCount()):
            row_data = {
                "titik": self.table.item(row, 0).text(),
                "sensor": self.table.item(row, 1).text(),
                "trafo": []
            }
            for col in range(len(self.trafo_names)):
                cell_widget = self.table.cellWidget(row, col + 2)
                yes_button = cell_widget.layout().itemAt(0).widget()
                lokasi_edit = cell_widget.layout().itemAt(2).widget()
                row_data["trafo"].append({
                    "yes": yes_button.isChecked(),
                    "lokasi": lokasi_edit.text()
                })
            result.append(row_data)

        beban_data = {trafo: edit.text() for trafo, edit in self.trafo_load_edits.items()}
        return {"rows": result, "beban_trafo": beban_data}

    # ===== Fungsi Load =====
    def load_tab(self, saved_data):
        """
        Isi ulang tabel dari dict hasil save_tab.
        - Centang ✔/✖ sesuai data
        - Isi lokasi temuan
        - Muat input beban trafo
        """
        saved_rows = saved_data.get("rows", [])
        for row, row_data in enumerate(saved_rows):
            for col, trafo_info in enumerate(row_data.get("trafo", [])):
                cell_widget = self.table.cellWidget(row, col + 2)
                yes_button = cell_widget.layout().itemAt(0).widget()
                no_button = cell_widget.layout().itemAt(1).widget()
                lokasi_edit = cell_widget.layout().itemAt(2).widget()

                if trafo_info["yes"]:
                    yes_button.setChecked(True)
                else:
                    no_button.setChecked(True)
                lokasi_edit.setText(trafo_info.get("lokasi", ""))

        beban_data = saved_data.get("beban_trafo", {})
        for trafo, edit in self.trafo_load_edits.items():
            edit.setText(beban_data.get(trafo, ""))

    # ===== Fungsi Reset =====
    def reset_tab(self):
        """
        Reset tabel & input beban:
        - Semua jadi ✖
        - Lokasi temuan kosong + disabled
        - Input beban kosong
        """
        for row in range(self.table.rowCount()):
            for col in range(len(self.trafo_names)):
                cell_widget = self.table.cellWidget(row, col + 2)
                no_button = cell_widget.layout().itemAt(1).widget()
                lokasi_edit = cell_widget.layout().itemAt(2).widget()

                no_button.setChecked(True)
                lokasi_edit.clear()
                lokasi_edit.setReadOnly(True)

        for edit in self.trafo_load_edits.values():
            edit.clear()

    def reset_trafo_column(self, trafo_index):
        """
        Setel ulang hanya satu kolom trafo di UI IndikasiPD:
        - Atur semua radio ke ✖, hapus lokasi, nonaktifkan input lokasi
        - Hapus kolom beban untuk trafo tersebut
        """
        # Kondisi tidak ada data
        if trafo_index is None:
            return

        # Reset kolom tabel
        for row in range(self.table.rowCount()):
            cell_widget = self.table.cellWidget(row, trafo_index + 2)
            if not cell_widget:
                continue
            try:
                yes_button = cell_widget.layout().itemAt(0).widget()
                no_button  = cell_widget.layout().itemAt(1).widget()
                lokasi_edit = cell_widget.layout().itemAt(2).widget()
            except Exception:
                continue

            #  Atur ke ✖ dan menghapus lokasi
            if no_button:
                no_button.setChecked(True)
            if lokasi_edit:
                lokasi_edit.clear()
                lokasi_edit.setReadOnly(True)

        # Reset beban trafo
        try:
            trf_key = self.trafo_names[trafo_index]  # "TRF#1"
            if trf_key in self.trafo_load_edits:
                self.trafo_load_edits[trf_key].clear()
        except Exception:
            pass
