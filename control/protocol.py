import serial


class RobotProtocol:
    def __init__(self, device):
        self.ser = serial.Serial(device, 115200)

    def stop(self):
        self.write('S\r')

    def move(self, units, motor_powers, time=False):
        # motor_powers consists of tuples (num, power)
        command = 'M' if time else 'R'
        out = [command, int(abs(units)), len(motor_powers)]
        for num, power in motor_powers:
            out.append(int(num))
            out.append(int(power))
        self.write(' '.join(str(x) for x in out))

    def transfer(self, byte):
        self.write_unsafe('T %d' % ord(byte))

    def write(self, message):
        self.ser.write(message + '\r')
        print("Message sent: %s" % message)
        s = self.ser.readline()
        while s != 'DONE\r\n':
            print("Got unknown response '%s'" % s)
            s = self.ser.readline()
        print("Got done")

    def write_unsafe(self, message):
        self.ser.write(message + '\r')
        print("Message sent: %s" % message)

    def read_all(self):
        s = self.ser.readline()
        while s == 'DONE\r\n':
            print("Got response '%s'" % s)
            s = self.ser.readline()
