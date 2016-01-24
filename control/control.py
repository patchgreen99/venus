import serial


MOTOR_LEFT = 0
MOTOR_RIGHT = 1
MOTOR_TURN = 3
MOTOR_KICK = 4


class RobotProtocol:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def stop(self):
        self.ser.write('S\r')

    def move(self, time, motor_powers):
        # motor_powers consists of tuples (num, power)
        out = ['M', time, len(motor_powers)] + list(sum(motor_powers, ()))
        self.write(' '.join(str(x) for x in out))
        
    def write(self, message):
        self.ser.write(message + '\r')
        print("Message sent: %s" % message)
        


class Milestone1:

    def __init__(self):
        self.p = RobotProtocol()
        
    def f(self, *args):
        """Shortcut for forward"""
        self.forward(*args)
    
    def c(self, *args):
        """Shortcut for backward"""
        self.clockwise(*args)

    def forward(self, time, power):
        """Move forward, negative power means backward"""
        self.p.move(time, [(MOTOR_LEFT, -power),
                           (MOTOR_RIGHT, -power)])

    def clockwise(self, time, power):
        """Rotate clockwise, negative power means counter-clockwise"""
        self.p.move(time, [(MOTOR_LEFT, power),
                           (MOTOR_RIGHT, -power),
                           (MOTOR_TURN, power)])

    def kicker(self, time, power):
        """Move kicker forward"""
        self.p.move(time, [(MOTOR_KICK, -power)])

    def move(self, x, y, deg):
        """Milestone 1: Move"""
        # x and y are supplied in meters, deg in degrees
        # Commands are going to be issued like this, we have to tweak the coefficients for time
        self.forward(100 * x, 100)
        self.clockwise(500, 100)
        self.forward(100 * y, 100)
        self.clockwise(100 * deg, 100)

    def kick(self, distance):
        """Milestone 1: Kick"""
        # The same goes for kicker
        self.kicker(distance, 100)
        self.kicker(200, -100)

    def send(self, filename):
        """Milestone 1: Communications and Timing"""
        print(filename)

    def prompt(self):
        text = raw_input('> ')
        while text != 'exit':
            tokens = text.split()
            if tokens:
                try:
                    getattr(self, tokens[0])(*[int(t) for t in tokens[1:]])
                except AttributeError:
                    print("No such command")
                except ValueError as e:
                    print("Value error: %s" % e)
            text = raw_input('> ')


if __name__ == '__main__':
    milestone1 = Milestone1()
    milestone1.prompt()

