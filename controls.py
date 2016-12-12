# coding:utf-8
# author: Wang Chao

from PyQt4 import QtGui
from PyQt4 import QtCore


class MyLabel(QtGui.QLabel):
    def __init__(self, *args):
        super(MyLabel, self).__init__(*args)
        self.setFont(QtGui.QFont("Calibri", 10))
        # self.setFixedSize(100, 20)


class MyEdit(QtGui.QLineEdit):
    def __init__(self, *args):
        super(MyEdit, self).__init__(*args)
        self.setFont(QtGui.QFont("Calibri", 10))
        # self.setFixedSize(100, 20)


class MyButton(QtGui.QPushButton):
    def __init__(self, *args):
        super(MyButton, self).__init__(*args)
        self.setFont(QtGui.QFont("Calibri", 11))
        self.setFixedSize(100, 50)


class MyComboBox(QtGui.QComboBox):

    pressed_signal = QtCore.pyqtSignal()

    def __init__(self, *args):
        super(MyComboBox, self).__init__(*args)
        self.setFont(QtGui.QFont("Calibri", 10))
        self.setFixedSize(80, 20)

    def mousePressEvent(self, QMouseEvent):
        super(MyComboBox, self).mousePressEvent(QMouseEvent)
        self.pressed_signal.emit()
