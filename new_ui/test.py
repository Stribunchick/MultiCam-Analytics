from PySide6.QtWidgets import QApplication
from mainConfigWindow import ConfigMainWindow
import sys

app = QApplication()
w = ConfigMainWindow()
w.show()
app.exec()
