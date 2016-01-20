import serial
from threading import Thread


class RobotProtocol:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def stop(self):
        self.ser.write("S\r")

    def move(self, num, direction, power, time):
        self.ser.write("M %d %d %d %d\r" % (num, direction, power, time))

s = RobotProtocol()
s.move(0, 0, 100, 1000)

