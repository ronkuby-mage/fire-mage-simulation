import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QCheckBox,
    QLineEdit,
    QMessageBox,
    QWidget,
    QLabel
)

class ConfigListWidget(QWidget):

    def __init__(self, config_list, expand=True):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self._items = [ConfigWidget(0, self.item_signal, config=config_list.config(0))]
        self.layout.addWidget(self._items[0])
        self._expand = expand
        self._set_size()
        self._config_list = config_list

    def _set_size(self):
        for item in self._items[:-1]:
            item.set_last(False)
        self._items[-1].set_last(self._expand)

    def item_signal(self, stype: int):
        if not stype:
            self.layout.removeWidget(self._items[-1])
            self._items = self._items[:-1]
        else:
            self._items.append(ConfigWidget(len(self._items), self.item_signal))
            self.layout.addWidget(self._items[-1])
        self._set_size()

    # update to current index
    def set_trigger(self, update_function):
        self._update_function = update_function
        self._items[0].set_trigger(update_function)

class ConfigWidget(QWidget):

    def __init__(self, index, item_signal, config=None):
        super().__init__()
        self._index = index
        self._config = config
        sidelayout = QHBoxLayout()

        self._filename = QLineEdit()
        self._filename.textChanged.connect(self.modify)
        self._load_button = QPushButton("Load", self)
        self._save_button = QPushButton("Save", self)
        self._load_button.setMaximumWidth(130)
        self._save_button.setMaximumWidth(130)
        self._load_button.clicked.connect(self._load)
        self._save_button.clicked.connect(self._save)

        self._add_button = QPushButton("+", self)
        self._del_button = QPushButton("X", self)
        self._add_button.setMaximumWidth(20)
        self._del_button.setMaximumWidth(20)
        self._add_button.clicked.connect(lambda: item_signal(1))
        self._del_button.clicked.connect(lambda: item_signal(0))

        sidelayout.addWidget(QLabel(f"Scenario {self._index + 1:d}"))
        sidelayout.addWidget(self._filename)
        sidelayout.addWidget(self._load_button)
        sidelayout.addWidget(self._save_button)
        sidelayout.addWidget(self._add_button)
        sidelayout.addWidget(self._del_button)
        self.setLayout(sidelayout)

        # default is initially loaded
        self._filename.setText(self._user_filename())
        self._filename.setStyleSheet("border:1px solid rgb(0, 255, 0); ")

    def _load(self):
        try:
            self._config.load(self._filename.text())
            self._update_function()
            self._filename.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("File not found.")
            msg.setWindowTitle("Load Error")
            msg.exec()
    
    def _save(self):
        self._config.save(self._filename.text())
        self._filename.setStyleSheet("border:1px solid rgb(0, 255, 0); ")

    def modify(self):
        self._filename.setStyleSheet("border:1px solid rgb(255, 0, 0); ")

    def _user_filename(self):
        if self._config is not None:
            filename = self._config.filename()
            base, ext = os.path.splitext(filename)
            return base

        return ""

    def set_last(self, is_last):
        self._add_button.setEnabled(is_last)
        self._del_button.setEnabled(is_last if self._index else False)

    def set_trigger(self, update_function):
        self._update_function = update_function
