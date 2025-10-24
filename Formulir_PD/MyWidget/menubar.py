from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction

# =========================================================
# MODUL : MENUBAR
# =========================================================
class MenuBar(QMenuBar):
    """
    Menu bar kustom untuk aplikasi PySide6.
    Menyediakan menu File (Save, Load, Reset) dan Navigate (Next/Previous Page).
    """
    def __init__(self, parent=None,
                 save_function=None,
                 load_function=None,
                 reset_all_function=None,
                 reset_current_function=None,
                 next_page=None,
                 prev_page=None,
                 first_page=False,
                 last_page=False):
        """
        Inisialisasi MenuBar.
        
        Args:
            save_function (callable): Fungsi untuk action Save.
            load_function (callable): Fungsi untuk action Load.
            reset_all_function (callable): Fungsi untuk Reset All Page.
            reset_current_function (callable): Fungsi untuk Reset Current Page.
            next_page (callable): Fungsi untuk Next Page.
            prev_page (callable): Fungsi untuk Previous Page.
            first_page (bool): True jika berada di halaman pertama (disable prev).
            last_page (bool): True jika berada di halaman terakhir (disable next).
        """
        super().__init__(parent)

        # ===== Menu File =====
        file_menu = QMenu("File", self)

        # Action Save
        self.save_action = QAction("Save", self)
        if save_function:
            self.save_action.triggered.connect(save_function)
        file_menu.addAction(self.save_action)

        # Action Load
        self.load_action = QAction("Load", self)
        if load_function:
            self.load_action.triggered.connect(load_function)
        file_menu.addAction(self.load_action)

        # Submenu Reset
        reset_menu = QMenu("Reset", self)

        # Reset semua halaman
        self.reset_all_action = QAction("All Page", self)
        if reset_all_function:
            self.reset_all_action.triggered.connect(reset_all_function)
        reset_menu.addAction(self.reset_all_action)

        # Reset halaman saat ini
        self.reset_current_action = QAction("Current Page", self)
        if reset_current_function:
            self.reset_current_action.triggered.connect(reset_current_function)
        reset_menu.addAction(self.reset_current_action)

        # Tambahkan submenu Reset ke menu File
        file_menu.addMenu(reset_menu)

        # Tambahkan menu File ke menubar
        self.addMenu(file_menu)

        # ===== Menu Navigate =====
        navigate_menu = QMenu("Navigate", self)

        # Action Previous Page
        self.prev_action = QAction("Previous Page", self)
        if prev_page:
            self.prev_action.triggered.connect(prev_page)
        self.prev_action.setEnabled(not first_page)  # disable jika di halaman pertama
        navigate_menu.addAction(self.prev_action)

        # Action Next Page
        self.next_action = QAction("Next Page", self)
        if next_page:
            self.next_action.triggered.connect(next_page)
        self.next_action.setEnabled(not last_page)  # disable jika di halaman terakhir
        navigate_menu.addAction(self.next_action)

        # Tambahkan menu Navigate ke menubar
        self.addMenu(navigate_menu)

    def set_file_menu_enabled(self, enabled: bool):
        """
        Mengaktifkan atau menonaktifkan semua action pada menu File.
        
        Args:
            enabled (bool): True untuk enable, False untuk disable
        """
        self.save_action.setEnabled(enabled)
        self.load_action.setEnabled(enabled)
        self.reset_all_action.setEnabled(enabled)
        self.reset_current_action.setEnabled(enabled)
