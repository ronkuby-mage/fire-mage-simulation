import os
import json
import pickle
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
    QFileDialog,
    QLabel,
    QHeaderView,
    QGroupBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from ..utils.icon_edit import get_pixmap
from ..utils.guard_lineedit import GuardLineEdit
from ...items.items import CharInfo

class Group(QGroupBox):

    _MAX_MAGES = 9
    _CONFIG_KEYS = ["target", "sapp", "toep", "zhc", "mqg", "udc", "pi"]

    def __init__(self, config_list, mod_mages_signal):
        super().__init__()
        self._settings_refresh = None
        self.setTitle("Mages")
        self._changed_trigger = None
        self._config = config_list
        config = self._config.current().config()
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self._mages = []
        for idx in range(self._MAX_MAGES):
            mage = Mage(config_list, idx, self.mod_mages, self.mod_target)
            self._mages.append(mage)
            self.layout.addWidget(mage)
        self.setLayout(self.layout)
        self._mms = mod_mages_signal

    def fill(self, top=False):
        config = self._config.current().config()

        # best way to clear the group
        chars_info = [mage._char_info for mage in self._mages]
        self._mages = []
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for mage_number in range(config["configuration"]["num_mages"]):
            mage = Mage(self._config, mage_number, self.mod_mages, self.mod_target)
            mage._char_info = chars_info[mage_number]
            self._mages.append(mage)
            self.layout.addWidget(mage)
            mage.fill(top=top)
        for index in range(0, config["configuration"]["num_mages"] - 1):
            self._mages[index].set_resize(False, False)
        remove = False if config["configuration"]["num_mages"] == 1 else True
        add = False if config["configuration"]["num_mages"] == self._MAX_MAGES else True
        self._mages[mage_number].set_resize(add, remove)
        self.layout.addStretch()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger
        for mage in self._mages:
            mage.set_changed_trigger(changed_trigger)

    def mod_mages(self, stype: int):
        config = self._config.current().config()

        # modify group
        if stype:
            for stat in config["stats"]:
                config["stats"][stat].append(config["stats"][stat][-1])
            config["buffs"]["racial"].append(config["buffs"]["racial"][-1])
            index = config["configuration"]["num_mages"]
            for key in self._CONFIG_KEYS:
                if index - 1 in config["configuration"][key]:
                    config["configuration"][key].append(index)
            config["configuration"]["num_mages"] += 1

            mage = Mage(self._config, index, self.mod_mages, self.mod_target)
            mage._char_info = self._mages[index - 1]._char_info
            self._mages.append(mage)
            self.layout.addWidget(mage)
        else:
            for stat in config["stats"]:
                config["stats"][stat] = config["stats"][stat][:-1]
            config["buffs"]["racial"] = config["buffs"]["racial"][:-1]
            index = config["configuration"]["num_mages"] - 1
            for key in self._CONFIG_KEYS:
                if index in config["configuration"][key]:
                    config["configuration"][key].remove(index)
            config["configuration"]["num_mages"] -= 1

        self.fill(top=True)
        self.set_changed_trigger(self._changed_trigger)
        self.mod_target()

        # send to rotation
        self._mms(stype)

        if self._changed_trigger is not None:
            self._changed_trigger()
        if self._settings_refresh is not None:
            self._settings_refresh()

    def settings_refresh(self, refresh):
        self._settings_refresh = refresh

    def mod_target(self):
        config = self._config.current().config()
        if len(self._mages) < config["configuration"]["num_mages"]:
            return # still building
        to_enable = set(range(config["configuration"]["num_mages"]))
        if len(config["configuration"]["target"]) == 1:
            to_enable.remove(config["configuration"]["target"][0])
        for index in range(config["configuration"]["num_mages"]):
            self._mages[index].set_target_enabled(index in to_enable)

class Mage(QWidget):

    _STATS = ["sp", "hit %", "crit %", "int"]
    _STAT_MAX = [2000, 100, 100, 1000]
    _STATS_MAP = {"sp": "spell_power", "hit %": "hit_chance", "crit %": "crit_chance", "int": "intellect"}
    _STAT_TYPES = ["int", "percent", "percent", "int"]
    _STAT_DOC = "\n". join(["Specified spell power, crit, and hit are gear/enchant only and do not include buffs",
                            "or talents (10% in the hit field is cap).  Int is base value + gear."])
    _BOOLEANS = ["target"]
    _BUTTONS = ["sapp", "toep", "zhc", "mqg", "udc", "pi"]
    _TRINKETS = 4
    _BUTTON_ICONS = ["inv_trinket_naxxramas06.jpg",
                     "inv_misc_stonetablet_11.jpg", 
                     "inv_jewelry_necklace_13.jpg",
                     "spell_nature_wispheal.jpg",
                     "inv_chest_cloth_04.jpg",
                     "spell_holy_powerinfusion.jpg"]
    _BUTTON_TOOLTIP = ["The Restrained Essence of Sapphiron",
                       "Talisman of Ephemeral Power",
                       "Zandalarian Hero Charm",
                       "Mind Quickening Gem",
                       "Regalia of Undead Cleansing",
                       "Power Infusion"]
    _RACIALS = ["human", "undead", "gnome"]
    _SAVEFILE = "./data/items.dat"
    _CHAR_DIRECTORY = "./data/characters/"

    def __init__(self, config_list, index: int, mod_mages, mod_target):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
        self._index = index
        self._mod_target = mod_target

        # character import variables
        self._char_info = None
        if os.path.exists(self._SAVEFILE):
            with open(self._SAVEFILE, "rb") as fid:
                self._saved = pickle.load(fid)
        else:
            self._saved = {}
        layout = QHBoxLayout()
        layout.setContentsMargins(3, 5, 3, 5)
        layout.setSpacing(2)
        self._load_mage = QPushButton()
        self._load_mage.setCheckable(True)
        self._load_mage.setMinimumWidth(150)
        self._load_mage.clicked.connect(self.character)
        self._load_mage.setText(f"Mage {index + 1:d}")
        layout.addWidget(self._load_mage)

        self._stats = {}
        for stat, max_val in zip(self._STATS, self._STAT_MAX):
            label = QLabel(f"{stat:s}")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label)
            self._stats[stat] = GuardLineEdit("int", max_val, required=True)
            self._stats[stat].setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self._stats[stat].textChanged.connect(lambda state, x=stat: self.modify_stat(x))
            self._stats[stat].setToolTip(self._STAT_DOC)
            self._stats[stat].setMaximumWidth(35)
            layout.addWidget(self._stats[stat])

        self._buttons = {}
        for button, icon_fn, tool_tip in zip(self._BUTTONS, self._BUTTON_ICONS, self._BUTTON_TOOLTIP):
            self._buttons[button] = QPushButton(self)
            self._buttons[button].setStyleSheet("QPushButton { background-color: transparent; border: 0px }")
            self._buttons[button].setCheckable(True)
            self._buttons[button].setToolTip(tool_tip)
            icon = QIcon()
            icon.addPixmap(get_pixmap(icon_fn))
            self._buttons[button].setIcon(icon)
            self._buttons[button].setIconSize(QSize(25, 25))


            #style = "QPushButton:disabled{background-color: #000000;} "
            style = "QPushButton:checked:disabled{background-color: #FFFFFF;}"
            #style += "QPushButton:checked{font-size: 18px; color: rgb(255, 255, 255);}"
            self._buttons[button].setStyleSheet(style)


            self._buttons[button].clicked.connect(lambda state, x=button: self.modify_button(x))
            layout.addWidget(self._buttons[button])

        self._booleans = {}
        for boolean in self._BOOLEANS:
            layout.addWidget(QLabel(f"{boolean:s}"))
            self._booleans[boolean] = QCheckBox()
            self._booleans[boolean].stateChanged.connect(lambda state, x=boolean: self.modify_boolean(x))
            layout.addWidget(self._booleans[boolean])

        self._racial = QComboBox()
        self._racial.addItems(self._RACIALS)
        self._racial.currentIndexChanged.connect(self.modify_racial)
        layout.addWidget(self._racial)

        self._add_button = QPushButton("+", self)
        self._del_button = QPushButton("X", self)
        self._add_button.setMinimumWidth(20)
        self._del_button.setMinimumWidth(20)
        self._add_button.setMaximumWidth(30)
        self._del_button.setMaximumWidth(30)
        self._add_button.clicked.connect(lambda: mod_mages(1))
        self._del_button.clicked.connect(lambda: mod_mages(0))
        layout.addWidget(self._add_button)
        layout.addWidget(self._del_button)

        self.setLayout(layout)

    def fill(self, top=False):
        config = self._config.current().config()
        if self._char_info is not None:
            self.fill_char()
            self._load_mage.setChecked(True)
        for key, ctype in zip(self._stats, self._STAT_TYPES):
            value = config["stats"][self._STATS_MAP[key]][self._index]
            if ctype == "percent":
                sval = f"{100*value:.0f}"
            else:
                sval = str(value)
            self._stats[key].setText(sval)
            if top:
                self._stats[key].set_text(sval)

        for key in self._buttons:
            state = 1 if self._index in config["configuration"][key] else 0
            self._buttons[key].setChecked(state)
            icon_fn = self._BUTTON_ICONS[self._BUTTONS.index(key)]
            icon = QIcon()
            icon.addPixmap(get_pixmap(icon_fn, fade=not state))
            self._buttons[key].setIcon(icon)

        for key in self._booleans:
            state = 1 if self._index in config["configuration"][key] else 0
            self._booleans[key].setChecked(state)

        self._racial.setCurrentIndex(self._RACIALS.index(config["buffs"]["racial"][self._index]))


    def fill_char(self):
        config = self._config.current().config()
        
        filename = os.path.join(self._CHAR_DIRECTORY, f"{self._char_info:s}.json")
        char_info = CharInfo(filename, self._char_info, self._saved)
        self._load_mage.setText(self._char_info)

        values = [char_info.spd,
                  0.01*char_info.hit,
                  0.01*char_info.crt,
                  char_info.intellect]                
        for stat, value in zip(self._STATS_MAP.values(), values):
            config["stats"][stat][self._index] = value

        for tidx in range(self._TRINKETS):
            name = self._BUTTONS[tidx]
            atm = set(config["configuration"][name])
            if name in char_info.act:
                atm.add(self._index)
            else:
                atm.discard(self._index)
            config["configuration"][name] = list(atm)

        atm = set(config["configuration"]["udc"])
        if char_info.is_udc:
            atm.add(self._index)
        else:
            atm.discard(self._index)
            config["configuration"]["udc"] = list(atm)

        for stat in self._STATS:
            self._stats[stat].setEnabled(False)

        for tidx in range(self._TRINKETS + 1):
            name = self._BUTTONS[tidx]
            self._buttons[name].setEnabled(False)

    def character(self):
        if self._load_mage.isChecked():
            filename, filter = QFileDialog.getOpenFileName(parent=self,
                                                   caption="Open SixtyUpgrades Character Export",
                                                   directory=self._CHAR_DIRECTORY,
                                                   filter="*.json")
            if filename is not None and os.path.isfile(filename):
                with open(self._SAVEFILE, "wb") as fid:
                    pickle.dump(self._saved, fid)
                head, tail = os.path.split(filename)
                name, ext = os.path.splitext(tail)
                self._char_info = name
                self.fill()
            else:
                self._load_mage.setChecked(False)
        else:
            self._load_mage.setText(f"Mage {self._index + 1:d}")

            for stat in self._STATS:
                self._stats[stat].setEnabled(True)
            for tidx in range(self._TRINKETS + 1):
                name = self._BUTTONS[tidx]
                self._buttons[name].setEnabled(True)

    def set_resize(self, add: bool, remove: bool):
        self._add_button.setEnabled(add)
        self._del_button.setEnabled(remove)

    def modify_stat(self, name):
        config = self._config.current().config()
        stype = self._STAT_TYPES[self._STATS.index(name)]
        sval = self._stats[name].text()
        if not sval:
            return
        elif stype == "percent":
            value = 0.01*float(sval)
        else:
            value = int(sval)
        config["stats"][self._STATS_MAP[name]][self._index] = value
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_button(self, name):
        config = self._config.current().config()
        state = self._buttons[name].isChecked()
        icon_fn = self._BUTTON_ICONS[self._BUTTONS.index(name)]
        icon = QIcon()
        icon.addPixmap(get_pixmap(icon_fn, fade=not state))
        self._buttons[name].setIcon(icon)
        atm = set(config["configuration"][name])
        if state:
            atm.add(self._index)
        elif self._index in atm:
            atm.remove(self._index)
        config["configuration"][name] = list(atm)
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_boolean(self, name):
        config = self._config.current().config()
        state = self._booleans[name].isChecked()
        atm = set(config["configuration"][name])
        if state:
            atm.add(self._index)
        elif self._index in atm:
            atm.remove(self._index)
        config["configuration"][name] = list(atm)
        if self._changed_trigger is not None:
            self._changed_trigger()
        if name == "target":
            self._mod_target()
    
    def set_target_enabled(self, enabled: bool):
        self._booleans["target"].setEnabled(enabled)

    def modify_racial(self):
        config = self._config.current().config()
        racial = self._racial.currentText()
        config["buffs"]["racial"][self._index] = racial
        if self._changed_trigger is not None:
            self._changed_trigger()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger
