import json
from PyQt5.QtWidgets import (
    QPushButton,
    QTabWidget,
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
from copy import deepcopy
from ...sim.constants import Constant
from ..utils.guard_lineedit import GuardLineEdit

class Rotation(QWidget):

    _SPELLS = list(Constant(0.0)._DECIDE.keys())
    _MAX_SPELLS = 12
    _REAL_SPELLS = 3
    _MAX_SPECIALS = 3
    _SPECIALS = ["maintain_scorch", "scorch", "scorch_wep", "cobimf", "cd_imf"]
    _SPECIAL_DOC = "\n".join([
        "maintain_scorch: Cast Scorch if there are less than 5 seconds left on the debuff or it is not fully stacked",
        "scorch: Also cast Scorch if ignite is fully stacked and no cooldowns (Combustion/PI/trinket) are active or available",
        "scorch_wep: Cast Scorch even with remaining cooldowns",
        "cobimf: Scorch under same conditions as scorch_wep, but if ignite has <= 2 seconds remaining cast Fire Blast",
        "  Here 'Parameter' is the response time of the caster -- even if ignite is refreshed within the response time,",
        "  the mage will still cast Fire Blast.  If ignite is refreshed after the response time but before Fire Blast",
        "  is cast, they will switch back to Scorch",
        "cd_imf: A hybrid of cobimf and scorch, best for one of four mages to adopt.  Scorch under same conditions as 'scorch',",
        "  (Fireball during cooldowns), but follow the cobimf Fire Blast rule during scorch spam."])
    _FROSTBOLT_DOC = "FROSTBOLT = Cast Frostbolt until a full ignite stack is reached"
    _INITIAL_NAME = ["other", "have_pi"]
    _INITIAL_NONSPLIT = ["Initial", ""]
    _INITIAL_SPLIT = ["No PI", "PI"]

    def __init__(self, config_list):
        super().__init__()
        self._changed_trigger = None
        self._config = config_list
        self._lock = False
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 5, 3, 5)
        layout.setSpacing(0)

        # initial rotation
        ann_row = QWidget()
        ann_layout = QHBoxLayout()
        ann_layout.addWidget(QLabel("Rotation"))
        ann_layout.addStretch()
        ann_layout.addWidget(QLabel("Split by PI"))
        self._split = QCheckBox()
        self._split.setChecked(False)
        self._split.stateChanged.connect(self.modify_split)
        ann_layout.addWidget(self._split)
        ann_row.setLayout(ann_layout)
        layout.addWidget(ann_row)
        
        self._tabs = QTabWidget()
        self._initial_table = {}
        self._initial = {}
        for open_type in self._INITIAL_NAME:
            table = QTableWidget(self._MAX_SPELLS, 2, self)
            table.setFixedHeight(302)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()
            self._initial[open_type] = []
            for row in range(table.rowCount()):
                table.setCellWidget(row, 0, QLabel(f"{row + 1:d}"))
                combo = QComboBox()
                combo.addItems(self._SPELLS)
                combo.currentIndexChanged.connect(lambda state, x=open_type, y=row: self.modify_initial(x, y))
                self._initial[open_type].append(combo)
                table.setCellWidget(row, 1, combo)
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self._tabs.addTab(table, open_type)
            self._initial_table[open_type] = table
        layout.addWidget(self._tabs, stretch=12)

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
            table.setFixedHeight(82)

            combo = QComboBox()
            combo.addItems(self._SPECIALS)
            combo.currentIndexChanged.connect(lambda state, x=idx: self.modify_special(x, "type"))
            this_special["type"] = combo
            table.setCellWidget(0, 1, combo)

            mage = QComboBox()
            mage.currentIndexChanged.connect(lambda state, x=idx: self.modify_special(x, "mage"))
            this_special["mage"] = mage
            table.setCellWidget(1, 1, mage)

            param = GuardLineEdit("float", 4.0, required=True)
            param.textChanged.connect(lambda state, x=idx: self.modify_special(x, "param"))
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

    def fill(self, top=False):
        config = self._config.current().config()
        self.lock()

        if "have_pi" in config["rotation"]["initial"]:
            self._tabs.setTabEnabled(1, True)
            self._split.setChecked(True)
            for index, tab_name in enumerate(self._INITIAL_SPLIT):
                self._tabs.setTabText(index, tab_name)
            self._initial_table["other"].setToolTip(self._FROSTBOLT_DOC)
        else:
            self._tabs.setTabEnabled(1, False)
            self._split.setChecked(False)
            for index, tab_name in enumerate(self._INITIAL_NONSPLIT):
                self._tabs.setTabText(index, tab_name)

        for name in self._INITIAL_NAME:
            # remove empty entry
            for idx in range(self._MAX_SPELLS):
                empty = [jdx for jdx in range(self._initial[name][idx].count()) if self._initial[name][idx].itemText(jdx) == ""]
                if len(empty):
                    self._initial[name][idx].removeItem(empty[0])
                frost_stack = [jdx for jdx in range(self._initial[name][idx].count()) if self._initial[name][idx].itemText(jdx) == "FROSTBOLT"]
                if len(frost_stack):
                    self._initial[name][idx].removeItem(frost_stack[0])

            if name in config["rotation"]["initial"]:
                for idx, spell in enumerate(config["rotation"]["initial"][name]):
                    if name == "other" and self._split.isChecked():
                        fb_ind = self._initial[name][idx].count()
                        self._initial[name][idx].addItem("FROSTBOLT")
                    self._initial_table[name].setCellWidget(idx, 0, QLabel(f"{idx + 1:d}"))
                    index = fb_ind if spell == "FROSTBOLT" else self._SPELLS.index(spell)
                    self._initial[name][idx].setCurrentIndex(index)
                    self._initial[name][idx].setEnabled(True)

            for jdx in range(idx, self._MAX_SPELLS):
                if jdx:
                    self._initial[name][jdx].addItem("")
                if jdx != idx:
                    self._initial_table[name].setCellWidget(jdx, 0, QLabel(f""))
                    self._initial[name][jdx].setCurrentText("")
                    self._initial[name][jdx].setEnabled(jdx == idx + 1)
                    if name == "other" and self._split.isChecked():
                        self._initial[name][jdx].addItem("FROSTBOLT")
        
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
                self._special[index]["type"].setEnabled(True)
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
                if stype in ["cobimf", "cd_imf"]:
                    if top:
                        param_val = val["cast_point_remain"]
                        self._special[index]["param"].setText(str(param_val))
                        self._special[index]["param"].set_text(str(param_val))
                    self._special[index]["param"].setEnabled(True)
                else:
                    if top:
                        self._special[index]["param"].setText("")
                        self._special[index]["param"].set_text("")
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
            if top:
                self._special[sidx]["param"].set_text("")
        self.unlock()

    def modify_split(self):
        if self._lock:
            return
        config = self._config.current().config()
        if self._split.isChecked():
            config["rotation"]["initial"][self._INITIAL_NAME[1]] = ["scorch"]
        else:
            config["rotation"]["initial"].pop(self._INITIAL_NAME[1])
        self.fill()
        if self._changed_trigger is not None:
            self._changed_trigger()

    def modify_initial(self, tab_name, row):
        if self._lock:
            return
        config = self._config.current().config()
        spell = self._initial[tab_name][row].currentText()
        if not spell:
            if row < len(config["rotation"]["initial"][tab_name]):
                config["rotation"]["initial"]["other"].pop()
        elif row >= len(config["rotation"]["initial"][tab_name]):
            config["rotation"]["initial"][tab_name].append(spell)
        else:
            config["rotation"]["initial"][tab_name][row] = spell
        self.fill()
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
        set_top = False
        config = self._config.current().config()
        if field == "type":
            spell = self._special[row]["type"].currentText()
            if f"special{row + 1:d}" in config["rotation"]["continuing"]: # exists
                if not spell: # removing
                    config["rotation"]["continuing"].pop(f"special{row + 1:d}")
                else: # modifying
                    if config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] != spell:
                        if spell in ["cobimf", "cd_imf"]:
                            config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = 0.5
                        elif config["rotation"]["continuing"][f"special{row + 1:d}"]["value"] in ["cobimf", "cd_imf"]:
                            config["rotation"]["continuing"][f"special{row + 1:d}"].pop("cast_point_remain")
                        set_top = True
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
                    if spell in ["cobimf", "cd_imf"]:
                        config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = 0.5
                        set_top = True
        elif field == "mage":
            text = self._special[row]["mage"].currentText()
            if len(text):
                value = int(text.split("mage")[1]) - 1
                config["rotation"]["continuing"][f"special{row + 1:d}"]["slot"] = [value]
        elif field == "param":
            value = self._special[row]["param"].text()
            if value and value != ".":
                config["rotation"]["continuing"][f"special{row + 1:d}"]["cast_point_remain"] = float(value)
        self.fill(top=set_top) # this is the fix? only config was altered
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
        self.fill(top=True)
