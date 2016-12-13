# coding:utf-8
# author: Wang Chao

from PyQt4 import QtCore
import weakref
import copy


class DrawCanvasThread(QtCore.QThread):

    # draw_canvas_signal = QtCore.pyqtSignal(list, list)

    def __init__(self, main_window, canvas, parent=None):
        super(DrawCanvasThread, self).__init__(parent)
        self.stop_flag = False
        self.main_window = weakref.proxy(main_window)
        self.canvas = weakref.proxy(canvas)
        # self.mutex = QtCore.QMutex()
        # self.draw_enable_flag = True

    def stop(self):
        # with QtCore.QMutexLocker(self.mutex):
        self.stop_flag = True

    # def enable_draw(self):
    #     with QtCore.QMutexLocker(self.mutex):
    #         self.draw_enable_flag = True

    def run(self):
        i = 0
        while True:
            i += 1
            if i % 100 == 0:
                print('draw count: %d' % i)
            if self.stop_flag is True:
                print('DrawCanvasThread stopped!')
                return
            if self.canvas.draw_enable_flag is True:
            # with QtCore.QMutexLocker(self.mutex):
                if self.main_window.show_mode == 'spectrum':
                    x = copy.copy(self.main_window.spectrum_data.keys())
                    y = copy.copy(self.main_window.spectrum_data.values())
                    # print(x)
                    if len(x) != len(y):
                        print('length not match ', len(x), len(y))
                        continue
                    # self.draw_canvas_signal.emit(x, y)
                    # self.draw_enable_flag = False
                    self.canvas.draw_data(x, y, 'spectrum')
                elif self.main_window.show_mode == 'time':
                    x = copy.copy(self.main_window.time_data_x)
                    y = copy.copy(self.main_window.time_data_y)
                    # print(x)
                    if len(x) != len(y):
                        print(len(x), len(y))
                        continue
                    draw_title = ('%.1f' % (float(self.main_window.time_mode_frequency) / 10)) + 'MHz Signal Strength'
                    self.canvas.draw_data(x, y, 'time', title=draw_title)
                    # self.draw_canvas_signal.emit(x, y)
                    # self.draw_enable_flag = False
                else:
                    print('unknown mode, draw thread return!')
                    return
