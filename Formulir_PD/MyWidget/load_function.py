import os
import json
from PySide6.QtWidgets import QMessageBox


class DataLoad:
    def __init__(self, json_file="saved_data.json"):
        self.json_file = json_file
        self.section_setters = {}  # set data callbacks
        self.data = {}

    def register_section_setter(self, section_name, set_data_callback):
        """Register a section setter for loading."""
        self.section_setters[section_name] = set_data_callback

    def load_from_file(self):
        """Load JSON data and apply to registered sections."""
        try:
            if not os.path.exists(self.json_file):
                QMessageBox.warning(None, "Warning", "No saved file found.")
                return

            with open(self.json_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            for section, data in self.data.items():
                if section in self.section_setters:
                    self.section_setters[section](data)

            QMessageBox.information(None, "Success", "Data loaded successfully.")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load data: {e}")