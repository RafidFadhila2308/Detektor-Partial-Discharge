import sys, os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox
from docxtpl import DocxTemplate
from docx2pdf import convert
from MyWidget import MenuBar

# =========================================================
# HALAMAN : KONVERSI/EKSPOR LAPORAN
# =========================================================
class HalamanKonversiLaporanPLN(QWidget):
    def __init__(self):
        super().__init__()
        
        # Judul & ukuran jendela
        self.setWindowTitle("Ekspor Laporan Pengujian Partial Discharge")
        self.setGeometry(100, 100, 400, 200)

        # ===== Layout utama =====
        main_layout = QVBoxLayout(self)
        
        # ===== Menubar =====
        menu_bar = MenuBar(
            self,
            save_function=None,
            load_function=None,
            reset_all_function=None,
            reset_current_function=None,
            next_page=None,
            prev_page=self.go_prev,
            first_page=False,
            last_page=True
        )
        menu_bar.set_file_menu_enabled(False)
        main_layout.setMenuBar(menu_bar)

        button_docx = QPushButton("Ekspor ke DOCX")
        button_docx.clicked.connect(self.export_docx)
        main_layout.addWidget(button_docx)

        button_pdf = QPushButton("Ekspor ke PDF")
        button_pdf.clicked.connect(self.export_pdf)
        main_layout.addWidget(button_pdf)

        self.setLayout(main_layout)

        # Direktori dasar
        if getattr(sys, 'frozen', False):
            # Ketika menjalankan dari .exe
            BASE_DIR = os.path.dirname(sys.executable)
        else:
            # Ketika menjalankan dari .py
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.json_file = os.path.join(BASE_DIR, "saved_data.json")
        self.template_file = os.path.join(BASE_DIR, "Document", "Form Pengujian PD Kabel Power dan Incoming 20KV.docx")

    # ---------------------------------------------------------
    # EKSPOR DOCX
    # ---------------------------------------------------------
    def export_docx(self, silent=False):
        data = self.load_data()
        if not data:
            return
        try:
            doc = DocxTemplate(self.template_file)
            doc.render(data)
            out_file = "Form_Pengujian_PD_(terisi).docx"
            doc.save(out_file)
            if not silent:
                QMessageBox.information(self, "Sukses", f"DOCX tersimpan di {os.path.abspath(out_file)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ---------------------------------------------------------
    # EKSPOR PDF
    # ---------------------------------------------------------
    def export_pdf(self):
        self.export_docx(silent=True)
        try:
            out_docx = "Form_Pengujian_PD_(terisi).docx"
            out_pdf = "Form_Pengujian_PD_(terisi).pdf"
            convert(out_docx, out_pdf)
            QMessageBox.information(self, "Sukses", f"PDF tersimpan di {os.path.abspath(out_pdf)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ---------------------------------------------------------
    # NAVIGASI HALAMAN
    # ---------------------------------------------------------
    def go_prev(self):
        from Halaman_Formulir_Laporan_PLN import HalamanFormulirLaporanPLN
        self.close()
        new_page = HalamanFormulirLaporanPLN()
        new_page.show()

    # ---------------------------------------------------------
    # MEMUAT DATA JSON
    # ---------------------------------------------------------
    def load_data(self):
        import json
        if not os.path.exists(self.json_file):
            QMessageBox.warning(self, "Error", f"{self.json_file} tidak ditemukan!")
            return None
        with open(self.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "formulir_laporan" in data and "indikasi_pd" in data["formulir_laporan"]:
            beban = data["formulir_laporan"]["indikasi_pd"].get("beban_trafo")
            if isinstance(beban, dict):
                data["formulir_laporan"]["indikasi_pd"]["beban_trafo_list"] = [
                    {"name": k, "value": v} for k, v in beban.items()
                ]
        return data

# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HalamanKonversiLaporanPLN()
    window.show()
    sys.exit(app.exec())
