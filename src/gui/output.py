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
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from ..sim.config import ConfigList, Config
from typing import Callable
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt


#    _OUTPUT_SIZE = 780
#     self.setFixedWidth(self._OUTPUT_SIZE)
class StatOutput(QWidget):
    _OUTPUT_SIZE = 780


    def __init__(self, config_list: ConfigList, filename_func: Callable):
        super().__init__()
        self._config_list = config_list
        self._filename_func = filename_func
        self.setFixedWidth(self._OUTPUT_SIZE)

    def handle_output(self, output):
        print(output.mean())

class CompareOutput(QWidget):
    _OUTPUT_SIZE = 780

    def __init__(self, config_list: ConfigList, filename_func: Callable):
        super().__init__()
        self._config_list = config_list
        self._filename_func = filename_func
        self.setFixedWidth(self._OUTPUT_SIZE)
