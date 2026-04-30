from PySide6.QtWidgets import QApplication
from mainConfigWindow import ConfigMainWindow
from gui.theme import apply_theme
import sys

if __name__ == "__main__":
    app = QApplication()
    apply_theme(app)
    w = ConfigMainWindow()
    w.show()
    sys.exit(app.exec())
