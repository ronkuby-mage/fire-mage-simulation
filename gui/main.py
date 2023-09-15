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
)
import qdarkstyle
#from style import QDarkPalette

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Mage Simulation")
        self.resize(1000, 800)
        # Create a top-level layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Create the tab widget with two tabs
        tabs = QTabWidget()
        tabs.addTab(self.generalTabUI(), "General")
        tabs.addTab(self.networkTabUI(), "Network")
        tabs.setAutoFillBackground(True)
        layout.addWidget(tabs)

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
