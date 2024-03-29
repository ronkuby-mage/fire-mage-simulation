import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QCheckBox,
    QRadioButton,
    QLineEdit,
    QMessageBox,
    QWidget,
    QLabel
)

class ConfigListWidget(QWidget):

    _MAX_CONFIGS = 5

    def __init__(self, config_list, update_trigger, expand=True):
        super().__init__()
        self._update_trigger = update_trigger
        self._settings_refresh = None
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self._items = [ConfigWidget(0, self.item_signal, self.update, self.select_trigger, config=config_list.current())]
        self.layout.addWidget(self._items[0])
        self._expand = expand
        self._set_size()
        self._config_list = config_list
        self._index = 0

    def _set_size(self):
        for item in self._items[:-1]:
            item.set_last(False)
        self._items[-1].set_last(self._expand, max_configs=self._MAX_CONFIGS)

    # to add or remove last config
    def item_signal(self, stype: int):
        if not stype:
            self.layout.removeWidget(self._items[-1])
            if self._index == len(self._items) - 1:
                self.set_index(self._index - 1)
            self._items = self._items[:-1]
            self._config_list.pop()
        else:
            filename = self._items[-1].filename() + "_copy"
            self._items.append(ConfigWidget(len(self._items),
                                            self.item_signal,
                                            self.update,
                                            self.select_trigger,
                                            config=self._config_list.copy(filename)))
            self.layout.addWidget(self._items[-1])
            self.set_index(len(self._items) - 1)
            self.changed_trigger()
            self._items[-1].settings_refresh(self._settings_refresh)
        self._set_size()
        if self._settings_refresh is not None:
            self._settings_refresh()

    def select_trigger(self, index: int):
        if index == self._index: #do nothing
            self._items[self._index].select(True)
        else:
            self.set_index(index)

    def set_index(self, index):
        self._items[self._index].select(False)
        self._index = index
        self._config_list.set_index(index)
        self._update_trigger()
        self._items[self._index].select(True)
        if self._settings_refresh is not None:
            self._settings_refresh()

    def changed_trigger(self):
        self._items[self._index].modify()

    def update(self, index):
        if index == self._index:
            self._update_trigger()

    def filenames(self, current=False):
        if current:
            return self._items[self._index].filename()
        else:
            return [item.filename() for item in self._items]
    
    def settings_refresh(self, refresh):
        for item in self._items:
            item.settings_refresh(refresh)
        self._settings_refresh = refresh

class ConfigWidget(QWidget):

    def __init__(self, index, item_signal, update_trigger, select_trigger, config=None):
        super().__init__()
        self._index = index
        self._config = config
        self._update_trigger = update_trigger
        self._settings_refresh = None
        sidelayout = QHBoxLayout()
        sidelayout.setContentsMargins(3, 5, 3, 5)

        self._select = QRadioButton(f"Scenario {index + 1:d}")
        self._select.setChecked(True)
        self._select.pressed.connect(lambda x=self._index: select_trigger(x))
        self._select.released.connect(lambda x=self._index: select_trigger(x))
  
        self._filename = QLineEdit()
        self._filename.textChanged.connect(self.modify)
        self._filename.returnPressed.connect(self._load)
        self._filename.setMaximumWidth(250)
        self._filename.setMinimumWidth(200)
        self._filename.setMaxLength(26)
        self._filename.setContentsMargins(0, 0, 0, 0)
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

        sidelayout.addStretch()
        sidelayout.addWidget(self._select)
        sidelayout.addWidget(self._filename)
        sidelayout.addWidget(self._load_button)
        sidelayout.addWidget(self._save_button)
        sidelayout.addWidget(self._add_button)
        sidelayout.addWidget(self._del_button)
        self.setLayout(sidelayout)

        # default is initially loaded
        self._filename.setText(self._user_filename())
        self._filename.setStyleSheet("border:1px solid rgb(0, 255, 0); ")

    def select(self, enabled: bool):
        self._select.setChecked(enabled)

    def _load(self):
        try:
            self._config.load(self._filename.text())
            self._update_trigger(self._index)
            self._filename.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
            self._filename.setToolTip("")
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("File not found.")
            msg.setWindowTitle("Load Error")
            msg.exec()
        if self._settings_refresh is not None:
            self._settings_refresh()
    
    def _save(self):
        self._config.save(self._filename.text())
        self._filename.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
        self._filename.setToolTip("")

    def modify(self):
        self._filename.setStyleSheet("border:1px solid rgb(255, 0, 0); ")
        self._filename.setToolTip("Scenario is not saved")
        if self._settings_refresh is not None:
            self._settings_refresh()

    def _user_filename(self):
        if self._config is not None:
            filename = self._config.filename()
            base, ext = os.path.splitext(filename)
            return base

        return ""

    def set_last(self, enabled, max_configs=100):
        if not enabled:
            self._add_button.setEnabled(False)
            self._del_button.setEnabled(False)
        else:
            self._add_button.setEnabled(True if self._index + 1 < max_configs else False)
            self._del_button.setEnabled(True if self._index else False)

    def filename(self):
        return self._filename.text()
    
    def settings_refresh(self, refresh):
        self._settings_refresh = refresh
