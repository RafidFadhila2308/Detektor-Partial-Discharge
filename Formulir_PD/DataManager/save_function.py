import json
import os
from PySide6.QtWidgets import QMessageBox

# =========================================================
# MODUL : FUNGSI SAVE
# =========================================================
class DataSave:
    """
    Modul untuk menyimpan data dari berbagai section ke file JSON.
    Data yang disimpan akan digabungkan (merge) dengan data lama jika ada.
    """
    
    def __init__(self, json_file="saved_data.json"):
        """
        Inisialisasi class DataSave.
        
        Args:
            json_file (str): Nama file JSON yang akan digunakan untuk menyimpan data.
        """
        self.json_file = json_file
        self.section_callbacks = {}  # Dictionary untuk menyimpan callback per section
        self.data = {}  # Menyimpan data terakhir yang disimpan (internal)

    def register_section_save(self, section_name, get_data_callback):
        """
        Mendaftarkan section untuk disimpan.
        Callback akan dipanggil untuk mendapatkan data dari section saat save.
        
        Args:
            section_name (str): Nama section.
            get_data_callback (function): Fungsi untuk mengambil data section.
        """
        self.section_callbacks[section_name] = get_data_callback

    def save_to_file(self):
        """
        Menyimpan semua section yang sudah didaftarkan ke file JSON.
        Data baru akan digabungkan dengan data lama jika file sudah ada.
        Menampilkan pesan informasi/error sesuai hasil.
        """
        try:
            # Load data lama jika file JSON sudah ada
            if os.path.exists(self.json_file):
                try:
                    with open(self.json_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    # Jika file corrupt atau kosong, buat dictionary kosong
                    existing_data = {}
            else:
                existing_data = {}

            # Update hanya section yang sudah didaftarkan
            for section, callback in self.section_callbacks.items():
                new_data = callback(existing_data.get(section, {}))  
                existing_data[section] = new_data

            # Simpan ke atribut internal juga
            self.data = existing_data

            # Simpan data gabungan kembali ke file JSON
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)

            # Tampilkan pesan sukses
            QMessageBox.information(None, "Sukses", "Data berhasil disimpan.")
        except Exception as e:
            # Tampilkan pesan error jika gagal
            QMessageBox.critical(None, "Kesalahan", f"Data gagal disimpan: {e}")
