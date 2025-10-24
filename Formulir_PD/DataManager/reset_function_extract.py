import json
from PySide6.QtWidgets import QMessageBox

# =========================================================
# MODUL : FUNGSI RESET HALAMAN EKSTRAKSI
# =========================================================
class DataResetExtract:
    """
    Modul untuk mereset data di file JSON dan mengosongkan/mengembalikan
    setiap section yang sudah didaftarkan ke kondisi awal.
    """
    
    def __init__(self, json_file="saved_data.json"):
        """
        Inisialisasi class DataResetExtract.
        
        Args:
            json_file (str): Nama file JSON yang akan di-reset.
        """
        self.json_file = json_file
        self.section_resetters = {}  # Dictionary untuk menyimpan callback reset per section

    def register_section_reset(self, section_name, reset_callback):
        """
        Mendaftarkan fungsi reset untuk sebuah section.
        Callback ini akan dipanggil saat reset dilakukan.
        """
        self.section_resetters[section_name] = reset_callback

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

    def reset_current(self, key, section="hasil_plot"):
        """
        Reset hanya entry tertentu dalam section JSON.
        Args:
            key (str): key unik (contoh: 'Lokasi|Sensor')
            section (str): nama section dalam JSON (default: 'hasil_plot')
        """
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            removed = False

            # Pastikan section ada
            if section in data and key in data[section]:
                del data[section][key]
                removed = True

                with open(self.json_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)

            # Panggil callback kalau ada (reset widget)
            if section in self.section_resetters:
                self.section_resetters[section]()  # Hanya clear widget, tidak boleh panggil reset_current lagi

            # Kasih pesan hanya kalau beneran ada data dihapus
            if removed:
                QMessageBox.information(None, "Sukses", f"Data untuk '{key}' di section '{section}' berhasil di-reset.")
            else:
                # Silent, tidak perlu popup
                pass

            return True
        except Exception as e:
            QMessageBox.critical(None, "Kesalahan", f"Gagal reset data: {e}")
            return False
