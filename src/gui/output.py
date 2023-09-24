import os
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
    QButtonGroup,
    QGroupBox,
    QFrame
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

class Output(QStackedWidget):

    _OUTPUT_SIZE = 780

    def __init__(self):
        super().__init__()

        self.setFixedWidth(self._OUTPUT_SIZE)
