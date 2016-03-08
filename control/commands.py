import time
import multiprocessing

import numpy as np

from control.protocol import RobotProtocol
from strategy.simple import SimpleStrategy
from strategy.highstrategy import StrategyTools
from strategy.game import Game
from strategy.world import World
from strategy.movement import get_movement_direction
from vision.vision import Vision

MOTOR_LEFT = 0
MOTOR_RIGHT = 1
MOTOR_TURN = 2
MOTOR_KICK = 3
MOTOR_GRAB = 4


def sign(x):
    return 1 if x >= 0 else -1


class Commands:
    def __init__(self):
        self.protocol = None
        self.vision_process = None
        self.world = None
        self.strategy = None
        self.highstrategy = None
        print("! Remember to call:")
        print("! vision <room: 0/1> <team_color: blue/yellow> <our_single_spot_color: green/pink>")
        print("! connect")
        #self.vision()
        #self.connect()

    def test_movement(self):
        a = np.array([[666, 100, 666, 100, 666],
                      [666, 100, 100, 100, 666],
                      [666, 100, 100, 100, 666],
                      [666, 100, 666, 100, 666],
                      [666, 100, 666, 0, 666]], dtype=np.float64)

        print get_movement_direction(a, self)

    def connect(self, device_no='0'):
        print("Connecting to RF stick")
        self.protocol = RobotProtocol('/dev/ttyACM' + device_no)

    def vision(self, room_num=1, team_color='yellow', our_color='pink', we_have_computer_goal=True):
        print("Starting vision")
        print("Room: %s, team color: %s, our single spot color: %s" % (str(room_num), team_color, our_color))
        if not self.vision_process:
            self.world = World(int(room_num), team_color, our_color, we_have_computer_goal)
            self.strategy = SimpleStrategy(self.world, self)
            self.highstrategy = StrategyTools(self.world, self)
            self.vision_process = multiprocessing.Process(target=Vision, args=(self.world,))
            self.vision_process.start()

    def attackwithball(self):
        self.highstrategy.attackwithball()

    def ballwithenemy(self):
        self.highstrategy.ballwithenemy()

    def grab_ball(self):
        self.strategy.grab_ball()

    def goal(self):
        self.strategy.goal()

    def grab_goal(self):
        self.strategy.grab_goal()

    def pass_ball(self):
        self.strategy.pass_ball()

    def catch_ball(self):
        self.strategy.catch_ball()

    def intercept(self):
        self.strategy.intercept()

    def catch_pass(self):
        self.strategy.catch_pass()

    def pw(self):
        print(self.world)

    def f(self, x):
        """Move forward, negative x means backward"""
        x = int(x)
        s = sign(x)
        if x > 0:
            x = 13.7627360975 * x - 53.5734818271
        else:
            x = 13.964509832 * -x - 75.2448595458
        x = int(x)
        if x > 0:
            self.protocol.move(x, [(MOTOR_LEFT, -100 * s),
                                   (MOTOR_RIGHT, -100 * s)])

    def forward_forever(self):
        """Move forward forever"""
        self.protocol.move_forever([(MOTOR_LEFT, -100),
                                    (MOTOR_RIGHT, -100)])

    def backward_forever(self):
        """Move backward forever"""
        self.protocol.move_forever([(MOTOR_LEFT, 100),
                                    (MOTOR_RIGHT, 100)])

    def swerve_right(self, x):
        """Swerve right whilst moving forwards

        x values:
        45 degrees: 200
        90 degrees: 500
        """
        self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_TURN, 100),
                                               (MOTOR_LEFT, -100),
                                               (MOTOR_RIGHT, -100)])

    def swerve_left(self, x):
        """Swerve left whilst moving forwards

        x values:
        45 degrees: 200
        90 degrees: 500
        """
        self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_TURN, -100),
                                               (MOTOR_LEFT, -100),
                                               (MOTOR_RIGHT, -100)])

    def test(self):
        """Test of swerving"""
        self.forward()
        self.swerve_left(200)
        self.swerve_right(200)
        self.swerve_left(200)
        self.swerve_right(200)
        self.forward()

    def forward(self):
        self.protocol.schedule(200, MOTOR_LEFT, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)])

    def backward(self):
        self.protocol.schedule(200, MOTOR_LEFT, [(MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, 100)])

    def forward_left(self):
        self.protocol.schedule(300, MOTOR_TURN, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, -70),
                                                 (MOTOR_RIGHT, -100)])
        self.protocol.schedule(120, MOTOR_LEFT, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)])

    def forward_right(self):
        self.protocol.schedule(340, MOTOR_TURN, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -70)])
        self.protocol.schedule(120, MOTOR_LEFT, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)])

    def backward_left(self):
        self.protocol.schedule(340, MOTOR_TURN, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, 90),
                                                 (MOTOR_RIGHT, 100)])

    def backward_right(self):
        self.protocol.schedule(340, MOTOR_TURN, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, 90)])

    def sharp_left(self):
        self.protocol.schedule(120, MOTOR_TURN, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, -100)])
        self.forward()

    def sharp_right(self):
        self.protocol.schedule(120, MOTOR_TURN, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, 100)])
        self.forward()

    def c(self, x):
        """Rotate clockwise, negative x means counter-clockwise"""
        x = int(x)
        s = sign(x)
        x = abs(x)
        if x > 90:
            x = 1.89444 * x - 59.5
        else:
            x = 0.0083027347 * (x ** 2) + 0.4557515777 * x
        x = int(x)
        if x > 0:
            self.protocol.move(x, [(MOTOR_LEFT, -100 * s),
                                   (MOTOR_RIGHT, 100 * s),
                                   (MOTOR_TURN, 100 * s)])

    def k(self, x):
        """Kick"""
        x = int(x)
        # Not using rotary encoders, granularity too low
        self.protocol.move(x, [(MOTOR_KICK, 100)], time=True)

    def g(self, x=300):
        """Grab, negative x means release"""
        x = int(x)
        # This motor does not have rotary encoders
        self.protocol.move(abs(x), [(MOTOR_GRAB, 100 * sign(x))], time=True)

    def open_wide(self):
        self.g(-400)

    def open_narrow(self):
        self.g(-200)

    def x(self, x):
        """Kick and release"""
        x = int(x)
        self.k(x)
        self.open_narrow()

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
        time_value = 0.7517522044 * distance + 199.265204612
        print("Time for kicking motor: " + str(time_value))
        self.k(time_value)
        '''
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
        '''

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

    def reset_input(self):
        self.protocol.reset_input()

    def block_goal(self, enemy_num=1):
        self.strategy.block_goal(int(enemy_num))
