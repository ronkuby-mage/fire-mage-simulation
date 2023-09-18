import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QCheckBox,
    QWidget,
    QLabel
)
import qdarkstyle
from .config_select import ConfigListWidget
from .scenario import Scenario
from ..sim.config import ConfigList

class Window(QWidget):

    _DEFAULT_WIDTH = 1200
    _DEFAULT_HEIGHT = 800
    _CONFIG_DIRECTORY = "./data/scenarios/"
    _CONFIG_DEFAULT = "default.json"

    def __init__(self):
        super().__init__()

        self.config_list = ConfigList(self._CONFIG_DIRECTORY, self._CONFIG_DEFAULT)

        self.setWindowTitle("Fire Mage Simulation")
        self.resize(self._DEFAULT_WIDTH, self._DEFAULT_HEIGHT)
        # Create a top-level layout
        self.toplayout = QVBoxLayout()
        # Create the tab widget with two tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.generalTabUI(), "Simulation")
        self._scenario = Scenario(self.config_list)
        self.tabs.addTab(self._scenario, "Scenario")
        self._config_widget = ConfigListWidget(self.config_list, self._scenario.update, expand=False)
        self._scenario.set_changed_trigger(self._config_widget.changed_trigger)

        self.toplayout.addWidget(self.tabs)
        self.toplayout.addWidget(self._config_widget)
        self.setLayout(self.toplayout)
        self._last_height = None

        # enable custom window hint
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)

        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)        
        #self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

    def show(self):
        super().show()
        self._zero_height = self._config_widget.geometry().height()
        self._last_height = self._zero_height

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._last_height is not None:
            current_height = self._config_widget.geometry().height()
            if current_height != self._last_height:
                new_height = self._DEFAULT_HEIGHT - self._zero_height + current_height
                self.resize(self._DEFAULT_WIDTH, new_height)
                self._last_height = current_height

    def generalTabUI(self):
        """Create the General page UI."""
        generalTab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QCheckBox("General Option 1"))
        layout.addWidget(QCheckBox("General Option 2"))
        generalTab.setLayout(layout)
        return generalTab

if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.show()
    sys.exit(app.exec_())
