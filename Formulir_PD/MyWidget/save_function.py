import json
import os
from PySide6.QtWidgets import QMessageBox


class DataSave:
    def __init__(self, json_file="saved_data.json"):
        self.json_file = json_file
        self.section_callbacks = {}  # get data callbacks
        self.data = {}  # <- tambahkan ini

    def register_section(self, section_name, get_data_callback):
        """Register a section for saving."""
        self.section_callbacks[section_name] = get_data_callback

    def save_to_file(self):
        """Save all registered sections into JSON (merge with existing)."""
        try:
            # Load existing data if file exists
            if os.path.exists(self.json_file):
                try:
                    with open(self.json_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}
            else:
                existing_data = {}

            # Update only the sections registered in this window
            for section, callback in self.section_callbacks.items():
                existing_data[section] = callback()

            # simpan ke atribut internal juga
            self.data = existing_data

            # Save merged data back
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)

            QMessageBox.information(None, "Success", "Data saved successfully.")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to save data: {e}")
