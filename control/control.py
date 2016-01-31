import serial
import time
import sys


MOTOR_LEFT = 0
MOTOR_RIGHT = 1
MOTOR_TURN = 2
MOTOR_KICK = 3
MOTOR_GRAB = 4


class RobotProtocol:
    def __init__(self, device):
        self.ser = serial.Serial(device, 115200)

    def stop(self):
        self.write('S\r')

    def move_time(self, time, motor_powers):
        # motor_powers consists of tuples (num, power)
        out = ['M', time, len(motor_powers)] + list(sum(motor_powers, ()))
        self.write(' '.join(str(x) for x in out))

    def move_rotary(self, rotary, motor_powers):
        # motor_powers consists of tuples (num, power)
        out = ['M', rotary, len(motor_powers)] + list(sum(motor_powers, ()))
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


class Milestone1:

    def __init__(self):
        device = sys.argv[1] if len(sys.argv) == 2 else '/dev/ttyACM0'
        self.p = RobotProtocol(device)
        
    def calc_forward(self, x):
        return 41.0 * x
        
    def calc_backward(self, x):
        return 38.0 * x
        
    def calc_clockwise(self, deg):
        if deg <= 30:
            deg = 47
        elif deg > 30 and deg <= 45:
            deg = 55
        elif deg > 45 and deg <= 60:
            deg = 70 
        return 6.2 * deg
        
    def calc_anticlockwise(self, deg):
        return self.calc_clockwise(deg)

    def f(self, x):
        """Shortcut for forward"""
        x = int(x)
        if x < 0:
            x = self.calc_backward(-x)
            power = -100
        else:
            x = self.calc_forward(x)
            power = 100
        self.forward(x, power)

    def c(self, deg):
        """Shortcut for backward"""
        deg = int(deg)
        if deg < 0:
            deg = self.calc_anticlockwise(-deg)
            power = -100
        else:
            deg = self.calc_clockwise(deg)
            power = 100
        self.clockwise_rotary(deg, power)

    def forward(self, rotary, power):
        """Move forward, negative power means backward"""
        rotary = int(rotary) if int(rotary) > 0 else 0
        power = int(power)
        self.p.move_rotary(rotary, [(MOTOR_LEFT, -power),
                                    (MOTOR_RIGHT, -power)])

    def clockwise_rotary(self, rotary, power):
        """Rotate clockwise, negative power means counter-clockwise"""
        rotary = int(rotary) if int(rotary) > 0 else 0
        power = int(power)
        self.p.move_rotary(rotary, [(MOTOR_LEFT, -power),
                                  (MOTOR_RIGHT, power),
                                  (MOTOR_TURN, power)])                              

    def kicker(self, rotary, power):
        """Move kicker forward"""
        rotary = int(rotary)
        power = int(power)
        self.p.move_rotary(rotary, [(MOTOR_KICK, power)])

    def move(self, x, y, deg):
        """Milestone 1: Move"""
        x = int(x)
        y = int(y)
        deg = int(deg)
        
        print("First turn, clockwise")
        self.c(90)
        time.sleep(1)
        
        print("Go x")
        self.f(x)
        time.sleep(1)
        
        print("Second turn, counterclockwise")
        self.c(-85)
        
        print("Go y")
        time.sleep(1)
        self.f(y)
        
        print("Do final turn")
        time.sleep(1)
        self.c(deg)

    def kick(self, distance):
        """Milestone 1: Kick"""
        distance = int(distance)
        if distance == 50:
            #time = 260
            rotary = 242
        elif distance == 100:
            #time = 290
            rotary = 275 #295?
        elif distance == 150:
            #time = 310
            rotary = 303
        else:
            rotary = 0
        self.kicker(rotary, 100)
        
    def g(self, time, power):
        self.p.move_time(time, [(MOTOR_GRAB, power)])

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
        #self.p.read_all()

    def prompt(self):
        text = raw_input('> ')
        while text != 'exit':
            tokens = text.split()
            if tokens:
                try:
                    getattr(self, tokens[0])(*tokens[1:])
                except AttributeError as e:
                    print("Attribute error: %s" % e)
                except ValueError as e:
                    print("Value error: %s" % e)
                except TypeError as e:
                    print("Type error: %s" % e)
            text = raw_input('> ')


if __name__ == '__main__':
    milestone1 = Milestone1()
    milestone1.prompt()

