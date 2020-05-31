
from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap
from pymodbus.client.sync import ModbusTcpClient
import time, datetime, threading, os, sys, io

SERVER_PORT = 502

form_class = uic.loadUiType("main.ui")[0]
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
            channelNum = self.comboBox.currentIndex()
            print(channelNum)
            ip = self.lineEdit.text()
            folderDir = './Datalog'
            makeDirectory(folderDir)
            t = MyThread(ip, channelNum)

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
    def __init__(self, IP_address, channelNum):
        threading.Thread.__init__(self)
        self.daemon = True
        self.IP_address = IP_address
        self.channelNum = channelNum

    def run(self):
        # 통신 설정
        SERVER_HOST = str(self.IP_address)
        c = ModbusTcpClient()
        c.host = self.IP_address
        c.port = SERVER_PORT
        channelNum = self.channelNum
        pre_regs = []

        ch0_switch_on_triger = ''
        ch0_tp_triger = ''
        ch0_busy_triger = ''
        ch0_err_triger = ''
        ch0_done_triger = ''

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
                    #--- ch0 input register
                    # status
                    ch0_status_regs = c.read_holding_registers(16384 + channelNum, 10)

                    # input data in buffer
                    ch0_input_buffer_regs = c.read_holding_registers(16464 + channelNum*80, 50)

                except:
                    print("데이터 획득 중 통신이 끊기거나 오류가 발생했습니다.")
                else:

                    ch0_status = boolean_def(int(ch0_status_regs.registers[0]))
                    ch0_switch_on = ch0_status[4]

                    if ch0_switch_on == 'True':
                        if ch0_switch_on_triger != ch0_switch_on:
                            myWindow.label_6.setStyleSheet("color: green;" "background-color: #7FFFD4")
                            ch0_switch_on_triger = ch0_switch_on
                    else :
                        if ch0_switch_on_triger != ch0_switch_on:
                            myWindow.label_6.setStyleSheet("color: black;" "background-color: #FFFFFF")
                            ch0_switch_on_triger = ch0_switch_on
                    ch0_tp = ch0_status[6]
                    if ch0_tp == 'True':
                        if ch0_tp_triger != ch0_tp:
                            myWindow.label_7.setStyleSheet("color: green;" "background-color: #7FFFD4")
                            ch0_tp_triger = ch0_tp
                    else :
                        if ch0_tp_triger != ch0_tp:
                            myWindow.label_7.setStyleSheet("color: black;" "background-color: #FFFFFF")
                            ch0_tp_triger = ch0_tp
                    ch0_busy = ch0_status[1]
                    if ch0_busy == 'True':
                        if ch0_busy_triger != ch0_busy:
                            myWindow.label_10.setStyleSheet("color: green;" "background-color: #7FFFD4")
                            ch0_busy_triger = ch0_busy
                    else :
                        if ch0_busy_triger != ch0_busy:
                            myWindow.label_10.setStyleSheet("color: black;" "background-color: #FFFFFF")
                            ch0_busy_triger = ch0_busy
                    ch0_err = ch0_status[2]
                    if ch0_err == 'True':
                        if ch0_err_triger != ch0_err:
                            myWindow.label_13.setStyleSheet("color: red;" "background-color: #FA8072")
                            ch0_err_triger = ch0_err
                    else :
                        if ch0_err_triger != ch0_err:
                            myWindow.label_13.setStyleSheet("color: black;" "background-color: #FFFFFF")
                            ch0_err_triger = ch0_err
                    ch0_done = ch0_status[0]
                    if ch0_done == 'True':
                        if ch0_done_triger != ch0_done:
                            myWindow.label_14.setStyleSheet("color: green;" "background-color: #7FFFD4")
                            ch0_done_triger = ch0_done
                    else :
                        if ch0_done_triger != ch0_done:
                            myWindow.label_14.setStyleSheet("color: black;" "background-color: #FFFFFF")
                            ch0_done_triger = ch0_done

                    if ch0_input_buffer_regs.registers[0] != 61440:
                        if ch0_input_buffer_regs.registers != pre_regs:
                            pre_regs = ch0_input_buffer_regs.registers
                            Read_data = []

                            for i in range(50):
                                test_n = intToBytes(ch0_input_buffer_regs.registers[i])
                                Read_data.append(chr(test_n[2]))
                                Read_data.append(chr(test_n[3]))

                            rfidDataAll = ''.join(Read_data[0:100])
                            curTime = dataLogging('./Datalog', rfidDataAll)
                            rfidData = ''.join(Read_data[0:10])
                            print(rfidData)
                            loggedDataView(rfidData, curTime, rfidDataAll)

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


def makeDirectory(folderDir):
    if not os.path.isdir(folderDir):
        os.mkdir(folderDir)

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
