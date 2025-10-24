from PySide6.QtWidgets import QMessageBox, QTableWidgetItem, QComboBox

# Import fungsi klasifikasi tiap sensor
from StandardValue import KlasifikasiPDTEV, KlasifikasiPDHFCT, KlasifikasiPDUltrasonik

# =========================================================
# MODUL : UPDATE HASIL KLASIFIKASI
# =========================================================
class UpdateHasilKlasifikasi:
    def __init__(self, table, sensor_type=None, col_map=None, output_cols=None, extra_params=None):
        """
        Args:
            table (QTableWidget): tabel target
            sensor_type (str): jenis sensor ("TEV", "HFCT", "Ultrasonik") atau None jika untuk summary
            col_map (dict): mapping input kolom sensor (untuk single sensor)
            output_cols (tuple): (kolom_keparahan, kolom_rekomendasi)
            extra_params (dict): tambahan parameter (contoh: {"sensor": "contact_probe"})
        """
        self.table = table
        self.sensor_type = sensor_type
        self.col_map = col_map or {}
        self.output_cols = output_cols
        self.extra_params = extra_params or {}

        # Jika mode sensor tunggal → hubungkan event
        if self.sensor_type:
            self.table.cellChanged.connect(self.update_individual)
            for r in range(self.table.rowCount()):
                for key, col in self.col_map.items():
                    combo = self.table.cellWidget(r, col)
                    if isinstance(combo, QComboBox):
                        combo.currentIndexChanged.connect(
                            lambda _, rr=r: self.update_individual(row=rr)
                )

    # ---------------------------------------------------------
    # UPDATE UNTUK SENSOR INDIVIDU
    # ---------------------------------------------------------
    def update_individual(self, row=None, col=None):
        """Proses klasifikasi otomatis untuk baris tertentu (single sensor)."""
        
        try:
            if row is None:
                return

            # Ambil input dari tabel
            data = {}
            for key, col in self.col_map.items():
                item = self.table.item(row, col)
                widget = self.table.cellWidget(row, col)

                if isinstance(widget, QComboBox):
                    data[key] = widget.currentText().strip() if widget.currentText() else None
                elif item and item.text():
                    try:
                        val = float(item.text())
                        if key in ["ppc", "kepastian"]:
                            val = int(val)
                    except ValueError:
                        val = item.text().strip()
                    data[key] = val
                else:
                    data[key] = None

            # Jalankan klasifikasi sesuai sensor
            if self.sensor_type == "TEV":
                result = KlasifikasiPDTEV(
                    data.get("nilai", 0),
                    data.get("ppc", 0),
                    data.get("interpretasi")
                )
            elif self.sensor_type == "HFCT":
                result = KlasifikasiPDHFCT(
                    nilai_pc=data.get("nilai", 0),
                    ppc=data.get("ppc", 0),
                    unipolar_waveform=data.get("unipolar_waveform"),
                    cluster_dua_gelombang=data.get("cluster_dua_gelombang")
                )
            elif self.sensor_type == "Ultrasonik":
                result = KlasifikasiPDUltrasonik(
                    nilai_dbuv=data.get("nilai", 0),
                    kepastian=data.get("kepastian", 0),
                    interpretasi=data.get("interpretasi"),
                    suara_gemerosok=data.get("suara_gemerosok"),
                    cluster_dua_gelombang=data.get("cluster_dua_gelombang"),
                    sensor=self.extra_params.get("sensor", "unknown")
                )
            else:
                result = {"tingkat_keparahan": "N/A", "rekomendasi": "Sensor tidak dikenali"}

            # Update tabel
            self.table.blockSignals(True)
            self.table.setItem(row, self.output_cols[0], QTableWidgetItem(result["tingkat_keparahan"]))
            self.table.setItem(row, self.output_cols[1], QTableWidgetItem(str(result["rekomendasi"])))
            self.table.blockSignals(False)

        except Exception as e:
            self.table.blockSignals(False)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Input Error")
            msg.setText(f"Terjadi kesalahan pada tabel {self.sensor_type} baris {row+1}.")
            msg.setInformativeText(f"Detail error: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

    # ---------------------------------------------------------
    # UPDATE UNTUK KOMBINASI SENSOR
    # ---------------------------------------------------------
    def update_summary(self, row_map: dict, output_cols: tuple):
        """
        Update klasifikasi gabungan antar-sensor (legacy style).
        Args:
            row_map (dict): mapping sensor → (table, col_keparahan, col_rekomendasi)
            output_cols (tuple): (col_keparahan_final, col_rekomendasi_final) di summary table
        """
        from StandardValue import KlasifikasiPDFinal

        row_count = max(t.rowCount() for _, (t, _, _) in row_map.items())
        self.table.setRowCount(row_count)

        for r in range(row_count):
            hasil = []

            # Gunakan get_result dari masing-masing sensor updater
            for sensor, (tabel, col_k, col_r) in row_map.items():
                # Ambil hasil langsung dari tabel → bentuk dict mirip get_result()
                keparahan_item = tabel.item(r, col_k)
                rekomendasi_item = tabel.item(r, col_r)

                if keparahan_item and rekomendasi_item:
                    hasil.append({
                        "metode": sensor,
                        "tingkat_keparahan": keparahan_item.text(),
                        "rekomendasi": rekomendasi_item.text()
                    })

            final = KlasifikasiPDFinal(hasil) if hasil else {
                "keparahan_final": "Tidak Ada Data",
                "rekomendasi_final": "Tidak ada hasil"
            }

            # Update tabel summary
            self.table.setItem(r, output_cols[0], QTableWidgetItem(final["keparahan_final"]))
            self.table.setItem(r, output_cols[1], QTableWidgetItem(final["rekomendasi_final"]))
