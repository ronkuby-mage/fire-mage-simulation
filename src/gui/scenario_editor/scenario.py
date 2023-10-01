import json
from PyQt5.QtWidgets import (
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QComboBox,
    QCheckBox,
    QWidget,
    QStackedWidget,
    QLabel,
    QHeaderView,
    QGroupBox
)
from .character import Character
from .mages import Group
from .rotation import Rotation
from .buffs import Buffs

class Scenario(QStackedWidget):

    def __init__(self, config_list):

        super().__init__()
        self._settings_refresh = None

        self._group = Group(config_list, self.mod_mages)
        self._buffs = Buffs(config_list)
        self._rotation = Rotation(config_list)

        self._character = Character()

        scen = QWidget()
        gbs = QWidget()
        layout1 = QHBoxLayout()
        layout2 = QVBoxLayout()

        layout2.addWidget(self._group)
        layout2.addWidget(self._buffs)
        gbs.setLayout(layout2)
        
        layout1.addWidget(gbs)
        layout1.addWidget(self._rotation)

        scen.setLayout(layout1)

        self.addWidget(scen)
        self.addWidget(self._character)
        self._changed_trigger = None

    def update(self):
        temp_ct = self._changed_trigger
        self.set_changed_trigger(None)
        self._group.fill(top=True)
        self._buffs.fill(top=True)
        self._rotation.fill(top=True)
        self.set_changed_trigger(temp_ct)

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger
        self._group.set_changed_trigger(changed_trigger)
        self._buffs.set_changed_trigger(changed_trigger)
        self._rotation.set_changed_trigger(changed_trigger)

    def mod_mages(self, stype: int):
        self._rotation.mod_mages(stype)

    def settings_refresh(self, refresh):
        self._settings_refresh = refresh
        self._group.settings_refresh(refresh)
