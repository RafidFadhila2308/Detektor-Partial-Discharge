import json
from PySide6.QtWidgets import QMessageBox


class DataReset:
    def __init__(self, json_file="saved_data.json"):
        self.json_file = json_file
        self.section_resetters = {}

    def register_section_resetter(self, section_name, reset_callback):
        """Register a section resetter (e.g., clear form)."""
        self.section_resetters[section_name] = reset_callback

    def reset_file(self):
        """Clear JSON file and reset registered sections."""
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

            for section, reset_cb in self.section_resetters.items():
                reset_cb()

            QMessageBox.information(None, "Success", "Data reset successfully.")
            return True
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to reset data: {e}")
            return False
