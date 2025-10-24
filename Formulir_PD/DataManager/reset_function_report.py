import json
from PySide6.QtWidgets import QMessageBox

# =========================================================
# MODUL : FUNGSI RESET HALAMAN LAPORAN
# =========================================================
class DataResetReport:
    """
    Modul untuk mereset data halaman laporan di file JSON.
    - reset_current: reset hanya 1 section (halaman saat ini)
    - reset_file: reset seluruh isi JSON
    """

    def __init__(self, json_file="saved_data.json"):
        """
        Inisialisasi class DataResetCover.
        
        Args:
            json_file (str): Nama file JSON yang akan di-reset.
        """
        self.json_file = json_file
        self.section_resetters = {}  # Dictionary untuk menyimpan callback reset per section

    def register_section_reset(self, section_name, reset_callback):
        """
        Mendaftarkan fungsi reset untuk sebuah section.
        Callback ini akan dipanggil saat reset dilakukan.
        
        Args:
            section_name (str): Nama section (contoh: "halaman_depan")
            reset_callback (function): Fungsi untuk mereset section (misal clear form).
        """
        self.section_resetters[section_name] = reset_callback

    # ------------------------------------------------------
    # RESET SELURUH FILE (ALL)
    # ------------------------------------------------------
    def reset_file(self):
        """
        Reset seluruh isi JSON dan panggil semua reset callback.
        """
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

            for _, reset_cb in self.section_resetters.items():
                reset_cb()

            QMessageBox.information(None, "Sukses", "Seluruh data berhasil di-reset.")
            return True
        except Exception as e:
            QMessageBox.critical(None, "Kesalahan", f"Data gagal di-reset: {e}")
            return False

    # ------------------------------------------------------
    # RESET HALAMAN SAAT INI (CURRENT)
    # ------------------------------------------------------
    def reset_current(self, section=None):
        """
        Reset hanya section tertentu dalam JSON.
        
        Args:
            section (str): nama section dalam JSON.
                        Jika None, maka akan dicari dari callback register.
        """
        try:
            # Pastikan section ada
            if section is None:
                raise ValueError("Nama section harus diberikan untuk reset_current.")

            # baca file JSON
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}

            # reset section ini
            data[section] = {}

            # tulis balik JSON
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # panggil callback kalau ada
            if section in self.section_resetters:
                self.section_resetters[section]()

            QMessageBox.information(None, "Sukses", f"Data untuk '{section}' berhasil di-reset.")
            return True

        except Exception as e:
            QMessageBox.critical(None, "Kesalahan", f"Gagal reset data: {e}")
            return False

