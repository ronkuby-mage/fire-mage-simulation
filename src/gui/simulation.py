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
from PyQt5.QtCore import Qt, QSize
from .output import Output
from .settings import StatSettings, CompareSettings

class Simulation(QWidget):

    _SAMPLE_DIRECTORY = "./data/samples/"
    _SIMULATION_TYPES = [
        ("Stat Weight/Distribution", "sample.png", StatSettings),
        ("Scenario Comparison", "sample.png", CompareSettings)
    ]
    _INDEX = ["name", "sample_file", "class"]

    def __init__(self, config_list, filename_func):
        super().__init__()
        self._config_list = config_list
        self._filenames = filename_func

        self._simtype_index = 0

        layout = QHBoxLayout()

        control_col = QWidget()    
        cc_layout = QVBoxLayout()

        # sample
        sample_frame = QFrame()
        sample_layout = QHBoxLayout()
        self._sample = QLabel()
        self.fill_sample()
        sample_layout.addWidget(self._sample)
        sample_frame.setLayout(sample_layout)
        cc_layout.addWidget(sample_frame)

        # selector
        select_frame = QGroupBox("Simulation Type")
        select_layout = QVBoxLayout()
        self._select = QButtonGroup()
        for index, stype in enumerate(self._SIMULATION_TYPES):
            sim_name = stype[self._INDEX.index("name")]
            button = QPushButton(sim_name)
            button.setCheckable(True)
            if index == self._simtype_index:
                button.setChecked(True)
            select_layout.addWidget(button)
            self._select.addButton(button)
            self._select.setId(button, index)
        self._select.buttonClicked.connect(self.modify_type)
        select_frame.setLayout(select_layout)
        cc_layout.addWidget(select_frame)

        # settings
        settings_frame = QGroupBox("Simulation Settings")
        settings_layout = QVBoxLayout()
        self._settings_stack = QStackedWidget()
        self._settings = []
        for stype in self._SIMULATION_TYPES:
            sim_class = stype[self._INDEX.index("class")]
            setting = sim_class(config_list, filename_func)
            self._settings_stack.addWidget(setting)
            self._settings.append(setting)
        settings_layout.addWidget(self._settings_stack)
        settings_frame.setLayout(settings_layout)
        cc_layout.addWidget(settings_frame)

        # progress/number of simulations
        self._progress = QLabel("Progress")
        cc_layout.addWidget(self._progress)

        # run button -- note the reverse is being used
        self._run = QPushButton("Run Simulation")
        self._run.setCheckable(True)
        self._run.setChecked(False)
        self._run.released.connect(self.run)
        self._run.setMinimumHeight(50)
        style = "QPushButton{font-size: 24px; background-color: rgb(168, 184, 194); color: rgb(192, 0, 0);} "
        style += "QPushButton:hover{font-size: 24px; background-color: rgb(208, 214, 224); color: rgb(192, 0, 0);} "
        style += "QPushButton:checked{font-size: 24px; background-color: rgb(72, 89, 104); color: rgb(192, 0, 0);}"
        self._run.setStyleSheet(style)
        cc_layout.addWidget(self._run)

        # end of control panel
        control_col.setLayout(cc_layout)
        layout.addWidget(control_col)

        # start output
        self._output = Output()
        layout.addWidget(self._output)

        self.setLayout(layout)

    def run(self):
        self._run.setEnabled(False)
        #import time
        #time.sleep(5)

        return_value = self._settings[self._simtype_index].run()
        print(return_value.shape, return_value.mean())

        self._run.setEnabled(True)
        self._run.setChecked(False)

    def modify_type(self, button: QPushButton):
        index = self._select.id(button)
        if index == self._simtype_index:
            return
        self._simtype_index = index
        self.fill_sample()
        self._settings_stack.setCurrentIndex(index)

    def fill_sample(self):
        filename = self._SIMULATION_TYPES[self._simtype_index][self._INDEX.index("sample_file")]
        fullfile = os.path.join(self._SAMPLE_DIRECTORY, filename)
        pixmap = QPixmap(fullfile)
        self._sample.setPixmap(pixmap)

    def refresh(self):
        for setting in self._settings:
            setting.refresh()
