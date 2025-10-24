import os
import json
from PySide6.QtWidgets import QMessageBox

# =========================================================
# MODUL : FUNGSI LOAD
# =========================================================
class DataLoad:
    """
    Modul untuk memuat data dari file JSON dan mengaplikasikannya ke
    bagian-bagian (sections) yang telah didaftarkan melalui callback.
    """
    
    def __init__(self, json_file="saved_data.json"):
        """
        Inisialisasi class DataLoad.
        
        Args:
            json_file (str): Nama file JSON yang akan dibaca.
        """
        self.json_file = json_file
        self.section_setters = {}  # Dictionary untuk menyimpan callback per section
        self.data = {}  # Menyimpan data JSON yang dibaca

    def register_section_load(self, section_name, load_callback):
        """
        Mendaftarkan setter (callback) untuk sebuah section tertentu.
        Callback ini akan dipanggil saat data section tersebut di-load.
        
        Args:
            section_name (str): Nama section sesuai key di file JSON.
            load_callback (function): Fungsi untuk menerapkan data section.
        """
        self.section_setters[section_name] = load_callback

    def load_from_file(self):
        try:
            if not os.path.exists(self.json_file):
                QMessageBox.warning(None, "Peringatan", "Tidak ditemukan file tersimpan.")
                return

            with open(self.json_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            for section, data in self.data.items():
                if section in self.section_setters:
                    self.section_setters[section](data)

            # ❌ jangan tampilkan QMessageBox disini
            # QMessageBox.information(None, "Sukses", "Data berhasil dimuat.")

        except Exception as e:
            QMessageBox.critical(None, "Kesalahan", f"Data gagal dimuat: {e}")
