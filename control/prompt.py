import time
import sys
import traceback
from multiprocessing import Process

from control.protocol import RobotProtocol
from vision.vision import Room

MOTOR_LEFT = 0
MOTOR_RIGHT = 1
MOTOR_TURN = 2
MOTOR_KICK = 3
MOTOR_GRAB = 4


def sign(x):
    return 1 if x >= 0 else -1


class Prompt:
    def __init__(self):
        self.protocol = None
        self.process = None
        print("Remember to call connect and vision")

    def connect(self):
        device = sys.argv[1] if len(sys.argv) == 2 else '/dev/ttyACM0'
        self.protocol = RobotProtocol(device)

    def vision(self, room_num, team_color, our_color):
        room = Room(int(room_num), team_color, our_color, debug=False)
        self.process = Process(target=room.vision, args=())
        self.process.start()

    def f(self, x):
        """Move forward, negative x means backward"""
        x = int(x)
        s = sign(x)
        if x > 0:
            x = 13.7627360975 * x - 53.5734818271
        else:
            x = 13.964509832 * -x - 75.2448595458
        self.protocol.move(abs(x), [(MOTOR_LEFT, -100 * s),
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
        self.protocol.move(abs(x), [(MOTOR_LEFT, -100 * s),
                                    (MOTOR_RIGHT, 100 * s),
                                    (MOTOR_TURN, 100 * s)])

    def k(self, x):
        """Kick"""
        x = int(x)
        # Not using rotary encoders, granularity too low
        self.protocol.move(x, [(MOTOR_KICK, 100)], time=True)

    def g(self, x=200):
        """Grab, negative x means release"""
        x = int(x)
        # This motor does not have rotary encoders
        self.protocol.move(abs(x), [(MOTOR_GRAB, 100 * sign(x))], time=True)

    def r(self):
        """Release"""
        self.g(-180)

    def x(self, x):
        """Kick and release"""
        x = int(x)
        self.k(x)
        self.r()

    def s(self):
        self.protocol.stop()

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
            # time = 260
            time = 242
        elif distance == 100:
            # time = 290
            time = 275  # 295?
        elif distance == 150:
            # time = 310
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
                self.protocol.transfer(byte)
                time.sleep(seconds)
                byte = f.read(1)
                # self.p.read_all()

    def run(self):
        text = raw_input('> ')
        while text != 'exit':
            tokens = text.split()
            if tokens:
                try:
                    getattr(self, tokens[0])(*tokens[1:])
                except:
                    traceback.print_exc()
            text = raw_input('> ')