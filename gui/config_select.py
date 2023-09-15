from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QCheckBox,
    QWidget,
    QLabel
)

class ConfigList(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self._items = [Config(0, self.item_signal)]
        self.layout.addWidget(self._items[0])

    def _set_size(self):
        for item in self._items[:-1]:
            item.set_last(False)
        self._items[-1].set_last(True)

    def item_signal(self, stype: int):
        if not stype:
            self.layout.removeWidget(self._items[-1])
            self._items = self._items[:-1]
        else:
            self._items.append(Config(len(self._items), self.item_signal))
            self.layout.addWidget(self._items[-1])
        self._set_size()

class Config(QWidget):

    def __init__(self, index, item_signal):
        super().__init__()
        self._index = index
        sidelayout = QHBoxLayout()

        self._add_button = QPushButton("+", self)
        self._del_button = QPushButton("X", self)
        self._add_button.setMaximumWidth(20)
        self._del_button.setMaximumWidth(20)

        self._add_button.clicked.connect(lambda: item_signal(1))
        self._del_button.clicked.connect(lambda: item_signal(0))

        sidelayout.addWidget(QLabel(f"Configuration {self._index + 1:d}"))
        sidelayout.addWidget(self._add_button)
        sidelayout.addWidget(self._del_button)
        self.setLayout(sidelayout)

    def set_last(self, is_last):
        self._add_button.setEnabled(is_last)
        self._del_button.setEnabled(is_last if self._index else False)
