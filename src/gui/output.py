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

#    _OUTPUT_SIZE = 780
#     self.setFixedWidth(self._OUTPUT_SIZE)
class StatOutput(QWidget):

    _OUTPUT_SIZE = 780
    _HIST_BINS = 512
    _EDGE_CHOP = (35, 15, 85, 75)
    _DPS_TYPES_ROW = ["Mean", "Min", "Max", "Median"]
    _EP_TYPES = ["crit", "hit"]
    _EP_METRICS = ["Mean", "90%"]

    def __init__(self):
        super().__init__()
        self._config = None
        self._filename = None
        self.setFixedWidth(self._OUTPUT_SIZE)

        layout = QVBoxLayout()
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

class CompareOutput(QWidget):
    _OUTPUT_SIZE = 780

    def __init__(self):
        super().__init__()
        self._config_list = None
        self._filename_func = None
        self.setFixedWidth(self._OUTPUT_SIZE)

    def prepare_output(self):
        pass
