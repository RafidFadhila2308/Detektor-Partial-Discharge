from PySide6.QtWidgets import QLineEdit, QComboBox
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

# =========================================================
# MODUL : PLACEHOLDER + AUTO-ADVANCE LINEEDIT
# =========================================================
class PlaceholderLineEdit(QLineEdit):
    """
    QLineEdit dengan placeholder dan auto-advance ke widget berikutnya
    jika panjang teks mencapai max_length. Hanya menerima input angka.
    """
    def __init__(self, placeholder, max_length=2, next_widget=None):
        """
        Args:
            placeholder (str): Teks placeholder.
            max_length (int): Panjang maksimum input.
            next_widget (QWidget): Widget yang akan diberi fokus otomatis setelah input penuh.
        """
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMaxLength(max_length)
        self.setValidator(QIntValidator())  # Hanya menerima angka
        self.setAlignment(Qt.AlignCenter)   # Teks rata tengah
        self.next_widget = next_widget
        self.textChanged.connect(self.check_auto_advance)

    def check_auto_advance(self, text):
        """
        Periksa panjang teks, jika mencapai max_length, pindahkan fokus ke next_widget.
        """
        if len(text) >= self.maxLength() and self.next_widget:
            self.next_widget.setFocus()


# =========================================================
# MODUL : PLACEHOLDER COMBOBOX
# =========================================================
class PlaceholderComboBox(QComboBox):
    """
    QComboBox dengan placeholder dan opsi item yang bisa ditentukan.
    Menampilkan placeholder ketika belum ada pilihan.
    """
    def __init__(self, placeholder, items=None, width=None):
        """
        Args:
            placeholder (str): Teks placeholder.
            items (list): Daftar string untuk item combobox.
            width (int): Lebar tetap combobox (opsional).
        """
        super().__init__()
        self.setEditable(True)            # Membuat combobox editable agar bisa menampilkan placeholder
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText(placeholder)
        if items:
            self.addItems(items)
        self.setCurrentIndex(-1)          # Menampilkan placeholder
        if width:
            self.setFixedWidth(width)     # Atur lebar tetap jika diberikan
