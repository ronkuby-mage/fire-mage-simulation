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
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
from ..sim.config import ConfigList, Config
from typing import Callable
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from .icon_edit import numpy_to_qt_pixmap
from skimage import io

class StatOutput(QWidget):

    _OUTPUT_SIZE = 780
    _HIST_BINS = 512
    _EDGE_CHOP = (50, 20, 85, 75)
    _DPS_TYPES_ROW = ["Mean", "Min", "Max", "Median"]
    _EP_TYPES = ["crit", "hit"]
    _EP_METRICS = ["Mean", "90%"]

    def __init__(self):
        super().__init__()
        self._config = None
        self._filename = None
        self._runs = None
        self.setFixedWidth(self._OUTPUT_SIZE)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        self._dist_plot = QLabel()
        layout.addWidget(self._dist_plot)

        style = "QLabel{font-size: 16px;}"

        self._dps = {}
        dps_frame = QGroupBox("DPS")
        dps_layout = QHBoxLayout()
        dps_layout.setContentsMargins(5, 0, 5, 0)
        dps_layout.setSpacing(0)
        dps_layout.setAlignment(Qt.AlignCenter)
        dps_layout.addStretch()
        for value in self._DPS_TYPES_ROW:
            self._dps[value] = QLabel("")
            self._dps[value].setStyleSheet(style)          
            dps_layout.addWidget(self._dps[value])
            dps_layout.addStretch()
        dps_frame.setLayout(dps_layout)
        layout.addWidget(dps_frame)
        dps_frame.setVisible(False)
        self._frames = [dps_frame]

        self._ep = {}
        ep_row = QWidget()
        ep_layout = QHBoxLayout()
        for ep_type in self._EP_TYPES:
            frame = QGroupBox(ep_type.capitalize())
            frame_layout = QHBoxLayout()
            frame_layout.setContentsMargins(5, 0, 5, 0)
            frame_layout.setSpacing(0)
            frame_layout.setAlignment(Qt.AlignCenter)
            frame_layout.addStretch()
            for metric in self._EP_METRICS:
                value = "_".join([ep_type, metric])
                self._ep[value] = QLabel("")
                self._ep[value].setStyleSheet(style)          
                frame_layout.addWidget(self._ep[value])
                frame_layout.addStretch()
            frame.setLayout(frame_layout)
            ep_layout.addWidget(frame)
            frame.setVisible(False)
            self._frames.append(frame)
        ep_row.setLayout(ep_layout)
        layout.addWidget(ep_row)

        self.setLayout(layout)

    def prepare_output(self, config, filename):
        self._config = config
        self._filename = filename

    def set_runs(self, runs):
        self._runs = runs
        self._received = {}
        for value in self._DPS_TYPES_ROW:
            self._dps[value].setText("")
        for ep_type in self._EP_TYPES:
            for metric in self._EP_METRICS:
                value = "_".join([ep_type, metric])
                self._ep[value].setText("")

    def handle_output(self, result):
        run_id, output = result
        output /= len(self._config["configuration"]["target"])
        self._received[run_id] = output
        if run_id == "dps":
            tmp_filename = "temp.png"
            hist, edges = np.histogram(output, self._HIST_BINS)
            centers = (edges[:-1] + edges[1:])/2.0

            plt.close('all')
            plt.figure(figsize=(9.0, 6.25), dpi=100)
            plt.style.use('dark_background')
            plt.title(f"{self._filename:s} Damage Distribution")
            plt.plot(centers, hist)
            plt.xlabel('DPS per Mage')
            plt.yticks([])
            plt.savefig(tmp_filename)
            data = io.imread(tmp_filename)
            os.unlink(tmp_filename)
            data = np.array(data[self._EDGE_CHOP[0]:(data.shape[0] - self._EDGE_CHOP[1]),
                                self._EDGE_CHOP[2]:(data.shape[1] - self._EDGE_CHOP[3]), :3])
            pixmap = numpy_to_qt_pixmap(data)
            self._dist_plot.setPixmap(pixmap)

            value = output.mean()
            self._dps["Mean"].setText(f"Mean: {value:.0f}")
            value = output.min()
            self._dps["Min"].setText(f"Min: {value:.0f}")
            value = output.max()
            self._dps["Max"].setText(f"Max: {value:.0f}")
            value = output[int(len(output)/2)]
            self._dps["Median"].setText(f"Median: {value:.0f}")
        for run_id3 in ["crit", "hit"]:
            if all([run_id2 in self._received for run_id2 in ["dps", "sp", run_id3]]):
                for metric in self._EP_METRICS:
                    if metric == "Mean":
                        value_cr = self._received[run_id3].mean()
                        value_0 = self._received["dps"].mean()
                        value_sp = self._received["sp"].mean()
                    elif metric == "90%":
                        size = self._received["dps"].size
                        level_90 = int(0.9*size)
                        value_cr = self._received[run_id3][level_90]
                        value_0 = self._received["dps"][level_90]
                        value_sp = self._received["sp"][level_90]
                    value = 10.0*(value_cr - value_0)/(value_sp - value_0)
                    if run_id3 == "hit":
                        value = -value
                    str_value = "_".join([run_id3, metric])                        
                    self._ep[str_value].setText(f"{metric:s}: {value:.1f}")
        if len(self._runs) == len(self._received):
            for frame in self._frames:
                frame.setVisible(True)

class CompareOutput(QWidget):
    _OUTPUT_SIZE = 780
    _EDGE_CHOP = (30, 10, 20, 30)
    _COLORS = ["#FF0000", "#FFFF00", "#00FF00", "#007FFF", "#FF00FF"]

    def __init__(self):
        super().__init__()
        self._num_mages = None
        self._runs = None
        self.setFixedWidth(self._OUTPUT_SIZE)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        self._plot = QLabel()
        layout.addWidget(self._plot)

        self.setLayout(layout)

    def prepare_output(self, num_mages, min_time, max_time, etimes):
        self._num_mages = num_mages
        self._min_time = min_time
        self._max_time = max_time
        self._etimes = etimes

    def set_runs(self, runs):
        self._runs = runs
        self._received = [None for dummy in range(len(runs))]

    def handle_output(self, result):
        run_id, output = result
        index = self._runs.index(run_id)
        output = np.array(output)/self._num_mages[index]
        self._received[index] = output
        if all([rec is not None for rec in self._received]):
            ymin = 99999.9
            ymax = 0.0
            cmin = self._min_time
            cmax = self._max_time
            for yvals in self._received:
                for ctime, yval in zip(self._etimes, yvals):
                    if ctime >= cmin and ctime <= cmax:
                        if yval < ymin:
                            ymin = yval
                        if yval > ymax:
                            ymax = yval

            tmp_filename = "temp.png"
            plt.close('all')
            plt.figure(figsize=(8.0, 6.75), dpi=100)
            plt.style.use('dark_background')
            plt.title("Scenario Comparison")
            for idx, (run_id, values) in enumerate(zip(self._runs, self._received)):
                plt.plot(self._etimes, values, label=run_id, color=self._COLORS[idx])
            plt.xlabel('Encounter Duration (seconds)')
            plt.ylabel('Damage per mage')
            plt.grid()
            plt.xlim(cmin, cmax)
            plt.ylim(ymin, ymax)
            plt.legend()
            plt.savefig(tmp_filename)
            data = io.imread(tmp_filename)
            os.unlink(tmp_filename)
            data = np.array(data[self._EDGE_CHOP[0]:(data.shape[0] - self._EDGE_CHOP[1]),
                                self._EDGE_CHOP[2]:(data.shape[1] - self._EDGE_CHOP[3]), :3])
            pixmap = numpy_to_qt_pixmap(data)
            self._plot.setPixmap(pixmap)
