from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap
from pymodbus.client.sync import ModbusTcpClient
import time, datetime, threading, os, sys, io

from threading import Event
exit = Event()
import logging.handlers

def makeDirectory(folderDir):
    if not os.path.isdir(folderDir):
        os.mkdir(folderDir)
makeDirectory('./log')

log_max_size = 1 * 1024 * 1024
log_file_count = 20

infoLog = logging.getLogger('infoLog')
infoLog.setLevel(logging.INFO)
infoFormatter = logging.Formatter('[%(levelname)s] %(asctime)s : %(message)s')
infoFileHandler = logging.handlers.RotatingFileHandler(filename='./log/info.txt', maxBytes=log_max_size, backupCount=log_file_count)
infoFileHandler.setFormatter(infoFormatter)
infoLog.addHandler(infoFileHandler)

dataLog = logging.getLogger('dataLog')
dataLog.setLevel(logging.INFO)
dataFormatter = logging.Formatter('[%(levelname)s] %(asctime)s : %(message)s')
dataFileHandler = logging.handlers.RotatingFileHandler(filename='./log/data.txt', maxBytes=log_max_size, backupCount=log_file_count)
dataFileHandler.setFormatter(dataFormatter)
dataLog.addHandler(dataFileHandler)



SERVER_PORT = 502
form_class = uic.loadUiType("main_v2.ui")[0]

class myWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.connectClicked)
        global stop
        stop = False
        self.btnClicked = False

    def connectClicked(self):
        global stop
        if self.btnClicked :
            self.btnClicked = False
            stop = True
            self.pushButton.setText('접속')
            self.label_4.setText('Disconnected')
        else:
            stop = False
            self.btnClicked = True
            ip = self.lineEdit.text()

            t = MyThread(ip)

            try:
                t.daemon = True   # Daemon True is necessary
                t.start()
            except:
                self.label_4.setText('Not Connected!!!')
                print("Fail Connection", ip)
            else:
                print("Connection", ip)

    def updateDisconnect(self):
        self.pushButton.setText('접속')

class MyThread(threading.Thread):
    def __init__(self, IP_address):
        threading.Thread.__init__(self)
        self.daemon = True
        self.IP_address = IP_address

    def run(self):
        # 통신 설정
        SERVER_HOST = str(self.IP_address)
        c = ModbusTcpClient()
        c.host = self.IP_address
        c.port = SERVER_PORT
        pre_regs = [0, 0, 0, 0]
        preStatusValue = [0, 0, 0, 0]

        while True:
            # open or reconnect TCP to server
            if not c.connect():
                print("해당 Server와 연결되지 않았습니다. " + SERVER_HOST + ":" + str(SERVER_PORT))
                myWindow.label_4.setText('Connection Fail')
                c.close()
                break
            else:
                myWindow.pushButton.setText('접속 종료')
                myWindow.label_4.setText('Connected')
                try:
                    status_regs = []
                    input_buffer_regs = []
                    for channelNum in range(4):
                        # status
                        status_regs.append(c.read_holding_registers(16384 + channelNum, 10))
                        # input data in buffer
                        input_buffer_regs.append(c.read_holding_registers(16464 + channelNum*80, 51))

                except:
                    print("데이터 획득 중 통신이 끊기거나 오류가 발생했습니다.")
                else:
                    for channelNum in range(4):
                        statusValue = int(status_regs[channelNum].registers[0])

                        # Status check with previous status
                        if statusValue != preStatusValue[channelNum] :
                            preStatusValue[channelNum] = statusValue
                            ch_status = boolean_def(statusValue)

                            switch_on = ch_status[4]
                            tp = ch_status[6]
                            busy = ch_status[1]
                            err = ch_status[2]
                            done = ch_status[0]
                            infoString = 'channelNum : [' + str(channelNum) + ']' + ' switch_on: ' +\
                                         str(switch_on) + ', tp: ' + str(tp)+ ', busy: ' + str(busy) +\
                                         ', err: ' + str(err) + ', done: ' + str(done)
                            infoLog.info(infoString)

                        # Read Data check with previous status
                        if input_buffer_regs[channelNum].registers[0] != 61440:
                            if input_buffer_regs[channelNum].registers != pre_regs[channelNum]:
                                pre_regs[channelNum] = input_buffer_regs[channelNum].registers
                                Read_data = []

                                for i in range(50):
                                    test_n = intToBytes(input_buffer_regs[channelNum].registers[i])
                                    Read_data.append(chr(test_n[2]))
                                    Read_data.append(chr(test_n[3]))

                                rfidDataAll = ''.join(Read_data[0:100])

                                dataString = 'channelNum[' + str(channelNum) + '] :' + rfidDataAll
                                dataLog.info(dataString)

                        else:
                            print("HERE")
                                # ReadTable(Read_data)

            # sleep 'n'second before next polling
            time.sleep(0.02)

            if stop == True:
                print("Break!")
                c.close()
                break

def loggedDataView(rfidData, curTime, rfidDataAll):
    myWindow.label_3.setText(rfidData)
    myWindow.label_3.setStyleSheet("color: black;" "background-color: #FFF882")
    myWindow.label_12.setText(curTime)


    # print(myWindow.tableWidget.item(2,0).text())
    for i in reversed(range(4)):
        try:
            preTime = myWindow.tableWidget.item(i,0).text()
            preData = myWindow.tableWidget.item(i,1).text()
        except:
            print('no data')
        else:
            myWindow.tableWidget.setItem(i+1, 0, QtWidgets.QTableWidgetItem(preTime))#
            myWindow.tableWidget.item(i+1, 0).setTextAlignment(Qt.AlignHCenter)
            myWindow.tableWidget.setItem(i+1, 1, QtWidgets.QTableWidgetItem(preData))#
            myWindow.tableWidget.item(i+1, 1).setTextAlignment(Qt.AlignHCenter)

    myWindow.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem(curTime))#
    myWindow.tableWidget.item(0, 0).setTextAlignment(Qt.AlignHCenter)
    myWindow.tableWidget.setItem(0, 1, QtWidgets.QTableWidgetItem(rfidDataAll))#
    myWindow.tableWidget.item(0, 1).setTextAlignment(Qt.AlignHCenter)
    myWindow.tableWidget.viewport().update() # neccessary for updating!!!


def dataLogging(folderDir, register_buffer):
    logging_file_name = folderDir + '/' + str(datetime.datetime.today().strftime("%Y%m%d")) +'.txt'
    f = open(logging_file_name, mode='a', encoding='utf-8')
    str_read_list = str(register_buffer)
    now = datetime.datetime.now()
    cur_time = datetime.time(now.hour, now.minute, now.second)

    RF_logging = str(cur_time) + ', ' + str_read_list +'\n'
    f.write(RF_logging)
    f.close()
    return str(cur_time)

# byte array conversion methods
def intToBytes(n):
    b = bytearray([0, 0, 0, 0])  # init
    b[3] = n & 0xFF
    n >>= 8
    b[2] = n & 0xFF
    n >>= 8
    b[1] = n & 0xFF
    n >>= 8
    b[0] = n & 0xFF

    # Return the result or as bytearray or as bytes (commented out)
    ##return bytes(b)  # uncomment if you need
    return b

def boolean_def(word):
    data = []
    b = 1
    for i in range(0, 16):
        if word & (b<<i) == 0:
            data.append("False")
        else:
            data.append("True")
    return data

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = myWindow()
    myWindow.show()
    sys.exit(app.exec_())
    # app.exec_()

    # run()
