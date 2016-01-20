import serial
import time


with serial.Serial('/dev/ttyACM0', 115200) as ser:
    while True:
        print("Received: %s" % ser.readline())
        ser.write(raw_input("Input: "))

