from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QPushButton, 
    QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

# =========================================================
# MODUL : TOMBOL PENGATUR BARIS
# =========================================================
class RowEditors(QWidget):
    """
    Widget untuk mengatur penambahan dan penghapusan baris pada satu atau lebih QTableWidget.
    Memungkinkan memilih posisi baris baru (Atas/Bawah) dan memanggil callback untuk setup baris.
    """
    
    def __init__(self, tables, row_setup_callback=None, parent=None):
        """
        :param tables: list QTableWidget yang akan dikontrol
        :param row_setup_callback: Fungsi untuk mengatur widget/item pada baris baru
                                   Signature: (table, row_index: int) -> None
        """
        super().__init__(parent)

        # Simpan daftar tabel & tabel aktif saat ini
        self.tables = tables
        self.current_table = tables[0]  # default tabel aktif
        self.row_setup_callback = row_setup_callback  # callback untuk setup baris baru

        # Deteksi klik pada tabel — set tabel aktif saat ini
        for t in tables:
            t.clicked.connect(lambda _, table=t: self.set_current_table(table))
        
        # ---------------------------------------------------------
        # Layout editor baris
        # ---------------------------------------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ===== Judul =====
        title_label = QLabel("Edit Baris")
        title_label.setStyleSheet("""
            font-weight: bold;
            text-decoration: underline;
            border-bottom: 1px solid gray;
            padding-bottom: 4px;
        """)
        layout.addWidget(title_label)  # Tampilkan judul

        # ===== Kontrol penambahan baris =====
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Atas", "Bawah"])
        self.position_combo.setCurrentIndex(-1)
        self.position_combo.setPlaceholderText("Pilih letak baris tambahan...")

        # Tombol tambah baris
        self.add_button = QPushButton("Tambah Baris")
        self.add_button.clicked.connect(self.add_row)

        add_layout = QHBoxLayout()
        add_layout.addWidget(self.position_combo)
        add_layout.addWidget(self.add_button)
        layout.addLayout(add_layout)

        # Tombol hapus baris
        self.delete_button = QPushButton("Hapus Baris")
        self.delete_button.clicked.connect(self.delete_row)
        layout.addWidget(self.delete_button)

    def set_current_table(self, table):
        """Set tabel yang saat ini aktif untuk operasi tambah/hapus baris."""
        self.current_table = table

    def renumber_titik(self, table):
        """
        Memberi nomor urut pada kolom 'Titik' mulai dari 1.
        Kolom ini dibuat read-only agar tidak bisa diubah user.
        """
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if not item:
                item = QTableWidgetItem()
                table.setItem(r, 0, item)
            item.setText(str(r + 1))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Tetap read-only

    # ---------------------------------------------------------
    # Fungsi editor
    # ---------------------------------------------------------
    # ===== Fungsi tambah baris =====
    def add_row(self):
        """
        Menambahkan baris baru di atas atau di bawah baris yang dipilih.
        Memanggil callback setup baris jika ada.
        """
        table = self.current_table
        pos_index = self.position_combo.currentIndex()
        
        if pos_index == -1:
            QMessageBox.warning(self, "Peringatan", "Pilih posisi baris tambahan (Atas/Bawah).")
            return

        # Ambil baris yang dipilih
        selected_rows = set(idx.row() for idx in table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Peringatan", "Pilih baris sebagai acuan penambahan.")
            return

        selected_row = min(selected_rows)
        insert_at = selected_row if pos_index == 0 else selected_row + 1

        table.insertRow(insert_at)

        # Panggil callback untuk setup baris baru jika ada
        if self.row_setup_callback:
            self.row_setup_callback(table, insert_at)

        self.renumber_titik(table)
        self.position_combo.setCurrentIndex(-1)  # Reset pilihan combobox

    # ===== Fungsi hapus baris =====
    def delete_row(self):
        """
        Menghapus baris yang dipilih.
        Selalu menjaga minimal 1 baris di tabel; jika tinggal 1 baris, hanya dikosongkan.
        """
        table = self.current_table
        selected_rows = sorted(set(idx.row() for idx in table.selectedIndexes()), reverse=True)

        if not selected_rows:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang ingin dihapus.")
            return

        for row in selected_rows:
            if table.rowCount() == 1:
                # Jika hanya ada 1 baris, kosongkan kontennya
                for col in range(table.columnCount()):
                    item = table.item(0, col)
                    if item:
                        item.setText("")
                    widget = table.cellWidget(0, col)
                    if isinstance(widget, QComboBox):
                        widget.setCurrentIndex(-1)
                self.renumber_titik(table)
                return
            else:
                table.removeRow(row)

        self.renumber_titik(table)
