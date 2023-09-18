import json
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QWidget,
    QStackedWidget,
    QLabel
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt
from .character import Character
from ..sim.constants import Constant

class Scenario(QStackedWidget):

    def __init__(self, config_list):

        super().__init__()

        # future: need to change based on the selected config
        self._config = config_list.config(0)

        self._group = Group(self._config)
        self._buffs = Buffs(self._config)
        self._rotation = Rotation(self._config)

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

    def update(self):
        self._group.fill()
        self._buffs.fill()
        self._rotation.fill()

    def set_config(self, config):
        self._group.set_config(config)
        self._buffs.set_config(config)
        self._rotation.set_config(config)

class Buffs(QWidget):

    _BUFFS = {
        "world": [
            "rallying_cry_of_the_dragonslayer",
            "spirit_of_zandalar",
            "dire_maul_tribute",
            "songflower_serenade",
            "sayges_dark_fortune_of_damage"],
        "consumes": [
            "greater_arcane_elixir",
            "elixir_of_greater_firepower",
            "flask_of_supreme_power",
            "brilliant_wizard_oil",
            "blessed_wizard_oil",
            "very_berry_cream",
            "infallible_mind",
            "stormwind_gift_of_friendship",
            "runn_tum_tuber_surprise"],
        "raid": [
             "arcane_intellect",
             "blessing_of_kings",
             "improved_mark"]
        }
    _BOSSES = ["", "loatheb", "thaddius"]

    def __init__(self, initial_config):
        super().__init__()

        config = initial_config.config()

        self._buffs = {}
        layout = QHBoxLayout()
        for buff_type in self._BUFFS:
            column = QWidget()
            clayout = QVBoxLayout()
            for buff_name in self._BUFFS[buff_type]:
                mod_name = " ".join(buff_name.split("_"))
                row = QWidget()
                rlayout = QHBoxLayout()
                rlayout.addWidget(QLabel(f"{mod_name:s}"))
                self._buffs[buff_name] = QCheckBox()
                self._buffs[buff_name].stateChanged.connect(lambda state, x=buff_type, y=buff_name: self.modify_buff(x, y))
                rlayout.addWidget(self._buffs[buff_name])
                row.setLayout(rlayout)
                clayout.addWidget(row)
            if buff_type == "raid":
                row = QWidget()
                rlayout = QHBoxLayout()
                rlayout.addWidget(QLabel(f"boss"))
                self._buffs["boss"] = QComboBox()
                self._buffs["boss"].addItems(self._BOSSES)
                self._buffs["boss"].currentIndexChanged.connect(self.modify_boss)
                rlayout.addWidget(self._buffs["boss"])
                row.setLayout(rlayout)
                clayout.addWidget(row)

            column.setLayout(clayout)
            layout.addWidget(column)
        self.setLayout(layout)
        self.set_config(initial_config)
        self.fill()

    def set_config(self, config):
        self._config = config

    def fill(self):
        config = self._config.config()

        for buff_type in self._BUFFS:
            for buff_name in self._BUFFS[buff_type]:
                state = 1 if buff_name in config["buffs"][buff_type] else 0
                self._buffs[buff_name].setChecked(state)
        self._buffs["boss"].setCurrentIndex(self._BOSSES.index(config["buffs"]["boss"]))

    def modify_buff(self, buff_type, buff_name):
        config = self._config.config()
        state = self._buffs[buff_name].isChecked()
        atm = set(config["buffs"][buff_type])
        if state:
            atm.add(buff_name)
        elif buff_name in atm:
            atm.remove(buff_name)
        config["buffs"][buff_type] = list(atm)

    def modify_boss(self):
        config = self._config.config()
        boss = self._buffs["boss"].currentText()
        config["buffs"]["boss"] = boss

class Rotation(QWidget):

    _SPELLS = list(Constant(0.0)._DECIDE.keys())
    _MAX_SPELLS = 12

    def __init__(self, initial_config):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Opening"))
        table = QTableWidget(self._MAX_SPELLS, 1, self)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        self._initial = []
        for row in range(table.rowCount()):
            combo = QComboBox()
            combo.addItems(self._SPELLS)
            self._initial.append(combo)
            table.setCellWidget(row, 0, combo)
        layout.addWidget(table)
        self.setLayout(layout)

        self.set_config(initial_config)
        self.fill()

    def set_config(self, config):
        self._config = config

    def fill(self):
        config = self._config.config()
        for idx, spell in enumerate(config["rotation"]["initial"]["other"]):
            self._initial[idx].setCurrentIndex(self._SPELLS.index(spell))

        for jdx in range(idx, self._MAX_SPELLS):
            self._initial[jdx].addItem("")
            if jdx != idx:
                self._initial[jdx].setCurrentText("")
                if jdx != idx + 1:
                    self._initial[jdx].setEnabled(False)

class Group(QWidget):

    def __init__(self, initial_config):
        super().__init__()
        layout = QVBoxLayout()
        self._mages = []
        config = initial_config.config()
        for idx in range(config["configuration"]["num_mages"]):
            mage = Mage(idx)
            mage.set_config(initial_config)
            self._mages.append(mage)
            layout.addWidget(mage)
        self.setLayout(layout)
        self.fill()

    def fill(self):
        for mage in self._mages:
            mage.fill()

    def set_config(self, config):
        for mage in self._mages:
            mage.set_config(config)

class Mage(QWidget):

    _STATS = ["sp", "hit %", "crit %", "int"]
    _STATS_MAP = {"sp": "spell_power", "hit %": "hit_chance", "crit %": "crit_chance", "int": "intellect"}
    _STAT_TYPES = ["int", "float", "float", "int"]
    _BOOLEANS = ["sapp", "toep", "zhc", "mqg", "udc", "pi", "target"]
    _RACIALS = ["human", "undead", "gnome"]

    def __init__(self, index):
        super().__init__()
        self._index = index
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Mage {index + 1:d}"))

        self._stats = {}
        for stat, val in zip(self._STATS, self._STAT_TYPES):
            label = QLabel(f"{stat:s}")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label)
            self._stats[stat] = QLineEdit()
            self._stats[stat].textChanged.connect(lambda state, x=stat: self.modify_stat(x))
            validator = QIntValidator() if val == "int" else QDoubleValidator()
            validator.setBottom(0.0 if val == "float" else 0)
            self._stats[stat].setValidator(validator)
            self._stats[stat].setMaximumWidth(40)
            layout.addWidget(self._stats[stat])

        self._booleans = {}
        for boolean in self._BOOLEANS:
            layout.addWidget(QLabel(f"{boolean:s}"))
            self._booleans[boolean] = QCheckBox()
            self._booleans[boolean].stateChanged.connect(lambda state, x=boolean: self.modify_boolean(x))
            layout.addWidget(self._booleans[boolean])

        layout.addWidget(QLabel(f"racial"))
        self._racial = QComboBox()
        self._racial.addItems(self._RACIALS)
        self._racial.currentIndexChanged.connect(self.modify_racial)
        layout.addWidget(self._racial)
        self.setLayout(layout)

    def set_config(self, config):
        self._config = config

    def fill(self):
        config = self._config.config()
        for key in self._stats:
            value = config["stats"][self._STATS_MAP[key]][self._index]
            if "%" in key:
                sval = f"{100*value:.1f}"
            else:
                sval = str(value)
            self._stats[key].setText(sval)

        for key in self._booleans:
            state = 1 if self._index in config["configuration"][key] else 0
            self._booleans[key].setChecked(state)

        self._racial.setCurrentIndex(self._RACIALS.index(config["buffs"]["racial"][self._index]))

    def modify_stat(self, name):
        config = self._config.config()
        stype = self._STAT_TYPES[self._STATS.index(name)]
        sval = self._stats[name].text()
        if not sval:
            return
        elif stype == "float":
            factor = 0.01 if "%" in name else 1.0
            value = factor*float(sval)
        else:
            value = int(sval)
        config["stats"][self._STATS_MAP[name]][self._index] = value

    def modify_boolean(self, name):
        config = self._config.config()
        state = self._booleans[name].isChecked()
        atm = set(config["configuration"][name])
        if state:
            atm.add(self._index)
        elif self._index in atm:
            atm.remove(self._index)
        config["configuration"][name] = list(atm)

    def modify_racial(self):
        config = self._config.config()
        racial = self._racial.currentText()
        config["buffs"]["racial"][self._index] = racial
