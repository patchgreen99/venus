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


def sign(x):
    return 1 if x >= 0 else -1


class Milestone1:

    def __init__(self):
        device = sys.argv[1] if len(sys.argv) == 2 else '/dev/ttyACM0'
        self.p = RobotProtocol(device)

    def f(self, x):
        """Move forward, negative x means backward"""
        x = int(x)
        s = sign(x)
        if x > 0:
            x = 13.7627360975 * x - 53.5734818271
        else:
            x = 13.964509832 * -x - 75.2448595458
        self.p.move(abs(x), [(MOTOR_LEFT,  -100 * s),
                             (MOTOR_RIGHT, -100 * s)])

    def c(self, x):
        """Rotate clockwise, negative x means counter-clockwise"""
        x = int(x)
        s = sign(x)
        x = abs(x)
        if x > 90:
            x = 1.89444 * x - 59.5
        else:
            x = 0.0083027347 * (x ** 2) + 0.4557515777 * x
        self.p.move(abs(x), [(MOTOR_LEFT,  -100 * s),
                             (MOTOR_RIGHT,  100 * s),
                             (MOTOR_TURN,   100 * s)])

    def k(self, x):
        """Kick"""
        x = int(x)
        # Not using rotary encoders, granularity too low
        self.p.move(x, [(MOTOR_KICK, 100)], time=True)

    def g(self, x=200):
        """Grab, negative x means release"""
        x = int(x)
        # This motor does not have rotary encoders
        self.p.move(abs(x), [(MOTOR_GRAB, 100 * sign(x))], time=True)
        
    def r(self):
        """Release"""
        self.g(-180)

    def x(self, x):
        """Kick and release"""
        x = int(x)
        self.k(x)
        self.r()

    def s(self):
        self.p.stop()

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
            time = 242
        elif distance == 100:
            #time = 290
            time = 275 #295?
        elif distance == 150:
            #time = 310
            time = 303
        else:
            time = 0
        self.k(time)

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

