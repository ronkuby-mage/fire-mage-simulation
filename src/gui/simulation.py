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
    QStatusBar,
    QFrame
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from .settings import StatSettings, CompareSettings
from .output import StatOutput, CompareOutput
from .icon_edit import numpy_to_qt_pixmap

class Progress(QLabel):

    _SHAPE = (35, 300, 3)
    _FONT_COLOR = f"rgb(255, 255, 255)"
    _BAR_COLOR = np.array([64, 192, 32])

    def __init__(self):
        super().__init__()
        self.setText("")
        self.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.setFixedHeight(self._SHAPE[0])
        self.setFixedWidth(self._SHAPE[1])
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._pl = QLabel()
        self._pl.setFixedHeight(20)
        self._pl.setFixedWidth(self._SHAPE[1])
        style = f"QLabel{{font-size: 18px; background: transparent; color: {self._FONT_COLOR:s};}}"
        self._pl.setStyleSheet(style)
        self._pl.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        layout.addWidget(self._pl)
        self.setLayout(layout)

    def set_value(self, value: float):
        img = np.zeros(self._SHAPE, dtype=np.uint8)
        frac = int(min([value*self._SHAPE[1]/100.0, self._SHAPE[1]]))
        img[:,:frac, :] = self._BAR_COLOR
        self.setPixmap(numpy_to_qt_pixmap(img))
        self._pl.setText(f"{int(value):d}%")

class Simulation(QWidget):

    _SAMPLE_DIRECTORY = "./data/samples/"
    _SIMULATION_TYPES = [
        ("Stat Weights/Distribution", "distribution.png", StatSettings, StatOutput),
        ("Scenario Comparison", "compare.png", CompareSettings, CompareOutput)
    ]
    _INDEX = ["name", "sample_file", "setting_class", "output_class"]

    def __init__(self, config_list, filename_func):
        super().__init__()
        self._config_list = config_list
        self._filenames = filename_func
        self._runs = None

        self._simtype_index = 0

        layout = QHBoxLayout()
        control_col = QWidget()    
        cc_layout = QVBoxLayout()

        # sample
        sample_frame = QFrame()
        sample_layout = QHBoxLayout()
        self._sample = QLabel()
        self.fill_sample()
        sample_layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
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
            style = "QPushButton{font-size: 18px; color: rgb(0, 0, 0);} "
            style += "QPushButton:hover{font-size: 18px; color: rgb(0, 0, 0);} "
            style += "QPushButton:checked{font-size: 18px; color: rgb(255, 255, 255);}"
            button.setStyleSheet(style)
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
            sim_class = stype[self._INDEX.index("setting_class")]
            setting = sim_class(config_list, filename_func)
            self._settings_stack.addWidget(setting)
            self._settings.append(setting)
        settings_layout.addWidget(self._settings_stack)
        settings_frame.setLayout(settings_layout)
        cc_layout.addWidget(settings_frame)

        # progress/number of simulations
        prog_frame = QWidget()
        prog_layout = QHBoxLayout()
        prog_layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self._progress = Progress()
        prog_layout.addWidget(self._progress)
        prog_frame.setLayout(prog_layout)
        cc_layout.addWidget(prog_frame)
    
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
        self._output_stack = QStackedWidget()
        self._output = []
        for stype in self._SIMULATION_TYPES:
            sim_class = stype[self._INDEX.index("output_class")]
            output = sim_class()
            self._output_stack.addWidget(output)
            self._output.append(output)
        layout.addWidget(self._output_stack)

        self.setLayout(layout)

        for setting, output in zip(self._settings, self._output):
            setting.set_progbar(self._progress.set_value)
            setting.set_output(output.prepare_output)

    def processing_complete(self):
        self._run_count += 1
        if self._run_count == self._runs:
            self._run.setEnabled(True)
            self._run.setChecked(False)

    def set_runs(self, runs):
        self._runs = len(runs)
        self._output[self._index_at_run].set_runs(runs)

    def run(self):
        self._run.setEnabled(False)
        self._index_at_run = self._simtype_index
        run_func = self._settings[self._simtype_index].run
        handle_output = self._output[self._simtype_index].handle_output
        self._run_count = 0
        run_func(self.processing_complete, handle_output, self.set_runs)

    def modify_type(self, button: QPushButton):
        index = self._select.id(button)
        if index == self._simtype_index:
            return
        self._simtype_index = index
        self.fill_sample()
        self._settings_stack.setCurrentIndex(index)
        self._output_stack.setCurrentIndex(index)

    def fill_sample(self):
        filename = self._SIMULATION_TYPES[self._simtype_index][self._INDEX.index("sample_file")]
        fullfile = os.path.join(self._SAMPLE_DIRECTORY, filename)
        pixmap = QPixmap(fullfile)
        self._sample.setPixmap(pixmap)

    def refresh(self):
        for setting in self._settings:
            setting.refresh()
