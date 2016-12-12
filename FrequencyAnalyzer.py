# coding:utf-8
# author: Wang Chao
# File: FrequencyAnalyzer.py
# date: 2016.11.30

from PyQt4 import QtGui
from PyQt4 import QtCore
import sys
import time
import serial
import serial.tools.list_ports
from collections import OrderedDict
from mplCanvas import MplCanvas
from controls import MyEdit, MyLabel, MyButton, MyComboBox
from drawThread import DrawCanvasThread
from getDataThread import GetDataThread
# _fromUtf8 = QtCore.QString.fromUtf8


# ========================================== Main Window Class =========================================================

class MainWindow(QtGui.QMainWindow):

    stop_thread_signal = QtCore.pyqtSignal()

    # thread_enable_draw_signal = QtCore.pyqtSignal()

    def __init__(self, force_port_num=None, parent=None):
        super(MainWindow, self).__init__(parent)
        self.force_port_num = force_port_num
        # self.setFixedSize(800, 500)
        self.resize(800, 600)
        # self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowTitle('Frequency Analyzer')

        # self.freqPointLabel = MyLabel('Frequency\nPoint (MHz) :')
        # self.freqPointLabel.setAlignment(QtCore.Qt.AlignCenter)
        # self.freqPointLabel.setFont(QtGui.QFont("Calibri", 12))
        self.freqPointEdit = MyEdit('908.0')
        self.freqPointEdit.setFont(QtGui.QFont("Calibri", 16))
        self.freqPointEdit.setFixedWidth(60)
        self.connect(self.freqPointEdit, QtCore.SIGNAL('returnPressed()'), self.freq_point_change)

        self.spectrumModeButton = MyButton('Spectrum\nAnalysis')
        self.spectrumModeButton.setFont(QtGui.QFont("Aharoni", 12))
        self.spectrumModeButton.setDisabled(True)
        self.connect(self.spectrumModeButton, QtCore.SIGNAL('clicked()'), self.spectrum_mode)
        self.timeModeButton = MyButton('Freq Point\nAnalysis')
        self.timeModeButton.setFont(QtGui.QFont("Aharoni", 13))
        self.connect(self.timeModeButton, QtCore.SIGNAL('clicked()'), self.time_mode)

        self.serialPortLabel = MyLabel('Serial Port :')
        self.serialPortComboBox = MyComboBox()
        self.serialPortComboBox.pressed_signal.connect(self.press_serial_port_combobox)
        self.serialPortChangeButton = QtGui.QPushButton('Change Serial\nPort')
        self.connect(self.serialPortChangeButton, QtCore.SIGNAL('clicked()'), self.change_serial_port)

        self.show_canvas = MplCanvas()
        self.show_canvas.canvas_clicked_signal.connect(self.show_click_position)

        self.startFreqShowLabel = MyLabel('Start Freq (MHz):')
        self.startFreqShowEdit = MyEdit('850.0')
        self.startFreqShowEdit.setFixedWidth(50)
        self.connect(self.startFreqShowEdit, QtCore.SIGNAL('returnPressed()'), self.start_stop_freq_show_change)
        self.stopFreqShowLabel = MyLabel('Stop Freq (MHz):')
        self.stopFreqShowEdit = MyEdit('928.0')
        self.stopFreqShowEdit.setFixedWidth(50)
        self.connect(self.stopFreqShowEdit, QtCore.SIGNAL('returnPressed()'), self.start_stop_freq_show_change)
        self.setDefaultFreqButton = QtGui.QPushButton('Set Default')
        self.setDefaultFreqButton.setFixedWidth(100)
        self.connect(self.setDefaultFreqButton, QtCore.SIGNAL('clicked()'), self.set_default_freq_start_stop)

        self.time_mode_x_show_length = 5
        self.show_canvas.canvas_time_mode_x_show_length = self.time_mode_x_show_length
        self.timeScaleLabel = MyLabel('Time Scale (Seconds):')
        self.timeScaleEdit = MyEdit(str(self.time_mode_x_show_length))
        self.timeScaleEdit.setFixedWidth(40)
        self.timeScaleEdit.setDisabled(True)
        self.connect(self.timeScaleEdit, QtCore.SIGNAL('returnPressed()'), self.time_scale_change)

        self.mark1Button = QtGui.QPushButton('Mark1')
        self.mark1Button.setDisabled(True)
        self.mark1Button.setStyleSheet('''color:red''')
        self.connect(self.mark1Button, QtCore.SIGNAL('clicked()'), self.mark1_button_clicked)
        self.mark2Button = QtGui.QPushButton('Mark2')
        self.mark2Button.setStyleSheet('''color:green''')
        self.connect(self.mark2Button, QtCore.SIGNAL('clicked()'), self.mark2_button_clicked)
        self.mark1Label = MyLabel()
        mark1_pe = QtGui.QPalette()
        mark1_pe.setColor(QtGui.QPalette.WindowText, QtCore.Qt.red)
        self.mark1Label.setPalette(mark1_pe)
        self.mark2Label = MyLabel()
        mark2_pe = QtGui.QPalette()
        mark2_pe.setColor(QtGui.QPalette.WindowText, QtCore.Qt.darkGreen)
        self.mark2Label.setPalette(mark2_pe)
        self.deltaTitleLabel = MyLabel('Delta ')
        self.deltaContentLabel = MyLabel()
        delta_pe = QtGui.QPalette()
        delta_pe.setColor(QtGui.QPalette.WindowText, QtCore.Qt.darkGray)
        self.deltaTitleLabel.setPalette(delta_pe)
        self.deltaContentLabel.setPalette(delta_pe)

        self.realTimeButton = MyButton('RealTime', self)
        self.connect(self.realTimeButton, QtCore.SIGNAL('clicked()'), self.show_real_time)
        self.accumulateButton = MyButton('Accumulate', self)
        self.connect(self.accumulateButton, QtCore.SIGNAL('clicked()'), self.show_accumulate)
        self.maxButton = MyButton('Maximum', self)
        self.connect(self.maxButton, QtCore.SIGNAL('clicked()'), self.show_max)
        self.startButton = MyButton('Start', self)
        self.startButton.setFont(QtGui.QFont("Calibri", 15))
        self.connect(self.startButton, QtCore.SIGNAL('clicked()'), self.start_show)
        self.stopButton = MyButton('Stop', self)
        self.stopButton.setFont(QtGui.QFont("Calibri", 15))
        self.connect(self.stopButton, QtCore.SIGNAL('clicked()'), self.stop_show)

        self.frame1 = QtGui.QFrame()
        self.frame1.setFrameShape(QtGui.QFrame.StyledPanel)
        frame1_grid = QtGui.QGridLayout()
        frame1_grid.addWidget(self.spectrumModeButton, 0, 0, 1, 1, QtCore.Qt.AlignCenter)
        # frame1_grid.addWidget(self.freqPointLabel, 0, 1, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.timeModeButton, 0, 1, 1, 1, QtCore.Qt.AlignCenter)
        frame1_grid.addWidget(self.freqPointEdit, 0, 2, 1, 1, QtCore.Qt.AlignLeft)
        frame1_grid.addWidget(self.serialPortLabel, 0, 4, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.serialPortComboBox, 0, 5, 1, 1, QtCore.Qt.AlignLeft)
        frame1_grid.addWidget(self.serialPortChangeButton, 0, 6, 1, 1, QtCore.Qt.AlignLeft)

        frame1_grid.addWidget(self.show_canvas, 1, 0, 1, 7, QtCore.Qt.AlignCenter)

        # grid.addWidget(testEdit, 6, 0, 1, 6, QtCore.Qt.AlignCenter)
        # grid.addWidget(self.mark_frame, 2, 3, 2, 3, QtCore.Qt.AlignRight)

        frame1_grid.addWidget(self.startFreqShowLabel, 2, 0, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.startFreqShowEdit, 2, 1, 1, 1, QtCore.Qt.AlignLeft)
        frame1_grid.addWidget(self.stopFreqShowLabel, 3, 0, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.stopFreqShowEdit, 3, 1, 1, 1, QtCore.Qt.AlignLeft)
        frame1_grid.addWidget(self.setDefaultFreqButton, 4, 0, 1, 1, QtCore.Qt.AlignRight)

        frame1_grid.addWidget(self.timeScaleLabel, 2, 2, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.timeScaleEdit, 2, 3, 1, 1, QtCore.Qt.AlignLeft)

        frame1_grid.addWidget(self.mark1Button, 2, 4, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.mark1Label, 2, 5, 1, 2, QtCore.Qt.AlignLeft)
        frame1_grid.addWidget(self.mark2Button, 3, 4, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.mark2Label, 3, 5, 1, 2, QtCore.Qt.AlignLeft)
        frame1_grid.addWidget(self.deltaTitleLabel, 4, 4, 1, 1, QtCore.Qt.AlignRight)
        frame1_grid.addWidget(self.deltaContentLabel, 4, 5, 1, 2, QtCore.Qt.AlignLeft)

        # self.frame1.setLayout(frame1_grid)
        #
        # self.frame2 = QtGui.QFrame()
        # self.frame2.setFrameShape(QtGui.QFrame.StyledPanel)
        # frame2_grid = QtGui.QGridLayout()

        frame1_grid.addWidget(self.realTimeButton, 5, 0, 1, 1, QtCore.Qt.AlignCenter)
        frame1_grid.addWidget(self.accumulateButton, 5, 1, 1, 1, QtCore.Qt.AlignCenter)
        frame1_grid.addWidget(self.maxButton, 5, 2, 1, 1, QtCore.Qt.AlignCenter)
        frame1_grid.addWidget(self.startButton, 5, 5, 1, 1, QtCore.Qt.AlignCenter)
        frame1_grid.addWidget(self.stopButton, 5, 6, 1, 1, QtCore.Qt.AlignCenter)

        self.frame1.setLayout(frame1_grid)

        # splitter_vertical = QtGui.QSplitter(QtCore.Qt.Vertical)
        # splitter_vertical.addWidget(self.frame1)
        # splitter_vertical.addWidget(self.frame2)

        self.setCentralWidget(self.frame1)

        self.statusBar = QtGui.QStatusBar(self)
        self.statusBar.setObjectName('statusBar')
        self.setStatusBar(self.statusBar)
        self.statusLeftLabel = QtGui.QLabel('')
        self.statusLeftLabel.setAlignment(QtCore.Qt.AlignLeft)
        # self.statusBar.addPermanentWidget(self.statusLeftLabel, 0)
        self.statusBar.addWidget(self.statusLeftLabel, 0)

        self.show_canvas.draw_enable_flag = True
        # self.show_accumulate_flag = False
        self.show_max_flag = False
        # self.stop_show_flag = False
        self.show_mode = 'spectrum'
        self.stop_get_data_flag = False
        # for starting mode match
        self.mode_changing_flag = True
        self.time_mode_frequency = 0
        self.time_mode_start_time = 0

        self.spectrum_data = OrderedDict()
        self.time_data_x = []
        self.time_data_y = []

        # thread to draw the canvas
        self.drawCanvasThread = DrawCanvasThread(self, self.show_canvas)
        # self.connect(self.drawCanvasThread, QtCore.SIGNAL('draw_canvas_signal(float)'), self.draw_canvas)
        # self.drawCanvasThread.draw_canvas_signal.connect(self.draw_canvas)
        # self.thread_enable_draw_signal.connect(self.drawCanvasThread.enable_draw)
        # thread to get the data
        self.getDataThread = GetDataThread(self)
        # self.getDataThread.set_thread_function(self.get_data)

        self.serial_port = serial.Serial()
        self.serial_port.baudrate = 115200
        self.serial_port.timeout = 0.1
        # get the serial port list
        self.port_list = list(serial.tools.list_ports.comports())
        for p in self.port_list:
            self.serialPortComboBox.addItem(p[0])

        self.stop_thread_signal.connect(self.drawCanvasThread.stop)
        self.stop_thread_signal.connect(self.getDataThread.stop)

        self.init_serial_port()
        self.start()

    # @staticmethod
    # def draw_canvas(self, x, y):
    #     # print('draw_canvas')
    #     if self.show_mode == 'spectrum':
    #         self.show_canvas.draw_data(x, y, self.show_mode)
    #     if self.show_mode == 'time':
    #         draw_title = ('%.1f' % (float(self.main_window.time_mode_frequency) / 10)) + 'MHz Signal Strength'
    #         self.show_canvas.draw_data(x, y, self.show_mode, title=draw_title)
    #     self.thread_enable_draw_signal.emit()

    @QtCore.pyqtSlot()
    def press_serial_port_combobox(self):
        print('refresh serial port list..')
        self.serialPortComboBox.clear()
        self.port_list = list(serial.tools.list_ports.comports())
        for p in self.port_list:
            self.serialPortComboBox.addItem(p[0])

    @QtCore.pyqtSlot()
    def mark1_button_clicked(self):
        self.show_canvas.mark_number = 1
        self.mark1Button.setDisabled(True)
        self.mark2Button.setDisabled(False)

    @QtCore.pyqtSlot()
    def mark2_button_clicked(self):
        self.show_canvas.mark_number = 2
        self.mark1Button.setDisabled(False)
        self.mark2Button.setDisabled(True)

    @QtCore.pyqtSlot()
    def set_default_freq_start_stop(self):
        self.show_canvas.start_freq = 850
        self.startFreqShowEdit.setText('850.0')
        self.show_canvas.stop_freq = 928
        self.stopFreqShowEdit.setText('928.0')

    @QtCore.pyqtSlot()
    def time_scale_change(self):
        try:
            time_scale_pre = float(self.timeScaleEdit.text())
        except Exception as e:
            print(e)
            return
        if time_scale_pre < 0.1:
            print('time scale too small')
            return
        if time_scale_pre > 3600:
            print('time scale too long')
            return
        self.time_mode_x_show_length = time_scale_pre
        self.show_canvas.canvas_time_mode_x_show_length = self.time_mode_x_show_length
        self.set_freq_point()
        self.mode_changing_flag = True

    @QtCore.pyqtSlot()
    def start_stop_freq_show_change(self):
        if len(self.startFreqShowEdit.text()) < 3 or len(self.startFreqShowEdit.text()) > 5:
            print('wrong frequency length, please enter like \'XXX.X\' or \'XXX\'')
        try:
            start_freq_show_pre = float(self.startFreqShowEdit.text())
        except Exception as e:
            print(e)
            return
        if start_freq_show_pre < 850 or start_freq_show_pre > self.show_canvas.stop_freq:
            print('wrong frequency, range:850 to %d' % self.show_canvas.stop_freq)
            return

        if len(self.stopFreqShowEdit.text()) < 3 or len(self.stopFreqShowEdit.text()) > 5:
            print('wrong frequency length, please enter like \'XXX.X\' or \'XXX\'')
        try:
            stop_freq_show_pre = float(self.stopFreqShowEdit.text())
        except Exception as e:
            print(e)
            return
        if stop_freq_show_pre < self.show_canvas.start_freq or stop_freq_show_pre > 928:
            print('wrong frequency, range:%d to 928' % self.show_canvas.start_freq)
            return

        self.show_canvas.start_freq = start_freq_show_pre
        self.show_canvas.stop_freq = stop_freq_show_pre

    def set_freq_point(self):
        if len(self.freqPointEdit.text()) < 3 or len(self.freqPointEdit.text()) > 5:
            print('wrong frequency length, please enter like \'XXX.X\' or \'XXX\'')
        try:
            time_mode_frequency_pre = float(self.freqPointEdit.text())
        except Exception as e:
            print(e)
            return
        if time_mode_frequency_pre < 850 or time_mode_frequency_pre > 928:
            print('wrong frequency, range:850 to 928')
            return
        self.time_mode_frequency = int(time_mode_frequency_pre * 10)
        print('set frequency: %f' % (float(self.time_mode_frequency)/10))
        self.clear_mark()

    def clear_mark(self):
        self.show_canvas.mark_number = 1
        self.show_canvas.mark1_x = None
        self.show_canvas.mark1_y = None
        self.show_canvas.mark2_x = None
        self.show_canvas.mark2_x = None
        self.mark1Label.setText('')
        self.mark2Label.setText('')
        self.deltaContentLabel.setText('')
        self.mark1_button_clicked()

    @QtCore.pyqtSlot()
    def freq_point_change(self):
        if self.show_mode != 'time':
            self.time_mode()
        else:
            self.set_freq_point()
            self.mode_changing_flag = True

    @QtCore.pyqtSlot()
    def time_mode(self):
        self.set_freq_point()
        print('start change mode to time mode...')
        self.show_mode = 'time'
        self.mode_changing_flag = True
        self.startFreqShowEdit.setDisabled(True)
        self.stopFreqShowEdit.setDisabled(True)
        self.setDefaultFreqButton.setDisabled(True)
        self.timeScaleEdit.setDisabled(False)
        self.realTimeButton.hide()
        self.accumulateButton.hide()
        self.maxButton.hide()
        self.spectrumModeButton.setDisabled(False)
        self.timeModeButton.setDisabled(True)

    @QtCore.pyqtSlot()
    def spectrum_mode(self):
        # if self.show_mode == 'spectrum':
        #     print('already spectrum mode')
        #     return
        print('start change mode to spectrum mode...')
        self.show_mode = 'spectrum'
        self.mode_changing_flag = True
        self.startFreqShowEdit.setDisabled(False)
        self.stopFreqShowEdit.setDisabled(False)
        self.setDefaultFreqButton.setDisabled(False)
        self.timeScaleEdit.setDisabled(True)
        self.clear_mark()
        self.realTimeButton.show()
        self.accumulateButton.show()
        self.maxButton.show()
        self.realTimeButton.setDisabled(True)
        self.accumulateButton.setDisabled(False)
        self.maxButton.setDisabled(False)
        self.spectrumModeButton.setDisabled(True)
        self.timeModeButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def show_real_time(self):
        self.show_canvas.accumulate_flag = False
        self.show_max_flag = False
        self.realTimeButton.setDisabled(True)
        self.accumulateButton.setDisabled(False)
        self.maxButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def show_accumulate(self):
        self.show_canvas.accumulate_flag = True
        self.show_max_flag = False
        self.realTimeButton.setDisabled(False)
        self.accumulateButton.setDisabled(True)
        self.maxButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def show_max(self):
        self.show_canvas.accumulate_flag = False
        self.show_max_flag = True
        self.realTimeButton.setDisabled(False)
        self.accumulateButton.setDisabled(False)
        self.maxButton.setDisabled(True)

    @QtCore.pyqtSlot()
    def start_show(self):
        if self.show_mode == 'time':
            self.time_mode_start_time = time.time()
            self.time_data_x = []
            self.time_data_y = []
            # this equal to the up 3
            # self.mode_changing_flag = True
            # clean the serial port buffer
        self.serial_port.close()
        self.serial_port.open()
        self.stop_get_data_flag = False
        # self.show_canvas.draw_enable_flag = True
        self.startButton.setDisabled(True)
        self.stopButton.setDisabled(False)

    @QtCore.pyqtSlot()
    def stop_show(self):
        self.stop_get_data_flag = True
        # self.show_canvas.draw_enable_flag = False
        self.startButton.setDisabled(False)
        self.stopButton.setDisabled(True)

    @QtCore.pyqtSlot()
    def show_click_position(self):
        if self.show_mode == 'spectrum':
            if self.show_canvas.mark_number == 1:
                self.mark1Label.setText((':    %.2f MHz' % self.show_canvas.mark1_x) +
                                        (':    %.2f dbm' % self.show_canvas.mark1_y))
            elif self.show_canvas.mark_number == 2:
                self.mark2Label.setText((':    %.2f MHz' % self.show_canvas.mark2_x) +
                                        (':    %.2f dbm' % self.show_canvas.mark2_y))
            if self.show_canvas.mark1_x is not None and \
                    self.show_canvas.mark1_y is not None and \
                    self.show_canvas.mark2_x is not None and \
                    self.show_canvas.mark2_y is not None:
                self.deltaContentLabel.setText(
                    (':     %.2f MHz' % (self.show_canvas.mark2_x - self.show_canvas.mark1_x)) +
                    (':      %.2f dbm' % (self.show_canvas.mark2_y - self.show_canvas.mark1_y)))
        elif self.show_mode == 'time':
            if self.show_canvas.mark_number == 1:
                self.mark1Label.setText((':    %.6f second' % self.show_canvas.mark1_x) +
                                        (':    %.2f dbm' % self.show_canvas.mark1_y))
            elif self.show_canvas.mark_number == 2:
                self.mark2Label.setText((':    %.6f second' % self.show_canvas.mark2_x) +
                                        (':    %.2f dbm' % self.show_canvas.mark2_y))
            if self.show_canvas.mark1_x is not None and \
                    self.show_canvas.mark1_y is not None and \
                    self.show_canvas.mark2_x is not None and \
                    self.show_canvas.mark2_y is not None:
                self.deltaContentLabel.setText(
                    (':     %.6f second' % (self.show_canvas.mark2_x - self.show_canvas.mark1_x)) +
                    (':      %.2f dbm' % (self.show_canvas.mark2_y - self.show_canvas.mark1_y)))

    @QtCore.pyqtSlot()
    def change_serial_port(self):
        if self.serial_port.isOpen():
            print('port: %s is opening, now close' % self.serial_port.port)
            self.getDataThread.close_port_flag = True
            time.sleep(0.3)

        if self.serial_port.isOpen():
            print('port: %s still open' % self.serial_port.port)
            return
        else:
            print('port: %s closed!' % self.serial_port.port)
        self.serial_port.port = str(self.serialPortComboBox.currentText())
        self.statusLeftLabel.setText('Serial Port :  ' + self.serial_port.port)
        self.start()

    def init_serial_port(self):
        # set the serial port number
        auto_set_port = False
        for port in self.port_list:
            print(port[1].decode("GB2312"))
            # print(port[1].decode( "GBK"))
            if port[1].startswith('Prolific') or port[1].startswith('USB-SERIAL CH340'):
                self.serial_port.port = port[0]
                self.statusLeftLabel.setText('Serial Port :  ' + port[1])
                # set the ComboBox to correct port
                for index in range(self.serialPortComboBox.count()):
                    if port[0] == self.serialPortComboBox.itemText(index):
                        self.serialPortComboBox.setCurrentIndex(index)
                auto_set_port = True
        if auto_set_port is False:
            self.statusLeftLabel.setText('Serial Port :  ' + 'Not find serial port!')
            print('Did not find serial port!')

        if self.force_port_num is not None:
            self.serial_port.port = self.force_port_num
            self.statusLeftLabel.setText('Serial Port :  ' + self.force_port_num)

    def start(self):
        try:
            self.serial_port.open()
            print('open serial port %s' % self.serial_port.port)
        except Exception as e:
            self.statusLeftLabel.setText('Serial Port :  ' + e.message)
            print(e)
            return

        for f_pre in range(8500, 9280):
            self.spectrum_data[(float(f_pre)/10)] = None
        self.mode_changing_flag = True
        # print(self.getDataThread.isRunning())
        self.getDataThread.start(QtCore.QThread.HighPriority)
        time.sleep(0.1)
        self.drawCanvasThread.start(QtCore.QThread.LowPriority)
        self.realTimeButton.setDisabled(True)
        self.startButton.setDisabled(True)
        # print(self.getDataThread.isRunning())

    def closeEvent(self, *args, **kwargs):
        self.stop_thread_signal.emit()
        # self.serial_port.close()
        super(MainWindow, self).closeEvent(*args, **kwargs)

# ======================================================================================================================
# ======================================================================================================================

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ui = MainWindow(force_port_num=None)
    ui.show()
    sys.exit(app.exec_())
