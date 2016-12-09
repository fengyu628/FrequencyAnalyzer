# coding:utf-8
# author: Wang Chao

from PyQt4 import QtCore
import weakref
import time


class GetDataThread(QtCore.QThread):
    def __init__(self, main_window, parent=None):
        super(GetDataThread, self).__init__(parent)
        self.stop_flag = False
        self.main_window = weakref.proxy(main_window)
        self.mutex = QtCore.QMutex()
        self.close_port_flag = False

    def stop(self):
        with QtCore.QMutexLocker(self.mutex):
            self.stop_flag = True

    def run(self):
        while True:
            if self.stop_flag is True:
                print('GetDataThread 1 stopped!')
                return
            if self.main_window.stop_get_data_flag is True:
                # time.sleep(0.1)
                continue

            if self.close_port_flag is True:
                print('close port in get data thread')
                self.main_window.serial_port.close()
                self.close_port_flag = False

            if not self.main_window.serial_port.isOpen():
                # print('serial port not open')
                time.sleep(0.1)
                continue
            try:
                line = self.main_window.serial_port.readline()
            except Exception as e:
                # if len(str(e)) > 5:
                print(e)
                continue
            # delete the bad line and other print message
            if not line.startswith('~') and not line.startswith('^'):
                if len(line) > 2:
                    print(line)
                continue
            if self.stop_flag is True:
                print('GetDataThread 2 stopped!')
                return
            # mode change not complete, to change the mode
            if self.main_window.mode_changing_flag is True:

                if self.main_window.show_mode == 'spectrum':
                    # mode changed
                    if line.startswith('~'):
                        for f_pre in range(8500, 9280):
                            self.main_window.spectrum_data[(float(f_pre) / 10)] = None
                            self.main_window.mode_changing_flag = False
                        print('have changed mode to spectrum!')
                        continue
                    # mode not changed, send command
                    else:
                        self.main_window.serial_port.write('FA01.')
                        print('sending FA01.')
                        time.sleep(0.01)
                        # clean the serial port buffer
                        self.main_window.serial_port.close()
                        self.main_window.serial_port.open()
                        continue

                elif self.main_window.show_mode == 'time':
                    print('self.time_mode_frequency: %d' % self.main_window.time_mode_frequency)
                    print('get frequency from hardware: %s' % line.split('#')[1])
                    # mode changed
                    if line.startswith('^') and line.split('#')[1] == str(self.main_window.time_mode_frequency):
                        # print(line.split('#')[1])
                        self.main_window.time_mode_start_time = time.time()
                        self.main_window.time_data_x = []
                        self.main_window.time_data_y = []
                        self.main_window.mode_changing_flag = False
                        print('have changed mode to time!')
                        continue
                    # mode not changed, send command
                    else:
                        self.main_window.serial_port.write(
                            'FA02' + str(self.main_window.time_mode_frequency) + '.')
                        print('sending FA02' + str(self.main_window.time_mode_frequency) + '.')
                        time.sleep(0.01)
                        # clean the serial port buffer
                        self.main_window.serial_port.close()
                        # print(self.main_window.serial_port.closed)
                        self.main_window.serial_port.open()
                        continue
                else:
                    print('unknown mode')

            # not deal with data, if mode change not complete
            if self.main_window.mode_changing_flag is True:
                continue

            line_list = line.split('#')
            # deal with different mode
            if self.main_window.show_mode == 'spectrum':
                try:
                    freq_spectrum = float(line_list[1]) / 10
                    rssi_spectrum = int(line_list[2])
                except Exception as e:
                    print(e)
                    continue
                # self.main_window.show_canvas.draw_enable_flag = False
                with QtCore.QMutexLocker(self.mutex):
                    if self.main_window.show_max_flag is True:
                        if rssi_spectrum > self.main_window.spectrum_data[freq_spectrum]:
                            self.main_window.spectrum_data[freq_spectrum] = rssi_spectrum
                    else:
                        self.main_window.spectrum_data[freq_spectrum] = rssi_spectrum
                # self.main_window.show_canvas.draw_enable_flag = True

            elif self.main_window.show_mode == 'time':
                try:
                    # freq_time = int(line_list[1])
                    time_time = time.time() - self.main_window.time_mode_start_time
                    rssi_time = int(line_list[2])
                except Exception as e:
                    print(e)
                    continue
                # self.main_window.show_canvas.draw_enable_flag = False
                with QtCore.QMutexLocker(self.mutex):
                    self.main_window.time_data_x.append(time_time)
                    self.main_window.time_data_y.append(rssi_time)
                    # keep fixed length
                    if self.main_window.time_data_x[-1] - self.main_window.time_data_x[0] > \
                            self.main_window.time_mode_x_show_length:
                        self.main_window.time_data_x = self.main_window.time_data_x[2:]
                        self.main_window.time_data_y = self.main_window.time_data_y[2:]
                # self.main_window.show_canvas.draw_enable_flag = True

            else:
                print('unknown mode, get data thread return!')
                return
