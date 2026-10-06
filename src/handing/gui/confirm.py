from PySide6.QtWidgets import QMessageBox

def confirm_warnings(parent, title: str, warnings: list[str]) -> bool:
    """True when there is nothing to warn about or the user saves anyway"""
    if not warnings:
        return True

    text = "\n".join(f"- {w}" for w in warnings) + "\n\nSave anyway?"
    answer = QMessageBox.warning(parent, title, text, QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel)

    return answer == QMessageBox.StandardButton.Save
