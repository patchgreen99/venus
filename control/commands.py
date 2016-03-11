import time
import multiprocessing

import numpy as np

from control.protocol import RobotProtocol
from strategy.simple import SimpleStrategy
from strategy.highstrategy import StrategyTools
from strategy.world import World
from strategy.game import Game
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
        self.game = None
        print("! Remember to call:")
        print("! init <room: 0/1> <team_color: blue/yellow> <our_single_spot_color: green/pink>")
        print("! vision")
        print("! connect <device_no>")
        self.init()
        self.vision()
        self.connect()

    def init(self, room_num=1, team_color='yellow', our_color='green', computer_goal=False):
        print("init: Room: %s, team color: %s, our single spot color: %s, computer goal: %s" %
              (room_num, team_color, our_color, computer_goal))
        self.world = World(int(room_num), team_color, our_color, computer_goal)
        self.strategy = SimpleStrategy(self.world, self)
        self.highstrategy = StrategyTools(self.world, self)
        self.game = Game(self.world, self)

    def connect(self, device_no='0'):
        print("connect: Connecting to RF stick")
        self.protocol = RobotProtocol('/dev/ttyACM' + device_no)

    def vision(self):
        if not self.vision_process:
            print("vision: Starting vision")
            self.vision_process = multiprocessing.Process(target=Vision, args=(self.world,))
            self.vision_process.start()

    def query_ball(self):
        print("We have the ball: %s" % self.protocol.query_ball())

    def attackwithball(self):
        self.highstrategy.attackwithball()

    def ballwithenemy(self, no):
        self.highstrategy.ballwithenemy(no)

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

    def potential(self):
        self.game.run()

    def test1(self):
        self.game.local_potential = np.array([[666, 100, 666, 100, 666],
                                              [666, 100, 0, 0, 666],
                                              [666, 100, 1, 100, 666],
                                              [666, 100, 666, 100, 666],
                                              [666, 100, 666, 100, 666]], dtype=np.float64)
        self.game.points = np.arange(50).reshape((5, 5, 2))
        print self.game.move()

    def test2(self):
        self.forward()
        self.forward_left()
        self.forward_right()
        self.forward_left()
        self.backward()
        self.backward()
        self.backward_left()

    def test3(self):
        self.forward()
        self.pause()
        self.sharp_left()

    def test4(self):
        """Test of swerving"""
        self.forward()
        self.swerve_left(200)
        self.swerve_right(200)
        self.swerve_left(200)
        self.swerve_right(200)
        self.forward()

    def forward_forever(self):
        """Move forward forever"""
        self.protocol.move_forever([(MOTOR_LEFT, -100),
                                    (MOTOR_RIGHT, -100)])

    def backward_forever(self):
        """Move backward forever"""
        self.protocol.move_forever([(MOTOR_LEFT, 100),
                                    (MOTOR_RIGHT, 100)])

    def swerve_right(self, x):
        """Swerve right whilst moving forwards"""
        self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_TURN, 100),
                                               (MOTOR_LEFT, -100),
                                               (MOTOR_RIGHT, -100)])

    def swerve_left(self, x):
        """Swerve left whilst moving forwards"""
        self.protocol.schedule(x, MOTOR_TURN, [(MOTOR_TURN, -100),
                                               (MOTOR_LEFT, -100),
                                               (MOTOR_RIGHT, -100)])

    def pause(self):
        """Pause between motions that immediately change motor direction"""
        self.protocol.schedule_pause(400)

    def forward(self):
        """Move a cell forward"""
        self.protocol.schedule(100, MOTOR_LEFT, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)])

    def backward(self):
        """Move a cell backward"""
        self.protocol.schedule(100, MOTOR_LEFT, [(MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, 100)])

    def forward_left(self):
        """Move forward and to left"""
        self.protocol.schedule(170, MOTOR_TURN, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, -70),
                                                 (MOTOR_RIGHT, -100)])
        self.protocol.schedule(50, MOTOR_LEFT, [(MOTOR_LEFT, -100),
                                                (MOTOR_RIGHT, -100)])

    def forward_right(self):
        """Move forward and to right"""
        self.protocol.schedule(240, MOTOR_TURN, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -70)])
        self.protocol.schedule(10, MOTOR_RIGHT, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)])

    def backward_left(self):
        """Move backward and to left"""
        self.protocol.schedule(10, MOTOR_LEFT, [(MOTOR_LEFT, 100),
                                                (MOTOR_RIGHT, 100)])
        self.protocol.schedule(190, MOTOR_TURN, [(MOTOR_TURN, 100),
                                                 (MOTOR_LEFT, 80),
                                                 (MOTOR_RIGHT, 100)])

    def backward_right(self):
        """Move backward and to right"""
        self.protocol.schedule(5, MOTOR_RIGHT, [(MOTOR_LEFT, 100),
                                                (MOTOR_RIGHT, 100)])
        self.protocol.schedule(230, MOTOR_TURN, [(MOTOR_TURN, -100),
                                                 (MOTOR_LEFT, 100),
                                                 (MOTOR_RIGHT, 60)])

    def sharp_left(self):
        """Move to a cell left"""
        self.protocol.schedule(35, MOTOR_TURN, [(MOTOR_TURN, -100),
                                                (MOTOR_LEFT, 100),
                                                (MOTOR_RIGHT, -100)])
        self.protocol.schedule(50, MOTOR_LEFT, [(MOTOR_LEFT, -100),
                                                (MOTOR_RIGHT, -100)])

    def sharp_right(self):
        """Move to a cell right"""
        self.protocol.schedule(50, MOTOR_TURN, [(MOTOR_TURN, 100),
                                                (MOTOR_LEFT, -100),
                                                (MOTOR_RIGHT, 100)])
        self.protocol.schedule(50, MOTOR_RIGHT, [(MOTOR_LEFT, -100),
                                                 (MOTOR_RIGHT, -100)])

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

    def g(self, x=-300):
        """Grab, negative x means release"""
        x = int(x)
        # This motor does not have rotary encoders
        self.protocol.move(abs(x), [(MOTOR_GRAB, 100 * sign(x))], time=True)

    def open_wide(self):
        self.world.grabber_open = True
        self.g(400)

    def open_narrow(self):
        self.g(200)

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

    def block_goal(self, enemy_num):
        self.strategy.block_goal(int(enemy_num))
