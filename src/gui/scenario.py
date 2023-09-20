import json
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QWidget,
    QStackedWidget,
    QLabel,
    QHeaderView
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from .icon_edit import get_pixmap
from .character import Character
from ..sim.constants import Constant

class Scenario(QStackedWidget):

    def __init__(self, config_list):

        super().__init__()

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

    def update(self):
        self._group.fill()
        self._buffs.fill()
        self._rotation.fill()

    def set_changed_trigger(self, changed_trigger):
        self._group.set_changed_trigger(changed_trigger)
        self._buffs.set_changed_trigger(changed_trigger)
        self._rotation.set_changed_trigger(changed_trigger)

    def mod_mages(self, stype: int):
        self._rotation.mod_mages(stype)

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

    def __init__(self, config_list):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
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
        #self.fill()

    def fill(self):
        config = self._config.current().config()

        for buff_type in self._BUFFS:
            for buff_name in self._BUFFS[buff_type]:
                state = 1 if buff_name in config["buffs"][buff_type] else 0
                self._buffs[buff_name].setChecked(state)
        self._buffs["boss"].setCurrentIndex(self._BOSSES.index(config["buffs"]["boss"]))

    def modify_buff(self, buff_type, buff_name):
        config = self._config.current().config()
        state = self._buffs[buff_name].isChecked()
        atm = set(config["buffs"][buff_type])
        if state:
            atm.add(buff_name)
        elif buff_name in atm:
            atm.remove(buff_name)
        config["buffs"][buff_type] = list(atm)
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_boss(self):
        config = self._config.current().config()
        boss = self._buffs["boss"].currentText()
        config["buffs"]["boss"] = boss
        if self._changed_trigger is not None:
            self._changed_trigger()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger

class Rotation(QWidget):

    _SPELLS = list(Constant(0.0)._DECIDE.keys())
    _MAX_SPELLS = 12
    _REAL_SPELLS = 3
    _MAX_SPECIALS = 3
    _SPECIALS = ["maintain_scorch", "scorch", "scorch_wep", "cobimf"]
    _SPECIAL_DOC = "maintain_scorch: Cast Scorch if there are less than 5 seconds left on the debuff or it is not fully stacked\n" +\
        "scorch: Also cast Scorch if ignite is fully stacked and there are no cooldowns going (Combustion/trinket)\n" +\
        "scorch_wep: Cast Scorch even with remaining cooldowns\n" +\
        "cobimf: Scorch under same conditions as scorch_wep, but if ignite has <= 2 seconds remaining cast Fire Blast"

    def __init__(self, config_list):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
        layout = QVBoxLayout()

        # initial rotation
        layout.addWidget(QLabel("Opening"))
        table = QTableWidget(self._MAX_SPELLS, 2, self)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        self._initial = []
        for row in range(table.rowCount()):
            table.setCellWidget(row, 0, QLabel(f"{row + 1:d}"))
            combo = QComboBox()
            combo.addItems(self._SPELLS)
            combo.currentIndexChanged.connect(lambda state, x=row: self.modify_initial(x))
            self._initial.append(combo)
            table.setCellWidget(row, 1, combo)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table, stretch=4)
        self._initial_table = table

        # default
        default = QWidget()
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel(f"Default:"))
        combo = QComboBox()
        combo.addItems(self._SPELLS[:self._REAL_SPELLS])
        combo.currentIndexChanged.connect(self.modify_default)
        default_layout.addWidget(combo)
        default.setLayout(default_layout)
        layout.addWidget(default)
        self._default = combo

        # specials
        self._special = []
        for idx in range(self._MAX_SPECIALS):
            this_special = {}
            table = QTableWidget(3, 2, self)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()
            table.setCellWidget(0, 0, (QLabel(f"Special {idx + 1:d}")))
            table.setCellWidget(1, 0, (QLabel(f"Apply to")))
            table.setCellWidget(2, 0, (QLabel(f"Parameter")))

            combo = QComboBox()
            combo.addItems(self._SPECIALS)
            combo.currentIndexChanged.connect(lambda state, x=idx: self.modify_special(x, "type"))
            this_special["type"] = combo
            table.setCellWidget(0, 1, combo)

            mage = QComboBox()
            mage.currentIndexChanged.connect(lambda state, x=idx: self.modify_special(x, "mage"))
            this_special["mage"] = mage
            table.setCellWidget(1, 1, mage)

            param = QLineEdit()
            param.textChanged.connect(lambda state, x=idx: self.modify_special(x, "param"))
            validator = QDoubleValidator()
            validator.setBottom(0.0)
            param.setValidator(validator)
            this_special["param"] = param
            table.setCellWidget(2, 1, param)
            
            self._special.append(this_special)

            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            layout.addWidget(table, stretch=1)

        self.setLayout(layout)

    def fill(self):
        config = self._config.current().config()
        for idx, spell in enumerate(config["rotation"]["initial"]["other"]):
            self._initial[idx].setCurrentIndex(self._SPELLS.index(spell))

        for jdx in range(idx, self._MAX_SPELLS):
            if jdx:
                self._initial[jdx].addItem("")
            if jdx != idx:
                self._initial_table.setCellWidget(jdx, 0, QLabel(f""))
                self._initial[jdx].setCurrentText("")
                if jdx != idx + 1:
                    self._initial[jdx].setEnabled(False)
        
        spell = config["rotation"]["continuing"]["default"]
        self._default.setCurrentIndex(self._SPELLS.index(spell))

        specials = 0
        for key, val in config["rotation"]["continuing"].items():
            if "special" in key:
                index = int(key.split("special")[1]) - 1
                if specials == self._MAX_SPECIALS:
                    continue
                stype = val["value"]
                self._special[index]["type"].setCurrentIndex(self._SPECIALS.index(stype))
                slot = val["slot"][0]
                self._special[index]["mage"].clear()
                num_mages = config["configuration"]["num_mages"]
                self._special[index]["mage"].addItems([f"mage {m + 1:d}" for m in range(num_mages)])
                self._special[index]["mage"].setCurrentText(f"mage {slot + 1:d}")
                if stype == "cobimf":
                    param_val = val["cast_point_remain"]
                    self._special[index]["param"].setText(str(param_val))
                specials += 1
        if specials > 1:
            self._special[specials - 1]["type"].addItem("")

        for sidx in range(specials, self._MAX_SPECIALS):
            self._special[sidx]["type"].addItem("")
            self._special[sidx]["type"].setCurrentText("")
            if sidx > specials:
                self._special[sidx]["type"].setEnabled(False)
            self._special[sidx]["mage"].setEnabled(False)
            self._special[sidx]["param"].setEnabled(False)

    def modify_initial(self, row):
        config = self._config.current().config()
        spell = self._initial[row].currentText()
        if not spell:
            if row < len(config["rotation"]["initial"]["other"]):
                config["rotation"]["initial"]["other"].pop()
                self._initial_table.setCellWidget(row, 0, QLabel(f""))
                if row > 1:
                    self._initial[row - 1].addItem("")
                if row < self._MAX_SPELLS - 1:
                    self._initial[row + 1].setEnabled(False)
        elif row >= len(config["rotation"]["initial"]["other"]):
            config["rotation"]["initial"]["other"].append(spell)
            self._initial_table.setCellWidget(row, 0, QLabel(f"{row + 1:d}"))
            if row > 1:
                self._initial[row - 1].removeItem(len(self._SPELLS))
            if row < self._MAX_SPELLS - 1:
                self._initial[row + 1].setEnabled(True)
        else:
            config["rotation"]["initial"]["other"][row] = spell
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_default(self):
        config = self._config.current().config()
        spell = self._default.currentText()
        config["rotation"]["continuing"]["default"] = spell
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_special(self, row, field):
        config = self._config.current().config()
        if field == "type":
            spell = self._special[row]["type"].currentText()
            if f"special{row + 1:d}" in config["rotation"]["continuing"]: # exists
                if not spell: # removing
                    self._special[row]["mage"].setEnabled(False)
                    self._special[row]["mage"].clear()
                    self._special[row]["param"].setEnabled(False)
                    self._special[row]["param"].setText("")
                    config["rotation"]["continuing"].pop(f"special{row + 1:d}")
                    if row > 1:
                        self._special[row - 1]["type"].addItem("")
                else: # modifying
                    if config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] != spell:
                        if spell == "cobimf":
                            self._special[row]["param"].setEnabled(True)
                            self._special[row]["param"].setText("0.5") # bad hard-coded value
                            #config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = 0.5
                        elif config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] == "cobimf":
                            self._special[row]["param"].setEnabled(False)
                            self._special[row]["param"].setText("")
                            config["rotation"]["continuing"][f"special{row + 1:d}"].pop("cast_point_remain")
                    config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] = spell
            else:
                if spell:
                    config["rotation"]["continuing"][f"special{row + 1:d}"] = {"value": spell}
                    self._special[row]["mage"].setEnabled(True)
                    num_mages = config["configuration"]["num_mages"]
                    self._special[row]["mage"].addItems([f"mage {m + 1:d}" for m in range(num_mages)])
                    self._special[row]["mage"].setCurrentText(f"mage 1")
                    config["rotation"]["continuing"][f"special{row + 1:d}"]["slot"] = [0] # more hard code
                    if spell == "cobimf":
                        self._special[row]["param"].setEnabled(True)
                        self._special[row]["param"].setText("0.5") # bad hard-coded value
                        #config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = 0.5
                    if row > 0:
                        self._special[row - 1]["type"].removeItem(len(self._SPECIALS))
                    if row + 1 < self._MAX_SPECIALS:
                        self._special[row + 1]["type"].setEnabled(True)
        elif field == "mage":
            text = self._special[row]["mage"].currentText()
            if len(text):
                value = int(text.split("mage")[1]) - 1
                config["rotation"]["continuing"][f"special{row + 1:d}"]["slot"] = [value]
        elif field == "param":
            value = self._special[row]["param"].text()
            if len(value):
                config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = float(value)
        if self._changed_trigger is not None:
            self._changed_trigger()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger

    def mod_mages(self, stype: int):
        pass

class Group(QWidget):

    _MAX_MAGES = 9
    _CONFIG_KEYS = ["target", "sapp", "toep", "zhc", "mqg", "udc", "pi"]

    def __init__(self, config_list, mod_mages_signal):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
        config = self._config.current().config()
        self.layout = QVBoxLayout()
        self._mages = []
        for idx in range(self._MAX_MAGES):
            mage = Mage(config_list, idx, self.mod_mages)
            self._mages.append(mage)
            self.layout.addWidget(mage)
        self.setLayout(self.layout)
        self._mms = mod_mages_signal

    def fill(self):
        config = self._config.current().config()
        # best way to clear the group
        self._mages = []
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for mage_number in range(config["configuration"]["num_mages"]):
            mage = Mage(self._config, mage_number, self.mod_mages)
            self._mages.append(mage)
            self.layout.addWidget(mage)
            mage.fill()
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

            mage = Mage(self._config, index, self.mod_mages)
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
        self.fill()

        # send to rotation
        self._mms(stype)

        if self._changed_trigger is not None:
            self._changed_trigger()

class Mage(QWidget):

    _STATS = ["sp", "hit %", "crit %", "int"]
    _STATS_MAP = {"sp": "spell_power", "hit %": "hit_chance", "crit %": "crit_chance", "int": "intellect"}
    _STAT_TYPES = ["int", "float", "float", "int"]
    _BOOLEANS = ["target"]
    _BUTTONS = ["sapp", "toep", "zhc", "mqg", "udc", "pi"]
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

    def __init__(self, config_list, index, mod_mages):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
        self._index = index
        layout = QHBoxLayout()
        layout.addWidget(QLabel(f"Mage {index + 1:d}"))

        self._stats = {}
        for stat, val in zip(self._STATS, self._STAT_TYPES):
            label = QLabel(f"{stat:s}")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label)
            self._stats[stat] = QLineEdit()
            self._stats[stat].setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self._stats[stat].textChanged.connect(lambda state, x=stat: self.modify_stat(x))
            validator = QIntValidator() if val == "int" else QDoubleValidator()
            validator.setBottom(0.0 if val == "float" else 0)
            self._stats[stat].setValidator(validator)
            self._stats[stat].setMaximumWidth(40)
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
            self._buttons[button].clicked.connect(lambda state, x=button: self.modify_button(x))
            #self._buttons[button].toggled.connect(lambda state, x=button: self.modify_button(x))
            layout.addWidget(self._buttons[button])


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

    def fill(self):
        config = self._config.current().config()
        for key in self._stats:
            value = config["stats"][self._STATS_MAP[key]][self._index]
            if "%" in key:
                sval = f"{100*value:.1f}"
            else:
                sval = str(value)
            self._stats[key].setText(sval)

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

    def set_resize(self, add: bool, remove: bool):
        self._add_button.setEnabled(add)
        self._del_button.setEnabled(remove)

    def modify_stat(self, name):
        config = self._config.current().config()
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

    def modify_racial(self):
        config = self._config.current().config()
        racial = self._racial.currentText()
        config["buffs"]["racial"][self._index] = racial
        if self._changed_trigger is not None:
            self._changed_trigger()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger
