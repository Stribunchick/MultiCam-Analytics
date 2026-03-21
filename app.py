from PySide6.QtWidgets import QApplication
from mainConfigWindow import ConfigMainWindow
import sys

if __name__ == "__main__":
    app = QApplication()
    w = ConfigMainWindow()
    w.show()
    sys.exit(app.exec())
