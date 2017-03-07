# coding:utf-8
# author: Wang Chao

from PyQt4 import QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):

    canvas_clicked_signal = QtCore.pyqtSignal()

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
        self.canvas_time_mode_x_show_length = 0
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

        self.mark_number = 1
        self.mark1_x = None
        self.mark1_y = None
        self.mark2_x = None
        self.mark2_y = None

        self.mpl_connect("button_press_event", self.on_press)

        self.mutex = QtCore.QMutex()

    def on_press(self, event):
        if event.xdata is not None and event.ydata is not None:
            with QtCore.QMutexLocker(self.mutex):
                if self.mark_number == 1:
                    self.mark1_x = event.xdata
                    self.mark1_y = event.ydata
                elif self.mark_number == 2:
                    self.mark2_x = event.xdata
                    self.mark2_y = event.ydata
            self.canvas_clicked_signal.emit()

    def draw_data(self, x, y, mode, title='Spectrum Analyzer'):
        if self.draw_enable_flag is False:
            return
        self.drawing_flag = True
        with QtCore.QMutexLocker(self.mutex):
            if mode == 'spectrum':
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
                    self.ax.scatter(self.mark1_x, self.mark1_y, c='r', s=10000000, marker='+')
                    self.ax.scatter(self.mark2_x, self.mark2_y, c='g', s=10000000, marker='+')
                    self.ax.plot(x, y, color="blue", linewidth=1)
                    self.draw()
                except Exception as e:
                    print(e)
                    return
            elif mode == 'time':
                try:
                    self.ax.clear()
                    self.ax.xaxis.grid(True, which='major')
                    self.ax.yaxis.grid(True, which='major')
                    # not draw if data too short
                    if len(x) < 5:
                        return
                    if x[-1] < self.canvas_time_mode_x_show_length:
                        self.ax.set_xlim(0, self.canvas_time_mode_x_show_length)
                    else:
                        self.ax.set_xlim(x[0], x[-1])
                    self.ax.set_ylim(self.low_limit_rssi, self.high_limit_rssi)
                    self.ax.set_title(title, fontsize=16)
                    self.ax.set_ylabel(self.title, fontsize=14)
                    self.ax.set_xlabel('Time (s)', fontsize=14)
                    self.ax.scatter(self.mark1_x, self.mark1_y, c='r', s=10000000, marker='+')
                    self.ax.scatter(self.mark2_x, self.mark2_y, c='g', s=10000000, marker='+')
                    self.ax.plot(x, y, color="blue", linewidth=1)
                    self.draw()
                except Exception as e:
                    print(e)
                    return
            else:
                print('unknown mode, not draw')
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
        # self.draw_enable_flag = False
        # while self.drawing_flag is True:
        #     continue
        with QtCore.QMutexLocker(self.mutex):
            super(MplCanvas, self).resizeEvent(event)
        # self.draw_enable_flag = True
