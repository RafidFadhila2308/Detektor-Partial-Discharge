from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, 
    QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt


class RowControls(QWidget):
    def __init__(self, tables, row_setup_callback=None, parent=None):
        """
        :param tables: list of QTableWidget to control
        :param row_setup_callback: Function to set up widgets/items in a newly inserted row
                                   Signature: (table, row_index: int) -> None
        """
        super().__init__(parent)

        # Store all tables & track active table
        self.tables = tables
        self.current_table = tables[0]
        self.row_setup_callback = row_setup_callback

        # Detect focus change — set the current active table
        for t in tables:
            t.clicked.connect(lambda _, table=t: self.set_current_table(table))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ==== Title ====
        title_label = QLabel("Edit Baris")
        title_label.setStyleSheet("""
            font-weight: bold;
            text-decoration: underline;
            border-bottom: 1px solid gray;
            padding-bottom: 4px;
        """)
        layout.addWidget(title_label)  # <-- This line makes it appear

        # --- Add row controls ---
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Atas", "Bawah"])
        self.position_combo.setCurrentIndex(-1)
        self.position_combo.setPlaceholderText("Pilih Letak Baris Tambahan...")


        self.add_button = QPushButton("Tambah Baris")
        self.add_button.clicked.connect(self.add_row)

        add_layout = QHBoxLayout()
        add_layout.addWidget(self.position_combo)
        add_layout.addWidget(self.add_button)
        layout.addLayout(add_layout)

        # --- Delete row button ---
        self.delete_button = QPushButton("Hapus Baris")
        self.delete_button.clicked.connect(self.delete_row)
        layout.addWidget(self.delete_button)

    def set_current_table(self, table):
        self.current_table = table

    def renumber_titik(self, table):
        """Renumber the 'Titik' column sequentially starting from 1."""
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if not item:
                item = QTableWidgetItem()
                table.setItem(r, 0, item)
            item.setText(str(r + 1))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Keep read-only

    def add_row(self):
        """Insert a row above or below the selected row."""
        table = self.current_table
        pos_index = self.position_combo.currentIndex()
        
        if pos_index == -1:
            QMessageBox.warning(self, "Peringatan", "Pilih posisi baris tambahan (Atas/Bawah).")
            return

        selected_rows = set(idx.row() for idx in table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Peringatan", "Pilih baris sebagai acuan penambahan.")
            return

        selected_row = min(selected_rows)
        insert_at = selected_row if pos_index == 0 else selected_row + 1

        table.insertRow(insert_at)

        if self.row_setup_callback:
            self.row_setup_callback(table, insert_at)

        self.renumber_titik(table)
        self.position_combo.setCurrentIndex(-1)  # reset selection

    def delete_row(self):
        """Delete selected row, but keep at least one row in the table."""
        table = self.current_table
        selected_rows = sorted(set(idx.row() for idx in table.selectedIndexes()), reverse=True)

        if not selected_rows:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang ingin dihapus.")
            return

        for row in selected_rows:
            if table.rowCount() == 1:
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
