import os
import numpy as np
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
    QButtonGroup,
    QGroupBox,
    QFrame
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon, QPixmap
from PyQt5.QtCore import QThreadPool, Qt
from copy import deepcopy
from ..sim.mechanics import get_damage
from ..sim.config import ConfigList
from typing import Callable
from .worker import Worker

class NumberOfSamples(QWidget):

    def __init__(self, edit_func, default_value):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(QLabel("Number of Samples:"))
        self._number_of_samples = QLineEdit(str(default_value))
        self._number_of_samples.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self._number_of_samples.setMaximumWidth(75)
        validator = QIntValidator()
        validator.setBottom(0)
        self._number_of_samples.setValidator(validator)
        self._number_of_samples.textChanged.connect(edit_func)
        layout.addWidget(self._number_of_samples)
        self.setLayout(layout)

    def widget(self):
        return self._number_of_samples

class TimeWidget(QWidget):

    def __init__(self, edit_func, default_value, message, key):
        super().__init__()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(QLabel(message))
        self._etime = QLineEdit(str(default_value))
        self._etime.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self._etime.setMaximumWidth(75)
        validator = QDoubleValidator()
        validator.setBottom(0)
        self._etime.setValidator(validator)
        self._etime.textChanged.connect(lambda: edit_func(key))
        layout.addWidget(self._etime)
        self.setLayout(layout)

    def widget(self):
        return self._etime

class StatSettings(QWidget):
    _INITIAL_DELAY = 1.0
    _RECAST_DELAY = 0.05
    _DEFAULT_TIME = 70.0
    _DEFAULT_VAR = 0.05
    _DEFAULT_SAMPLES = 100000
    _MAX_MAGES = 9 # repeat from scenario

    def __init__(self, config_list: ConfigList, filename_func: Callable):
        super().__init__()
        self._config_list = config_list
        self._filename_func = filename_func
        self._progbar = None
        self._output = None
        self.threadpool = QThreadPool()
        # stat settings need:
        # l1: list scenario currently set for editing
        # l2: grid of mages pushbuttons
        # l3: display min to max, or how many STDs
        # l3: do crit EP?, do hit EP?
        # l3: if doing EPs, set to mean, or -2s, 10, -1s, median, +1s, 90, 2s values
        # l4: setting for all mages or custom on mod
        # l5: encounter time - set var to 5%
        # l6: number of samples
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        index = config_list.index()
        # L1
        scen_name = filename_func()[index]
        self._scenario_name = QLabel(f"Distribution for: {scen_name:s}")
        self._scenario_name.setStyleSheet("QLabel{font-size: 14px;}")
        layout.addWidget(self._scenario_name)

        self._ep = {}
        # L2
        ep_row = QWidget()
        ep_layout = QHBoxLayout()
        ep_layout.setContentsMargins(0, 0, 0, 0)
        ep_layout.setSpacing(0)
        ep_layout.setAlignment(Qt.AlignVCenter)
        label = QLabel("Run Crit Weight")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ep_layout.addWidget(label)
        self._ep["crit"] = QCheckBox()
        self._ep["crit"].setChecked(True)
        self._ep["crit"].clicked.connect(lambda: self.modify_ep("crit"))
        ep_layout.addWidget(self._ep["crit"])
        ep_layout.addStretch()
        label = QLabel("Run Hit Weight")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ep_layout.addWidget(label)
        self._ep["hit"] = QCheckBox()
        self._ep["hit"].setChecked(True)
        self._ep["hit"].clicked.connect(lambda: self.modify_ep("hit"))
        ep_layout.addWidget(self._ep["hit"])
        ep_layout.addStretch()
        label = QLabel("Vary All Mages")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ep_layout.addWidget(label)
        self._ep["all"] = QCheckBox()
        self._ep["all"].setChecked(True)
        self._ep["all"].clicked.connect(lambda: self.modify_ep("all"))
        ep_layout.addWidget(self._ep["all"])
        ep_row.setLayout(ep_layout)
        layout.addWidget(ep_row)

        # L3
        ep_row2 = QWidget()
        ep_layout2 = QHBoxLayout()
        ep_layout2.setContentsMargins(0, 0, 0, 0)
        ep_layout2.setSpacing(0)

        label = QLabel("Vary Mage")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ep_layout2.addWidget(label)
        mages = QWidget()
        mages_layout = QGridLayout()
        mages_layout.setAlignment(Qt.AlignVCenter)
        self._ep["mages"] = []
        style = "QPushButton:checked{border-width: 2px; border-color: #9158FF; border-style: solid;}"
        for index in range(self._MAX_MAGES):
            button = QPushButton(f"{index + 1:d}")
            button.setCheckable(True)
            button.setChecked(False)
            button.setStyleSheet(style)
            button.setEnabled(False)
            button.setMinimumWidth(15)
            button.setMaximumWidth(80)
            button.clicked.connect(lambda state, x=index: self.modify_ep(x))
            mages_layout.addWidget(button, 0, index)
            self._ep["mages"].append(button)
        mages.setLayout(mages_layout)
        ep_layout2.addWidget(mages)
        ep_row2.setLayout(ep_layout2)
        layout.addWidget(ep_row2)

        self._time = {}
        self._time_widget = {}

        # L4
        self._time["duration"] = self._DEFAULT_TIME
        self._time_widget["duration"] = TimeWidget(self.modify_time, self._DEFAULT_TIME, "Encounter Time (seconds):", "duration")
        layout.addWidget(self._time_widget["duration"])

        # L5
        time_row = QWidget()
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._time["delay"] = self._INITIAL_DELAY
        self._time_widget["delay"] = TimeWidget(self.modify_time, self._INITIAL_DELAY, "Initial Delay", "delay")
        time_layout.addWidget(self._time_widget["delay"])
        self._time["response"] = self._RECAST_DELAY
        self._time_widget["response"] = TimeWidget(self.modify_time, self._RECAST_DELAY, "Recast Delay", "response")
        time_layout.addWidget(self._time_widget["response"])
        time_row.setLayout(time_layout)
        layout.addWidget(time_row)

        # L6
        self._samples = self._DEFAULT_SAMPLES
        self._samples_widget = NumberOfSamples(self.modify_samples, self._DEFAULT_SAMPLES)
        layout.addWidget(self._samples_widget)

        self.setLayout(layout)

    def modify_samples(self):
        widget = self._samples_widget.widget()
        value = widget.text()
        if value:
            self._samples = int(value)

    def modify_time(self, key):
        widget = self._time_widget[key].widget()
        value = widget.text()
        if value and value != ".":
            self._time[key] = float(value)

    def modify_ep(self, ep_type):
        if ep_type == "all":
            if self._ep["all"].isChecked():
                for mage in self._ep["mages"]:
                    mage.setChecked(False)
                    mage.setEnabled(False)
            else:
                config = self._config_list.current().config()
                for index in range(config["configuration"]["num_mages"]):
                    self._ep["mages"][index].setEnabled(True)
                    self._ep["mages"][index].setChecked(True)
                if config["configuration"]["num_mages"] == 1:
                    self._ep["mages"][index].setEnabled(False)
        elif not isinstance(ep_type, str):
            config = self._config_list.current().config()
            checked = sum([int(self._ep["mages"][index].isChecked()) for index in range(config["configuration"]["num_mages"])])
            if checked == 1:
                for index in range(config["configuration"]["num_mages"]):
                    if self._ep["mages"][index].isChecked():
                        self._ep["mages"][index].setEnabled(False)
            else:
                for index in range(config["configuration"]["num_mages"]):
                    self._ep["mages"][index].setEnabled(True)

    def refresh(self):
        index = self._config_list.index()
        scen_name = self._filename_func()[index]
        self._scenario_name.setText(f"Distribution for: {scen_name:s}")
        config = self._config_list.current().config()
        if not self._ep["all"].isChecked():
            config = self._config_list.current().config()
            for index in range(config["configuration"]["num_mages"]):
                self._ep["mages"][index].setEnabled(True)
            for index2 in range(index + 1, self._MAX_MAGES):
                self._ep["mages"][index2].setEnabled(False)
                self._ep["mages"][index2].setChecked(False)
            checked = sum([int(self._ep["mages"][index].isChecked()) for index in range(config["configuration"]["num_mages"])])
            if not checked:
                self._ep["mages"][0].setChecked(True)
            else:
                self.modify_ep(self._MAX_MAGES) # other conditions caught by modify_ep

    def run(self, processing_complete: Callable, handle_output: Callable, set_runs: Callable):
        main_config = self._config_list.current().config()
        config = deepcopy(main_config)

        config['timing'] = {
            "duration": {
                "mean": self._time["duration"],
                "var": self._DEFAULT_VAR*self._time["duration"],
                "clip": [3.0, 10000.0]},
            "delay": self._time["delay"],
            "response": self._time["response"]}
        config["sim_size"] = self._samples
        run_parameters = {"type": "distribution"}
        self._output(config, self._filename_func(current=True))
        run_iter = ["dps"]
        if self._ep["crit"].isChecked() or self._ep["hit"].isChecked():
            run_iter.append("sp")
            if self._ep["all"].isChecked():
                to_mod = list(range(config["configuration"]["num_mages"]))
            else:
                to_mod = [index for index in range(config["configuration"]["num_mages"]) if self._ep["mages"][index].isChecked()]
        if self._ep["crit"].isChecked():
            run_iter.append("crit")
        if self._ep["hit"].isChecked():
            run_iter.append("hit")
        set_runs(run_iter)

        # loop starts here
        for run_type in run_iter:
            iconfig = deepcopy(config)
            iparam = deepcopy(run_parameters)
            iparam["id"] = run_type
            if run_type == "sp":
                for mod in to_mod:
                    iconfig["stats"]["spell_power"][mod] += 15
            elif run_type == "crit":
                for mod in to_mod:
                    iconfig["stats"]["crit_chance"][mod] += 0.015
            elif run_type == "hit":
                for mod in to_mod:
                    iconfig["stats"]["hit_chance"][mod] -= 0.015

            worker = Worker(get_damage, iconfig, iparam) # Any other args, kwargs are passed to the run function
            worker.signals.result.connect(handle_output)
            worker.signals.finished.connect(processing_complete)
            worker.signals.progress.connect(self.update_progress)
            self.threadpool.start(worker)

    def update_progress(self, prog: tuple):
        run_id, value = prog
        if run_id == "dps":
            if self._progbar is not None:
                self._progbar(value)

    def set_progbar(self, progbar: Callable):
        self._progbar = progbar

    def set_output(self, output: Callable):
        self._output = output

class CompareSettings(QWidget):

    _DEFAULT_MIN = 30.0
    _DEFAULT_MAX = 150.0
    _INITIAL_DELAY = 1.0
    _RECAST_DELAY = 0.05
    _DEFAULT_VAR = 0.05
    _DEFAULT_SAMPLES = 20000

    def __init__(self, config_list: ConfigList, filename_func: Callable):
        super().__init__()
        self._config_list = config_list
        self._filenames = filename_func
        self._progbar = None
        self._output = None
        self.threadpool = QThreadPool()

        # start time for y scale
        # max time for sim
        # number of samples
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()

        self._time = {}
        self._time_widget = {}

        # L4
        self._time["min_time"] = self._DEFAULT_MIN
        self._time_widget["min_time"] = TimeWidget(self.modify_time, self._DEFAULT_MIN, "Minimum Time (seconds)", "min_time")
        self._time_widget["min_time"].widget().setToolTip("Y-scale minimum will usually be the minimum damage at this time.")
        layout.addWidget(self._time_widget["min_time"])

        self._time["max_time"] = self._DEFAULT_MAX
        self._time_widget["max_time"] = TimeWidget(self.modify_time, self._DEFAULT_MAX, "Maximum Time (seconds)", "max_time")
        layout.addWidget(self._time_widget["max_time"])

        # L5
        self._time["delay"] = self._INITIAL_DELAY
        self._time_widget["delay"] = TimeWidget(self.modify_time, self._INITIAL_DELAY, "Initial Delay (seconds)", "delay")
        layout.addWidget(self._time_widget["delay"])

        self._time["response"] = self._RECAST_DELAY
        self._time_widget["response"] = TimeWidget(self.modify_time, self._RECAST_DELAY, "Recast Delay (seconds)", "response")
        layout.addWidget(self._time_widget["response"])

        #row = QWidget()
        #row_layout = QHBoxLayout()
        #row_layout.setContentsMargins(0, 0, 0, 0)
        #row_layout.addStretch()
        #row_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        #row_layout.addWidget(QLabel("Adaptive Sample Number"))
        #self._adaptive = QLineEdit()

        # L6
        self._samples = self._DEFAULT_SAMPLES
        self._samples_widget = NumberOfSamples(self.modify_samples, self._DEFAULT_SAMPLES)
        layout.addWidget(self._samples_widget)

        self.setLayout(layout)

    def modify_samples(self):
        widget = self._samples_widget.widget()
        value = widget.text()
        if value:
            self._samples = int(value)

    def modify_time(self, key):
        widget = self._time_widget[key].widget()
        value = widget.text()
        if value and value != ".":
            self._time[key] = float(value)

    def refresh(self):
        pass # no compare settings need to be adjusted based on external actions

    def run(self, processing_complete: Callable, handle_output: Callable, set_runs: Callable):
        runs = deepcopy(self._filenames())
        if len(set(runs)) != len(runs):
            runs = [f"{r:s}_{idx:d}" for idx, r in enumerate(runs)]
            
        set_runs(runs) # sets self._runs in simulation so it knows when all are done and in output
        self._runs = runs
        num_mages = []
        self._latest_prog = []
        for config_serv in self._config_list.configs():
            num_mages.append(len(config_serv.config()["configuration"]["target"]))
            self._latest_prog.append(0.0)

        # in case the user wants to play games
        cmax = min([max([10.0, self._time["max_time"]]), 1000.0])
        cmin = min([max([5.0, self._time["min_time"]]), 1000.0])
        if cmax <= cmin:
            ave = (cmin + cmax)/2
            etimes = np.array([ave - 2.0, ave + 2])
        else:
            cmin = 15*((cmin - 10)//15)
            etimes = np.arange(cmin, cmax + 20, 5, dtype=np.int32)
            etimes = etimes[np.where(np.logical_or(np.logical_not(np.mod(etimes, 15)), etimes < 90))[0]].astype(float)

        self._output(num_mages, self._time["min_time"], self._time["max_time"], etimes) # calls "prepare_output" in output Class

        for index, config_serv in enumerate(self._config_list.configs()):
            config = deepcopy(config_serv.config())
            config['timing'] = {
                "duration": {
                    "mean": self._time["max_time"] + 15.0,
                    "var": 3.0,
                    "clip": [3.0, 10000.0]},
                "delay": self._time["delay"],
                "response": self._time["response"]}
            config["sim_size"] = self._samples
            run_parameters = {"type": "over_time", "id": runs[index], "dur_dist": deepcopy(etimes)}
            worker = Worker(get_damage, config, run_parameters)
            worker.signals.result.connect(handle_output)
            worker.signals.finished.connect(processing_complete)
            worker.signals.progress.connect(self.update_progress)
            self.threadpool.start(worker)

    def update_progress(self, prog: tuple):
        run_id, value = prog
        self._latest_prog[self._runs.index(run_id)] = value
        self._progbar(min(self._latest_prog))

    def set_progbar(self, progbar: Callable):
        self._progbar = progbar

    def set_output(self, output: Callable):
        self._output = output
