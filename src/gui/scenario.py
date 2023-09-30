import json
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
    QGroupBox
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon
from PyQt5.QtCore import Qt, QSize
from copy import deepcopy
from .icon_edit import get_pixmap
from .character import Character
from ..sim.constants import Constant

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
        self._group.fill()
        self._buffs.fill()
        self._rotation.fill()
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


class Buffs(QGroupBox):
    _VALUES = ["name",
               "row",
               "col",
               "tooltip",
               "icon_fn",
               "enabled"]

    _BUFFS = {
        "world": [
            ("rallying_cry_of_the_dragonslayer", 0, 0, "Ony", "inv_misc_head_dragon_01.jpg", True),
            ("spirit_of_zandalar", 0, 1, "Heart", "ability_creature_poison_05.jpg", True),
            ("dire_maul_tribute", 1, 0, "DMT", "spell_holy_lesserheal02.jpg", True),
            ("songflower_serenade", 1, 1, "Songflower", "spell_holy_mindvision.jpg", True),
            ("sayges_dark_fortune_of_damage", 2, 0, "DMF", "inv_misc_orb_02.jpg", True),
            ("traces_of_silithus", 2, 1, "Silithus", "spell_nature_timestop.jpg", False)],
        "consumes": [
            ("greater_arcane_elixir", 0, 0, "GAE", "inv_potion_25.jpg", True),
            ("elixir_of_greater_firepower", 0, 1, "Greater Firepower", "inv_potion_60.jpg", True),
            ("flask_of_supreme_power", 0, 2, "FoSP", "inv_potion_41.jpg", True),
            ("brilliant_wizard_oil", 1, 0, "Brilliant Oil", "inv_potion_105.jpg", True),
            ("blessed_wizard_oil", 1, 1, "Blessed Oil", "inv_potion_26.jpg", True),
            ("very_berry_cream", 1, 2, "VDay Candy", "inv_valentineschocolate02.jpg", True),
            ("infallible_mind", 2, 0, "BL Int", "spell_ice_lament.jpg", True),
            ("stormwind_gift_of_friendship", 2, 1, "VDay Int", "inv_misc_gift_03.jpg", True),
            ("runn_tum_tuber_surprise", 2, 2, "Tuber", "inv_misc_food_63.jpg", True)],
        "raid": [
             ("arcane_intellect", 0, 0, "Int", "spell_holy_magicalsentry.jpg", True),
             ("blessing_of_kings", 1, 0, "BoK", "spell_magic_greaterblessingofkings.jpg", True),
             ("improved_mark", 2, 0, "Mark", "spell_nature_regeneration.jpg", True)]
        }   
    _BOSSES = ["", "loatheb", "thaddius"]
    _DRAGONLING_DEFAULT = 30.0
    _DRAGONLING_ICON_FN = "spell_fire_fireball.jpg"
    _NIGHTFALL_DEFAULT = 2.55
    _NIGHTFALL_ICON_FN = "spell_holy_elunesgrace.jpg"
    _MAX_NIGHTFALL = 5

    def __init__(self, config_list):
        super().__init__()
        self.setTitle("Buffs")
        self._changed_trigger = None
        self._config = config_list
        self._buffs = {}

        layout = QHBoxLayout()

        misc = QGroupBox("Misc")
        misc_layout = QGridLayout()
        misc_layout.setSpacing(0)
        misc_layout.addWidget(QLabel(f"boss"), 0, 1)
        self._buffs["boss"] = QComboBox()
        self._buffs["boss"].addItems(self._BOSSES)
        self._buffs["boss"].currentIndexChanged.connect(self.modify_boss)
        misc_layout.addWidget(self._buffs["boss"], 0, 2)
        self._buffs["dragonling"] = QPushButton(self)
        self._buffs["dragonling"].setStyleSheet("QPushButton { background-color: transparent; border: 0px }")
        self._buffs["dragonling"].setCheckable(True)
        self._buffs["dragonling"].setToolTip("Arcanite Dragonling")
        icon = QIcon()
        icon.addPixmap(get_pixmap(self._DRAGONLING_ICON_FN))
        self._buffs["dragonling"].setIcon(icon)
        self._buffs["dragonling"].setIconSize(QSize(25, 25))
        misc_layout.addWidget(self._buffs["dragonling"], 1, 0)
        misc_layout.addWidget(QLabel(f"Dragonling | Stack Time"), 1, 1)
        self._buffs["dragonling_time"] = QLineEdit()
        validator = QDoubleValidator()
        validator.setBottom(0.0)
        self._buffs["dragonling_time"].setValidator(validator)
        self._buffs["dragonling_time"].textChanged.connect(self.time_dragon)
        misc_layout.addWidget(self._buffs["dragonling_time"], 1, 2)

        self._buffs["nightfall"] = []
        self._buffs["nightfall_timer"] = []
        for index in range(self._MAX_NIGHTFALL):
            nightfall = QPushButton(self)
            nightfall.setStyleSheet("QPushButton { background-color: transparent; border: 0px }")
            nightfall.setCheckable(True)
            nightfall.setToolTip("Nightfall")
            icon = QIcon()
            icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN))
            nightfall.setIcon(icon)
            nightfall.setIconSize(QSize(25, 25))
            misc_layout.addWidget(nightfall, index + 2, 0)
            self._buffs["nightfall"].append(nightfall)
            misc_layout.addWidget(QLabel(f"Swing Timer {index + 1:d}"), index + 2, 1)
            swing = QLineEdit()
            validator = QDoubleValidator()
            validator.setBottom(0.0)
            swing.setValidator(validator)
            swing.textChanged.connect(lambda state, x=index: self.timer_nightfall(x))
            misc_layout.addWidget(swing, index + 2, 2)
            self._buffs["nightfall_timer"].append(swing)
        misc.setLayout(misc_layout)
        layout.addWidget(misc)

        layout.addStretch()
        for buff_type in self._BUFFS:
            grid = QGroupBox(buff_type.capitalize())
            grid_layout = QGridLayout()
            grid_layout.setSpacing(0)
            for index, vals in enumerate(self._BUFFS[buff_type]):
                name = vals[self._VALUES.index("name")]
                tooltip = vals[self._VALUES.index("tooltip")]
                icon_fn = vals[self._VALUES.index("icon_fn")]
                row = vals[self._VALUES.index("row")]
                col = vals[self._VALUES.index("col")]

                self._buffs[name] = QPushButton(self)
                self._buffs[name].setStyleSheet("QPushButton { background-color: transparent; border: 0px }")
                self._buffs[name].setCheckable(True)
                self._buffs[name].setToolTip(tooltip)
                icon = QIcon()
                icon.addPixmap(get_pixmap(icon_fn))
                self._buffs[name].setIcon(icon)
                self._buffs[name].setIconSize(QSize(40, 40))
                self._buffs[name].clicked.connect(lambda state, x=buff_type, y=index: self.modify_button(x, y))
                grid_layout.addWidget(self._buffs[name], row, col)
            grid.setLayout(grid_layout)
            layout.addWidget(grid)
            layout.addStretch()

        self.setLayout(layout)

    def fill(self):
        config = self._config.current().config()
        self._buffs["boss"].setCurrentIndex(self._BOSSES.index(config["buffs"]["boss"]))
        clear_dragonling = False
        clear_nightfall = False
        if "proc" in config["buffs"]:
            if "dragonling" in config["buffs"]["proc"]:
                icon = QIcon()
                icon.addPixmap(get_pixmap(self._DRAGONLING_ICON_FN, fade=False))
                self._buffs["dragonling"].setIcon(icon)
                self._buffs["dragonling_time"].setText(str(config["buffs"]["proc"]["dragonling"]))
            else:
                clear_dragonling = True
            if "nightfall" in config["buffs"]["proc"]:
                for index, val in enumerate(config["buffs"]["proc"]["nightfall"]):
                    icon = QIcon()
                    icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=False))
                    self._buffs["nightfall"][index].setIcon(icon)
                    self._buffs["nightfall"][index].setChecked(True)
                    self._buffs["nightfall_timer"][index].setText(str(val))
                    self._buffs["nightfall_timer"][index].setEnabled(False)
                self._buffs["nightfall_timer"][index].setEnabled(True)
                for index2 in range(index + 1, self._MAX_NIGHTFALL):
                    icon = QIcon()
                    icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=True))
                    self._buffs["nightfall"][index2].setIcon(icon)
                    self._buffs["nightfall_timer"][index2].setText("")
                    enabled = index2 == index + 1
                    self._buffs["nightfall_timer"][index2].setEnabled(enabled)
            else:
                clear_nightfall = True
        else:
            clear_nightfall = True
            clear_dragonling = True
        if clear_dragonling:
            icon = QIcon()
            icon.addPixmap(get_pixmap(self._DRAGONLING_ICON_FN, fade=True))
            self._buffs["dragonling"].setIcon(icon)
            self._buffs["dragonling_time"].setText("")
        if clear_nightfall:
            for index in range(self._MAX_NIGHTFALL):
                icon = QIcon()
                icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=True))
                self._buffs["nightfall"][index].setIcon(icon)
                enabled = True if not index else False
                self._buffs["nightfall_timer"][index].setEnabled(enabled)
                self._buffs["nightfall_timer"][index].setText("")

        for btype in self._BUFFS:
            for vals in self._BUFFS[btype]:
                name = vals[self._VALUES.index("name")]
                icon_fn = vals[self._VALUES.index("icon_fn")]
                enabled = vals[self._VALUES.index("enabled")]

                state = 1 if name in config["buffs"][btype] else 0
                self._buffs[name].setChecked(state)
                icon = QIcon()
                icon.addPixmap(get_pixmap(icon_fn, fade=not state))
                self._buffs[name].setIcon(icon)
                self._buffs[name].setEnabled(enabled)

    def modify_boss(self):
        config = self._config.current().config()
        boss = self._buffs["boss"].currentText()
        config["buffs"]["boss"] = boss
        if self._changed_trigger is not None:
            self._changed_trigger()
       
    def time_dragon(self):
        config = self._config.current().config()
        value = self._buffs["dragonling_time"].text()
        icon = QIcon()
        if value and value != ".":
            if "proc" not in config["buffs"]:
                config["buffs"]["proc"] = {"dragonling": float(value)}
            else:
                config["buffs"]["proc"]["dragonling"] = float(value)
            icon.addPixmap(get_pixmap(self._DRAGONLING_ICON_FN, fade=False))
        else:
            icon.addPixmap(get_pixmap(self._DRAGONLING_ICON_FN, fade=True))
            if "proc" in config["buffs"]:
                if "dragonling" in config["buffs"]["proc"]:
                    config["buffs"]["proc"].pop("dragonling")
                if not config["buffs"]["proc"]:
                    config["buffs"].pop("proc")
        self._buffs["dragonling"].setIcon(icon)

        if self._changed_trigger is not None:
            self._changed_trigger()

       
    def timer_nightfall(self, index):
        config = self._config.current().config()
        value = self._buffs["nightfall_timer"][index].text()
        icon = QIcon()
        icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=not value))
        self._buffs["nightfall"][index].setIcon(icon)
        if value and value != ".":
            if "proc" not in config["buffs"]:
                config["buffs"]["proc"] = {"nightfall": [float(value)]}
            elif "nightfall" not in config["buffs"]["proc"]:
                config["buffs"]["proc"]["nightfall"] = [float(value)]
            else:
                if index >= len(config["buffs"]["proc"]["nightfall"]):
                    config["buffs"]["proc"]["nightfall"].append(float(value))
                    self._buffs["nightfall_timer"][index - 1].setEnabled(False)
                else:
                    config["buffs"]["proc"]["nightfall"][index] = float(value)
            if index + 1 < self._MAX_NIGHTFALL:
                self._buffs["nightfall_timer"][index + 1].setEnabled(True)
        elif value != ".":
            if "proc" in config["buffs"]:
                if "nightfall" in config["buffs"]["proc"]:
                    config["buffs"]["proc"]["nightfall"].pop()
                    if not config["buffs"]["proc"]["nightfall"]:
                        config["buffs"]["proc"].pop("nightfall")
                        if not config["buffs"]["proc"]:
                            config["buffs"].pop("proc")
            if index > 0:
                self._buffs["nightfall_timer"][index - 1].setEnabled(True)
            if index + 1 < self._MAX_NIGHTFALL:
                self._buffs["nightfall_timer"][index + 1].setEnabled(False)
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_button(self, btype, index):
        config = self._config.current().config()

        vals = self._BUFFS[btype][index]
        name = vals[self._VALUES.index("name")]
        icon_fn = vals[self._VALUES.index("icon_fn")]

        state = self._buffs[name].isChecked()
        icon = QIcon()
        icon.addPixmap(get_pixmap(icon_fn, fade=not state))
        self._buffs[name].setIcon(icon)
        atm = config["buffs"][btype]
        if state:
            atm.append(name)
        elif name in atm:
            atm.remove(name)
        config["buffs"][btype] = atm
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
    _SPECIAL_DOC = "\n".join([
        "maintain_scorch: Cast Scorch if there are less than 5 seconds left on the debuff or it is not fully stacked",
        "scorch: Also cast Scorch if ignite is fully stacked and there are no cooldowns going (Combustion/trinket)",
        "scorch_wep: Cast Scorch even with remaining cooldowns",
        "cobimf: Scorch under same conditions as scorch_wep, but if ignite has <= 2 seconds remaining cast Fire Blast",
        "  Here 'Parameter' is the response time of the caster -- even if ignite is refreshed within the response time,",
        "  the mage will still cast Fire Blast.  If ignite is refreshed after the response time but before Fire Blast",
        "  is cast, they will switch back to Scorch"])

    def __init__(self, config_list):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
        self._lock = False
        layout = QVBoxLayout()

        # initial rotation
        layout.addWidget(QLabel("Rotation"))
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
            table.setToolTip(self._SPECIAL_DOC)
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

    def lock(self):
        self._lock = True

    def unlock(self):
        self._lock = False

    def fill(self):
        config = self._config.current().config()
        self.lock()

        for idx in range(self._MAX_SPELLS):
            empty = [jdx for jdx in range(self._initial[idx].count()) if self._initial[idx].itemText(jdx) == ""]
            if len(empty):
                self._initial[idx].removeItem(empty[0])

        for idx, spell in enumerate(config["rotation"]["initial"]["other"]):
            self._initial_table.setCellWidget(idx, 0, QLabel(f"{idx + 1:d}"))
            self._initial[idx].setCurrentIndex(self._SPELLS.index(spell))
            self._initial[idx].setEnabled(True)

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

        # and now the annoyingly complex specials
        for idx in range(self._MAX_SPECIALS):
            empty = [jdx for jdx in range(self._special[idx]["type"].count()) if self._special[idx]["type"].itemText(jdx) == ""]
            if len(empty):
                self._special[idx]["type"].removeItem(empty[0])

        num_mages = config["configuration"]["num_mages"]
        slots_taken = []
        for key, val in config["rotation"]["continuing"].items():
            if "special" in key:
                slots_taken.append(val["slot"][0])
        resort = True if len(slots_taken) > num_mages or any([slot >= num_mages for slot in slots_taken]) else False
        if resort:
            to_remove = []
            specials = 0
            for key, val in config["rotation"]["continuing"].items():
                if "special" in key:
                    index = int(key.split("special")[1]) - 1
                    if index >= num_mages:
                        to_remove.append(key)
                    specials += 1
            for key in to_remove:
                config["rotation"]["continuing"].pop(key)
            slots_taken = list(range(min([num_mages, specials])))
        specials = 0
        for key, val in config["rotation"]["continuing"].items():
            if "special" in key:
                index = int(key.split("special")[1]) - 1
                stype = val["value"]
                self._special[index]["type"].setCurrentIndex(self._SPECIALS.index(stype))
                if resort:
                    slot = specials
                else:
                    slot = val["slot"][0]
                self._special[index]["mage"].clear()
                tst = deepcopy(slots_taken)
                tst.remove(slot)
                self._special[index]["mage"].addItems([f"mage {m + 1:d}" for m in range(num_mages) if m not in tst])
                self._special[index]["mage"].setCurrentText(f"mage {slot + 1:d}")
                self._special[index]["mage"].setEnabled(True)
                if stype == "cobimf":
                    param_val = val["cast_point_remain"]
                    self._special[index]["param"].setText(str(param_val))
                    self._special[index]["param"].setEnabled(True)
                else:
                    self._special[index]["param"].setText("")
                    self._special[index]["param"].setEnabled(False)
                specials += 1
        if specials:
            self._special[specials - 1]["type"].addItem("")

        for sidx in range(specials, self._MAX_SPECIALS):
            self._special[sidx]["type"].addItem("")
            self._special[sidx]["type"].setCurrentText("")
            self._special[sidx]["type"].setEnabled(sidx == specials and sidx < num_mages)
            self._special[sidx]["mage"].setEnabled(False)
            self._special[sidx]["mage"].clear()
            self._special[sidx]["param"].setEnabled(False)
            self._special[sidx]["param"].setText("")
        self.unlock()

    def modify_initial(self, row):
        if self._lock:
            return
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
        if self._lock:
            return
        config = self._config.current().config()
        spell = self._default.currentText()
        config["rotation"]["continuing"]["default"] = spell
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_special(self, row, field): # what a fucking mess
        if self._lock:
            return
        config = self._config.current().config()
        if field == "type":
            spell = self._special[row]["type"].currentText()
            if f"special{row + 1:d}" in config["rotation"]["continuing"]: # exists
                if not spell: # removing
                    config["rotation"]["continuing"].pop(f"special{row + 1:d}")
                else: # modifying
                    if config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] != spell:
                        if spell == "cobimf":
                            config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = 0.5
                        elif config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] == "cobimf":
                            config["rotation"]["continuing"][f"special{row + 1:d}"].pop("cast_point_remain")
                    config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] = spell
            else:
                specials = len([1 for key in config["rotation"]["continuing"] if "special" in key])
                if spell and specials < config["configuration"]["num_mages"]:
                    slots_taken = set()
                    for key, val in config["rotation"]["continuing"].items():
                        if "special" in key:
                            slots_taken.add(val["slot"][0])
                    slots_taken = list(slots_taken)
                    num_mages = config["configuration"]["num_mages"]
                    slots_not_taken = [m for m in range(num_mages) if m not in slots_taken]

                    config["rotation"]["continuing"][f"special{row + 1:d}"] = {"value": spell}
                    config["rotation"]["continuing"][f"special{row + 1:d}"]["slot"] = [slots_not_taken[0]] # more hard code
                    if spell == "cobimf":
                        config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = 0.5
            self.fill() # this is the fix? only config was altered
        elif field == "mage":
            text = self._special[row]["mage"].currentText()
            if len(text):
                value = int(text.split("mage")[1]) - 1
                config["rotation"]["continuing"][f"special{row + 1:d}"]["slot"] = [value]
        elif field == "param":
            value = self._special[row]["param"].text()
            if value and value != ".":
                config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = float(value)
        if self._changed_trigger is not None:
            self._changed_trigger()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger

    def mod_mages(self, stype: int):
        config = self._config.current().config()
        num_mages = config["configuration"]["num_mages"]
        for key, val in config["rotation"]["continuing"].items():
            if "special" in key:
                slot = val["slot"][0]
                if slot == num_mages:
                    config["rotation"]["continuing"][key]["slot"] = [slot - 1]
        self.fill()

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
        self.set_changed_trigger(self._changed_trigger)

        # send to rotation
        self._mms(stype)

        if self._changed_trigger is not None:
            self._changed_trigger()
        if self._settings_refresh is not None:
            self._settings_refresh()

    def settings_refresh(self, refresh):
        self._settings_refresh = refresh

class Mage(QWidget):

    _STATS = ["sp", "hit %", "crit %", "int"]
    _STATS_MAP = {"sp": "spell_power", "hit %": "hit_chance", "crit %": "crit_chance", "int": "intellect"}
    _STAT_TYPES = ["int", "percent", "percent", "int"]
    _STAT_DOC = "\n". join(["Specified spell power, crit, and hit are gear/enchant only and do not include buffs",
                            "or talents (10% in the hit field is cap).  Int is base value + gear."])
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
        layout.setContentsMargins(3, 5, 3, 5)
        layout.addWidget(QLabel(f"Mage {index + 1:d}"))

        self._stats = {}
        for stat in self._STATS:
            label = QLabel(f"{stat:s}")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label)
            self._stats[stat] = QLineEdit()
            self._stats[stat].setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self._stats[stat].textChanged.connect(lambda state, x=stat: self.modify_stat(x))
            self._stats[stat].setToolTip(self._STAT_DOC)
            validator = QIntValidator()
            validator.setBottom(0)
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
        for key, ctype in zip(self._stats, self._STAT_TYPES):
            value = config["stats"][self._STATS_MAP[key]][self._index]
            if ctype == "percent":
                sval = f"{100*value:.0f}"
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

    def modify_racial(self):
        config = self._config.current().config()
        racial = self._racial.currentText()
        config["buffs"]["racial"][self._index] = racial
        if self._changed_trigger is not None:
            self._changed_trigger()

    def set_changed_trigger(self, changed_trigger):
        self._changed_trigger = changed_trigger
