from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QCheckBox,
    QWidget,
    QStackedWidget,
    QLabel
)
from character import Character

class Scenario(QStackedWidget):

    def __init__(self):
        super().__init__()
        self.group = Group()
        self.character = Character()

        hbox = QHBoxLayout(self)
        self.addWidget(self.group)
        self.addWidget(self.character)

        self.setLayout(hbox)


class Group(QWidget):

    def __init__(self):
        super().__init__()
