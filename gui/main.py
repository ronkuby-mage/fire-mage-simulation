import sys
from PyQt5.QtWidgets import QApplication, QWidget
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
from PyQt5.QtCore import Qt
import qdarkstyle
from config_select import ConfigList


class Window(QWidget):

    _DEFAULT_HEIGHT = 800

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Mage Simulation")
        self.resize(1200, self._DEFAULT_HEIGHT)
        # Create a top-level layout
        self.toplayout = QVBoxLayout()
        # Create the tab widget with two tabs
        tabs = QTabWidget()
        tabs.addTab(self.generalTabUI(), "Simulation")
        tabs.addTab(self.networkTabUI(), "Scenario")
        self._config_list = ConfigList()

        self.toplayout.addWidget(tabs)
        self.toplayout.addWidget(self._config_list)
        self.setLayout(self.toplayout)
        self._last_height = None

        # enable custom window hint
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)

        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)        
        #self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

    def show(self):
        super().show()
        self._zero_height = self._config_list.geometry().height()
        self._last_height = self._zero_height

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._last_height is not None:
            current_height = self._config_list.geometry().height()
            if current_height != self._last_height:
                new_height = self._DEFAULT_HEIGHT - self._zero_height + current_height
                self.resize(1200, new_height)
                self._last_height = current_height

    def generalTabUI(self):
        """Create the General page UI."""
        generalTab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QCheckBox("General Option 1"))
        layout.addWidget(QCheckBox("General Option 2"))
        generalTab.setLayout(layout)
        return generalTab

    def networkTabUI(self):
        """Create the Network page UI."""
        networkTab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QCheckBox("Network Option 1"))
        layout.addWidget(QCheckBox("Network Option 2"))
        networkTab.setLayout(layout)
        return networkTab

if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.show()
    sys.exit(app.exec_())
