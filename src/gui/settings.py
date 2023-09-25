import os
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
from PyQt5.QtCore import QThreadPool
from copy import deepcopy
from ..sim.mechanics import get_damage
from ..sim.config import ConfigList
from typing import Callable
from .worker import Worker

class NumberOfSamples(QWidget):

    def __init__(self, edit_func, default_value):
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Number of Samples:"))
        self._number_of_samples = QLineEdit(str(default_value))
        validator = QIntValidator()
        validator.setBottom(0)
        self._number_of_samples.setValidator(validator)
        self._number_of_samples.textChanged.connect(edit_func)
        layout.addWidget(self._number_of_samples)
        self.setLayout(layout)

    def widget(self):
        return self._number_of_samples

class EncounterTime(QWidget):

    def __init__(self, edit_func, default_value):
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Encounter Time (seconds):"))
        self._etime = QLineEdit(str(default_value))
        validator = QDoubleValidator()
        validator.setBottom(0)
        self._etime.setValidator(validator)
        self._etime.textChanged.connect(edit_func)
        layout.addWidget(self._etime)
        self.setLayout(layout)

    def widget(self):
        return self._number_of_samples

class StatSettings(QWidget):

    _DEFAULT_TIME = 70.0
    _DEFAULT_VAR = 0.05
    _DEFAULT_SAMPLES = 100000

    def __init__(self, config_list: ConfigList, filename_func: Callable):
        super().__init__()
        self._config_list = config_list
        self._filename_func = filename_func
        self._progbar = None
        self.threadpool = QThreadPool()        
        # stat settings need:
        # l1: list scenario currently set for editing
        # l2: setting for all mages or custom on mod
        # l3: grid of mages pushbuttons
        # l4: display min to max, or how many STDs
        # l4: do crit EP?, do hit EP?
        # l5: encounter time - set var to 5%
        # l6: number of samples
        layout = QVBoxLayout()

        index = config_list.index()
        # L1
        scen_name = filename_func()[index]
        self._scenario_name = QLabel(f"Running {scen_name:s}")
        layout.addWidget(self._scenario_name)



        # L5
        self._etime = self._DEFAULT_TIME
        self._etime_widget = EncounterTime(self.modify_etime, self._DEFAULT_TIME)
        layout.addWidget(self._etime_widget)

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

    def modify_etime(self):
        widget = self._etime_widget.widget()
        value = widget.text()
        if value:
            self._etime = float(value)

    def refresh(self):
        index = self._config_list.index()
        scen_name = self._filename_func()[index]
        self._scenario_name.setText(f"Running {scen_name:s}")

    def run(self, processing_complete: Callable, handle_output: Callable):
        print("running")
        main_config = self._config_list.current().config()
        config = deepcopy(main_config)

        config['timing']['duration'] = {
            "mean": self._etime,
            "var": self._DEFAULT_VAR*self._etime,
            "clip": [3.0, 10000.0]}
        config["sim_size"] = self._samples
        run_parameters = {"type": "distribution"}

        # loop starts here
        worker = Worker(get_damage, config, run_parameters) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(handle_output)
        worker.signals.finished.connect(processing_complete)
        worker.signals.progress.connect(self.update_progress)
        self.threadpool.start(worker)

    def update_progress(self, value: float):
        if self._progbar is not None:
            self._progbar(value)

    def set_progbar(self, progbar: Callable):
        self._progbar = progbar

class CompareSettings(QWidget):

    _DEFAULT_VALUE = 100000

    def __init__(self, config_list: ConfigList, filename_func: Callable):
        super().__init__()
        self._config_list = config_list
        self._filenames = filename_func
        self._progbar = None

        # start time for y scale
        # max time for sim
        # number of samples
        layout = QVBoxLayout()
        self._samples = self._DEFAULT_VALUE
        self._num_samp = NumberOfSamples(self.modify_samples, self._DEFAULT_VALUE)
        layout.addWidget(self._num_samp)

        self.setLayout(layout)

    def modify_samples(self):
        widget = self._num_samp.widget()
        value = widget.text()
        if value:
            self._samples = int(value)

    def refresh(self):
        pass

    def set_progbar(self, progbar: Callable):
        self._progbar = progbar
