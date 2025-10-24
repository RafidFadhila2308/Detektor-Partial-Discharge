from PySide6.QtWidgets import QComboBox
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

# =========================================================
# MODUL : CHECKABLE COMBOBOX
# =========================================================
class CheckableComboBox(QComboBox):
    """
    QComboBox kustom yang memungkinkan item di dalamnya dapat dicentang (checkable).
    Mendukung placeholder text dan pengambilan/mengatur item yang dicentang.
    """
    
    def __init__(self, placeholder_text="Pilih...", items=None, parent=None):
        super().__init__(parent)
        self.setEditable(True)  # Membuat QComboBox bisa diubah (editable) agar bisa menampilkan teks secara custom
        self.setModel(QStandardItemModel(self))  # Menggunakan model standar untuk mendukung item checkable
        self.lineEdit().setReadOnly(True)  # Membuat pengguna tidak bisa mengetik langsung di line edit
        self.lineEdit().setPlaceholderText(placeholder_text)  # Set placeholder text
        self.model().dataChanged.connect(self._update_display)  # Update teks di line edit saat item dicentang

        # Menyimpan setting internal
        self._placeholder_text = placeholder_text
        self._items_list = items or []  # Jika tidak diberikan, gunakan list kosong

        # Jika diberikan daftar item, tambahkan ke combobox
        if self._items_list:
            self.addItems(self._items_list)

    def addItem(self, text, userData=None):
        """
        Menambahkan satu item ke combobox.
        Item akan bersifat checkable.
        """
        item = QStandardItem(text)
        if userData is not None:
            item.setData(userData)  # Menyimpan data tambahan jika diberikan
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)  # Set item agar bisa dicentang
        item.setData(Qt.Unchecked, Qt.CheckStateRole)  # Awalnya belum dicentang
        self.model().appendRow(item)  # Tambahkan item ke model combobox

    def addItems(self, texts):
        """
        Menambahkan beberapa item sekaligus ke combobox.
        """
        for text in texts:
            self.addItem(text)
        # Pastikan tidak ada item yang dipilih saat awal
        self.setCurrentIndex(-1)

    def _update_display(self):
        """
        Update teks pada line edit untuk menampilkan semua item yang dicentang,
        dipisahkan dengan koma.
        """
        checked_items = [
            self.model().item(i).text()
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == Qt.Checked
        ]
        self.lineEdit().setText(", ".join(checked_items))

    @property
    def SelectedItems(self):
        """Mengembalikan daftar item yang sedang dicentang."""
        return [
            self.model().item(i).text()
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == Qt.Checked
        ]

    @SelectedItems.setter
    def SelectedItems(self, items_to_check):
        """
        Check hanya item yang diberi.
        Semua item lain akan di-uncheck.
        """
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.text() in items_to_check:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    @property
    def PlaceHolderText(self):
        """Mendapatkan placeholder text."""
        return self._placeholder_text

    @PlaceHolderText.setter
    def PlaceHolderText(self, text):
        """Mengatur placeholder text."""
        self._placeholder_text = text
        self.lineEdit().setPlaceholderText(text)

    @property
    def ItemsList(self):
        """Mendapatkan daftar item saat ini."""
        return self._items_list

    @ItemsList.setter
    def ItemsList(self, items):
        """
        Mengatur ulang daftar item combobox.
        Semua item lama akan dihapus dan diganti dengan item baru.
        """
        self.clear()
        self._items_list = items
        self.addItems(items)
