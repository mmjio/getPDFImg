import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget

from main_event import main_event
from ui.main import Ui_MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    window = Ui_MainWindow()
    window.setupUi(mainWindow)
    event = main_event(window)
    mainWindow.show()
    sys.exit(app.exec())
