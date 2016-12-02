# coding:utf-8
# author: Wang Chao
# date: 2016.11.24

from PyQt4 import QtGui
from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import time
import copy
import serial
import serial.tools.list_ports
from collections import OrderedDict


class MyLabel(QtGui.QLabel):
    def __init__(self, *args):
        super(MyLabel, self).__init__(*args)
        self.setFont(QtGui.QFont("Calibri", 10))
        # self.setFixedSize(100, 20)


class MyButton(QtGui.QPushButton):
    def __init__(self, *args):
        super(MyButton, self).__init__(*args)
        self.setFont(QtGui.QFont("Calibri", 11))
        self.setFixedSize(150, 50)


class MyGeneralThread(QtCore.QThread):

    def __init__(self, parent=None):
        super(MyGeneralThread, self).__init__(parent)
        self.function = None

    def set_thread_function(self, function):
        self.function = function

    def run(self):
        self.function()


class MplCanvas(FigureCanvas):
    """
    My Canvas
    """
    def __init__(self,
                 title='RSSI (dbm)',
                 start_freq=850,
                 stop_freq=928,
                 high_limit_rssi=-10,
                 low_limit_rssi=-130):
        """
        :param title:
        :param start_freq: default 850
        :param stop_freq: default 928
        :param high_limit_rssi: default -10
        :param low_limit_rssi: default -130
        """
        self.fig = Figure(figsize=(20, 20))
        super(MplCanvas, self).__init__(self.fig)
        self.start_freq = start_freq
        self.stop_freq = stop_freq
        self.high_limit_rssi = high_limit_rssi
        self.low_limit_rssi = low_limit_rssi
        self.ax = self.fig.add_subplot(111)
        self.ax.xaxis.grid(True, which='major')
        self.ax.yaxis.grid(True, which='major')
        self.ax.set_xlim(self.start_freq, self.stop_freq)
        self.ax.set_ylim(self.low_limit_rssi, self.high_limit_rssi)
        self.title = title
        self.ax.set_title('Spectrum Analyzer', fontsize=16)
        self.ax.set_ylabel(self.title, fontsize=14)
        self.ax.set_xlabel('Frequency (MHz)', fontsize=14)

        self.index_list = []
        self.value_list = []

        self.draw_enable_flag = True
        self.drawing_flag = False
        self.accumulate_flag = False

        self.mark_x = None
        self.mark_y = None

        self.mpl_connect("button_press_event", self.on_press)

    def on_press(self, event):
        if event.xdata is not None and event.ydata is not None:
            self.mark_x = event.xdata
            self.mark_y = event.ydata
            self.emit(QtCore.SIGNAL('canvasClickedAt(float, float)'), self.mark_x, self.mark_y)

    def draw_data(self, x, y):
        if self.draw_enable_flag is False:
            return
        self.drawing_flag = True
        try:
            if self.accumulate_flag is False:
                self.ax.clear()
            self.ax.xaxis.grid(True, which='major')
            self.ax.yaxis.grid(True, which='major')
            self.ax.set_xlim(self.start_freq, self.stop_freq)
            self.ax.set_ylim(self.low_limit_rssi, self.high_limit_rssi)
            self.ax.set_title('Spectrum Analyzer', fontsize=16)
            self.ax.set_ylabel(self.title, fontsize=14)
            self.ax.set_xlabel('Frequency (MHz)', fontsize=14)
            self.ax.scatter(self.mark_x, self.mark_y, c='r', s=200, marker='+')
            self.ax.plot(x, y, color="blue", linewidth=1)
            self.draw()
        except Exception as e:
            print(e)
            return
        self.drawing_flag = False

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            try:
                super(MplCanvas, self).mousePressEvent(event)
            except Exception as e:
                print(e)

    def mouseDoubleClickEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def wheelEvent(self, event):
        pass

    def keyPressEvent(self, event):
        pass

    def keyReleaseEvent(self, event):
        pass

    def resizeEvent(self, event):
        self.draw_enable_flag = False
        while self.drawing_flag is True:
            continue
        super(MplCanvas, self).resizeEvent(event)
        self.draw_enable_flag = True


class MainWindow(QtGui.QMainWindow):
    def __init__(self, force_port_num=None, parent=None):
        super(MainWindow, self).__init__(parent)
        self.force_port_num = force_port_num
        # self.setFixedSize(800, 500)
        self.resize(800, 500)
        # self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowTitle('Spectrum Analyzer')

        self.portLabel = MyLabel('Serial Port :')
        self.markLabel = MyLabel('Mark Position :')

        self.freq_canvas = MplCanvas()
        self.connect(self.freq_canvas, QtCore.SIGNAL('canvasClickedAt(float, float)'), self.show_click_position)

        self.realTimeButton = MyButton('RealTime\nMode', self)
        self.connect(self.realTimeButton, QtCore.SIGNAL('clicked()'), self.show_real_time)
        self.accumulateButton = MyButton('Accumulate\nMode', self)
        self.connect(self.accumulateButton, QtCore.SIGNAL('clicked()'), self.show_accumulate)
        self.maxButton = MyButton('Maximum\nMode', self)
        self.connect(self.maxButton, QtCore.SIGNAL('clicked()'), self.show_max)
        self.startButton = MyButton('Start', self)
        self.startButton.setFont(QtGui.QFont("Calibri", 15))
        self.connect(self.startButton, QtCore.SIGNAL('clicked()'), self.start_show)
        self.stopButton = MyButton('Stop', self)
        self.stopButton.setFont(QtGui.QFont("Calibri", 15))
        self.connect(self.stopButton, QtCore.SIGNAL('clicked()'), self.stop_show)

        self.main_frame = QtGui.QFrame()
        self.main_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        grid = QtGui.QGridLayout()
        grid.addWidget(self.portLabel, 0, 0, 1, 3, QtCore.Qt.AlignLeft)
        grid.addWidget(self.markLabel, 0, 3, 1, 2, QtCore.Qt.AlignLeft)
        grid.addWidget(self.freq_canvas, 1, 0, 1, 5, QtCore.Qt.AlignCenter)
        grid.addWidget(self.realTimeButton, 2, 0, 1, 1, QtCore.Qt.AlignCenter)
        grid.addWidget(self.accumulateButton, 2, 1, 1, 1, QtCore.Qt.AlignCenter)
        grid.addWidget(self.maxButton, 2, 2, 1, 1, QtCore.Qt.AlignCenter)
        grid.addWidget(self.startButton, 2, 3, 1, 1, QtCore.Qt.AlignCenter)
        grid.addWidget(self.stopButton, 2, 4, 1, 1, QtCore.Qt.AlignCenter)
        self.main_frame.setLayout(grid)
        self.setCentralWidget(self.main_frame)

        self.freq_canvas.draw_enable_flag = False
        # self.show_accumulate_flag = False
        self.show_max_flag = False
        self.stop_show_flag = False

        self.data = OrderedDict()

        # thread to draw the canvas
        self.drawCanvasThread = MyGeneralThread()
        self.drawCanvasThread.set_thread_function(self.draw_canvas)
        # thread to get the data
        self.getDataThread = MyGeneralThread()
        self.getDataThread.set_thread_function(self.get_data)

        self.serial_port = serial.Serial()
        self.serial_port.baudrate = 115200
        self.serial_port.timeout = None
        # get the serial port list
        self.port_list = list(serial.tools.list_ports.comports())

    @QtCore.pyqtSlot()
    def show_accumulate(self):
        self.freq_canvas.accumulate_flag = True
        self.show_max_flag = False
        self.accumulateButton.setDisabled(True)
        self.realTimeButton.setDisabled(False)
        self.maxButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def show_real_time(self):
        self.freq_canvas.accumulate_flag = False
        self.show_max_flag = False
        self.accumulateButton.setDisabled(False)
        self.realTimeButton.setDisabled(True)
        self.maxButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def show_max(self):
        self.freq_canvas.accumulate_flag = False
        self.show_max_flag = True
        self.accumulateButton.setDisabled(False)
        self.realTimeButton.setDisabled(False)
        self.maxButton.setDisabled(True)

    @QtCore.pyqtSlot()
    def start_show(self):
        self.stop_show_flag = False
        self.startButton.setDisabled(True)
        self.stopButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def stop_show(self):
        self.stop_show_flag = True
        self.startButton.setDisabled(False)
        self.stopButton.setDisabled(True)

    @QtCore.pyqtSlot()
    def show_click_position(self):
        self.markLabel.setText('Mark Position :' +
                               ('    %.2f MHz' % self.freq_canvas.mark_x) +
                               ('    %.2f dbm' % self.freq_canvas.mark_y))

    def run(self):
        for f_pre in range(8500, 9280):
            self.data[(float(f_pre)/10)] = None

        # set the serial port number
        auto_set_port = False
        for port in self.port_list:
            if port[1].startswith('Prolific') or port[1].startswith('USB-SERIAL CH340'):
                self.serial_port.port = port[0]
                self.portLabel.setText('Serial Port :  ' + port[1])
                auto_set_port = True
        if auto_set_port is False:
            self.portLabel.setText('Serial Port :  ' + 'Not find serial port!')
            print('Did not find serial port!')

        if self.force_port_num is not None:
            self.serial_port.port = self.force_port_num
            self.portLabel.setText('Serial Port :  ' + self.force_port_num)
        try:
            self.serial_port.open()
        except Exception as e:
            print(e)
            return
        self.getDataThread.start(QtCore.QThread.HighPriority)
        time.sleep(0.1)
        self.drawCanvasThread.start(QtCore.QThread.LowPriority)
        self.realTimeButton.setDisabled(True)
        self.startButton.setDisabled(True)

    # function of thread to draw the canvas
    def draw_canvas(self):
        while True:
            # time.sleep(0.1)
            if self.freq_canvas.draw_enable_flag is True and self.stop_show_flag is False:
                # OrderedDict(sorted(self.data.items(), key=lambda t: t[1]))
                x = copy.copy(self.data.keys())
                y = copy.copy(self.data.values())
                # print(x)
                if len(x) != len(y):
                    print(len(x), len(y))
                    continue
                self.freq_canvas.draw_data(x, y)

    # function of thread to get the data
    def get_data(self):
        while True:
            line = self.serial_port.readline()
            if self.stop_show_flag is True:
                continue
            if not line.startswith('~'):
                print(line)
                continue
            line_list = line.split('#')
            try:
                freq = float(line_list[1]) / 10
                rssi = int(line_list[2])
            except Exception as e:
                print(e)
                continue

            self.freq_canvas.draw_enable_flag = False
            if self.show_max_flag is True:
                if rssi > self.data[freq]:
                    self.data[freq] = rssi
            else:
                self.data[freq] = rssi
            self.freq_canvas.draw_enable_flag = True

# ======================================================================================================================
# ======================================================================================================================

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ui = MainWindow(force_port_num=None)
    ui.show()
    ui.run()
    sys.exit(app.exec_())
