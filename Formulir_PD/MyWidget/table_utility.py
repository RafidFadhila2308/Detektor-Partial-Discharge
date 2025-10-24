from PySide6.QtWidgets import QTableWidget
from PySide6.QtCore import Qt

# =========================================================
# MODUL : FUNGSI UTILITAS TABEL
# =========================================================
class TableUtility:
    """
    Kumpulan fungsi utilitas untuk QTableWidget
    agar tinggi tabel otomatis menyesuaikan jumlah baris.
    """

    @staticmethod
    def update_table_height(table: QTableWidget, margin: int = 4):
        """
        Atur tinggi tabel agar semua baris + header terlihat penuh
        tanpa scrollbar vertikal.
        
        :param table: QTableWidget target
        :param margin: tambahan tinggi opsional (default = 4 px)
        """
        if table is None:
            return

        # Tinggi header
        header_h = table.horizontalHeader().height()

        # Jumlahkan tinggi semua baris (fallback ke default jika rowHeight = 0)
        rows_h = 0
        for r in range(table.rowCount()):
            rh = table.rowHeight(r)
            if rh <= 0:
                rh = table.verticalHeader().defaultSectionSize()
            rows_h += rh

        # Hitung total tinggi
        height = header_h + rows_h + 2 * table.frameWidth() + margin
        table.setFixedHeight(height)

    @staticmethod
    def connect_auto_resize(table: QTableWidget, margin: int = 4):
        """
        Hubungkan tabel dengan auto-resize tinggi.
        Tiap kali baris ditambah/dihapus, tinggi tabel akan menyesuaikan.
        
        :param table: QTableWidget target
        :param margin: tambahan tinggi opsional
        """
        if table is None:
            return

        # Hilangkan scrollbar vertikal
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Panggil resize awal
        TableUtility.update_table_height(table, margin)

        # Koneksi sinyal jika ada baris bertambah/berkurang
        table.model().rowsInserted.connect(lambda *_: TableUtility.update_table_height(table, margin))
        table.model().rowsRemoved.connect(lambda *_: TableUtility.update_table_height(table, margin))
