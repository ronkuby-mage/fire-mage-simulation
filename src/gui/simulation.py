from PyQt5.QtWidgets import (
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QWidget,
    QStackedWidget,
    QLabel,
    QHeaderView,
    QGroupBox,
    QFrame
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon
from PyQt5.QtCore import Qt, QSize

class Simulation(QWidget):

    def __init__(self, config_list, filename_func):
        super().__init__()
        self._config_list = config_list
        self._filenames = filename_func

        layout = QHBoxLayout()

        self.setLayout(layout)

class Settings(QFrame):

    def __init__(self, config_list):
        super().__init__()
        self._config_list = config_list


