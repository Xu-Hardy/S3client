from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer


class AutoCloseMessageBox(QMessageBox):
    def __init__(self, timeout=3, parent=None):
        super().__init__(parent)
        self.timeout = timeout
        self.setStyleSheet("QLabel{min-width: 200px;}")

    def showEvent(self, event):
        QTimer.singleShot(self.timeout * 1000, self.accept)
        super().showEvent(event)
