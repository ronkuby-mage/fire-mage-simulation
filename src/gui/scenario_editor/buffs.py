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
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from ..utils.icon_edit import get_pixmap
from ..utils.guard_lineedit import GuardLineEdit

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
        self._buffs["dragonling_time"] = GuardLineEdit("float", 1000.0)
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
            swing = GuardLineEdit("float", 100.0)
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

    def fill(self, top=False):
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
                if top:
                    self._buffs["dragonling_time"].set_text(str(config["buffs"]["proc"]["dragonling"]))
            else:
                clear_dragonling = True
            if "nightfall" in config["buffs"]["proc"]:
                for index, val in enumerate(config["buffs"]["proc"]["nightfall"]):
                    icon = QIcon()
                    icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=False))
                    self._buffs["nightfall"][index].setIcon(icon)
                    self._buffs["nightfall"][index].setChecked(True)
                    self._buffs["nightfall_timer"][index].setText(str(val))
                    if top:
                        self._buffs["nightfall_timer"][index].set_text(str(val))
                    self._buffs["nightfall_timer"][index].setEnabled(False)
                self._buffs["nightfall_timer"][index].setEnabled(True)
                for index2 in range(index + 1, self._MAX_NIGHTFALL):
                    icon = QIcon()
                    icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=True))
                    self._buffs["nightfall"][index2].setIcon(icon)
                    self._buffs["nightfall_timer"][index2].setText("")
                    if top:
                        self._buffs["nightfall_timer"][index2].set_text("")
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
            if top:
                self._buffs["dragonling_time"].set_text("")
        if clear_nightfall:
            for index in range(self._MAX_NIGHTFALL):
                icon = QIcon()
                icon.addPixmap(get_pixmap(self._NIGHTFALL_ICON_FN, fade=True))
                self._buffs["nightfall"][index].setIcon(icon)
                enabled = True if not index else False
                self._buffs["nightfall_timer"][index].setEnabled(enabled)
                self._buffs["nightfall_timer"][index].setText("")
                if top:
                    self._buffs["nightfall_timer"][index].set_text("")

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
