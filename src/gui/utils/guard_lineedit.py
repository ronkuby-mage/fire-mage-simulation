import json
from PyQt5.QtWidgets import (
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QWidget,
    QStackedWidget,
    QLabel,
    QHeaderView,
    QGroupBox
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class GuardLineEdit(QLineEdit):

    #currenttextedited = pyqtSignal(str)

    def __init__(self, ftype, max_val, min_val=0, required=False, parent=None):
        super(GuardLineEdit, self).__init__(parent)
        self._ftype = ftype
        self._min_val = min_val
        self._max_val = max_val
        self._required = required


        # any change to text, happens second
        # self.textChanged.connect(self.text_changed)

        # only user changes
        self.textEdited.connect(self.text_edited)

        # works!
        #self.Enter.connect(self.editing_finished)
        self.editingFinished.connect(self.editing_finished)
        self._last = None
        self._last_edit = None
        self._lock = False

    #def text_changed(self, text):
    #    print("text_changed", text)

    def pop_message(self, message):
        if not self._lock: # prevent double popup on enter
            self._lock = True
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(message)
            msg.setWindowTitle("Invalid Input")
            msg.exec()
            self._lock = False

    def text_edited(self, text):
        if self._ftype == "float":
            if text not in [".", ""]:
                try:
                    new_text = float(text)
                    self._last_edit = text
                except ValueError:
                    if self._last_edit is not None:
                        self.setText(self._last_edit)
                    else:
                        self.setText(self._last)
        elif self._ftype == "int":
            if text not in [""]:
                try:
                    new_text = int(text)
                    self._last_edit = text
                except ValueError:
                    if self._last_edit is not None:
                        self.setText(self._last_edit)
                    else:
                        self.setText(self._last)

    def editing_finished(self):
        text = self.text()
        self._last_edit = None
        if not text:
            if not self._required:
                return
            else:
                self.setText(self._last)
        if self._ftype == "float":
            try:
                value = float(text)
            except ValueError:
                self.pop_message("Not a floating point value.")
                self.setText(self._last)
                return
            if value < self._min_val or value > self._max_val:
                self.pop_message(f"Value out of bounds ({self._min_val:.1f}, {self._max_val:.1f}).")
                self.setText(self._last)
            else:
                if text[0] == '.':
                    text = "0" + text
                elif "." not in text:
                    text += ".0"
                self._last = text
                self.setText(text)
        elif self._ftype == "int":
            try:
                value = int(text)
            except ValueError:
                self.pop_message("Not an integer value.")
                self.setText(self._last)
                return
            if value < self._min_val or value > self._max_val:
                self.pop_message(f"Value out of bounds ({self._min_val:d}, {self._max_val:d}).")
                self.setText(self._last)
            else:
                self._last = text
                self.setText(text)

    def set_text(self, text):
        self._last = text
