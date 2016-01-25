import serial
import time
import sys


MOTOR_LEFT = 0
MOTOR_RIGHT = 1
MOTOR_TURN = 2
MOTOR_KICK = 3


class RobotProtocol:
    def __init__(self, device):
        self.ser = serial.Serial(device, 115200)

    def stop(self):
        self.write('S\r')

    def move(self, time, motor_powers):
        # motor_powers consists of tuples (num, power)
        out = ['M', time, len(motor_powers)] + list(sum(motor_powers, ()))
        self.write(' '.join(str(x) for x in out))
        
    def transfer(self, byte):
        self.write('T %d' % ord(byte))
        
    def write(self, message):
        self.ser.write(message + '\r')
        print("Message sent: %s" % message)


class Milestone1:

    def __init__(self):
        device = sys.argv[1] if len(sys.argv) == 2 else '/dev/ttyACM0'
        self.p = RobotProtocol(device)
        
    def calc_move(self, x):
        return 45.0 * x# 38.0 * x + 100.0
        
    def calc_clockwise(self, deg):
        return 5.9 * deg + 45.0
        
    def calc_anticlockwise(self, deg):
        return 6.4 * deg + 50.0
        
    def calc_turn(self, deg):
        if deg < 0:
            return self.calc_anticlockwise(deg)
        else:
            return self.calc_clockwise(deg)

    def f(self, x):
        """Shortcut for forward"""
        x = int(x)
        if x < 0:
            x = -x
            power = -100
        else:
            power = 100
        self.forward(self.calc_move(x), power)

    def c(self, deg):
        """Shortcut for backward"""
        deg = int(deg)
        if deg < 0:
            deg = -deg
            power = -100
        else:
            power = 100
        self.clockwise(self.calc_turn(deg), power)

    def forward(self, time, power):
        """Move forward, negative power means backward"""
        time = int(time) if int(time) > 0 else 0
        power = int(power)
        self.p.move(time, [(MOTOR_LEFT, -power),
                           (MOTOR_RIGHT, -power)])

    def clockwise(self, time, power):
        """Rotate clockwise, negative power means counter-clockwise"""
        time = int(time) if int(time) > 0 else 0
        power = int(power)
        self.p.move(time, [(MOTOR_LEFT, -power),
                           (MOTOR_RIGHT, power),
                           (MOTOR_TURN, power)])

    def kicker(self, time, power):
        """Move kicker forward"""
        time = int(time)
        power = int(power)
        self.p.move(time, [(MOTOR_KICK, power)])

    def move(self, x, y, deg):
        """Milestone 1: Move"""
        # x and y are supplied in meters, deg in degrees
        # Commands are going to be issued like this, we have to tweak the coefficients for time
        x = int(x)
        y = int(y)
        deg = int(deg)
        self.forward(self.calc_move(x), 100)
        if x > 0:
            self.clockwise(self.calc_turn(-90), 100)
        else:
            self.clockwise(self.calc_turn(90), 100)
        self.forward(self.calc_move(y), 100)
        self.clockwise(self.calc_move(deg), 100)

    def kick(self, distance):
        """Milestone 1: Kick"""
        distance = int(distance)
        if distance == 50:
            time = 260
        elif distance == 100:
            time = 290
        elif distance == 150:
            time = 320 # 330
        else:
            time = 0
        self.kicker(time, 100)

    def transfer(self, filename, freq_hz):
        """Milestone 1: Communications and Timing"""
        freq_hz = float(freq_hz)
        seconds = 1.0 / freq_hz
        print("Transferring file '%s' at freq %fHz, %fs" %
              (filename, freq_hz, seconds))
        with open(filename, "rb") as f:
            byte = f.read(1)
            while byte != "":
                self.p.transfer(byte)
                time.sleep(seconds)
                byte = f.read(1)

    def prompt(self):
        text = raw_input('> ')
        while text != 'exit':
            tokens = text.split()
            if tokens:
                try:
                    getattr(self, tokens[0])(*tokens[1:])
                except AttributeError:
                    print("No such command")
                except ValueError as e:
                    print("Value error: %s" % e)
                except TypeError as e:
                    print("Type error: %s" % e)
            text = raw_input('> ')


if __name__ == '__main__':
    milestone1 = Milestone1()
    milestone1.prompt()

